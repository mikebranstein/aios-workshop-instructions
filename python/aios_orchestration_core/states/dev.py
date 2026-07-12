from enum import Enum


class DevState(str, Enum):
    """Typed states for the development pipeline."""

    DEV_INTAKE = "DEV_INTAKE"
    DEV_DESIGN = "DEV_DESIGN"
    DEV_BUILD = "DEV_BUILD"
    DEV_QA = "DEV_QA"
    DEV_POLICY = "DEV_POLICY"
    DEV_RELEASED = "DEV_RELEASED"
    DEV_BLOCKED = "DEV_BLOCKED"
    DEV_NEEDS_HUMAN = "DEV_NEEDS_HUMAN"


TERMINAL_DEV_STATES = {
    DevState.DEV_RELEASED,
    DevState.DEV_BLOCKED,
    DevState.DEV_NEEDS_HUMAN,
}


def is_terminal_dev_state(state: DevState) -> bool:
    return state in TERMINAL_DEV_STATES
