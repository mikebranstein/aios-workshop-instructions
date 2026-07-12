from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional
from uuid import uuid4

from aios_orchestration_core.core.circuit_breaker import BlockContext
from aios_orchestration_core.github.dev_gateway import DevGateway
from aios_orchestration_core.labels.dev_labels import (
    DEV_CANONICAL_LABEL_BY_STATE,
    DEV_CANONICAL_STATE_LABELS,
    DEV_LABEL_REGISTRY,
)
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.policies.retry import RetryPolicy, RetryState
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.runlog.sqlite_store import TransitionLogStore
from aios_orchestration_core.states.dev import DevState, TERMINAL_DEV_STATES
from dev_orchestrator.circuit_breaker import DevCircuitBreaker
from dev_orchestrator.nodes.build import DevBuildNode
from dev_orchestrator.nodes.design import DevDesignNode
from dev_orchestrator.nodes.intake import DevIntakeNode
from dev_orchestrator.nodes.policy import DevPolicyNode
from dev_orchestrator.nodes.qa import DevQANode


@dataclass
class DevRunRecord:
    run_id: str
    source_issue_number: int
    started_at_utc: str
    ended_at_utc: Optional[str] = None
    cycle_count: int = 0


@dataclass
class DevRunRegistry:
    by_source_issue: Dict[int, DevRunRecord] = field(default_factory=dict)
    retry_state_by_issue: Dict[int, RetryState] = field(default_factory=dict)

    def start_new_run(self, source_issue_number: int) -> DevRunRecord:
        record = DevRunRecord(
            run_id=str(uuid4()),
            source_issue_number=source_issue_number,
            started_at_utc=datetime.now(timezone.utc).isoformat(),
        )
        self.by_source_issue[source_issue_number] = record
        return record


def _normalize_dev_state(labels: Iterable[str]) -> Optional[DevState]:
    canonical_hits = set()
    all_hits = set()
    for label in labels:
        state = DEV_LABEL_REGISTRY.state_for_label(label)
        if state is not None:
            all_hits.add(state)
            if label in DEV_LABEL_REGISTRY.all_canonical_labels:
                canonical_hits.add(state)
    if len(canonical_hits) == 1:
        return next(iter(canonical_hits))
    if len(all_hits) == 1:
        return next(iter(all_hits))
    return None


class DevRunOnceOrchestrator:
    """Single-issue Dev run_once flow.

    Advances a feature-request issue through the full dev pipeline in one
    invocation.  Feedback loops (DESIGN_REVISE → INTAKE, QA_FAILED → DESIGN)
    are bounded by ``max_cycles`` to prevent runaway loops.
    """

    def __init__(
        self,
        gateway: DevGateway,
        log_store: TransitionLogStore,
        run_registry: DevRunRegistry,
        intake_adapter: JudgmentLLMAdapter,
        design_adapter: JudgmentLLMAdapter,
        build_adapter: JudgmentLLMAdapter,
        qa_adapter: JudgmentLLMAdapter,
        policy_adapter: JudgmentLLMAdapter,
        retry_policy: Optional[RetryPolicy] = None,
        max_cycles: int = 3,
    ) -> None:
        self.gateway = gateway
        self.log_store = log_store
        self.run_registry = run_registry
        self.max_cycles = max_cycles
        self.intake_node = DevIntakeNode(intake_adapter, gateway, log_store)
        self.design_node = DevDesignNode(design_adapter, gateway, log_store)
        self.build_node = DevBuildNode(build_adapter, gateway, log_store)
        self.qa_node = DevQANode(qa_adapter, gateway, log_store)
        self.policy_node = DevPolicyNode(policy_adapter, gateway, log_store)
        self.circuit_breaker = DevCircuitBreaker(retry_policy or RetryPolicy(max_attempts=3), log_store)

    def run_once(self, source_issue_number: int) -> DevRunRecord:
        run = self.run_registry.start_new_run(source_issue_number)
        issue = self.gateway.get_issue(source_issue_number)
        current_state = _normalize_dev_state(issue.labels) or DevState.DEV_INTAKE
        retry_state = self.run_registry.retry_state_by_issue.setdefault(
            source_issue_number, RetryState()
        )

        try:
            while run.cycle_count < self.max_cycles:
                if current_state in TERMINAL_DEV_STATES:
                    break
                run.cycle_count += 1

                if current_state == DevState.DEV_INTAKE:
                    current_state = self.intake_node.run(run.run_id, source_issue_number)

                if current_state in TERMINAL_DEV_STATES:
                    break

                if current_state == DevState.DEV_DESIGN:
                    current_state = self.design_node.run(run.run_id, source_issue_number)
                    if current_state == DevState.DEV_INTAKE:
                        continue  # feedback loop: back to top of while

                if current_state in TERMINAL_DEV_STATES:
                    break

                if current_state == DevState.DEV_BUILD:
                    current_state = self.build_node.run(run.run_id, source_issue_number)

                if current_state in TERMINAL_DEV_STATES:
                    break

                if current_state == DevState.DEV_QA:
                    current_state = self.qa_node.run(run.run_id, source_issue_number)
                    if current_state == DevState.DEV_DESIGN:
                        continue  # feedback loop: back to top of while

                if current_state in TERMINAL_DEV_STATES:
                    break

                if current_state == DevState.DEV_POLICY:
                    current_state = self.policy_node.run(run.run_id, source_issue_number)

                break  # all stages complete for this cycle

            retry_state.attempts = 0

        except Exception as ex:
            resulting_state = self.circuit_breaker.handle_failure(
                run_id=run.run_id,
                issue_number=source_issue_number,
                from_state=current_state,
                retry_state=retry_state,
                context=BlockContext(
                    blocked_stage=current_state.value,
                    reason_code="RUN_ONCE_NODE_FAILURE",
                    reason_detail=str(ex),
                    last_error_class=type(ex).__name__,
                ),
            )
            if resulting_state == DevState.DEV_NEEDS_HUMAN:
                self.gateway.set_state_labels(
                    source_issue_number,
                    list(DEV_CANONICAL_STATE_LABELS),
                    [DEV_CANONICAL_LABEL_BY_STATE[DevState.DEV_NEEDS_HUMAN]],
                )
                self.gateway.post_comment(
                    source_issue_number,
                    "Dev run_once: transitioned to needs-human after retry threshold",
                )

        run.ended_at_utc = datetime.now(timezone.utc).isoformat()
        return run
