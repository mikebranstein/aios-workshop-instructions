"""Node wrapper for refactor planner logic in ArchReview loop.

This node class wraps the planner adapter invocation to fit the LangGraph node
pattern, handling refactor planning and creating refactor request issues.
"""

from datetime import datetime, timezone
from typing import List

from aios_orchestration_core.events.arch_review import ArchReviewEvent
from aios_orchestration_core.github.arch_review_gateway import ArchReviewGateway
from aios_orchestration_core.labels.arch_review_labels import (
    ARCH_REVIEW_CANONICAL_LABEL_BY_STATE,
    ARCH_REVIEW_CANONICAL_STATE_LABELS,
)
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.arch_review import ArchReviewState
from aios_orchestration_core.transitions.arch_review import get_next_arch_review_state


class ArchRefactorPlannerNode:
    """Invokes the planner adapter to create refactor requests for an issue.

    Accepted decisions: CREATE_REFACTOR_REQUESTS | DEFER | BLOCKED
    Transitions from ARCH_REFACTOR_PLANNED to the appropriate next state,
    creates refactor request issues if needed, and logs the transition.
    """

    def __init__(
        self,
        adapter: JudgmentLLMAdapter,
        gateway: ArchReviewGateway,
        log_store: TransitionLogStore,
    ) -> None:
        self.adapter = adapter
        self.gateway = gateway
        self.log_store = log_store

    def run(self, run_id: str, issue_number: int) -> tuple[ArchReviewState, List[int]]:
        """Execute refactor planner and return next state + created issue numbers.

        Args:
            run_id: Unique run identifier for logging.
            issue_number: GitHub issue number being planned.

        Returns:
            Tuple of (next_state, list_of_created_refactor_request_numbers)
        """
        issue = self.gateway.get_issue(issue_number)
        result = self.adapter.invoke_json(
            "arch_refactor_plan",
            {"issue_number": issue.number, "title": issue.title},
        )

        plan_decision = result.payload["decision"]
        plan_event_map = {
            "CREATE_REFACTOR_REQUESTS": ArchReviewEvent.REFACTOR_REQUESTS_CREATED,
            "DEFER": ArchReviewEvent.REFACTOR_DEFERRED,
            "BLOCKED": ArchReviewEvent.REFACTOR_BLOCKED,
        }
        plan_event = plan_event_map[plan_decision]

        # Create refactor requests if needed
        created_refactor_numbers: List[int] = []
        if plan_decision == "CREATE_REFACTOR_REQUESTS":
            for req in result.payload.get("refactor_requests", []):
                n = self.gateway.create_refactor_request(
                    req["title"], req["body"], issue_number
                )
                created_refactor_numbers.append(n)

        next_state = get_next_arch_review_state(
            ArchReviewState.ARCH_REFACTOR_PLANNED, plan_event
        )

        # Set state label
        self.gateway.set_state_labels(
            issue_number,
            list(ARCH_REVIEW_CANONICAL_STATE_LABELS),
            [ARCH_REVIEW_CANONICAL_LABEL_BY_STATE[next_state]],
        )

        # Log transition
        entry = TransitionLogEntry(
            loop_id="arch_review",
            run_id=run_id,
            issue_number=issue_number,
            from_state=ArchReviewState.ARCH_REFACTOR_PLANNED.value,
            to_state=next_state.value,
            trigger_event=plan_event.value,
            reason_code=f"ARCH_PLAN_{plan_decision}",
            reason_detail=result.payload.get("reason", "Architecture refactor planning"),
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            adapter_source=self.adapter.adapter_source,
        )
        self.log_store.append(entry)
        self.gateway.post_comment(issue_number, entry.to_comment())

        return next_state, created_refactor_numbers