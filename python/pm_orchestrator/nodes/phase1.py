from dataclasses import dataclass
from datetime import datetime, timezone

from aios_orchestration_core.events.pm import PMEvent
from aios_orchestration_core.github.pm_gateway import PMGateway
from aios_orchestration_core.labels.pm_labels import PM_CANONICAL_LABEL_BY_STATE, PM_CANONICAL_STATE_LABELS, PM_LEGACY_LABEL_BY_STATE
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.runlog.sqlite_store import TransitionLogStore
from aios_orchestration_core.states.pm import PMState
from aios_orchestration_core.transitions.pm import get_next_pm_state


@dataclass
class Phase1Config:
    dual_write_legacy_labels: bool = True


class PMPhase1Node:
    def __init__(self, adapter: JudgmentLLMAdapter, gateway: PMGateway, log_store: TransitionLogStore, config: Phase1Config):
        self.adapter = adapter
        self.gateway = gateway
        self.log_store = log_store
        self.config = config

    def run(self, run_id: str, issue_number: int) -> PMState:
        issue = self.gateway.get_issue(issue_number)
        result = self.adapter.invoke_json(
            "pm_phase1",
            {"issue_number": issue.number, "title": issue.title, "body": issue.body},
            model_hint="copilot-standard",
        )

        decision = result.payload["decision"]
        event = {
            "PROVISIONAL_CHAMPION": PMEvent.PHASE1_PROVISIONAL_CHAMPION,
            "DEFER": PMEvent.PHASE1_DEFER,
            "BLOCK": PMEvent.PHASE1_BLOCK,
        }[decision]
        next_state = get_next_pm_state(PMState.PM_PHASE1_VALIDATING, event)

        labels_to_add = [PM_CANONICAL_LABEL_BY_STATE[next_state]]
        if self.config.dual_write_legacy_labels and next_state in PM_LEGACY_LABEL_BY_STATE:
            labels_to_add.append(PM_LEGACY_LABEL_BY_STATE[next_state])

        self.gateway.set_state_labels(issue_number, list(PM_CANONICAL_STATE_LABELS), labels_to_add)

        if next_state in {PMState.PM_DEFERRED, PMState.PM_BLOCKED}:
            self.gateway.close_issue(issue_number, "not planned")

        entry = TransitionLogEntry(
            run_id=run_id,
            issue_number=issue_number,
            from_state=PMState.PM_PHASE1_VALIDATING.value,
            to_state=next_state.value,
            trigger_event=event.value,
            reason_code=f"PM_PHASE1_{decision}",
            reason_detail=result.payload.get("reason", "PM phase1 decision"),
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )
        self.log_store.append(entry)
        self.gateway.post_comment(issue_number, entry.to_comment())
        return next_state
