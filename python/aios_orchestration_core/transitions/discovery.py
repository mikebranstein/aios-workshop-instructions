from typing import Dict, FrozenSet, Tuple

from aios_orchestration_core.core.transition_table import TransitionError, TransitionTable
from aios_orchestration_core.events.discovery import DiscoveryEvent
from aios_orchestration_core.states.discovery import DiscoveryState, TERMINAL_DISCOVERY_STATES


class DiscoveryTransitionError(ValueError):
    pass


_DISCOVERY_TABLE: TransitionTable[DiscoveryState, DiscoveryEvent] = TransitionTable(
    {
        (DiscoveryState.DISCOVERY_IDLE, DiscoveryEvent.RUN_TRIGGERED): DiscoveryState.DISCOVERY_RUNNING,
        (DiscoveryState.DISCOVERY_RUNNING, DiscoveryEvent.GATE_MISSING): DiscoveryState.DISCOVERY_HALTED_NO_GATE,
        (DiscoveryState.DISCOVERY_RUNNING, DiscoveryEvent.FOCUS_MISSING): DiscoveryState.DISCOVERY_HALTED_NO_FOCUS,
        (DiscoveryState.DISCOVERY_RUNNING, DiscoveryEvent.IDEA_SCOUT_COMPLETED): DiscoveryState.DISCOVERY_COMPLETE,
    }
)

DISCOVERY_TRANSITIONS: Dict[Tuple[DiscoveryState, DiscoveryEvent], DiscoveryState] = dict(_DISCOVERY_TABLE.items())


def get_next_discovery_state(state: DiscoveryState, event: DiscoveryEvent) -> DiscoveryState:
    try:
        return _DISCOVERY_TABLE.next_state(state, event)
    except TransitionError as exc:
        raise DiscoveryTransitionError(str(exc)) from exc


def allowed_events_for_discovery_state(state: DiscoveryState) -> FrozenSet[DiscoveryEvent]:
    return _DISCOVERY_TABLE.allowed_events(state)
