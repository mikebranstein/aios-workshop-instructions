from typing import Dict, FrozenSet, Iterable, NamedTuple, Optional, Set

from aios_orchestration_core.core.label_registry import LabelRegistry
from aios_orchestration_core.states.po import POState

PO_CANONICAL_LABEL_BY_STATE: Dict[POState, str] = {
    POState.PO_QUEUED: "po:queued",
    POState.PO_PRIORITIZING: "po:prioritizing",
    POState.PO_CREATING_FEATURES: "po:creating-features",
    POState.PO_FEATURE_REQUESTS_CREATED: "po:feature-requests-created",
    POState.PO_DEFERRED: "po:deferred",
    POState.PO_REJECTED: "po:rejected",
    POState.PO_NEEDS_HUMAN: "po:needs-human",
}

PO_CANONICAL_STATE_LABELS: FrozenSet[str] = frozenset(PO_CANONICAL_LABEL_BY_STATE.values())

# Legacy labels match the templates-v2 orchestrator style for bridge compatibility.
PO_LEGACY_LABEL_BY_STATE: Dict[POState, str] = {
    POState.PO_QUEUED: "strategic-opportunity",
    POState.PO_FEATURE_REQUESTS_CREATED: "feature-requests-created",
    POState.PO_DEFERRED: "po-deferred",
    POState.PO_REJECTED: "po-rejected",
}

PO_LABEL_REGISTRY: LabelRegistry[POState] = LabelRegistry(
    canonical=PO_CANONICAL_LABEL_BY_STATE,
    legacy=PO_LEGACY_LABEL_BY_STATE,
)

# Map all known labels (canonical + legacy) to states
_STATE_BY_KNOWN_LABEL: Dict[str, POState] = {
    **{v: k for k, v in PO_CANONICAL_LABEL_BY_STATE.items()},
    **{v: k for k, v in PO_LEGACY_LABEL_BY_STATE.items()},
}


class PONormalizedLabelState(NamedTuple):
    """Normalized PO state read from a mixed label set during migration phases."""

    state: Optional[POState]
    saw_legacy_label: bool
    saw_canonical_label: bool
    conflict_labels: FrozenSet[str]
    unknown_po_labels: FrozenSet[str]


def normalize_po_state_from_labels(labels: Iterable[str]) -> PONormalizedLabelState:
    """Derive PO state from an issue's label set.

    Canonical labels take precedence. Returns a struct with the derived state
    and metadata about label conflicts / unknowns.
    """
    observed_labels = {label.strip() for label in labels if label and label.strip()}

    mapped_states: Set[POState] = set()
    conflict_labels: Set[str] = set()
    saw_legacy = False
    saw_canonical = False
    unknown_po_labels: Set[str] = set()

    for label in observed_labels:
        if label in PO_CANONICAL_LABEL_BY_STATE.values():
            saw_canonical = True
        if label in PO_LEGACY_LABEL_BY_STATE.values():
            saw_legacy = True

        if label in _STATE_BY_KNOWN_LABEL:
            mapped_states.add(_STATE_BY_KNOWN_LABEL[label])
        elif label.startswith("po:") or label.startswith("po-"):
            unknown_po_labels.add(label)

    if not mapped_states:
        return PONormalizedLabelState(
            state=None,
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_po_labels=frozenset(unknown_po_labels),
        )

    if len(mapped_states) == 1:
        return PONormalizedLabelState(
            state=next(iter(mapped_states)),
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_po_labels=frozenset(unknown_po_labels),
        )

    # Canonical labels take precedence if they resolve to exactly one state.
    canonical_states = {
        _STATE_BY_KNOWN_LABEL[label]
        for label in observed_labels
        if label in PO_CANONICAL_LABEL_BY_STATE.values()
    }
    if len(canonical_states) == 1:
        return PONormalizedLabelState(
            state=next(iter(canonical_states)),
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(mapped_states - canonical_states),
            unknown_po_labels=frozenset(unknown_po_labels),
        )

    # Conflict: multiple states mapped
    return PONormalizedLabelState(
        state=None,
        saw_legacy_label=saw_legacy,
        saw_canonical_label=saw_canonical,
        conflict_labels=frozenset(mapped_states),
        unknown_po_labels=frozenset(unknown_po_labels),
    )

