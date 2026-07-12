from typing import Dict, FrozenSet, Tuple

from aios_orchestration_core.core.transition_table import TransitionError, TransitionTable
from aios_orchestration_core.events.dev import DevEvent
from aios_orchestration_core.states.dev import DevState, TERMINAL_DEV_STATES


class DevTransitionError(ValueError):
    """Raised when a transition is invalid for the dev state machine."""


_DEV_TABLE: TransitionTable[DevState, DevEvent] = TransitionTable(
    {
        (DevState.DEV_INTAKE, DevEvent.INTAKE_APPROVED): DevState.DEV_DESIGN,
        (DevState.DEV_INTAKE, DevEvent.INTAKE_BLOCKED): DevState.DEV_BLOCKED,
        (DevState.DEV_DESIGN, DevEvent.DESIGN_APPROVED): DevState.DEV_BUILD,
        (DevState.DEV_DESIGN, DevEvent.DESIGN_REVISE): DevState.DEV_INTAKE,     # feedback loop
        (DevState.DEV_DESIGN, DevEvent.DESIGN_BLOCKED): DevState.DEV_BLOCKED,
        (DevState.DEV_BUILD, DevEvent.BUILD_COMPLETE): DevState.DEV_QA,
        (DevState.DEV_BUILD, DevEvent.BUILD_BLOCKED): DevState.DEV_BLOCKED,
        (DevState.DEV_QA, DevEvent.QA_PASSED): DevState.DEV_POLICY,
        (DevState.DEV_QA, DevEvent.QA_FAILED): DevState.DEV_DESIGN,             # feedback loop
        (DevState.DEV_POLICY, DevEvent.POLICY_APPROVED): DevState.DEV_RELEASED,
        (DevState.DEV_POLICY, DevEvent.POLICY_REVIEW_REQUIRED): DevState.DEV_NEEDS_HUMAN,
        **{
            (active, DevEvent.RETRY_THRESHOLD_EXCEEDED): DevState.DEV_NEEDS_HUMAN
            for active in (
                DevState.DEV_INTAKE,
                DevState.DEV_DESIGN,
                DevState.DEV_BUILD,
                DevState.DEV_QA,
                DevState.DEV_POLICY,
            )
        },
    }
)

DEV_TRANSITIONS: Dict[Tuple[DevState, DevEvent], DevState] = dict(_DEV_TABLE.items())


def get_next_dev_state(state: DevState, event: DevEvent) -> DevState:
    try:
        return _DEV_TABLE.next_state(state, event)
    except TransitionError as exc:
        raise DevTransitionError(str(exc)) from exc


def allowed_events_for_dev_state(state: DevState) -> FrozenSet[DevEvent]:
    return _DEV_TABLE.allowed_events(state)
