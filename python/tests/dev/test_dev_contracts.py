import unittest

from aios_orchestration_core.events.dev import DevEvent
from aios_orchestration_core.labels.dev_labels import DEV_CANONICAL_LABEL_BY_STATE, DEV_LABEL_REGISTRY
from aios_orchestration_core.states.dev import DevState, TERMINAL_DEV_STATES
from aios_orchestration_core.transitions.dev import (
    DevTransitionError,
    allowed_events_for_dev_state,
    get_next_dev_state,
)


class DevContractsTests(unittest.TestCase):
    def test_terminal_states_have_no_outgoing_events(self) -> None:
        for state in TERMINAL_DEV_STATES:
            self.assertEqual(allowed_events_for_dev_state(state), frozenset())

    def test_happy_path_chain(self) -> None:
        chain = [
            (DevState.DEV_INTAKE, DevEvent.INTAKE_APPROVED, DevState.DEV_DESIGN),
            (DevState.DEV_DESIGN, DevEvent.DESIGN_APPROVED, DevState.DEV_BUILD),
            (DevState.DEV_BUILD, DevEvent.BUILD_COMPLETE, DevState.DEV_QA),
            (DevState.DEV_QA, DevEvent.QA_PASSED, DevState.DEV_POLICY),
            (DevState.DEV_POLICY, DevEvent.POLICY_APPROVED, DevState.DEV_RELEASED),
        ]
        for src, event, expected in chain:
            self.assertEqual(get_next_dev_state(src, event), expected)

    def test_feedback_loops(self) -> None:
        self.assertEqual(get_next_dev_state(DevState.DEV_DESIGN, DevEvent.DESIGN_REVISE), DevState.DEV_INTAKE)
        self.assertEqual(get_next_dev_state(DevState.DEV_QA, DevEvent.QA_FAILED), DevState.DEV_DESIGN)

    def test_block_paths_are_terminal(self) -> None:
        for state, event in [
            (DevState.DEV_INTAKE, DevEvent.INTAKE_BLOCKED),
            (DevState.DEV_DESIGN, DevEvent.DESIGN_BLOCKED),
            (DevState.DEV_BUILD, DevEvent.BUILD_BLOCKED),
        ]:
            self.assertIn(get_next_dev_state(state, event), TERMINAL_DEV_STATES)

    def test_policy_review_required_goes_to_needs_human(self) -> None:
        self.assertEqual(
            get_next_dev_state(DevState.DEV_POLICY, DevEvent.POLICY_REVIEW_REQUIRED),
            DevState.DEV_NEEDS_HUMAN,
        )

    def test_retry_from_active_goes_to_needs_human(self) -> None:
        for state in (DevState.DEV_INTAKE, DevState.DEV_DESIGN, DevState.DEV_BUILD, DevState.DEV_QA, DevState.DEV_POLICY):
            self.assertEqual(get_next_dev_state(state, DevEvent.RETRY_THRESHOLD_EXCEEDED), DevState.DEV_NEEDS_HUMAN)

    def test_retry_from_terminal_raises(self) -> None:
        with self.assertRaises(DevTransitionError):
            get_next_dev_state(DevState.DEV_RELEASED, DevEvent.RETRY_THRESHOLD_EXCEEDED)

    def test_all_states_have_canonical_labels(self) -> None:
        for state in DevState:
            self.assertIn(state, DEV_CANONICAL_LABEL_BY_STATE)

    def test_label_registry_canonical_lookup(self) -> None:
        self.assertEqual(DEV_LABEL_REGISTRY.state_for_label("dev:intake"), DevState.DEV_INTAKE)
        self.assertEqual(DEV_LABEL_REGISTRY.state_for_label("feature-request"), DevState.DEV_INTAKE)
        self.assertEqual(DEV_LABEL_REGISTRY.state_for_label("released"), DevState.DEV_RELEASED)


if __name__ == "__main__":
    unittest.main()
