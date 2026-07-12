from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional
from uuid import uuid4

from aios_orchestration_core.core.circuit_breaker import BlockContext
from aios_orchestration_core.events.arch_review import ArchReviewEvent
from aios_orchestration_core.github.arch_review_gateway import ArchReviewGateway
from aios_orchestration_core.labels.arch_review_labels import (
    ARCH_REVIEW_CANONICAL_LABEL_BY_STATE,
    ARCH_REVIEW_CANONICAL_STATE_LABELS,
    ARCH_REVIEW_LABEL_REGISTRY,
)
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.policies.retry import RetryPolicy, RetryState
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.arch_review import ArchReviewState, TERMINAL_ARCH_REVIEW_STATES
from aios_orchestration_core.transitions.arch_review import get_next_arch_review_state
from arch_review_orchestrator.circuit_breaker import ArchReviewCircuitBreaker


@dataclass
class ArchReviewRunRecord:
    run_id: str
    source_issue_number: int
    started_at_utc: str
    ended_at_utc: Optional[str] = None
    created_refactor_request_numbers: List[int] = field(default_factory=list)


@dataclass
class ArchReviewRunRegistry:
    by_source_issue: Dict[int, ArchReviewRunRecord] = field(default_factory=dict)
    retry_state_by_issue: Dict[int, RetryState] = field(default_factory=dict)

    def start_new_run(self, source_issue_number: int) -> ArchReviewRunRecord:
        record = ArchReviewRunRecord(
            run_id=str(uuid4()),
            source_issue_number=source_issue_number,
            started_at_utc=datetime.now(timezone.utc).isoformat(),
        )
        self.by_source_issue[source_issue_number] = record
        return record


def _normalize_arch_review_state(labels: Iterable[str]) -> Optional[ArchReviewState]:
    canonical_hits, all_hits = set(), set()
    for label in labels:
        state = ARCH_REVIEW_LABEL_REGISTRY.state_for_label(label)
        if state is not None:
            all_hits.add(state)
            if label in ARCH_REVIEW_LABEL_REGISTRY.all_canonical_labels:
                canonical_hits.add(state)
    if len(canonical_hits) == 1:
        return next(iter(canonical_hits))
    if len(all_hits) == 1:
        return next(iter(all_hits))
    return None


class ArchReviewRunOnceOrchestrator:
    """Bounded architecture review orchestrator.

    Drives one arch-review issue through: pending → in-progress → outcome.
    If FITNESS_WARN, invokes the refactor planner before closing.
    """

    def __init__(
        self,
        gateway: ArchReviewGateway,
        log_store: TransitionLogStore,
        run_registry: ArchReviewRunRegistry,
        review_adapter: JudgmentLLMAdapter,
        planner_adapter: JudgmentLLMAdapter,
        retry_policy: Optional[RetryPolicy] = None,
    ) -> None:
        self.gateway = gateway
        self.log_store = log_store
        self.run_registry = run_registry
        self.review_adapter = review_adapter
        self.planner_adapter = planner_adapter
        self.circuit_breaker = ArchReviewCircuitBreaker(retry_policy or RetryPolicy(max_attempts=3), log_store)

    def run_once(self, source_issue_number: int) -> ArchReviewRunRecord:
        run = self.run_registry.start_new_run(source_issue_number)
        issue = self.gateway.get_issue(source_issue_number)
        current_state = _normalize_arch_review_state(issue.labels) or ArchReviewState.ARCH_REVIEW_PENDING
        retry_state = self.run_registry.retry_state_by_issue.setdefault(source_issue_number, RetryState())

        try:
            if current_state in TERMINAL_ARCH_REVIEW_STATES:
                run.ended_at_utc = datetime.now(timezone.utc).isoformat()
                return run

            if current_state == ArchReviewState.ARCH_REVIEW_PENDING:
                next_state = get_next_arch_review_state(ArchReviewState.ARCH_REVIEW_PENDING, ArchReviewEvent.EVALUATION_STARTED)
                self._apply(run.run_id, source_issue_number, ArchReviewState.ARCH_REVIEW_PENDING, next_state, ArchReviewEvent.EVALUATION_STARTED, "EVALUATION_STARTED", "Starting architecture review")
                current_state = next_state

            if current_state == ArchReviewState.ARCH_REVIEW_IN_PROGRESS:
                result = self.review_adapter.invoke_json("arch_review", {"issue_number": issue.number, "title": issue.title})
                decision = result.payload["decision"]
                event_map = {
                    "NO_ACTION": ArchReviewEvent.FITNESS_PASS,
                    "CREATE_REFACTOR_PLAN": ArchReviewEvent.FITNESS_WARN,
                    "ESCALATE": ArchReviewEvent.FITNESS_FAIL_CRITICAL,
                }
                event = event_map[decision]
                next_state = get_next_arch_review_state(ArchReviewState.ARCH_REVIEW_IN_PROGRESS, event)
                self._apply(run.run_id, source_issue_number, ArchReviewState.ARCH_REVIEW_IN_PROGRESS, next_state, event, f"ARCH_REVIEW_{decision}", result.payload.get("reason", ""))
                current_state = next_state

            if current_state == ArchReviewState.ARCH_REFACTOR_PLANNED:
                result = self.planner_adapter.invoke_json("arch_refactor_plan", {"issue_number": issue.number, "title": issue.title})
                plan_decision = result.payload["decision"]
                plan_event_map = {
                    "CREATE_REFACTOR_REQUESTS": ArchReviewEvent.REFACTOR_REQUESTS_CREATED,
                    "DEFER": ArchReviewEvent.REFACTOR_DEFERRED,
                    "BLOCKED": ArchReviewEvent.REFACTOR_BLOCKED,
                }
                plan_event = plan_event_map[plan_decision]
                if plan_decision == "CREATE_REFACTOR_REQUESTS":
                    for req in result.payload.get("refactor_requests", []):
                        n = self.gateway.create_refactor_request(req["title"], req["body"], source_issue_number)
                        run.created_refactor_request_numbers.append(n)
                next_state = get_next_arch_review_state(ArchReviewState.ARCH_REFACTOR_PLANNED, plan_event)
                self._apply(run.run_id, source_issue_number, ArchReviewState.ARCH_REFACTOR_PLANNED, next_state, plan_event, f"ARCH_PLAN_{plan_decision}", result.payload.get("reason", ""))
                current_state = next_state

            if current_state in TERMINAL_ARCH_REVIEW_STATES:
                self.gateway.close_issue(source_issue_number, "arch review complete")

            retry_state.attempts = 0

        except Exception as ex:
            resulting = self.circuit_breaker.handle_failure(
                run_id=run.run_id, issue_number=source_issue_number, from_state=current_state,
                retry_state=retry_state,
                context=BlockContext(blocked_stage=current_state.value, reason_code="RUN_ONCE_NODE_FAILURE", reason_detail=str(ex), last_error_class=type(ex).__name__),
            )
            if resulting == ArchReviewState.ARCH_REVIEW_NEEDS_HUMAN:
                self.gateway.set_state_labels(source_issue_number, list(ARCH_REVIEW_CANONICAL_STATE_LABELS), [ARCH_REVIEW_CANONICAL_LABEL_BY_STATE[ArchReviewState.ARCH_REVIEW_NEEDS_HUMAN]])

        run.ended_at_utc = datetime.now(timezone.utc).isoformat()
        return run

    def _apply(self, run_id, issue_number, from_state, to_state, event, reason_code, reason_detail):
        self.gateway.set_state_labels(issue_number, list(ARCH_REVIEW_CANONICAL_STATE_LABELS), [ARCH_REVIEW_CANONICAL_LABEL_BY_STATE[to_state]])
        entry = TransitionLogEntry(
            loop_id="arch_review", run_id=run_id, issue_number=issue_number,
            from_state=from_state.value, to_state=to_state.value, trigger_event=event.value,
            reason_code=reason_code, reason_detail=reason_detail, timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )
        self.log_store.append(entry)
        self.gateway.post_comment(issue_number, entry.to_comment())
