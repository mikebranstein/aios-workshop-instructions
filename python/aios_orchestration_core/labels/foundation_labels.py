from typing import Dict, FrozenSet, Iterable, NamedTuple, Optional, Set

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

# Map all known labels (canonical + legacy) to states
_STATE_BY_KNOWN_LABEL: Dict[str, FoundationState] = {
    **{v: k for k, v in FOUNDATION_CANONICAL_LABEL_BY_STATE.items()},
    **{v: k for k, v in FOUNDATION_LEGACY_LABEL_BY_STATE.items()},
}


class FoundationNormalizedLabelState(NamedTuple):
    """Normalized Foundation state read from a mixed label set during migration phases."""

    state: Optional[FoundationState]
    saw_legacy_label: bool
    saw_canonical_label: bool
    conflict_labels: FrozenSet[str]
    unknown_foundation_labels: FrozenSet[str]


def normalize_foundation_state_from_labels(labels: Iterable[str]) -> FoundationNormalizedLabelState:
    """Derive Foundation state from an issue's label set.

    Canonical labels take precedence. Returns a struct with the derived state
    and metadata about label conflicts / unknowns.
    """
    observed_labels = {label.strip() for label in labels if label and label.strip()}

    mapped_states: Set[FoundationState] = set()
    conflict_labels: Set[str] = set()
    saw_legacy = False
    saw_canonical = False
    unknown_foundation_labels: Set[str] = set()

    for label in observed_labels:
        if label in FOUNDATION_CANONICAL_LABEL_BY_STATE.values():
            saw_canonical = True
        if label in FOUNDATION_LEGACY_LABEL_BY_STATE.values():
            saw_legacy = True

        if label in _STATE_BY_KNOWN_LABEL:
            mapped_states.add(_STATE_BY_KNOWN_LABEL[label])
        elif label.startswith("foundation:") or label.startswith("foundation-"):
            unknown_foundation_labels.add(label)

    if not mapped_states:
        return FoundationNormalizedLabelState(
            state=None,
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_foundation_labels=frozenset(unknown_foundation_labels),
        )

    if len(mapped_states) == 1:
        return FoundationNormalizedLabelState(
            state=next(iter(mapped_states)),
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_foundation_labels=frozenset(unknown_foundation_labels),
        )

    # Canonical labels take precedence if they resolve to exactly one state.
    canonical_states = {
        _STATE_BY_KNOWN_LABEL[label]
        for label in observed_labels
        if label in FOUNDATION_CANONICAL_LABEL_BY_STATE.values()
    }
    if len(canonical_states) == 1:
        return FoundationNormalizedLabelState(
            state=next(iter(canonical_states)),
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_foundation_labels=frozenset(unknown_foundation_labels),
        )

    for label in observed_labels:
        if label in _STATE_BY_KNOWN_LABEL:
            conflict_labels.add(label)

    return FoundationNormalizedLabelState(
        state=None,
        saw_legacy_label=saw_legacy,
        saw_canonical_label=saw_canonical,
        conflict_labels=frozenset(conflict_labels),
        unknown_foundation_labels=frozenset(unknown_foundation_labels),
    )