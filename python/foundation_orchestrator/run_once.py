from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional
from uuid import uuid4

from aios_orchestration_core.core.circuit_breaker import BlockContext
from aios_orchestration_core.events.foundation import FoundationEvent
from aios_orchestration_core.github.foundation_gateway import FoundationGateway
from aios_orchestration_core.labels.foundation_labels import (
    FOUNDATION_CANONICAL_LABEL_BY_STATE,
    FOUNDATION_CANONICAL_STATE_LABELS,
    FOUNDATION_LABEL_REGISTRY,
)
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.policies.retry import RetryPolicy, RetryState
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.foundation import FoundationState, TERMINAL_FOUNDATION_STATES
from aios_orchestration_core.transitions.foundation import get_next_foundation_state
from foundation_orchestrator.circuit_breaker import FoundationCircuitBreaker
from foundation_orchestrator.nodes.gate import FoundationGateNode
from foundation_orchestrator.nodes.research import FoundationResearchNode


@dataclass
class FoundationRunRecord:
    run_id: str
    source_issue_number: int
    started_at_utc: str
    ended_at_utc: Optional[str] = None
    cycle_count: int = 0


@dataclass
class FoundationRunRegistry:
    by_source_issue: Dict[int, FoundationRunRecord] = field(default_factory=dict)
    retry_state_by_issue: Dict[int, RetryState] = field(default_factory=dict)

    def start_new_run(self, source_issue_number: int) -> FoundationRunRecord:
        record = FoundationRunRecord(
            run_id=str(uuid4()),
            source_issue_number=source_issue_number,
            started_at_utc=datetime.now(timezone.utc).isoformat(),
        )
        self.by_source_issue[source_issue_number] = record
        return record


def _normalize_foundation_state(labels: Iterable[str]) -> Optional[FoundationState]:
    canonical_hits, all_hits = set(), set()
    for label in labels:
        state = FOUNDATION_LABEL_REGISTRY.state_for_label(label)
        if state is not None:
            all_hits.add(state)
            if label in FOUNDATION_LABEL_REGISTRY.all_canonical_labels:
                canonical_hits.add(state)
    if len(canonical_hits) == 1:
        return next(iter(canonical_hits))
    if len(all_hits) == 1:
        return next(iter(all_hits))
    return None


class FoundationRunOnceOrchestrator:
    """Bounded foundation orchestrator.  Advances one issue through the
    foundation pipeline; stops when approved, blocked, or max_cycles reached.
    """

    def __init__(
        self,
        gateway: FoundationGateway,
        log_store: TransitionLogStore,
        run_registry: FoundationRunRegistry,
        research_adapter: JudgmentLLMAdapter,
        gate_adapter: JudgmentLLMAdapter,
        retry_policy: Optional[RetryPolicy] = None,
        max_cycles: int = 5,
    ) -> None:
        self.gateway = gateway
        self.log_store = log_store
        self.run_registry = run_registry
        self.max_cycles = max_cycles
        self.research_node = FoundationResearchNode(research_adapter, gateway, log_store)
        self.gate_node = FoundationGateNode(gate_adapter, gateway, log_store)
        self.circuit_breaker = FoundationCircuitBreaker(retry_policy or RetryPolicy(max_attempts=3), log_store)

    def run_once(self, source_issue_number: int) -> FoundationRunRecord:
        run = self.run_registry.start_new_run(source_issue_number)
        issue = self.gateway.get_issue(source_issue_number)
        current_state = _normalize_foundation_state(issue.labels) or FoundationState.FOUNDATION_NEEDED
        retry_state = self.run_registry.retry_state_by_issue.setdefault(source_issue_number, RetryState())

        try:
            while run.cycle_count < self.max_cycles:
                if current_state in TERMINAL_FOUNDATION_STATES:
                    break
                run.cycle_count += 1

                if current_state == FoundationState.FOUNDATION_NEEDED:
                    next_state = get_next_foundation_state(FoundationState.FOUNDATION_NEEDED, FoundationEvent.FOUNDATION_STARTED)
                    self._apply(run.run_id, source_issue_number, FoundationState.FOUNDATION_NEEDED, next_state, FoundationEvent.FOUNDATION_STARTED, "FOUNDATION_STARTED", "Starting foundation research")
                    current_state = next_state

                if current_state == FoundationState.FOUNDATION_IN_PROGRESS:
                    current_state = self.research_node.run(run.run_id, source_issue_number)
                    if current_state == FoundationState.FOUNDATION_IN_PROGRESS:
                        continue  # NEEDS_MORE_RESEARCH cycles

                if current_state == FoundationState.FOUNDATION_REVIEW:
                    current_state = self.gate_node.run(run.run_id, source_issue_number)
                    if current_state == FoundationState.FOUNDATION_IN_PROGRESS:
                        continue  # REVISE cycles

                break

            retry_state.attempts = 0

        except Exception as ex:
            resulting = self.circuit_breaker.handle_failure(
                run_id=run.run_id, issue_number=source_issue_number, from_state=current_state,
                retry_state=retry_state,
                context=BlockContext(blocked_stage=current_state.value, reason_code="RUN_ONCE_NODE_FAILURE", reason_detail=str(ex), last_error_class=type(ex).__name__),
            )
            if resulting == FoundationState.FOUNDATION_NEEDS_HUMAN:
                self.gateway.set_state_labels(source_issue_number, list(FOUNDATION_CANONICAL_STATE_LABELS), [FOUNDATION_CANONICAL_LABEL_BY_STATE[FoundationState.FOUNDATION_NEEDS_HUMAN]])

        run.ended_at_utc = datetime.now(timezone.utc).isoformat()
        return run

    def _apply(self, run_id, issue_number, from_state, to_state, event, reason_code, reason_detail):
        self.gateway.set_state_labels(issue_number, list(FOUNDATION_CANONICAL_STATE_LABELS), [FOUNDATION_CANONICAL_LABEL_BY_STATE[to_state]])
        entry = TransitionLogEntry(
            loop_id="foundation", run_id=run_id, issue_number=issue_number,
            from_state=from_state.value, to_state=to_state.value, trigger_event=event.value,
            reason_code=reason_code, reason_detail=reason_detail, timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )
        self.log_store.append(entry)
        self.gateway.post_comment(issue_number, entry.to_comment())
