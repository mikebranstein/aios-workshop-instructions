import unittest

from aios_orchestration_core.events.foundation import FoundationEvent
from aios_orchestration_core.labels.foundation_labels import FOUNDATION_CANONICAL_LABEL_BY_STATE, FOUNDATION_LABEL_REGISTRY
from aios_orchestration_core.states.foundation import FoundationState, TERMINAL_FOUNDATION_STATES
from aios_orchestration_core.transitions.foundation import (
    FoundationTransitionError,
    allowed_events_for_foundation_state,
    get_next_foundation_state,
)


class FoundationContractsTests(unittest.TestCase):
    def test_terminal_states_no_outgoing_events(self) -> None:
        for state in TERMINAL_FOUNDATION_STATES:
            self.assertEqual(allowed_events_for_foundation_state(state), frozenset())

    def test_happy_path(self) -> None:
        s = get_next_foundation_state(FoundationState.FOUNDATION_NEEDED, FoundationEvent.FOUNDATION_STARTED)
        self.assertEqual(s, FoundationState.FOUNDATION_IN_PROGRESS)
        s = get_next_foundation_state(s, FoundationEvent.RESEARCH_RECOMMEND)
        self.assertEqual(s, FoundationState.FOUNDATION_REVIEW)
        s = get_next_foundation_state(s, FoundationEvent.APPROVE_FOUNDATION)
        self.assertEqual(s, FoundationState.FOUNDATION_APPROVED)

    def test_needs_more_research_cycles(self) -> None:
        s = get_next_foundation_state(FoundationState.FOUNDATION_IN_PROGRESS, FoundationEvent.RESEARCH_NEEDS_MORE)
        self.assertEqual(s, FoundationState.FOUNDATION_IN_PROGRESS)

    def test_revise_cycles_back(self) -> None:
        s = get_next_foundation_state(FoundationState.FOUNDATION_REVIEW, FoundationEvent.REVISE_FOUNDATION)
        self.assertEqual(s, FoundationState.FOUNDATION_IN_PROGRESS)

    def test_blocked_paths(self) -> None:
        self.assertIn(get_next_foundation_state(FoundationState.FOUNDATION_IN_PROGRESS, FoundationEvent.RESEARCH_BLOCKED), TERMINAL_FOUNDATION_STATES)
        self.assertIn(get_next_foundation_state(FoundationState.FOUNDATION_REVIEW, FoundationEvent.BLOCK_FOUNDATION), TERMINAL_FOUNDATION_STATES)

    def test_retry_escalates(self) -> None:
        for active in (FoundationState.FOUNDATION_NEEDED, FoundationState.FOUNDATION_IN_PROGRESS, FoundationState.FOUNDATION_REVIEW):
            self.assertEqual(get_next_foundation_state(active, FoundationEvent.RETRY_THRESHOLD_EXCEEDED), FoundationState.FOUNDATION_NEEDS_HUMAN)

    def test_retry_from_terminal_raises(self) -> None:
        with self.assertRaises(FoundationTransitionError):
            get_next_foundation_state(FoundationState.FOUNDATION_APPROVED, FoundationEvent.RETRY_THRESHOLD_EXCEEDED)

    def test_all_states_have_canonical_labels(self) -> None:
        for state in FoundationState:
            self.assertIn(state, FOUNDATION_CANONICAL_LABEL_BY_STATE)

    def test_label_registry_round_trips(self) -> None:
        self.assertEqual(FOUNDATION_LABEL_REGISTRY.state_for_label("foundation:approved"), FoundationState.FOUNDATION_APPROVED)
        self.assertEqual(FOUNDATION_LABEL_REGISTRY.state_for_label("foundation-approved"), FoundationState.FOUNDATION_APPROVED)


if __name__ == "__main__":
    unittest.main()
