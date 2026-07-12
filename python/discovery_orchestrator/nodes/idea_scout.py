"""Node wrapper for idea-scout adapter invocation in Discovery loop.

This node class wraps the IdeaScoutAdapter to fit the LangGraph node pattern,
handling adapter invocation and PM-idea issue creation.
"""

from typing import List

from discovery_orchestrator.idea_scout_adapter import IdeaScoutAdapter
from aios_orchestration_core.states.discovery import DiscoveryState


class IdeaScoutNode:
    """Wraps IdeaScoutAdapter invocation for LangGraph integration.

    Invokes the idea-scout adapter to generate and score candidates,
    creates PM-idea issues based on decisions, and returns the completion state.
    """

    def __init__(
        self,
        adapter: IdeaScoutAdapter,
        pm_idea_store: PMIdeaIssueStore,
    ) -> None:
        self.adapter = adapter
        self.pm_idea_store = pm_idea_store

    def run(
        self,
        creation_cap: int = 3,
        context_summary: str = "discovery run",
    ) -> tuple[DiscoveryState, List[int], int, int]:
        """Execute idea-scout and return created issue numbers, deferred & dropped counts.

        Args:
            creation_cap: Maximum number of PM-idea issues to create in this run.
            context_summary: Context description for the adapter invocation.

        Returns:
            Tuple of (final_state, created_numbers, deferred_count, dropped_count)
        """
        scout_result = self.adapter.run(
            context_summary=context_summary,
            creation_cap=creation_cap,
        )

        created: List[int] = []
        deferred = 0
        dropped = 0

        for candidate in scout_result.candidates:
            if candidate.decision == "CREATE_PM_IDEA" and len(created) < creation_cap:
                number = self.pm_idea_store.create(candidate.title, candidate.body)
                created.append(number)
            elif candidate.decision == "DEFER":
                deferred += 1
            else:  # DROP
                dropped += 1

        return DiscoveryState.DISCOVERY_COMPLETE, created, deferred, dropped