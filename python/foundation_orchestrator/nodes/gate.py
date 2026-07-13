from datetime import datetime, timezone
import logging
from typing import List

from aios_orchestration_core.events.foundation import FoundationEvent
from aios_orchestration_core.github.foundation_gateway import FoundationGateway
from aios_orchestration_core.labels.foundation_labels import (
    FOUNDATION_CANONICAL_LABEL_BY_STATE,
    FOUNDATION_CANONICAL_STATE_LABELS,
    normalize_foundation_state_from_labels,
)
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.foundation import FoundationState
from aios_orchestration_core.transitions.foundation import get_next_foundation_state
from foundation_orchestrator.evidence import classify_adr_links, classify_wiki_links, extract_links

logger = logging.getLogger(__name__)

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
        normalized = normalize_foundation_state_from_labels(issue.labels)
        if normalized.state != FoundationState.FOUNDATION_REVIEW:
            logger.warning(
                f"  Issue #{issue_number}: FoundationGateNode — unexpected state "
                f"{normalized.state!r} (expected foundation:review); aborting gate"
            )
            self.gateway.post_comment(
                issue_number,
                "Transition validation failed: G1 source state invalid for foundation gate (expected foundation:review).",
            )
            self.gateway.add_labels(issue_number, ["transition-validation-failed"])
            return normalized.state or FoundationState.FOUNDATION_NEEDED

        comments = self.gateway.get_issue_comments(issue_number)
        linked_research = self.gateway.list_linked_research_issues(issue_number)
        foundation_markdown = self.gateway.read_foundation_markdown()
        logger.info(
            f"  Issue #{issue_number}: FoundationGateNode — invoking LLM (foundation_gate), "
            f"{len(linked_research)} linked research item(s)"
        )
        result = self.adapter.invoke_json(
            "foundation_gate",
            {
                "issue_number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "comments": comments,
                "foundation_markdown": foundation_markdown,
                "linked_research": [
                    {
                        "number": r.number,
                        "title": r.title,
                        "body": r.body,
                        "open": r.open,
                    }
                    for r in linked_research
                ],
            },
        )
        decision = result.payload["decision"]
        reason_detail = result.payload.get("reason", "")
        if decision == "APPROVE_FOUNDATION":
            evidence_failures = self._approval_evidence_failures(issue_number, issue.body, comments)
            if evidence_failures:
                logger.info(
                    f"  Issue #{issue_number}: FoundationGateNode — LLM said APPROVE but "
                    f"evidence preconditions not met; downgrading to REVISE_FOUNDATION"
                )
                decision = "REVISE_FOUNDATION"
                reason_detail = (
                    f"{reason_detail}\nApproval preconditions not met: " + "; ".join(evidence_failures)
                ).strip()
        event = _DECISION_MAP[decision]
        next_state = get_next_foundation_state(FoundationState.FOUNDATION_REVIEW, event)
        logger.info(
            f"  Issue #{issue_number}: FoundationGateNode — decision={decision}, "
            f"transitioning to {next_state.value}"
        )

        self.gateway.set_state_labels(issue_number, list(FOUNDATION_CANONICAL_STATE_LABELS), [FOUNDATION_CANONICAL_LABEL_BY_STATE[next_state]])

        if next_state == FoundationState.FOUNDATION_APPROVED:
            self.gateway.close_issue(issue_number, "completed")

        entry = TransitionLogEntry(
            loop_id="foundation", run_id=run_id, issue_number=issue_number,
            from_state=FoundationState.FOUNDATION_REVIEW.value, to_state=next_state.value,
            trigger_event=event.value, reason_code=f"FOUNDATION_GATE_{decision}",
            reason_detail=reason_detail, timestamp_utc=datetime.now(timezone.utc).isoformat(),
            adapter_source=self.adapter.adapter_source,
        )
        self.log_store.append(entry)
        self.gateway.post_comment(issue_number, entry.to_comment())
        return next_state

    def _approval_evidence_failures(self, issue_number: int, issue_body: str, comments: List[str]) -> List[str]:
        failures: List[str] = []
        linked_open = self.gateway.count_open_linked_research_issues(issue_number)
        linked_closed = self.gateway.count_closed_linked_research_issues(issue_number)
        if linked_closed == 0:
            failures.append("no linked foundation research issues are closed")
        if linked_open > 0:
            failures.append(f"{linked_open} linked foundation research issue(s) still open")

        links = extract_links([issue_body, *comments])
        wiki_links = classify_wiki_links(links)
        adr_links = classify_adr_links(links)
        if not (wiki_links or adr_links):
            failures.append("no wiki/ADR outcome links found in issue body or comments")
        if not adr_links:
            failures.append("at least one ADR link is required")
        return failures
