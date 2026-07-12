from dataclasses import dataclass
from typing import FrozenSet, Iterable, List, Optional, Set

from aios_orchestration_core.core.label_registry import LabelRegistry
from aios_orchestration_core.states.pm import PMState


PM_CANONICAL_LABEL_BY_STATE = {
    PMState.PM_QUEUED: "pm:queued",
    PMState.PM_PHASE1_VALIDATING: "pm:phase1-validating",
    PMState.PM_RESEARCH_PLANNING: "pm:research-planning",
    PMState.PM_RESEARCH_WAITING: "pm:research-wait",
    PMState.PM_RESEARCH_SYNTHESIZING: "pm:research-synthesizing",
    PMState.PM_PHASE2_VALIDATING: "pm:phase2-validating",
    PMState.PM_OUTPUT_PUBLISHED: "pm:output-published",
    PMState.PM_DEFERRED: "pm:deferred",
    PMState.PM_BLOCKED: "pm:blocked",
    PMState.PM_ESCALATED: "pm:escalated",
    PMState.PM_NEEDS_HUMAN: "pm:needs-human",
}

PM_CANONICAL_STATE_LABELS = frozenset(PM_CANONICAL_LABEL_BY_STATE.values())

PM_LEGACY_LABEL_BY_STATE = {
    PMState.PM_QUEUED: "pm-idea",
    PMState.PM_PHASE1_VALIDATING: "pm-validating",
    PMState.PM_RESEARCH_WAITING: "pm-provisional-champion",
    PMState.PM_PHASE2_VALIDATING: "pm-finalizing",
    PMState.PM_OUTPUT_PUBLISHED: "pm-opportunity",
    PMState.PM_DEFERRED: "pm-deferred",
    PMState.PM_BLOCKED: "pm-blocked",
    PMState.PM_ESCALATED: "pm-escalated",
    PMState.PM_NEEDS_HUMAN: "needs_human",
}

# Canonical LabelRegistry instance for PM — used by new multi-loop code.
PM_LABEL_REGISTRY: LabelRegistry[PMState] = LabelRegistry(
    canonical=PM_CANONICAL_LABEL_BY_STATE,
    legacy=PM_LEGACY_LABEL_BY_STATE,
)

_STATE_BY_KNOWN_LABEL = {
    **{label: state for state, label in PM_CANONICAL_LABEL_BY_STATE.items()},
    **{label: state for state, label in PM_LEGACY_LABEL_BY_STATE.items()},
}


@dataclass(frozen=True)
class PMNormalizedLabelState:
    """Normalized PM state read from a mixed label set during migration phases."""

    state: Optional[PMState]
    saw_legacy_label: bool
    saw_canonical_label: bool
    conflict_labels: FrozenSet[str]
    unknown_pm_labels: FrozenSet[str]


def normalize_pm_state_from_labels(labels: Iterable[str]) -> PMNormalizedLabelState:
    observed_labels = {label.strip() for label in labels if label and label.strip()}

    mapped_states: Set[PMState] = set()
    conflict_labels: Set[str] = set()
    saw_legacy = False
    saw_canonical = False
    unknown_pm_labels: Set[str] = set()

    for label in observed_labels:
        if label in PM_CANONICAL_LABEL_BY_STATE.values():
            saw_canonical = True
        if label in PM_LEGACY_LABEL_BY_STATE.values():
            saw_legacy = True

        if label in _STATE_BY_KNOWN_LABEL:
            mapped_states.add(_STATE_BY_KNOWN_LABEL[label])
        elif label.startswith("pm:") or label.startswith("pm-"):
            unknown_pm_labels.add(label)

    if not mapped_states:
        return PMNormalizedLabelState(
            state=None,
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_pm_labels=frozenset(unknown_pm_labels),
        )

    if len(mapped_states) == 1:
        return PMNormalizedLabelState(
            state=next(iter(mapped_states)),
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_pm_labels=frozenset(unknown_pm_labels),
        )

    # Canonical labels take precedence if they resolve to exactly one state.
    canonical_states = {
        _STATE_BY_KNOWN_LABEL[label]
        for label in observed_labels
        if label in PM_CANONICAL_LABEL_BY_STATE.values()
    }
    if len(canonical_states) == 1:
        return PMNormalizedLabelState(
            state=next(iter(canonical_states)),
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_pm_labels=frozenset(unknown_pm_labels),
        )

    for label in observed_labels:
        if label in _STATE_BY_KNOWN_LABEL:
            conflict_labels.add(label)

    return PMNormalizedLabelState(
        state=None,
        saw_legacy_label=saw_legacy,
        saw_canonical_label=saw_canonical,
        conflict_labels=frozenset(conflict_labels),
        unknown_pm_labels=frozenset(unknown_pm_labels),
    )


def labels_for_pm_state(state: PMState, dual_write_legacy: bool) -> List[str]:
    labels = [PM_CANONICAL_LABEL_BY_STATE[state]]
    if dual_write_legacy and state in PM_LEGACY_LABEL_BY_STATE:
        labels.append(PM_LEGACY_LABEL_BY_STATE[state])
    return labels
