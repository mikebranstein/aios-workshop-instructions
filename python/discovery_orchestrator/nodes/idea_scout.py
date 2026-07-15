"""Node for Idea Scout LLM invocation in the Discovery loop.

Follows the foundation orchestrator node pattern: accepts a JudgmentLLMAdapter
and DiscoveryGateway directly, calls invoke_json, and writes PM-idea issues.
"""

import logging
from typing import TYPE_CHECKING, List, Tuple

from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.states.discovery import DiscoveryState

if TYPE_CHECKING:
    from aios_orchestration_core.github.discovery_gateway import DiscoveryGateway

logger = logging.getLogger(__name__)


class IdeaScoutNode:
    """Invokes the LLM to generate PM-idea candidates and writes approved ones as GitHub issues.

    Mirrors the structure of FoundationResearchNode: accepts adapter + gateway,
    calls invoke_json with the discovery_idea_scout task type, and applies decisions.
    """

    def __init__(
        self,
        adapter: JudgmentLLMAdapter,
        gateway: "DiscoveryGateway",
    ) -> None:
        self.adapter = adapter
        self.gateway = gateway

    def run(
        self,
        run_id: str,
        creation_cap: int = 3,
        batch_cap: int = 5,
    ) -> Tuple[DiscoveryState, List[int], int, int]:
        """Invoke idea-scout LLM and create PM-idea issues for approved candidates.

        G1 source-state validation: this node should only be called when the
        discovery run is in DISCOVERY_RUNNING state. The preconditions node
        enforces this before routing here.

        Args:
            run_id: Current run identifier for logging.
            creation_cap: Maximum PM-idea issues to create this run.
            batch_cap: Maximum candidates to evaluate (sent to LLM as context).

        Returns:
            Tuple of (final_state, created_numbers, deferred_count, dropped_count)
        """
        focus_content = self.gateway.read_focus_file()
        logger.info(
            f"IdeaScoutNode — invoking LLM (discovery_idea_scout), "
            f"creation_cap={creation_cap}, batch_cap={batch_cap}"
        )

        result = self.adapter.invoke_json(
            "discovery_idea_scout",
            {
                "focus_content": focus_content,
                "creation_cap": creation_cap,
                "batch_cap": batch_cap,
            },
        )

        raw_candidates = result.payload.get("candidates", [])
        logger.info(f"IdeaScoutNode — LLM returned {len(raw_candidates)} candidate(s)")

        created: List[int] = []
        deferred_candidates: List[dict] = []
        dropped = 0

        for candidate in raw_candidates:
            decision = str(candidate.get("decision", "DROP")).upper()
            raw_title = str(candidate.get("title", "Untitled opportunity"))
            title = raw_title if raw_title.startswith("[PM Idea]:") else f"[PM Idea]: {raw_title}"
            body = str(candidate.get("body", ""))

            if decision == "CREATE_PM_IDEA" and len(created) < creation_cap:
                issue_number = self.gateway.create_pm_idea_issue(title, body)
                created.append(issue_number)
                logger.info(f"IdeaScoutNode — created pm-idea #{issue_number}: {title!r}")
            elif decision == "DEFER":
                deferred_candidates.append({"title": title, "body": body})
            else:
                dropped += 1

        if deferred_candidates:
            ok = self.gateway.append_deferred_candidates(deferred_candidates)
            if not ok:
                logger.warning("IdeaScoutNode — deferred-candidate wiki write failed")

        deferred_count = len(deferred_candidates)
        logger.info(
            f"IdeaScoutNode — complete: created={len(created)}, "
            f"deferred={deferred_count}, dropped={dropped}"
        )
        return DiscoveryState.DISCOVERY_COMPLETE, created, deferred_count, dropped
