from datetime import datetime, timezone

from aios_orchestration_core.events.foundation import FoundationEvent
from aios_orchestration_core.github.foundation_gateway import FoundationGateway
from aios_orchestration_core.labels.foundation_labels import FOUNDATION_CANONICAL_LABEL_BY_STATE, FOUNDATION_CANONICAL_STATE_LABELS
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.runlog.sqlite_store import TransitionLogStore
from aios_orchestration_core.states.foundation import FoundationState
from aios_orchestration_core.transitions.foundation import get_next_foundation_state

_DECISION_MAP = {
    "APPROVE_FOUNDATION": FoundationEvent.APPROVE_FOUNDATION,
    "REVISE_FOUNDATION": FoundationEvent.REVISE_FOUNDATION,
    "BLOCK_FOUNDATION": FoundationEvent.BLOCK_FOUNDATION,
}


class FoundationGateNode:
    def __init__(self, adapter: JudgmentLLMAdapter, gateway: FoundationGateway, log_store: TransitionLogStore) -> None:
        self.adapter, self.gateway, self.log_store = adapter, gateway, log_store

    def run(self, run_id: str, issue_number: int) -> FoundationState:
        issue = self.gateway.get_issue(issue_number)
        result = self.adapter.invoke_json(
            "foundation_gate",
            {"issue_number": issue.number, "title": issue.title, "body": issue.body},
        )
        decision = result.payload["decision"]
        event = _DECISION_MAP[decision]
        next_state = get_next_foundation_state(FoundationState.FOUNDATION_REVIEW, event)

        self.gateway.set_state_labels(issue_number, list(FOUNDATION_CANONICAL_STATE_LABELS), [FOUNDATION_CANONICAL_LABEL_BY_STATE[next_state]])

        if next_state == FoundationState.FOUNDATION_APPROVED:
            self.gateway.close_issue(issue_number, "foundation approved")

        entry = TransitionLogEntry(
            loop_id="foundation", run_id=run_id, issue_number=issue_number,
            from_state=FoundationState.FOUNDATION_REVIEW.value, to_state=next_state.value,
            trigger_event=event.value, reason_code=f"FOUNDATION_GATE_{decision}",
            reason_detail=result.payload.get("reason", ""), timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )
        self.log_store.append(entry)
        self.gateway.post_comment(issue_number, entry.to_comment())
        return next_state
