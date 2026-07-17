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
        """Full happy path through all 10 phases."""
        transitions = [
            (FoundationState.FOUNDATION_NEEDED,                    FoundationEvent.FOUNDATION_STARTED,          FoundationState.FOUNDATION_INTENT_CAPTURE_CREATE),
            (FoundationState.FOUNDATION_INTENT_CAPTURE_CREATE,     FoundationEvent.INTENT_CAPTURE_CREATED,      FoundationState.FOUNDATION_INTENT_CAPTURE_VERIFY),
            (FoundationState.FOUNDATION_INTENT_CAPTURE_VERIFY,     FoundationEvent.INTENT_CAPTURE_VERIFIED,     FoundationState.FOUNDATION_SHELL_DESIGN_CREATE),
            (FoundationState.FOUNDATION_SHELL_DESIGN_CREATE,       FoundationEvent.SHELL_DESIGN_CREATED,        FoundationState.FOUNDATION_SHELL_DESIGN_VERIFY),
            (FoundationState.FOUNDATION_SHELL_DESIGN_VERIFY,       FoundationEvent.SHELL_DESIGN_VERIFIED,       FoundationState.FOUNDATION_BACKLOG_BUILD_CREATE),
            (FoundationState.FOUNDATION_BACKLOG_BUILD_CREATE,      FoundationEvent.BACKLOG_BUILD_CREATED,       FoundationState.FOUNDATION_BACKLOG_BUILD_VERIFY),
            (FoundationState.FOUNDATION_BACKLOG_BUILD_VERIFY,      FoundationEvent.BACKLOG_BUILD_VERIFIED,      FoundationState.FOUNDATION_READINESS_ASSESS_CREATE),
            (FoundationState.FOUNDATION_READINESS_ASSESS_CREATE,   FoundationEvent.READINESS_ASSESS_CREATED,   FoundationState.FOUNDATION_READINESS_ASSESS_VERIFY),
            (FoundationState.FOUNDATION_READINESS_ASSESS_VERIFY,   FoundationEvent.READINESS_ASSESS_VERIFIED,  FoundationState.FOUNDATION_HANDOFF_PACK_CREATE),
            (FoundationState.FOUNDATION_HANDOFF_PACK_CREATE,       FoundationEvent.HANDOFF_PACK_CREATED,        FoundationState.FOUNDATION_HANDOFF_PACK_VERIFY),
            (FoundationState.FOUNDATION_HANDOFF_PACK_VERIFY,       FoundationEvent.HANDOFF_PACK_VERIFIED,       FoundationState.FOUNDATION_APPROVED),
        ]
        for from_state, event, expected_state in transitions:
            actual = get_next_foundation_state(from_state, event)
            self.assertEqual(actual, expected_state, f"{from_state.value} + {event.value}")

    def test_verify_revise_cycles_back_to_create(self) -> None:
        """Each verify→revise pair should send the issue back to the corresponding create phase."""
        revise_cycles = [
            (FoundationState.FOUNDATION_INTENT_CAPTURE_VERIFY,    FoundationEvent.INTENT_CAPTURE_REVISE,   FoundationState.FOUNDATION_INTENT_CAPTURE_CREATE),
            (FoundationState.FOUNDATION_SHELL_DESIGN_VERIFY,      FoundationEvent.SHELL_DESIGN_REVISE,     FoundationState.FOUNDATION_SHELL_DESIGN_CREATE),
            (FoundationState.FOUNDATION_BACKLOG_BUILD_VERIFY,     FoundationEvent.BACKLOG_BUILD_REVISE,    FoundationState.FOUNDATION_BACKLOG_BUILD_CREATE),
            (FoundationState.FOUNDATION_READINESS_ASSESS_VERIFY,  FoundationEvent.READINESS_ASSESS_REVISE, FoundationState.FOUNDATION_READINESS_ASSESS_CREATE),
            (FoundationState.FOUNDATION_HANDOFF_PACK_VERIFY,      FoundationEvent.HANDOFF_PACK_REVISE,     FoundationState.FOUNDATION_HANDOFF_PACK_CREATE),
        ]
        for from_state, event, expected in revise_cycles:
            self.assertEqual(get_next_foundation_state(from_state, event), expected)

    def test_blocked_paths(self) -> None:
        """Each verify phase must have a path to BLOCKED."""
        block_transitions = [
            (FoundationState.FOUNDATION_INTENT_CAPTURE_VERIFY,    FoundationEvent.INTENT_CAPTURE_BLOCK),
            (FoundationState.FOUNDATION_SHELL_DESIGN_VERIFY,      FoundationEvent.SHELL_DESIGN_BLOCK),
            (FoundationState.FOUNDATION_BACKLOG_BUILD_VERIFY,     FoundationEvent.BACKLOG_BUILD_BLOCK),
            (FoundationState.FOUNDATION_READINESS_ASSESS_VERIFY,  FoundationEvent.READINESS_ASSESS_BLOCK),
            (FoundationState.FOUNDATION_HANDOFF_PACK_VERIFY,      FoundationEvent.HANDOFF_PACK_BLOCK),
        ]
        for from_state, event in block_transitions:
            result = get_next_foundation_state(from_state, event)
            self.assertIn(result, TERMINAL_FOUNDATION_STATES, f"{from_state.value} + {event.value}")

    def test_retry_escalates_all_active_states(self) -> None:
        active_states = [
            FoundationState.FOUNDATION_NEEDED,
            FoundationState.FOUNDATION_INTENT_CAPTURE_CREATE,
            FoundationState.FOUNDATION_INTENT_CAPTURE_VERIFY,
            FoundationState.FOUNDATION_SHELL_DESIGN_CREATE,
            FoundationState.FOUNDATION_SHELL_DESIGN_VERIFY,
            FoundationState.FOUNDATION_BACKLOG_BUILD_CREATE,
            FoundationState.FOUNDATION_BACKLOG_BUILD_VERIFY,
            FoundationState.FOUNDATION_READINESS_ASSESS_CREATE,
            FoundationState.FOUNDATION_READINESS_ASSESS_VERIFY,
            FoundationState.FOUNDATION_HANDOFF_PACK_CREATE,
            FoundationState.FOUNDATION_HANDOFF_PACK_VERIFY,
        ]
        for state in active_states:
            result = get_next_foundation_state(state, FoundationEvent.RETRY_THRESHOLD_EXCEEDED)
            self.assertEqual(result, FoundationState.FOUNDATION_NEEDS_HUMAN, f"retry from {state.value}")

    def test_retry_from_terminal_raises(self) -> None:
        with self.assertRaises(FoundationTransitionError):
            get_next_foundation_state(FoundationState.FOUNDATION_APPROVED, FoundationEvent.RETRY_THRESHOLD_EXCEEDED)

    def test_all_states_have_canonical_labels(self) -> None:
        for state in FoundationState:
            self.assertIn(state, FOUNDATION_CANONICAL_LABEL_BY_STATE)

    def test_label_registry_round_trips(self) -> None:
        self.assertEqual(FOUNDATION_LABEL_REGISTRY.state_for_label("foundation:approved"), FoundationState.FOUNDATION_APPROVED)
        self.assertEqual(FOUNDATION_LABEL_REGISTRY.state_for_label("foundation:backlog-build-verify"), FoundationState.FOUNDATION_BACKLOG_BUILD_VERIFY)


if __name__ == "__main__":
    unittest.main()
