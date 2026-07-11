from typing import Dict, FrozenSet, Set, Tuple

from aios_orchestration_core.events.pm import PMEvent
from aios_orchestration_core.states.pm import PMState, TERMINAL_PM_STATES


class PMTransitionError(ValueError):
    """Raised when a transition is invalid for the PM state machine."""


PM_TRANSITIONS: Dict[Tuple[PMState, PMEvent], PMState] = {
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
}

for _active in (
    PMState.PM_QUEUED,
    PMState.PM_PHASE1_VALIDATING,
    PMState.PM_RESEARCH_PLANNING,
    PMState.PM_RESEARCH_WAITING,
    PMState.PM_RESEARCH_SYNTHESIZING,
    PMState.PM_PHASE2_VALIDATING,
):
    PM_TRANSITIONS[(_active, PMEvent.RETRY_THRESHOLD_EXCEEDED)] = PMState.PM_NEEDS_HUMAN


def get_next_pm_state(state: PMState, event: PMEvent) -> PMState:
    key = (state, event)
    if key not in PM_TRANSITIONS:
        raise PMTransitionError(f"No PM transition defined for state={state} event={event}")
    return PM_TRANSITIONS[key]


def allowed_events_for_state(state: PMState) -> FrozenSet[PMEvent]:
    events: Set[PMEvent] = set()
    for source_state, event in PM_TRANSITIONS:
        if source_state == state:
            events.add(event)
    return frozenset(events)
