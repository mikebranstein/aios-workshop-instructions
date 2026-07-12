from typing import Dict, FrozenSet

from aios_orchestration_core.core.label_registry import LabelRegistry
from aios_orchestration_core.states.foundation import FoundationState

FOUNDATION_CANONICAL_LABEL_BY_STATE: Dict[FoundationState, str] = {
    FoundationState.FOUNDATION_NEEDED: "foundation:needed",
    FoundationState.FOUNDATION_IN_PROGRESS: "foundation:in-progress",
    FoundationState.FOUNDATION_REVIEW: "foundation:review",
    FoundationState.FOUNDATION_APPROVED: "foundation:approved",
    FoundationState.FOUNDATION_BLOCKED: "foundation:blocked",
    FoundationState.FOUNDATION_NEEDS_HUMAN: "foundation:needs-human",
}

FOUNDATION_CANONICAL_STATE_LABELS: FrozenSet[str] = frozenset(FOUNDATION_CANONICAL_LABEL_BY_STATE.values())

FOUNDATION_LEGACY_LABEL_BY_STATE: Dict[FoundationState, str] = {
    FoundationState.FOUNDATION_NEEDED: "foundation-needed",
    FoundationState.FOUNDATION_IN_PROGRESS: "foundation-in-progress",
    FoundationState.FOUNDATION_REVIEW: "foundation-review",
    FoundationState.FOUNDATION_APPROVED: "foundation-approved",
    FoundationState.FOUNDATION_BLOCKED: "foundation-blocked",
}

FOUNDATION_LABEL_REGISTRY: LabelRegistry[FoundationState] = LabelRegistry(
    canonical=FOUNDATION_CANONICAL_LABEL_BY_STATE,
    legacy=FOUNDATION_LEGACY_LABEL_BY_STATE,
)
