from typing import Dict, FrozenSet, Iterable, NamedTuple, Optional, Set

from aios_orchestration_core.core.label_registry import LabelRegistry
from aios_orchestration_core.states.dev import DevState

DEV_CANONICAL_LABEL_BY_STATE: Dict[DevState, str] = {
    DevState.DEV_INTAKE: "dev:intake",
    DevState.DEV_DESIGN: "dev:design",
    DevState.DEV_BUILD: "dev:build",
    DevState.DEV_QA: "dev:qa",
    DevState.DEV_POLICY: "dev:policy",
    DevState.DEV_RELEASED: "dev:released",
    DevState.DEV_BLOCKED: "dev:blocked",
    DevState.DEV_NEEDS_HUMAN: "dev:needs-human",
}

DEV_CANONICAL_STATE_LABELS: FrozenSet[str] = frozenset(DEV_CANONICAL_LABEL_BY_STATE.values())

DEV_LEGACY_LABEL_BY_STATE: Dict[DevState, str] = {
    DevState.DEV_INTAKE: "feature-request",
    DevState.DEV_DESIGN: "intake-approved",
    DevState.DEV_BUILD: "design-approved",
    DevState.DEV_QA: "build-complete",
    DevState.DEV_POLICY: "qa-passed",
    DevState.DEV_RELEASED: "released",
    DevState.DEV_BLOCKED: "feature-blocked",
}

DEV_LABEL_REGISTRY: LabelRegistry[DevState] = LabelRegistry(
    canonical=DEV_CANONICAL_LABEL_BY_STATE,
    legacy=DEV_LEGACY_LABEL_BY_STATE,
)

# Map all known labels (canonical + legacy) to states
_STATE_BY_KNOWN_LABEL: Dict[str, DevState] = {
    **{v: k for k, v in DEV_CANONICAL_LABEL_BY_STATE.items()},
    **{v: k for k, v in DEV_LEGACY_LABEL_BY_STATE.items()},
}


class DevNormalizedLabelState(NamedTuple):
    """Normalized Dev state read from a mixed label set during migration phases."""

    state: Optional[DevState]
    saw_legacy_label: bool
    saw_canonical_label: bool
    conflict_labels: FrozenSet[str]
    unknown_dev_labels: FrozenSet[str]


def normalize_dev_state_from_labels(labels: Iterable[str]) -> DevNormalizedLabelState:
    """Derive Dev state from an issue's label set.

    Canonical labels take precedence. Returns a struct with the derived state
    and metadata about label conflicts / unknowns.
    """
    observed_labels = {label.strip() for label in labels if label and label.strip()}

    mapped_states: Set[DevState] = set()
    conflict_labels: Set[str] = set()
    saw_legacy = False
    saw_canonical = False
    unknown_dev_labels: Set[str] = set()

    for label in observed_labels:
        if label in DEV_CANONICAL_LABEL_BY_STATE.values():
            saw_canonical = True
        if label in DEV_LEGACY_LABEL_BY_STATE.values():
            saw_legacy = True

        if label in _STATE_BY_KNOWN_LABEL:
            mapped_states.add(_STATE_BY_KNOWN_LABEL[label])
        elif label.startswith("dev:") or label.startswith("dev-"):
            unknown_dev_labels.add(label)

    if not mapped_states:
        return DevNormalizedLabelState(
            state=None,
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_dev_labels=frozenset(unknown_dev_labels),
        )

    if len(mapped_states) == 1:
        return DevNormalizedLabelState(
            state=next(iter(mapped_states)),
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_dev_labels=frozenset(unknown_dev_labels),
        )

    # Canonical labels take precedence if they resolve to exactly one state.
    canonical_states = {
        _STATE_BY_KNOWN_LABEL[label]
        for label in observed_labels
        if label in DEV_CANONICAL_LABEL_BY_STATE.values()
    }
    if len(canonical_states) == 1:
        return DevNormalizedLabelState(
            state=next(iter(canonical_states)),
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_dev_labels=frozenset(unknown_dev_labels),
        )

    for label in observed_labels:
        if label in _STATE_BY_KNOWN_LABEL:
            conflict_labels.add(label)

    return DevNormalizedLabelState(
        state=None,
        saw_legacy_label=saw_legacy,
        saw_canonical_label=saw_canonical,
        conflict_labels=frozenset(conflict_labels),
        unknown_dev_labels=frozenset(unknown_dev_labels),
    )