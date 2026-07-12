import unittest

from aios_orchestration_core.events.arch_review import ArchReviewEvent, DebtEvent
from aios_orchestration_core.labels.arch_review_labels import (
    ARCH_REVIEW_CANONICAL_LABEL_BY_STATE,
    ARCH_REVIEW_LABEL_REGISTRY,
    DEBT_LABEL_REGISTRY,
)
from aios_orchestration_core.states.arch_review import (
    ArchReviewState, TERMINAL_ARCH_REVIEW_STATES,
    DebtState, TERMINAL_DEBT_STATES,
)
from aios_orchestration_core.transitions.arch_review import (
    ArchReviewTransitionError,
    DebtTransitionError,
    allowed_events_for_arch_review_state,
    allowed_events_for_debt_state,
    get_next_arch_review_state,
    get_next_debt_state,
)


class ArchReviewContractsTests(unittest.TestCase):
    def test_terminal_review_states_no_events(self) -> None:
        for state in TERMINAL_ARCH_REVIEW_STATES:
            self.assertEqual(allowed_events_for_arch_review_state(state), frozenset())

    def test_happy_path_no_action(self) -> None:
        s = get_next_arch_review_state(ArchReviewState.ARCH_REVIEW_PENDING, ArchReviewEvent.EVALUATION_STARTED)
        self.assertEqual(s, ArchReviewState.ARCH_REVIEW_IN_PROGRESS)
        s = get_next_arch_review_state(s, ArchReviewEvent.FITNESS_PASS)
        self.assertEqual(s, ArchReviewState.ARCH_NO_ACTION)

    def test_warn_leads_to_refactor_planned(self) -> None:
        s = get_next_arch_review_state(ArchReviewState.ARCH_REVIEW_IN_PROGRESS, ArchReviewEvent.FITNESS_WARN)
        self.assertEqual(s, ArchReviewState.ARCH_REFACTOR_PLANNED)
        s = get_next_arch_review_state(s, ArchReviewEvent.REFACTOR_REQUESTS_CREATED)
        self.assertEqual(s, ArchReviewState.ARCH_REFACTOR_CREATED)

    def test_critical_escalates(self) -> None:
        s = get_next_arch_review_state(ArchReviewState.ARCH_REVIEW_IN_PROGRESS, ArchReviewEvent.FITNESS_FAIL_CRITICAL)
        self.assertEqual(s, ArchReviewState.ARCH_REVIEW_ESCALATED)

    def test_retry_escalates_to_needs_human(self) -> None:
        for active in (ArchReviewState.ARCH_REVIEW_PENDING, ArchReviewState.ARCH_REVIEW_IN_PROGRESS, ArchReviewState.ARCH_REFACTOR_PLANNED):
            self.assertEqual(get_next_arch_review_state(active, ArchReviewEvent.RETRY_THRESHOLD_EXCEEDED), ArchReviewState.ARCH_REVIEW_NEEDS_HUMAN)

    def test_review_label_registry(self) -> None:
        self.assertEqual(ARCH_REVIEW_LABEL_REGISTRY.state_for_label("arch:review-pending"), ArchReviewState.ARCH_REVIEW_PENDING)
        self.assertEqual(ARCH_REVIEW_LABEL_REGISTRY.state_for_label("arch-review-pending"), ArchReviewState.ARCH_REVIEW_PENDING)

    def test_all_review_states_have_canonical_labels(self) -> None:
        for state in ArchReviewState:
            self.assertIn(state, ARCH_REVIEW_CANONICAL_LABEL_BY_STATE)


class DebtContractsTests(unittest.TestCase):
    def test_terminal_debt_states_no_events(self) -> None:
        for state in TERMINAL_DEBT_STATES:
            self.assertEqual(allowed_events_for_debt_state(state), frozenset())

    def test_happy_path_triage_schedule_resolve(self) -> None:
        s = get_next_debt_state(DebtState.DEBT_NEW, DebtEvent.DEBT_TRIAGE)
        self.assertEqual(s, DebtState.DEBT_TRIAGED)
        s = get_next_debt_state(s, DebtEvent.DEBT_SCHEDULE)
        self.assertEqual(s, DebtState.DEBT_SCHEDULED)
        s = get_next_debt_state(s, DebtEvent.DEBT_RESOLVE)
        self.assertEqual(s, DebtState.DEBT_RESOLVED)

    def test_defer_from_any_active(self) -> None:
        for state in (DebtState.DEBT_NEW, DebtState.DEBT_TRIAGED, DebtState.DEBT_SCHEDULED):
            self.assertEqual(get_next_debt_state(state, DebtEvent.DEBT_DEFER), DebtState.DEBT_DEFERRED)

    def test_override_re_activates_deferred(self) -> None:
        s = get_next_debt_state(DebtState.DEBT_DEFERRED, DebtEvent.DEBT_OVERRIDE_ACTIVATE)
        self.assertEqual(s, DebtState.DEBT_TRIAGED)

    def test_debt_label_registry(self) -> None:
        self.assertEqual(DEBT_LABEL_REGISTRY.state_for_label("debt:new"), DebtState.DEBT_NEW)
        self.assertEqual(DEBT_LABEL_REGISTRY.state_for_label("architecture-debt"), DebtState.DEBT_NEW)


if __name__ == "__main__":
    unittest.main()
