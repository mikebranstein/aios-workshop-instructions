"""ArchReview run_once orchestrator using LangGraph.

Refactored to use ArchReviewGraphOrchestrator (LangGraph implementation) instead
of inline orchestration logic. Maintains circuit breaker and retry policies for
resilience and error handling.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from aios_orchestration_core.core.circuit_breaker import BlockContext
from aios_orchestration_core.github.arch_review_gateway import ArchReviewGateway
from aios_orchestration_core.labels.arch_review_labels import (
    ARCH_REVIEW_CANONICAL_LABEL_BY_STATE,
    ARCH_REVIEW_CANONICAL_STATE_LABELS,
    normalize_arch_review_state_from_labels,
)
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.policies.retry import RetryPolicy, RetryState
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.arch_review import (
    ArchReviewState,
    TERMINAL_ARCH_REVIEW_STATES,
)
from arch_review_orchestrator.circuit_breaker import ArchReviewCircuitBreaker
from arch_review_orchestrator.langgraph_arch_review_graph import (
    ArchReviewGraphOrchestrator,
    ArchReviewRunState,
)


@dataclass
class ArchReviewRunRecord:
    """Record of one architecture review run."""

    run_id: str
    source_issue_number: int
    started_at_utc: str
    ended_at_utc: Optional[str] = None
    created_refactor_request_numbers: List[int] = field(default_factory=list)


@dataclass
class ArchReviewRunRegistry:
    """Registry of ArchReview runs by source issue number."""

    by_source_issue: Dict[int, ArchReviewRunRecord] = field(default_factory=dict)
    retry_state_by_issue: Dict[int, RetryState] = field(default_factory=dict)

    def start_new_run(self, source_issue_number: int) -> ArchReviewRunRecord:
        """Create and register a new ArchReview run."""
        record = ArchReviewRunRecord(
            run_id=str(uuid4()),
            source_issue_number=source_issue_number,
            started_at_utc=datetime.now(timezone.utc).isoformat(),
        )
        self.by_source_issue[source_issue_number] = record
        return record


class ArchReviewRunOnceOrchestrator:
    """Bounded architecture review orchestrator using LangGraph.

    Drives one arch-review issue through: pending → in-progress → outcome.
    If FITNESS_WARN, invokes the refactor planner before closing.
    Orchestration is managed by LangGraph StateGraph via ArchReviewGraphOrchestrator.
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
        self.circuit_breaker = ArchReviewCircuitBreaker(
            retry_policy or RetryPolicy(max_attempts=3), log_store
        )

        # Create LangGraph orchestrator
        self.graph_orchestrator = ArchReviewGraphOrchestrator(
            gateway=gateway,
            log_store=log_store,
            review_adapter=review_adapter,
            planner_adapter=planner_adapter,
        )

    def run_once(self, source_issue_number: int) -> ArchReviewRunRecord:
        """Execute one bounded architecture review run via LangGraph.

        Args:
            source_issue_number: GitHub issue number to review.

        Returns:
            ArchReviewRunRecord with run details and outcomes.
        """
        run = self.run_registry.start_new_run(source_issue_number)
        retry_state = self.run_registry.retry_state_by_issue.setdefault(
            source_issue_number, RetryState()
        )
        current_state = None

        try:
            # Normalize initial state from labels
            issue = self.gateway.get_issue(source_issue_number)
            normalized = normalize_arch_review_state_from_labels(issue.labels)
            current_state = (
                normalized.state or ArchReviewState.ARCH_REVIEW_PENDING
            )

            # Check if already terminal
            if current_state in TERMINAL_ARCH_REVIEW_STATES:
                run.ended_at_utc = datetime.now(timezone.utc).isoformat()
                return run

            # Prepare initial state for graph
            initial_state: ArchReviewRunState = {
                "run_id": run.run_id,
                "source_issue_number": source_issue_number,
                "current_state": current_state,
                "created_refactor_request_numbers": [],
            }

            # Invoke graph orchestrator
            final_state = self.graph_orchestrator.invoke(initial_state)

            # Update run record with results
            run.ended_at_utc = datetime.now(timezone.utc).isoformat()
            run.created_refactor_request_numbers = final_state.get(
                "created_refactor_request_numbers", []
            )

            retry_state.attempts = 0

        except Exception as ex:
            # Handle circuit breaker on error
            if current_state is None:
                current_state = ArchReviewState.ARCH_REVIEW_PENDING

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
            if resulting == ArchReviewState.ARCH_REVIEW_NEEDS_HUMAN:
                self.gateway.set_state_labels(
                    source_issue_number,
                    list(ARCH_REVIEW_CANONICAL_STATE_LABELS),
                    [
                        ARCH_REVIEW_CANONICAL_LABEL_BY_STATE[
                            ArchReviewState.ARCH_REVIEW_NEEDS_HUMAN
                        ]
                    ],
                )

        run.ended_at_utc = datetime.now(timezone.utc).isoformat()
        return run