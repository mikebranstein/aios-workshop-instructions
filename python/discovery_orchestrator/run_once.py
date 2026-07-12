from dataclasses import dataclass, field
from typing import Dict, List, Optional

from aios_orchestration_core.events.discovery import DiscoveryEvent
from aios_orchestration_core.states.discovery import DiscoveryState
from aios_orchestration_core.transitions.discovery import get_next_discovery_state
from discovery_orchestrator.context import DiscoveryContext, DiscoveryRunResult
from discovery_orchestrator.idea_scout_adapter import IdeaScoutAdapter


@dataclass
class PMIdeaIssueStore:
    """Simple in-memory store for created pm-idea issues (used in tests)."""
    issues: Dict[int, Dict] = field(default_factory=dict)
    _next: int = 1000

    def create(self, title: str, body: str) -> int:
        self._next += 1
        self.issues[self._next] = {"title": title, "body": body, "labels": {"pm-idea", "pm-idea-auto"}}
        return self._next


class DiscoveryRunOnceOrchestrator:
    """Bounded discovery orchestrator.

    Checks preconditions (foundation gate, focus file), invokes the
    idea-scout adapter, and creates pm-idea issues up to creation_cap.
    """

    def __init__(
        self,
        context: DiscoveryContext,
        idea_scout: IdeaScoutAdapter,
        pm_idea_store: PMIdeaIssueStore,
    ) -> None:
        self.context = context
        self.idea_scout = idea_scout
        self.pm_idea_store = pm_idea_store

    def run(self) -> DiscoveryRunResult:
        state = DiscoveryState.DISCOVERY_IDLE
        state = get_next_discovery_state(state, DiscoveryEvent.RUN_TRIGGERED)

        if not self.context.foundation_gate_passed:
            state = get_next_discovery_state(state, DiscoveryEvent.GATE_MISSING)
            return DiscoveryRunResult(state=state.value, halted_reason="Foundation gate not passed")

        if not self.context.focus_file_exists or not self.context.focus_file_populated:
            state = get_next_discovery_state(state, DiscoveryEvent.FOCUS_MISSING)
            return DiscoveryRunResult(state=state.value, halted_reason="docs/discovery-focus.md missing or empty")

        scout_result = self.idea_scout.run(
            context_summary="discovery run",
            creation_cap=self.context.creation_cap,
        )

        created: List[int] = []
        deferred = 0
        dropped = 0

        for candidate in scout_result.candidates:
            if candidate.decision == "CREATE_PM_IDEA" and len(created) < self.context.creation_cap:
                number = self.pm_idea_store.create(candidate.title, candidate.body)
                created.append(number)
            elif candidate.decision == "DEFER":
                deferred += 1
            else:
                dropped += 1

        state = get_next_discovery_state(state, DiscoveryEvent.IDEA_SCOUT_COMPLETED)
        return DiscoveryRunResult(
            state=state.value,
            created_pm_idea_numbers=created,
            deferred_count=deferred,
            dropped_count=dropped,
        )
