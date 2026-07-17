from typing import Dict, FrozenSet, Tuple

from aios_orchestration_core.core.transition_table import TransitionError, TransitionTable
from aios_orchestration_core.events.foundation import FoundationEvent
from aios_orchestration_core.states.foundation import FoundationState, TERMINAL_FOUNDATION_STATES


class FoundationTransitionError(ValueError):
    pass


_FOUNDATION_TABLE: TransitionTable[FoundationState, FoundationEvent] = TransitionTable(
    {
        (FoundationState.FOUNDATION_NEEDED, FoundationEvent.FOUNDATION_STARTED): FoundationState.FOUNDATION_INTENT_CAPTURE_CREATE,
        (FoundationState.FOUNDATION_INTENT_CAPTURE_CREATE, FoundationEvent.INTENT_CAPTURE_CREATED): FoundationState.FOUNDATION_INTENT_CAPTURE_VERIFY,
        (FoundationState.FOUNDATION_INTENT_CAPTURE_VERIFY, FoundationEvent.INTENT_CAPTURE_VERIFIED): FoundationState.FOUNDATION_SHELL_DESIGN_CREATE,
        (FoundationState.FOUNDATION_INTENT_CAPTURE_VERIFY, FoundationEvent.INTENT_CAPTURE_REVISE): FoundationState.FOUNDATION_INTENT_CAPTURE_CREATE,
        (FoundationState.FOUNDATION_INTENT_CAPTURE_VERIFY, FoundationEvent.INTENT_CAPTURE_BLOCK): FoundationState.FOUNDATION_BLOCKED,
        (FoundationState.FOUNDATION_SHELL_DESIGN_CREATE, FoundationEvent.SHELL_DESIGN_CREATED): FoundationState.FOUNDATION_SHELL_DESIGN_VERIFY,
        (FoundationState.FOUNDATION_SHELL_DESIGN_VERIFY, FoundationEvent.SHELL_DESIGN_VERIFIED): FoundationState.FOUNDATION_BACKLOG_BUILD_CREATE,
        (FoundationState.FOUNDATION_SHELL_DESIGN_VERIFY, FoundationEvent.SHELL_DESIGN_REVISE): FoundationState.FOUNDATION_SHELL_DESIGN_CREATE,
        (FoundationState.FOUNDATION_SHELL_DESIGN_VERIFY, FoundationEvent.SHELL_DESIGN_BLOCK): FoundationState.FOUNDATION_BLOCKED,
        (FoundationState.FOUNDATION_BACKLOG_BUILD_CREATE, FoundationEvent.BACKLOG_BUILD_CREATED): FoundationState.FOUNDATION_BACKLOG_BUILD_VERIFY,
        (FoundationState.FOUNDATION_BACKLOG_BUILD_VERIFY, FoundationEvent.BACKLOG_BUILD_VERIFIED): FoundationState.FOUNDATION_READINESS_ASSESS_CREATE,
        (FoundationState.FOUNDATION_BACKLOG_BUILD_VERIFY, FoundationEvent.BACKLOG_BUILD_REVISE): FoundationState.FOUNDATION_BACKLOG_BUILD_CREATE,
        (FoundationState.FOUNDATION_BACKLOG_BUILD_VERIFY, FoundationEvent.BACKLOG_BUILD_BLOCK): FoundationState.FOUNDATION_BLOCKED,
        (FoundationState.FOUNDATION_READINESS_ASSESS_CREATE, FoundationEvent.READINESS_ASSESS_CREATED): FoundationState.FOUNDATION_READINESS_ASSESS_VERIFY,
        (FoundationState.FOUNDATION_READINESS_ASSESS_VERIFY, FoundationEvent.READINESS_ASSESS_VERIFIED): FoundationState.FOUNDATION_HANDOFF_PACK_CREATE,
        (FoundationState.FOUNDATION_READINESS_ASSESS_VERIFY, FoundationEvent.READINESS_ASSESS_REVISE): FoundationState.FOUNDATION_READINESS_ASSESS_CREATE,
        (FoundationState.FOUNDATION_READINESS_ASSESS_VERIFY, FoundationEvent.READINESS_ASSESS_BLOCK): FoundationState.FOUNDATION_BLOCKED,
        (FoundationState.FOUNDATION_HANDOFF_PACK_CREATE, FoundationEvent.HANDOFF_PACK_CREATED): FoundationState.FOUNDATION_HANDOFF_PACK_VERIFY,
        (FoundationState.FOUNDATION_HANDOFF_PACK_VERIFY, FoundationEvent.HANDOFF_PACK_VERIFIED): FoundationState.FOUNDATION_APPROVED,
        (FoundationState.FOUNDATION_HANDOFF_PACK_VERIFY, FoundationEvent.HANDOFF_PACK_REVISE): FoundationState.FOUNDATION_HANDOFF_PACK_CREATE,
        (FoundationState.FOUNDATION_HANDOFF_PACK_VERIFY, FoundationEvent.HANDOFF_PACK_BLOCK): FoundationState.FOUNDATION_BLOCKED,
        **{
            (active, FoundationEvent.RETRY_THRESHOLD_EXCEEDED): FoundationState.FOUNDATION_NEEDS_HUMAN
            for active in (
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
