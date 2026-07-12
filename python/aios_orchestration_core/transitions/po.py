from typing import Dict, FrozenSet, Tuple

from aios_orchestration_core.core.transition_table import TransitionError, TransitionTable
from aios_orchestration_core.events.po import POEvent
from aios_orchestration_core.states.po import POState, TERMINAL_PO_STATES


class POTransitionError(ValueError):
    """Raised when a transition is invalid for the PO state machine."""


_PO_TABLE: TransitionTable[POState, POEvent] = TransitionTable(
    {
        (POState.PO_QUEUED, POEvent.ENTERED_PRIORITIZATION): POState.PO_PRIORITIZING,
        (POState.PO_PRIORITIZING, POEvent.PRIORITIZATION_CREATE): POState.PO_CREATING_FEATURES,
        (POState.PO_PRIORITIZING, POEvent.PRIORITIZATION_DEFER): POState.PO_DEFERRED,
        (POState.PO_PRIORITIZING, POEvent.PRIORITIZATION_REJECT): POState.PO_REJECTED,
        (POState.PO_CREATING_FEATURES, POEvent.FEATURE_REQUESTS_COMMITTED): POState.PO_FEATURE_REQUESTS_CREATED,
        **{
            (active, POEvent.RETRY_THRESHOLD_EXCEEDED): POState.PO_NEEDS_HUMAN
            for active in (
                POState.PO_QUEUED,
                POState.PO_PRIORITIZING,
                POState.PO_CREATING_FEATURES,
            )
        },
    }
)

# Expose as plain dict for registry cross-validation.
PO_TRANSITIONS: Dict[Tuple[POState, POEvent], POState] = dict(_PO_TABLE.items())


def get_next_po_state(state: POState, event: POEvent) -> POState:
    try:
        return _PO_TABLE.next_state(state, event)
    except TransitionError as exc:
        raise POTransitionError(str(exc)) from exc


def allowed_events_for_po_state(state: POState) -> FrozenSet[POEvent]:
    return _PO_TABLE.allowed_events(state)
