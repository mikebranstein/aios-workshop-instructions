from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from aios_orchestration_core.artifacts.feature_request import FeatureRequestArtifact
from aios_orchestration_core.events.po import POEvent
from aios_orchestration_core.github.po_gateway import POGateway
from aios_orchestration_core.labels.po_labels import PO_CANONICAL_LABEL_BY_STATE, PO_CANONICAL_STATE_LABELS
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.po import POState
from aios_orchestration_core.transitions.po import get_next_po_state


class POCreateFeaturesNode:
    """Invokes the LLM to produce a feature-request plan and writes the issues.

    Validates each feature request against FeatureRequestArtifact schema before
    creating the GitHub issue.  Transitions from PO_CREATING_FEATURES to
    PO_FEATURE_REQUESTS_CREATED and closes the source opportunity.
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
            "po_create_features",
            {"issue_number": issue.number, "title": issue.title, "body": issue.body},
        )

        created_numbers: List[int] = []
        now = datetime.now(timezone.utc).isoformat()

        for spec in result.payload["feature_requests"]:
            artifact = FeatureRequestArtifact(
                artifact_version="1.0.0",
                artifact_id=f"fr-{uuid4()}",
                source_opportunity_number=issue_number,
                title=spec["title"],
                body=spec["body"],
                priority_score=int(spec["priority_score"]),
                produced_at=now,
            )
            artifact.validate()
            fr_number = self.gateway.create_feature_request(
                source_opportunity_number=issue_number,
                title=artifact.title,
                body=artifact.body,
                priority_score=artifact.priority_score,
            )
            created_numbers.append(fr_number)

        next_state = get_next_po_state(POState.PO_CREATING_FEATURES, POEvent.FEATURE_REQUESTS_COMMITTED)

        self.gateway.set_state_labels(
            issue_number,
            list(PO_CANONICAL_STATE_LABELS),
            [PO_CANONICAL_LABEL_BY_STATE[next_state]],
        )
        self.gateway.close_issue(issue_number, "completed")

        entry = TransitionLogEntry(
            loop_id="po",
            run_id=run_id,
            issue_number=issue_number,
            from_state=POState.PO_CREATING_FEATURES.value,
            to_state=next_state.value,
            trigger_event=POEvent.FEATURE_REQUESTS_COMMITTED.value,
            reason_code="FEATURE_REQUESTS_COMMITTED",
            reason_detail=f"Created {len(created_numbers)} feature request(s): {created_numbers}",
            timestamp_utc=now,
            adapter_source=self.adapter.adapter_source,
        )
        self.log_store.append(entry)
        self.gateway.post_comment(issue_number, entry.to_comment())
        return next_state
