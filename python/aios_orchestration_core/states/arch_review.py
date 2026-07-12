from enum import Enum


class ArchReviewState(str, Enum):
    """States for architecture review issues."""
    ARCH_REVIEW_PENDING = "ARCH_REVIEW_PENDING"
    ARCH_REVIEW_IN_PROGRESS = "ARCH_REVIEW_IN_PROGRESS"
    ARCH_NO_ACTION = "ARCH_NO_ACTION"
    ARCH_REFACTOR_PLANNED = "ARCH_REFACTOR_PLANNED"
    ARCH_REFACTOR_CREATED = "ARCH_REFACTOR_CREATED"
    ARCH_REVIEW_ESCALATED = "ARCH_REVIEW_ESCALATED"
    ARCH_REVIEW_NEEDS_HUMAN = "ARCH_REVIEW_NEEDS_HUMAN"


TERMINAL_ARCH_REVIEW_STATES = {
    ArchReviewState.ARCH_NO_ACTION,
    ArchReviewState.ARCH_REFACTOR_CREATED,
    ArchReviewState.ARCH_REVIEW_ESCALATED,
    ArchReviewState.ARCH_REVIEW_NEEDS_HUMAN,
}


class DebtState(str, Enum):
    """States for architecture-debt issues."""
    DEBT_NEW = "DEBT_NEW"
    DEBT_TRIAGED = "DEBT_TRIAGED"
    DEBT_SCHEDULED = "DEBT_SCHEDULED"
    DEBT_RESOLVED = "DEBT_RESOLVED"
    DEBT_DEFERRED = "DEBT_DEFERRED"


TERMINAL_DEBT_STATES = {
    DebtState.DEBT_RESOLVED,
    # DEBT_DEFERRED is omitted: it has an outgoing DEBT_OVERRIDE_ACTIVATE transition
    # that re-activates debt when debt-must-address is applied (per routing registry).
}
