from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

from aios_orchestration_core.events.pm import PMEvent
from aios_orchestration_core.github.pm_gateway import PMGitHubGateway
from aios_orchestration_core.labels.pm_labels import normalize_pm_state_from_labels
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.runlog.sqlite_store import TransitionLogStore
from aios_orchestration_core.states.pm import PMState
from aios_orchestration_core.transitions.pm import get_next_pm_state


@dataclass
class PMRunRecord:
    run_id: str
    source_issue_number: int
    linked_prior_run_id: Optional[str]
    started_at_utc: str
    ended_at_utc: Optional[str] = None


@dataclass
class PMRunRegistry:
    by_source_issue: Dict[int, PMRunRecord] = field(default_factory=dict)

    def start_new_run(self, source_issue_number: int, linked_prior_run_id: Optional[str]) -> PMRunRecord:
        record = PMRunRecord(
            run_id=str(uuid4()),
            source_issue_number=source_issue_number,
            linked_prior_run_id=linked_prior_run_id,
            started_at_utc=datetime.now(timezone.utc).isoformat(),
        )
        self.by_source_issue[source_issue_number] = record
        return record


class PMRunOnceOrchestrator:
    """Phase 4 shell. Node execution integration lands in later phases."""

    def __init__(self, gateway: PMGitHubGateway, log_store: TransitionLogStore, run_registry: PMRunRegistry):
        self.gateway = gateway
        self.log_store = log_store
        self.run_registry = run_registry

    def run_once(self, source_issue_number: int, external_resume_link_run_id: Optional[str] = None) -> PMRunRecord:
        run = self.run_registry.start_new_run(source_issue_number, linked_prior_run_id=external_resume_link_run_id)

        issue = self.gateway.get_issue(source_issue_number)
        normalized = normalize_pm_state_from_labels(issue.labels)
        current_state = normalized.state or PMState.PM_QUEUED

        # Skeleton transition: queued issues can move to phase 1 when foundation gate is externally satisfied.
        if current_state == PMState.PM_QUEUED and "foundation-approved" in issue.labels:
            next_state = get_next_pm_state(PMState.PM_QUEUED, PMEvent.FOUNDATION_GATE_PASSED)
            entry = TransitionLogEntry(
                run_id=run.run_id,
                issue_number=issue.number,
                from_state=current_state.value,
                to_state=next_state.value,
                trigger_event=PMEvent.FOUNDATION_GATE_PASSED.value,
                reason_code="FOUNDATION_GATE",
                reason_detail="Foundation gate present on source issue",
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            )
            self.log_store.append(entry)
            self.gateway.post_comment(issue.number, entry.to_comment())

        run.ended_at_utc = datetime.now(timezone.utc).isoformat()
        return run
