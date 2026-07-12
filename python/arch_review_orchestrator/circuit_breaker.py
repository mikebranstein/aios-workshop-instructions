from aios_orchestration_core.core.circuit_breaker import LoopCircuitBreaker
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.runlog.sqlite_store import TransitionLogStore
from aios_orchestration_core.states.arch_review import ArchReviewState


class ArchReviewCircuitBreaker(LoopCircuitBreaker[ArchReviewState]):
    def __init__(self, retry_policy: RetryPolicy, log_store: TransitionLogStore) -> None:
        super().__init__(
            retry_policy=retry_policy,
            log_store=log_store,
            escalation_state=ArchReviewState.ARCH_REVIEW_NEEDS_HUMAN,
            loop_id="arch_review",
        )
