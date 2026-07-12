from aios_orchestration_core.core.circuit_breaker import LoopCircuitBreaker
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.dev import DevState


class DevCircuitBreaker(LoopCircuitBreaker[DevState]):
    """Dev-specific circuit breaker that escalates to DEV_NEEDS_HUMAN."""

    def __init__(self, retry_policy: RetryPolicy, log_store: TransitionLogStore) -> None:
        super().__init__(
            retry_policy=retry_policy,
            log_store=log_store,
            escalation_state=DevState.DEV_NEEDS_HUMAN,
            loop_id="dev",
        )
