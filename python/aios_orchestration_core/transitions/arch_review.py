from typing import Dict, FrozenSet, Tuple

from aios_orchestration_core.core.transition_table import TransitionError, TransitionTable
from aios_orchestration_core.events.arch_review import ArchReviewEvent, DebtEvent
from aios_orchestration_core.states.arch_review import (
    ArchReviewState, TERMINAL_ARCH_REVIEW_STATES,
    DebtState, TERMINAL_DEBT_STATES,
)


class ArchReviewTransitionError(ValueError):
    pass


class DebtTransitionError(ValueError):
    pass


_ARCH_REVIEW_TABLE: TransitionTable[ArchReviewState, ArchReviewEvent] = TransitionTable(
    {
        (ArchReviewState.ARCH_REVIEW_PENDING, ArchReviewEvent.EVALUATION_STARTED): ArchReviewState.ARCH_REVIEW_IN_PROGRESS,
        (ArchReviewState.ARCH_REVIEW_IN_PROGRESS, ArchReviewEvent.FITNESS_PASS): ArchReviewState.ARCH_NO_ACTION,
        (ArchReviewState.ARCH_REVIEW_IN_PROGRESS, ArchReviewEvent.FITNESS_WARN): ArchReviewState.ARCH_REFACTOR_PLANNED,
        (ArchReviewState.ARCH_REVIEW_IN_PROGRESS, ArchReviewEvent.FITNESS_FAIL_CRITICAL): ArchReviewState.ARCH_REVIEW_ESCALATED,
        (ArchReviewState.ARCH_REFACTOR_PLANNED, ArchReviewEvent.REFACTOR_REQUESTS_CREATED): ArchReviewState.ARCH_REFACTOR_CREATED,
        (ArchReviewState.ARCH_REFACTOR_PLANNED, ArchReviewEvent.REFACTOR_DEFERRED): ArchReviewState.ARCH_NO_ACTION,
        (ArchReviewState.ARCH_REFACTOR_PLANNED, ArchReviewEvent.REFACTOR_BLOCKED): ArchReviewState.ARCH_REVIEW_ESCALATED,
        **{
            (active, ArchReviewEvent.RETRY_THRESHOLD_EXCEEDED): ArchReviewState.ARCH_REVIEW_NEEDS_HUMAN
            for active in (
                ArchReviewState.ARCH_REVIEW_PENDING,
                ArchReviewState.ARCH_REVIEW_IN_PROGRESS,
                ArchReviewState.ARCH_REFACTOR_PLANNED,
            )
        },
    }
)

_DEBT_TABLE: TransitionTable[DebtState, DebtEvent] = TransitionTable(
    {
        (DebtState.DEBT_NEW, DebtEvent.DEBT_TRIAGE): DebtState.DEBT_TRIAGED,
        (DebtState.DEBT_NEW, DebtEvent.DEBT_DEFER): DebtState.DEBT_DEFERRED,
        (DebtState.DEBT_TRIAGED, DebtEvent.DEBT_SCHEDULE): DebtState.DEBT_SCHEDULED,
        (DebtState.DEBT_TRIAGED, DebtEvent.DEBT_DEFER): DebtState.DEBT_DEFERRED,
        (DebtState.DEBT_SCHEDULED, DebtEvent.DEBT_RESOLVE): DebtState.DEBT_RESOLVED,
        (DebtState.DEBT_SCHEDULED, DebtEvent.DEBT_DEFER): DebtState.DEBT_DEFERRED,
        (DebtState.DEBT_DEFERRED, DebtEvent.DEBT_OVERRIDE_ACTIVATE): DebtState.DEBT_TRIAGED,
    }
)

ARCH_REVIEW_TRANSITIONS: Dict[Tuple[ArchReviewState, ArchReviewEvent], ArchReviewState] = dict(_ARCH_REVIEW_TABLE.items())
DEBT_TRANSITIONS: Dict[Tuple[DebtState, DebtEvent], DebtState] = dict(_DEBT_TABLE.items())


def get_next_arch_review_state(state: ArchReviewState, event: ArchReviewEvent) -> ArchReviewState:
    try:
        return _ARCH_REVIEW_TABLE.next_state(state, event)
    except TransitionError as exc:
        raise ArchReviewTransitionError(str(exc)) from exc


def get_next_debt_state(state: DebtState, event: DebtEvent) -> DebtState:
    try:
        return _DEBT_TABLE.next_state(state, event)
    except TransitionError as exc:
        raise DebtTransitionError(str(exc)) from exc


def allowed_events_for_arch_review_state(state: ArchReviewState) -> FrozenSet[ArchReviewEvent]:
    return _ARCH_REVIEW_TABLE.allowed_events(state)


def allowed_events_for_debt_state(state: DebtState) -> FrozenSet[DebtEvent]:
    return _DEBT_TABLE.allowed_events(state)
