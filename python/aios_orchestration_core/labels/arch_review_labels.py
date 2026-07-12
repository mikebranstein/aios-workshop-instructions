from typing import Dict, FrozenSet, Iterable, NamedTuple, Optional, Set

from aios_orchestration_core.core.label_registry import LabelRegistry
from aios_orchestration_core.states.arch_review import ArchReviewState, DebtState

ARCH_REVIEW_CANONICAL_LABEL_BY_STATE: Dict[ArchReviewState, str] = {
    ArchReviewState.ARCH_REVIEW_PENDING: "arch:review-pending",
    ArchReviewState.ARCH_REVIEW_IN_PROGRESS: "arch:review-in-progress",
    ArchReviewState.ARCH_NO_ACTION: "arch:no-action",
    ArchReviewState.ARCH_REFACTOR_PLANNED: "arch:refactor-planned",
    ArchReviewState.ARCH_REFACTOR_CREATED: "arch:refactor-created",
    ArchReviewState.ARCH_REVIEW_ESCALATED: "arch:review-escalated",
    ArchReviewState.ARCH_REVIEW_NEEDS_HUMAN: "arch:needs-human",
}

ARCH_REVIEW_CANONICAL_STATE_LABELS: FrozenSet[str] = frozenset(ARCH_REVIEW_CANONICAL_LABEL_BY_STATE.values())

ARCH_REVIEW_LEGACY_LABEL_BY_STATE: Dict[ArchReviewState, str] = {
    ArchReviewState.ARCH_REVIEW_PENDING: "arch-review-pending",
    ArchReviewState.ARCH_REVIEW_IN_PROGRESS: "arch-review-in-progress",
    ArchReviewState.ARCH_NO_ACTION: "arch-review-no-action",
    ArchReviewState.ARCH_REFACTOR_PLANNED: "arch-refactor-planned",
    ArchReviewState.ARCH_REFACTOR_CREATED: "arch-refactor-requests-created",
    ArchReviewState.ARCH_REVIEW_ESCALATED: "arch-review-escalated",
}

ARCH_REVIEW_LABEL_REGISTRY: LabelRegistry[ArchReviewState] = LabelRegistry(
    canonical=ARCH_REVIEW_CANONICAL_LABEL_BY_STATE,
    legacy=ARCH_REVIEW_LEGACY_LABEL_BY_STATE,
)

DEBT_CANONICAL_LABEL_BY_STATE: Dict[DebtState, str] = {
    DebtState.DEBT_NEW: "debt:new",
    DebtState.DEBT_TRIAGED: "debt:triaged",
    DebtState.DEBT_SCHEDULED: "debt:scheduled",
    DebtState.DEBT_RESOLVED: "debt:resolved",
    DebtState.DEBT_DEFERRED: "debt:deferred",
}

DEBT_CANONICAL_STATE_LABELS: FrozenSet[str] = frozenset(DEBT_CANONICAL_LABEL_BY_STATE.values())

DEBT_LEGACY_LABEL_BY_STATE: Dict[DebtState, str] = {
    DebtState.DEBT_NEW: "architecture-debt",
    DebtState.DEBT_TRIAGED: "debt-triaged",
    DebtState.DEBT_SCHEDULED: "debt-scheduled",
    DebtState.DEBT_RESOLVED: "debt-resolved",
    DebtState.DEBT_DEFERRED: "debt-deferred",
}

DEBT_LABEL_REGISTRY: LabelRegistry[DebtState] = LabelRegistry(
    canonical=DEBT_CANONICAL_LABEL_BY_STATE,
    legacy=DEBT_LEGACY_LABEL_BY_STATE,
)


# ArchReview normalization

_ARCH_REVIEW_STATE_BY_KNOWN_LABEL: Dict[str, ArchReviewState] = {
    **{v: k for k, v in ARCH_REVIEW_CANONICAL_LABEL_BY_STATE.items()},
    **{v: k for k, v in ARCH_REVIEW_LEGACY_LABEL_BY_STATE.items()},
}


class ArchReviewNormalizedLabelState(NamedTuple):
    """Normalized ArchReview state read from a mixed label set during migration phases."""

    state: Optional[ArchReviewState]
    saw_legacy_label: bool
    saw_canonical_label: bool
    conflict_labels: FrozenSet[str]
    unknown_arch_review_labels: FrozenSet[str]


def normalize_arch_review_state_from_labels(
    labels: Iterable[str],
) -> ArchReviewNormalizedLabelState:
    """Derive ArchReview state from an issue's label set.

    Canonical labels take precedence over legacy labels. Returns a struct with
    the derived state and metadata about label conflicts / unknowns.

    Args:
        labels: Iterable of label strings from a GitHub issue.

    Returns:
        ArchReviewNormalizedLabelState with state and conflict info.
    """
    observed_labels = {label.strip() for label in labels if label and label.strip()}

    mapped_states: Set[ArchReviewState] = set()
    conflict_labels: Set[str] = set()
    saw_legacy = False
    saw_canonical = False
    unknown_arch_review_labels: Set[str] = set()

    for label in observed_labels:
        if label in ARCH_REVIEW_CANONICAL_LABEL_BY_STATE.values():
            saw_canonical = True
        if label in ARCH_REVIEW_LEGACY_LABEL_BY_STATE.values():
            saw_legacy = True

        if label in _ARCH_REVIEW_STATE_BY_KNOWN_LABEL:
            mapped_states.add(_ARCH_REVIEW_STATE_BY_KNOWN_LABEL[label])
        elif label.startswith("arch:") or label.startswith("arch-"):
            unknown_arch_review_labels.add(label)

    if not mapped_states:
        return ArchReviewNormalizedLabelState(
            state=None,
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_arch_review_labels=frozenset(unknown_arch_review_labels),
        )

    if len(mapped_states) == 1:
        return ArchReviewNormalizedLabelState(
            state=next(iter(mapped_states)),
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_arch_review_labels=frozenset(unknown_arch_review_labels),
        )

    # Canonical labels take precedence if they resolve to exactly one state.
    canonical_states = {
        _ARCH_REVIEW_STATE_BY_KNOWN_LABEL[label]
        for label in observed_labels
        if label in ARCH_REVIEW_CANONICAL_LABEL_BY_STATE.values()
    }
    if len(canonical_states) == 1:
        return ArchReviewNormalizedLabelState(
            state=next(iter(canonical_states)),
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_arch_review_labels=frozenset(unknown_arch_review_labels),
        )

    # Conflict: multiple states mapped
    for label in observed_labels:
        if label in _ARCH_REVIEW_STATE_BY_KNOWN_LABEL:
            conflict_labels.add(label)

    return ArchReviewNormalizedLabelState(
        state=None,
        saw_legacy_label=saw_legacy,
        saw_canonical_label=saw_canonical,
        conflict_labels=frozenset(conflict_labels),
        unknown_arch_review_labels=frozenset(unknown_arch_review_labels),
    )


# Debt normalization

_DEBT_STATE_BY_KNOWN_LABEL: Dict[str, DebtState] = {
    **{v: k for k, v in DEBT_CANONICAL_LABEL_BY_STATE.items()},
    **{v: k for k, v in DEBT_LEGACY_LABEL_BY_STATE.items()},
}


class DebtNormalizedLabelState(NamedTuple):
    """Normalized Debt state read from a mixed label set during migration phases."""

    state: Optional[DebtState]
    saw_legacy_label: bool
    saw_canonical_label: bool
    conflict_labels: FrozenSet[str]
    unknown_debt_labels: FrozenSet[str]


def normalize_debt_state_from_labels(
    labels: Iterable[str],
) -> DebtNormalizedLabelState:
    """Derive Debt state from an issue's label set.

    Canonical labels take precedence over legacy labels. Returns a struct with
    the derived state and metadata about label conflicts / unknowns.

    Args:
        labels: Iterable of label strings from a GitHub issue.

    Returns:
        DebtNormalizedLabelState with state and conflict info.
    """
    observed_labels = {label.strip() for label in labels if label and label.strip()}

    mapped_states: Set[DebtState] = set()
    conflict_labels: Set[str] = set()
    saw_legacy = False
    saw_canonical = False
    unknown_debt_labels: Set[str] = set()

    for label in observed_labels:
        if label in DEBT_CANONICAL_LABEL_BY_STATE.values():
            saw_canonical = True
        if label in DEBT_LEGACY_LABEL_BY_STATE.values():
            saw_legacy = True

        if label in _DEBT_STATE_BY_KNOWN_LABEL:
            mapped_states.add(_DEBT_STATE_BY_KNOWN_LABEL[label])
        elif label.startswith("debt:") or label.startswith("debt-"):
            unknown_debt_labels.add(label)

    if not mapped_states:
        return DebtNormalizedLabelState(
            state=None,
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_debt_labels=frozenset(unknown_debt_labels),
        )

    if len(mapped_states) == 1:
        return DebtNormalizedLabelState(
            state=next(iter(mapped_states)),
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_debt_labels=frozenset(unknown_debt_labels),
        )

    # Canonical labels take precedence if they resolve to exactly one state.
    canonical_states = {
        _DEBT_STATE_BY_KNOWN_LABEL[label]
        for label in observed_labels
        if label in DEBT_CANONICAL_LABEL_BY_STATE.values()
    }
    if len(canonical_states) == 1:
        return DebtNormalizedLabelState(
            state=next(iter(canonical_states)),
            saw_legacy_label=saw_legacy,
            saw_canonical_label=saw_canonical,
            conflict_labels=frozenset(),
            unknown_debt_labels=frozenset(unknown_debt_labels),
        )

    # Conflict: multiple states mapped
    for label in observed_labels:
        if label in _DEBT_STATE_BY_KNOWN_LABEL:
            conflict_labels.add(label)

    return DebtNormalizedLabelState(
        state=None,
        saw_legacy_label=saw_legacy,
        saw_canonical_label=saw_canonical,
        conflict_labels=frozenset(conflict_labels),
        unknown_debt_labels=frozenset(unknown_debt_labels),
    )