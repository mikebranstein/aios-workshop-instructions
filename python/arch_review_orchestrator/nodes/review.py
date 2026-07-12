"""Node wrapper for architecture review logic in ArchReview loop.

This node class wraps the review adapter invocation to fit the LangGraph node
pattern, handling review evaluation and state transitions.
"""

from datetime import datetime, timezone

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


class ArchReviewNode:
    """Invokes the review adapter to evaluate an architecture review issue.

    Accepted decisions: NO_ACTION | CREATE_REFACTOR_PLAN | ESCALATE
    Transitions from ARCH_REVIEW_IN_PROGRESS to the appropriate next state and
    writes a TransitionLogEntry + GitHub comment.
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

    def run(self, run_id: str, issue_number: int) -> ArchReviewState:
        """Execute review evaluation and return next state.

        Args:
            run_id: Unique run identifier for logging.
            issue_number: GitHub issue number to review.

        Returns:
            Next ArchReviewState after evaluation.
        """
        issue = self.gateway.get_issue(issue_number)
        result = self.adapter.invoke_json(
            "arch_review",
            {"issue_number": issue.number, "title": issue.title},
        )

        decision = result.payload["decision"]
        event_map = {
            "NO_ACTION": ArchReviewEvent.FITNESS_PASS,
            "CREATE_REFACTOR_PLAN": ArchReviewEvent.FITNESS_WARN,
            "ESCALATE": ArchReviewEvent.FITNESS_FAIL_CRITICAL,
        }
        event = event_map[decision]

        next_state = get_next_arch_review_state(
            ArchReviewState.ARCH_REVIEW_IN_PROGRESS, event
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
            from_state=ArchReviewState.ARCH_REVIEW_IN_PROGRESS.value,
            to_state=next_state.value,
            trigger_event=event.value,
            reason_code=f"ARCH_REVIEW_{decision}",
            reason_detail=result.payload.get("reason", "Architecture review evaluation"),
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            adapter_source=self.adapter.adapter_source,
        )
        self.log_store.append(entry)
        self.gateway.post_comment(issue_number, entry.to_comment())

        return next_state