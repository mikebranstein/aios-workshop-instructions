from typing import Dict, FrozenSet, Set, Tuple

from aios_orchestration_core.core.transition_table import TransitionError, TransitionTable
from aios_orchestration_core.events.pm import PMEvent
from aios_orchestration_core.states.pm import PMState, TERMINAL_PM_STATES


class PMTransitionError(ValueError):
    """Raised when a transition is invalid for the PM state machine."""


_PM_TABLE: TransitionTable[PMState, PMEvent] = TransitionTable(
    {
        (PMState.PM_QUEUED, PMEvent.FOUNDATION_GATE_PASSED): PMState.PM_PHASE1_VALIDATING,
        (PMState.PM_PHASE1_VALIDATING, PMEvent.PHASE1_PROVISIONAL_CHAMPION): PMState.PM_RESEARCH_PLANNING,
        (PMState.PM_PHASE1_VALIDATING, PMEvent.PHASE1_DEFER): PMState.PM_DEFERRED,
        (PMState.PM_PHASE1_VALIDATING, PMEvent.PHASE1_BLOCK): PMState.PM_BLOCKED,
        (PMState.PM_RESEARCH_PLANNING, PMEvent.RESEARCH_TASKS_CREATED): PMState.PM_RESEARCH_WAITING,
        (PMState.PM_RESEARCH_WAITING, PMEvent.LINKED_RESEARCH_ALL_CLOSED): PMState.PM_RESEARCH_SYNTHESIZING,
        (PMState.PM_RESEARCH_SYNTHESIZING, PMEvent.SYNTHESIS_READY): PMState.PM_PHASE2_VALIDATING,
        (PMState.PM_PHASE2_VALIDATING, PMEvent.PHASE2_CHAMPION): PMState.PM_OUTPUT_PUBLISHED,
        (PMState.PM_PHASE2_VALIDATING, PMEvent.PHASE2_DEFER): PMState.PM_DEFERRED,
        (PMState.PM_PHASE2_VALIDATING, PMEvent.PHASE2_BLOCK): PMState.PM_BLOCKED,
        (PMState.PM_PHASE2_VALIDATING, PMEvent.PHASE2_ESCALATE): PMState.PM_ESCALATED,
        **{
            (active, PMEvent.RETRY_THRESHOLD_EXCEEDED): PMState.PM_NEEDS_HUMAN
            for active in (
                PMState.PM_QUEUED,
                PMState.PM_PHASE1_VALIDATING,
                PMState.PM_RESEARCH_PLANNING,
                PMState.PM_RESEARCH_WAITING,
                PMState.PM_RESEARCH_SYNTHESIZING,
                PMState.PM_PHASE2_VALIDATING,
            )
        },
    }
)

# Expose as a plain dict for any code that iterates PM_TRANSITIONS directly.
PM_TRANSITIONS: Dict[Tuple[PMState, PMEvent], PMState] = dict(_PM_TABLE.items())


def get_next_pm_state(state: PMState, event: PMEvent) -> PMState:
    try:
        return _PM_TABLE.next_state(state, event)
    except TransitionError as exc:
        raise PMTransitionError(str(exc)) from exc


def allowed_events_for_state(state: PMState) -> FrozenSet[PMEvent]:
    return _PM_TABLE.allowed_events(state)
