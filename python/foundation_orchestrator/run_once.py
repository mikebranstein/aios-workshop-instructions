from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

from aios_orchestration_core.core.circuit_breaker import BlockContext
from aios_orchestration_core.github.foundation_gateway import FoundationGateway
from aios_orchestration_core.labels.foundation_labels import (
    FOUNDATION_CANONICAL_LABEL_BY_STATE,
    FOUNDATION_CANONICAL_STATE_LABELS,
    normalize_foundation_state_from_labels,
)
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.policies.retry import RetryPolicy, RetryState
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.foundation import FoundationState
from foundation_orchestrator.circuit_breaker import FoundationCircuitBreaker
from foundation_orchestrator.langgraph_foundation_graph import FoundationGraphOrchestrator


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


class FoundationRunOnceOrchestrator:
    """Bounded foundation orchestrator. Advances one issue through the
    foundation pipeline; stops when approved, blocked, or max_cycles reached.
    
    Uses LangGraph StateGraph to handle state transitions and feedback loops.
    Circuit breaker remains outside the graph for error handling.
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
        self.graph_orchestrator = FoundationGraphOrchestrator(
            gateway, log_store, research_adapter, gate_adapter
        )
        self.circuit_breaker = FoundationCircuitBreaker(
            retry_policy or RetryPolicy(max_attempts=3), log_store
        )

    def run_once(self, source_issue_number: int) -> FoundationRunRecord:
        run = self.run_registry.start_new_run(source_issue_number)
        retry_state = self.run_registry.retry_state_by_issue.setdefault(
            source_issue_number, RetryState()
        )

        try:
            final_state = self.graph_orchestrator.invoke({
                "run_id": run.run_id,
                "source_issue_number": source_issue_number,
            })
            
            run.cycle_count = 1
            retry_state.attempts = 0

        except Exception as ex:
            current_state = self._get_current_state(source_issue_number)
            resulting = self.circuit_breaker.handle_failure(
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
            if resulting == FoundationState.FOUNDATION_NEEDS_HUMAN:
                self.gateway.set_state_labels(
                    source_issue_number,
                    list(FOUNDATION_CANONICAL_STATE_LABELS),
                    [FOUNDATION_CANONICAL_LABEL_BY_STATE[FoundationState.FOUNDATION_NEEDS_HUMAN]],
                )
                self.gateway.post_comment(
                    source_issue_number,
                    "Foundation run_once: transitioned to needs-human after retry threshold",
                )

        run.ended_at_utc = datetime.now(timezone.utc).isoformat()
        return run

    def _get_current_state(self, issue_number: int) -> FoundationState:
        """Fetch current state from GitHub labels."""
        issue = self.gateway.get_issue(issue_number)
        normalized = normalize_foundation_state_from_labels(issue.labels)
        return normalized.state or FoundationState.FOUNDATION_NEEDED