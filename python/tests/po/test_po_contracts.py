import unittest

from aios_orchestration_core.events.po import POEvent
from aios_orchestration_core.labels.po_labels import (
    PO_CANONICAL_LABEL_BY_STATE,
    PO_LABEL_REGISTRY,
)
from aios_orchestration_core.states.po import POState, TERMINAL_PO_STATES
from aios_orchestration_core.transitions.po import (
    POTransitionError,
    allowed_events_for_po_state,
    get_next_po_state,
)


class POContractsTests(unittest.TestCase):
    def test_terminal_states_have_no_outgoing_events(self) -> None:
        for state in TERMINAL_PO_STATES:
            self.assertEqual(allowed_events_for_po_state(state), frozenset())

    def test_queued_to_prioritizing_via_entered_event(self) -> None:
        next_state = get_next_po_state(POState.PO_QUEUED, POEvent.ENTERED_PRIORITIZATION)
        self.assertEqual(next_state, POState.PO_PRIORITIZING)

    def test_prioritizing_create_goes_to_creating_features(self) -> None:
        next_state = get_next_po_state(POState.PO_PRIORITIZING, POEvent.PRIORITIZATION_CREATE)
        self.assertEqual(next_state, POState.PO_CREATING_FEATURES)

    def test_prioritizing_defer_is_terminal(self) -> None:
        next_state = get_next_po_state(POState.PO_PRIORITIZING, POEvent.PRIORITIZATION_DEFER)
        self.assertIn(next_state, TERMINAL_PO_STATES)

    def test_prioritizing_reject_is_terminal(self) -> None:
        next_state = get_next_po_state(POState.PO_PRIORITIZING, POEvent.PRIORITIZATION_REJECT)
        self.assertIn(next_state, TERMINAL_PO_STATES)

    def test_creating_features_to_feature_requests_created(self) -> None:
        next_state = get_next_po_state(
            POState.PO_CREATING_FEATURES, POEvent.FEATURE_REQUESTS_COMMITTED
        )
        self.assertEqual(next_state, POState.PO_FEATURE_REQUESTS_CREATED)

    def test_retry_from_active_state_goes_to_needs_human(self) -> None:
        for active in (POState.PO_QUEUED, POState.PO_PRIORITIZING, POState.PO_CREATING_FEATURES):
            next_state = get_next_po_state(active, POEvent.RETRY_THRESHOLD_EXCEEDED)
            self.assertEqual(next_state, POState.PO_NEEDS_HUMAN)

    def test_retry_from_terminal_state_raises(self) -> None:
        with self.assertRaises(POTransitionError):
            get_next_po_state(POState.PO_DEFERRED, POEvent.RETRY_THRESHOLD_EXCEEDED)

    def test_canonical_label_registry_covers_all_states(self) -> None:
        for state in POState:
            self.assertIn(state, PO_CANONICAL_LABEL_BY_STATE)

    def test_label_registry_reverse_lookup(self) -> None:
        self.assertEqual(
            PO_LABEL_REGISTRY.state_for_label("po:queued"), POState.PO_QUEUED
        )
        self.assertEqual(
            PO_LABEL_REGISTRY.state_for_label("strategic-opportunity"), POState.PO_QUEUED
        )
        self.assertEqual(
            PO_LABEL_REGISTRY.state_for_label("feature-requests-created"),
            POState.PO_FEATURE_REQUESTS_CREATED,
        )

    def test_canonical_label_wins_over_legacy(self) -> None:
        # PO_QUEUED has canonical po:queued and legacy strategic-opportunity
        canonical = PO_LABEL_REGISTRY.canonical_label(POState.PO_QUEUED)
        legacy = PO_LABEL_REGISTRY.legacy_label(POState.PO_QUEUED)
        self.assertEqual(canonical, "po:queued")
        self.assertEqual(legacy, "strategic-opportunity")


if __name__ == "__main__":
    unittest.main()
