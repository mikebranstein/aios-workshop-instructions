from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

from aios_orchestration_core.core.circuit_breaker import BlockContext
from aios_orchestration_core.github.dev_gateway import DevGateway
from aios_orchestration_core.labels.dev_labels import (
    DEV_CANONICAL_LABEL_BY_STATE,
    DEV_CANONICAL_STATE_LABELS,
    normalize_dev_state_from_labels,
)
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.policies.retry import RetryPolicy, RetryState
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.dev import DevState
from dev_orchestrator.circuit_breaker import DevCircuitBreaker
from dev_orchestrator.langgraph_dev_graph import DevGraphOrchestrator


@dataclass
class DevRunRecord:
    run_id: str
    source_issue_number: int
    started_at_utc: str
    ended_at_utc: Optional[str] = None
    cycle_count: int = 0
    current_state: Optional[str] = None


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


class DevRunOnceOrchestrator:
    """Single-issue Dev run_once flow.

    Advances a feature-request issue through the full dev pipeline in one
    invocation using LangGraph. Feedback loops (DESIGN_REVISE → INTAKE, QA_FAILED → DESIGN)
    are handled by conditional edges.
    
    Circuit breaker remains outside the graph for error handling.
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
        self.graph_orchestrator = DevGraphOrchestrator(
            gateway,
            log_store,
            intake_adapter,
            design_adapter,
            build_adapter,
            qa_adapter,
            policy_adapter,
        )
        self.circuit_breaker = DevCircuitBreaker(
            retry_policy or RetryPolicy(max_attempts=3), log_store
        )

    def run_once(self, source_issue_number: int) -> DevRunRecord:
        run = self.run_registry.start_new_run(source_issue_number)
        retry_state = self.run_registry.retry_state_by_issue.setdefault(
            source_issue_number, RetryState()
        )

        try:
            final_state = self.graph_orchestrator.invoke({
                "run_id": run.run_id,
                "source_issue_number": source_issue_number,
            })
            resulting_state = final_state.get("current_state", self._get_current_state(source_issue_number))
            
            run.cycle_count = 1
            retry_state.attempts = 0

        except Exception as ex:
            current_state = self._get_current_state(source_issue_number)
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
        run.current_state = resulting_state.value if hasattr(resulting_state, "value") else str(resulting_state)
        return run

    def _get_current_state(self, issue_number: int) -> DevState:
        """Fetch current state from GitHub labels."""
        issue = self.gateway.get_issue(issue_number)
        normalized = normalize_dev_state_from_labels(issue.labels)
        return normalized.state or DevState.DEV_INTAKE