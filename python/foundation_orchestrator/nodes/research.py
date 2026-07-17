from datetime import datetime, timezone
import logging
import re
from typing import Dict, List, Optional

from aios_orchestration_core.events.foundation import FoundationEvent
from aios_orchestration_core.github.foundation_gateway import FoundationGateway, LinkedFoundationIssue
from aios_orchestration_core.labels.foundation_labels import FOUNDATION_CANONICAL_LABEL_BY_STATE, FOUNDATION_CANONICAL_STATE_LABELS
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.foundation import FoundationState
from aios_orchestration_core.transitions.foundation import get_next_foundation_state

logger = logging.getLogger(__name__)

_DECISION_MAP = {
    "RECOMMEND": FoundationEvent.BACKLOG_BUILD_VERIFIED,
    "NEEDS_MORE_RESEARCH": FoundationEvent.BACKLOG_BUILD_REVISE,
    "BLOCKED": FoundationEvent.BACKLOG_BUILD_BLOCK,
}

# Matches the "## Decision Area" section and captures text until the next heading or end of body.
_DECISION_AREA_RE = re.compile(
    r"##\s*Decision Area[^\n]*\n(.*?)(?=\n##|\Z)",
    re.IGNORECASE | re.DOTALL,
)


def _extract_decision_area(body: str) -> Optional[str]:
    """Return the normalised decision area value from a research issue body, or None."""
    m = _DECISION_AREA_RE.search(body or "")
    if not m:
        return None
    for line in m.group(1).splitlines():
        stripped = line.strip()
        # Skip empty lines, HTML comments, italic placeholders, and parenthesised option hints.
        if stripped and not stripped.startswith("<!--") and not stripped.startswith("_") and not stripped.startswith("("):
            return stripped.lower()
    return None


class FoundationResearchNode:
    def __init__(self, adapter: JudgmentLLMAdapter, gateway: FoundationGateway, log_store: TransitionLogStore) -> None:
        self.adapter, self.gateway, self.log_store = adapter, gateway, log_store

    def run(self, run_id: str, issue_number: int) -> FoundationState:
        issue = self.gateway.get_issue(issue_number)
        linked_research = self.gateway.list_linked_research_issues(issue_number)
        foundation_markdown = self.gateway.read_foundation_markdown()
        comments = self.gateway.get_issue_comments(issue_number)

        try:
            foundation_decision_pack = self.gateway.read_repo_file("docs/foundation-decision-pack.md")
        except Exception:
            foundation_decision_pack = ""

        logger.info(
            f"  Issue #{issue_number}: FoundationResearchNode — invoking LLM (foundation_research), "
            f"{len(linked_research)} linked research item(s)"
        )
        result = self.adapter.invoke_json(
            "foundation_research",
            {
                "issue_number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "comments": comments,
                "foundation_markdown": foundation_markdown,
                "foundation_decision_pack": foundation_decision_pack,
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

        # Hard precondition: if the LLM recommends promotion but closed research
        # issues share a decision area without reconciliation, downgrade to
        # NEEDS_MORE_RESEARCH before any state is written.
        if decision == "RECOMMEND":
            contradictions = self._contradiction_check(linked_research)
            if contradictions:
                logger.info(
                    f"  Issue #{issue_number}: FoundationResearchNode — LLM said RECOMMEND but "
                    f"contradiction check found conflicts; downgrading to NEEDS_MORE_RESEARCH"
                )
                decision = "NEEDS_MORE_RESEARCH"
                reason_detail = (
                    f"{reason_detail}\nContradiction check failed: " + "; ".join(contradictions)
                ).strip()

        # When more research is needed, post a structured feedback comment so that
        # backlog_build_create can spawn targeted gap-filling sub-issues on the next pass.
        if decision == "NEEDS_MORE_RESEARCH":
            self.gateway.post_comment(
                issue_number,
                "## Backlog Build — Verify Feedback\n\n"
                "The decision pack is not yet complete. Gaps to address on next attempt:\n\n"
                + "\n".join(f"- {line.strip()}" for line in reason_detail.splitlines() if line.strip())
                or "- (see reason above)",
            )

        event = _DECISION_MAP[decision]
        next_state = get_next_foundation_state(FoundationState.FOUNDATION_BACKLOG_BUILD_VERIFY, event)
        logger.info(
            f"  Issue #{issue_number}: FoundationResearchNode — decision={decision}, "
            f"transitioning to {next_state.value}"
        )

        self.gateway.set_state_labels(issue_number, list(FOUNDATION_CANONICAL_STATE_LABELS), [FOUNDATION_CANONICAL_LABEL_BY_STATE[next_state]])

        entry = TransitionLogEntry(
            loop_id="foundation", run_id=run_id, issue_number=issue_number,
            from_state=FoundationState.FOUNDATION_BACKLOG_BUILD_VERIFY.value, to_state=next_state.value,
            trigger_event=event.value, reason_code=f"FOUNDATION_RESEARCH_{decision}",
            reason_detail=reason_detail, timestamp_utc=datetime.now(timezone.utc).isoformat(),
            adapter_source=self.adapter.adapter_source,
        )
        self.log_store.append(entry)
        self.gateway.post_comment(issue_number, entry.to_comment())
        return next_state

    def _contradiction_check(self, linked_research: List[LinkedFoundationIssue]) -> List[str]:
        """Return conflict descriptions for each decision area with 2+ closed research issues.

        A single decision area covered by multiple closed research issues (e.g. one
        recommending Unreal Engine 5, another recommending Unity) is a contradiction
        that must be resolved before the research cycle advances to foundation review.
        Issues without a parseable Decision Area field are skipped — the check degrades
        gracefully when the template field is absent.
        """
        area_to_issues: Dict[str, List[int]] = {}
        for issue in linked_research:
            if issue.open:
                continue
            area = _extract_decision_area(issue.body)
            if area is None:
                continue
            area_to_issues.setdefault(area, []).append(issue.number)

        conflicts: List[str] = []
        for area, issue_numbers in area_to_issues.items():
            if len(issue_numbers) > 1:
                conflicts.append(
                    f"decision area '{area}' has {len(issue_numbers)} closed research issues "
                    f"({', '.join(f'#{n}' for n in issue_numbers)}) — reconcile before promoting to review"
                )
        return conflicts
