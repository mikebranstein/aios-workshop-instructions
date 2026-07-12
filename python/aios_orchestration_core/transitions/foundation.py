from typing import Dict, FrozenSet, Tuple

from aios_orchestration_core.core.transition_table import TransitionError, TransitionTable
from aios_orchestration_core.events.foundation import FoundationEvent
from aios_orchestration_core.states.foundation import FoundationState, TERMINAL_FOUNDATION_STATES


class FoundationTransitionError(ValueError):
    pass


_FOUNDATION_TABLE: TransitionTable[FoundationState, FoundationEvent] = TransitionTable(
    {
        (FoundationState.FOUNDATION_NEEDED, FoundationEvent.FOUNDATION_STARTED): FoundationState.FOUNDATION_IN_PROGRESS,
        (FoundationState.FOUNDATION_IN_PROGRESS, FoundationEvent.RESEARCH_RECOMMEND): FoundationState.FOUNDATION_REVIEW,
        (FoundationState.FOUNDATION_IN_PROGRESS, FoundationEvent.RESEARCH_NEEDS_MORE): FoundationState.FOUNDATION_IN_PROGRESS,
        (FoundationState.FOUNDATION_IN_PROGRESS, FoundationEvent.RESEARCH_BLOCKED): FoundationState.FOUNDATION_BLOCKED,
        (FoundationState.FOUNDATION_REVIEW, FoundationEvent.APPROVE_FOUNDATION): FoundationState.FOUNDATION_APPROVED,
        (FoundationState.FOUNDATION_REVIEW, FoundationEvent.REVISE_FOUNDATION): FoundationState.FOUNDATION_IN_PROGRESS,
        (FoundationState.FOUNDATION_REVIEW, FoundationEvent.BLOCK_FOUNDATION): FoundationState.FOUNDATION_BLOCKED,
        **{
            (active, FoundationEvent.RETRY_THRESHOLD_EXCEEDED): FoundationState.FOUNDATION_NEEDS_HUMAN
            for active in (
                FoundationState.FOUNDATION_NEEDED,
                FoundationState.FOUNDATION_IN_PROGRESS,
                FoundationState.FOUNDATION_REVIEW,
            )
        },
    }
)

FOUNDATION_TRANSITIONS: Dict[Tuple[FoundationState, FoundationEvent], FoundationState] = dict(_FOUNDATION_TABLE.items())


def get_next_foundation_state(state: FoundationState, event: FoundationEvent) -> FoundationState:
    try:
        return _FOUNDATION_TABLE.next_state(state, event)
    except TransitionError as exc:
        raise FoundationTransitionError(str(exc)) from exc


def allowed_events_for_foundation_state(state: FoundationState) -> FrozenSet[FoundationEvent]:
    return _FOUNDATION_TABLE.allowed_events(state)
