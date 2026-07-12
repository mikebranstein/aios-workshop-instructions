from datetime import datetime, timezone

from aios_orchestration_core.events.po import POEvent
from aios_orchestration_core.github.po_gateway import POGateway
from aios_orchestration_core.labels.po_labels import PO_CANONICAL_LABEL_BY_STATE, PO_CANONICAL_STATE_LABELS
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.po import POState
from aios_orchestration_core.transitions.po import get_next_po_state


class POPrioritizeNode:
    """Invokes the LLM to make the PO prioritization decision for one opportunity.

    Accepted decisions: CREATE_FEATURE_REQUESTS | DEFER | REJECT
    Transitions from PO_PRIORITIZING to the appropriate next state and
    writes a TransitionLogEntry + GitHub comment.
    """

    def __init__(
        self,
        adapter: JudgmentLLMAdapter,
        gateway: POGateway,
        log_store: TransitionLogStore,
    ) -> None:
        self.adapter = adapter
        self.gateway = gateway
        self.log_store = log_store

    def run(self, run_id: str, issue_number: int) -> POState:
        issue = self.gateway.get_issue(issue_number)
        result = self.adapter.invoke_json(
            "po_prioritize",
            {"issue_number": issue.number, "title": issue.title, "body": issue.body},
        )

        decision = result.payload["decision"]
        event = {
            "CREATE_FEATURE_REQUESTS": POEvent.PRIORITIZATION_CREATE,
            "DEFER": POEvent.PRIORITIZATION_DEFER,
            "REJECT": POEvent.PRIORITIZATION_REJECT,
        }[decision]

        next_state = get_next_po_state(POState.PO_PRIORITIZING, event)

        self.gateway.set_state_labels(
            issue_number,
            list(PO_CANONICAL_STATE_LABELS),
            [PO_CANONICAL_LABEL_BY_STATE[next_state]],
        )

        if next_state in {POState.PO_DEFERRED, POState.PO_REJECTED}:
            self.gateway.close_issue(issue_number, "not planned")

        entry = TransitionLogEntry(
            loop_id="po",
            run_id=run_id,
            issue_number=issue_number,
            from_state=POState.PO_PRIORITIZING.value,
            to_state=next_state.value,
            trigger_event=event.value,
            reason_code=f"PO_PRIORITIZE_{decision}",
            reason_detail=result.payload.get("reason", "PO prioritization decision"),
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            adapter_source=self.adapter.adapter_source,
        )
        self.log_store.append(entry)
        self.gateway.post_comment(issue_number, entry.to_comment())
        return next_state
