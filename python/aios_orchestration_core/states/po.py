from enum import Enum


class POState(str, Enum):
    """Typed PO states for the product-owner state machine."""

    PO_QUEUED = "PO_QUEUED"
    PO_PRIORITIZING = "PO_PRIORITIZING"
    PO_CREATING_FEATURES = "PO_CREATING_FEATURES"
    PO_FEATURE_REQUESTS_CREATED = "PO_FEATURE_REQUESTS_CREATED"
    PO_DEFERRED = "PO_DEFERRED"
    PO_REJECTED = "PO_REJECTED"
    PO_NEEDS_HUMAN = "PO_NEEDS_HUMAN"


TERMINAL_PO_STATES = {
    POState.PO_FEATURE_REQUESTS_CREATED,
    POState.PO_DEFERRED,
    POState.PO_REJECTED,
    POState.PO_NEEDS_HUMAN,
}


def is_terminal_po_state(state: POState) -> bool:
    return state in TERMINAL_PO_STATES
