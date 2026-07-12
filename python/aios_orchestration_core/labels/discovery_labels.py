"""Label registry and normalization for Discovery state machine.

This module defines canonical and legacy labels for discovery states,
providing a label registry and normalization function to derive state
from mixed label sets during migration phases.
"""

from typing import Dict, FrozenSet, Iterable, NamedTuple, Optional, Set

from aios_orchestration_core.core.label_registry import LabelRegistry
from aios_orchestration_core.states.discovery import DiscoveryState

DISCOVERY_CANONICAL_LABEL_BY_STATE: Dict[DiscoveryState, str] = {
    DiscoveryState.DISCOVERY_IDLE: "discovery:idle",
    DiscoveryState.DISCOVERY_RUNNING: "discovery:running",
    DiscoveryState.DISCOVERY_COMPLETE: "discovery:complete",
    DiscoveryState.DISCOVERY_HALTED_NO_GATE: "discovery:halted-no-gate",
    DiscoveryState.DISCOVERY_HALTED_NO_FOCUS: "discovery:halted-no-focus",
}

DISCOVERY_CANONICAL_STATE_LABELS: FrozenSet[str] = frozenset(
    DISCOVERY_CANONICAL_LABEL_BY_STATE.values()
)

# Legacy labels for bridge compatibility during migration
DISCOVERY_LEGACY_LABEL_BY_STATE: Dict[DiscoveryState, str] = {
    DiscoveryState.DISCOVERY_IDLE: "discovery-idle",
    DiscoveryState.DISCOVERY_RUNNING: "discovery-running",
    DiscoveryState.DISCOVERY_COMPLETE: "discovery-complete",
    DiscoveryState.DISCOVERY_HALTED_NO_GATE: "discovery-halted-no-gate",
    DiscoveryState.DISCOVERY_HALTED_NO_FOCUS: "discovery-halted-no-focus",
}

DISCOVERY_LABEL_REGISTRY: LabelRegistry[DiscoveryState] = LabelRegistry(
    canonical=DISCOVERY_CANONICAL_LABEL_BY_STATE,
    legacy=DISCOVERY_LEGACY_LABEL_BY_STATE,
)

# Map all known labels (canonical + legacy) to states
_STATE_BY_KNOWN_LABEL: Dict[str, DiscoveryState] = {
    **{v: k for k, v in DISCOVERY_CANONICAL_LABEL_BY_STATE.items()},
    **{v: k for k, v in DISCOVERY_LEGACY_LABEL_BY_STATE.items()},
}


class DiscoveryNormalizedLabelState(NamedTuple):
    """Normalized Discovery state read from a mixed label set during migration phases."""

    state: Optional[DiscoveryState]
    saw_legacy_label: bool
    saw_canonical_label: bool
    conflict_labels: FrozenSet[str]
    unknown_discovery_labels: FrozenSet[str]


def normalize_discovery_state_from_labels(
    labels: Iterable[str],
) -> DiscoveryNormalizedLabelState:
    """Derive Discovery state from an issue's label set.

    Canonical labels take precedence over legacy labels. Returns a struct with
    the derived state and metadata about label conflicts / unknowns.

    Args:
        labels: Iterable of label strings from a GitHub issue.

    Returns:
        DiscoveryNormalizedLabelState with state and conflict info.
    """
    observed_labels = {label.strip() for label in labels if label and label.strip()}

    mapped_states: Set[DiscoveryState] = set()
    conflict_labels: Set[str] = set()
    saw_legacy = False
    saw_canonical = False
    unknown_discovery_labels: Set[str] = set()

    for label in observed_labels:
        if label in DISCOVERY_CANONICAL_LABEL_BY_STATE.values():
            saw_canonical = True
        if label in DISCOVERY_LEGACY_LABEL_BY_STATE.values():
            saw_legacy = True

        if label in _STATE_BY_KNOWN_LABEL:
            mapped_states.add(_STATE_BY_KNOWN_LABEL[label])
        elif label.startswith("discovery:") or label.startswith("discovery-"):
            unknown_discovery_labels.add(label)

    if not mapped_states:
        return DiscoveryNormalizedLabelState(
            state=None,
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_discovery_labels=frozenset(unknown_discovery_labels),
        )

    if len(mapped_states) == 1:
        return DiscoveryNormalizedLabelState(
            state=next(iter(mapped_states)),
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_discovery_labels=frozenset(unknown_discovery_labels),
        )

    # Canonical labels take precedence if they resolve to exactly one state.
    canonical_states = {
        _STATE_BY_KNOWN_LABEL[label]
        for label in observed_labels
        if label in DISCOVERY_CANONICAL_LABEL_BY_STATE.values()
    }
    if len(canonical_states) == 1:
        return DiscoveryNormalizedLabelState(
            state=next(iter(canonical_states)),
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_discovery_labels=frozenset(unknown_discovery_labels),
        )

    # Conflict: multiple states mapped
    for label in observed_labels:
        if label in _STATE_BY_KNOWN_LABEL:
            conflict_labels.add(label)

    return DiscoveryNormalizedLabelState(
        state=None,
        saw_legacy_label=saw_legacy,
        saw_canonical_label=saw_canonical,
        conflict_labels=frozenset(conflict_labels),
        unknown_discovery_labels=frozenset(unknown_discovery_labels),
    )