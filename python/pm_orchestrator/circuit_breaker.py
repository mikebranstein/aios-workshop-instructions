from aios_orchestration_core.core.circuit_breaker import BlockContext, LoopCircuitBreaker
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.runlog.sqlite_store import TransitionLogStore
from aios_orchestration_core.states.pm import PMState

# Backward-compatible alias so existing call sites keep working.
PMBlockContext = BlockContext


class PMCircuitBreaker(LoopCircuitBreaker[PMState]):
    """PM-specific circuit breaker that escalates to PM_NEEDS_HUMAN."""

    def __init__(self, retry_policy: RetryPolicy, log_store: TransitionLogStore) -> None:
        super().__init__(
            retry_policy=retry_policy,
            log_store=log_store,
            escalation_state=PMState.PM_NEEDS_HUMAN,
            loop_id="pm",
        )
