import unittest

from aios_orchestration_core.events.discovery import DiscoveryEvent
from aios_orchestration_core.states.discovery import DiscoveryState, TERMINAL_DISCOVERY_STATES
from aios_orchestration_core.transitions.discovery import (
    DiscoveryTransitionError,
    allowed_events_for_discovery_state,
    get_next_discovery_state,
)
from discovery_orchestrator.context import DiscoveryContext
from discovery_orchestrator.idea_scout_adapter import IdeaCandidate, StaticIdeaScoutAdapter
from discovery_orchestrator.run_once import DiscoveryRunOnceOrchestrator, PMIdeaIssueStore


class DiscoveryContractsTests(unittest.TestCase):
    def test_terminal_states_no_events(self) -> None:
        for state in TERMINAL_DISCOVERY_STATES:
            self.assertEqual(allowed_events_for_discovery_state(state), frozenset())

    def test_happy_path_transitions(self) -> None:
        s = get_next_discovery_state(DiscoveryState.DISCOVERY_IDLE, DiscoveryEvent.RUN_TRIGGERED)
        self.assertEqual(s, DiscoveryState.DISCOVERY_RUNNING)
        s = get_next_discovery_state(s, DiscoveryEvent.IDEA_SCOUT_COMPLETED)
        self.assertEqual(s, DiscoveryState.DISCOVERY_COMPLETE)

    def test_gate_missing_halts(self) -> None:
        s = get_next_discovery_state(DiscoveryState.DISCOVERY_RUNNING, DiscoveryEvent.GATE_MISSING)
        self.assertEqual(s, DiscoveryState.DISCOVERY_HALTED_NO_GATE)

    def test_focus_missing_halts(self) -> None:
        s = get_next_discovery_state(DiscoveryState.DISCOVERY_RUNNING, DiscoveryEvent.FOCUS_MISSING)
        self.assertEqual(s, DiscoveryState.DISCOVERY_HALTED_NO_FOCUS)

    def test_invalid_transition_raises(self) -> None:
        with self.assertRaises(DiscoveryTransitionError):
            get_next_discovery_state(DiscoveryState.DISCOVERY_IDLE, DiscoveryEvent.GATE_MISSING)


class DiscoveryRunOnceTests(unittest.TestCase):
    def _orch(self, candidates, *, gate=True, focus=True, cap=3):
        ctx = DiscoveryContext(foundation_gate_passed=gate, focus_file_exists=focus, focus_file_populated=focus, creation_cap=cap)
        scout = StaticIdeaScoutAdapter(candidates)
        store = PMIdeaIssueStore()
        return DiscoveryRunOnceOrchestrator(ctx, scout, store), store

    def test_happy_path_creates_ideas(self) -> None:
        candidates = [
            IdeaCandidate("Idea A", "body a", "CREATE_PM_IDEA"),
            IdeaCandidate("Idea B", "body b", "CREATE_PM_IDEA"),
        ]
        orch, store = self._orch(candidates)
        result = orch.run()
        self.assertEqual(result.state, "DISCOVERY_COMPLETE")
        self.assertEqual(len(result.created_pm_idea_numbers), 2)
        self.assertEqual(len(store.issues), 2)

    def test_creation_cap_enforced(self) -> None:
        candidates = [IdeaCandidate(f"Idea {i}", "b", "CREATE_PM_IDEA") for i in range(5)]
        orch, store = self._orch(candidates, cap=2)
        result = orch.run()
        self.assertEqual(len(result.created_pm_idea_numbers), 2)

    def test_gate_missing_halts(self) -> None:
        orch, _ = self._orch([], gate=False)
        result = orch.run()
        self.assertEqual(result.state, "DISCOVERY_HALTED_NO_GATE")
        self.assertIsNotNone(result.halted_reason)

    def test_focus_missing_halts(self) -> None:
        orch, _ = self._orch([], focus=False)
        result = orch.run()
        self.assertEqual(result.state, "DISCOVERY_HALTED_NO_FOCUS")

    def test_defer_and_drop_counted(self) -> None:
        candidates = [
            IdeaCandidate("A", "b", "CREATE_PM_IDEA"),
            IdeaCandidate("B", "b", "DEFER"),
            IdeaCandidate("C", "b", "DROP"),
        ]
        orch, _ = self._orch(candidates)
        result = orch.run()
        self.assertEqual(len(result.created_pm_idea_numbers), 1)
        self.assertEqual(result.deferred_count, 1)
        self.assertEqual(result.dropped_count, 1)


if __name__ == "__main__":
    unittest.main()
