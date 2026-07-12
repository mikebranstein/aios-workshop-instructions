from typing import Dict, FrozenSet

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
