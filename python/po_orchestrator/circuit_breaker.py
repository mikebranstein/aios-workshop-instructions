from aios_orchestration_core.core.circuit_breaker import LoopCircuitBreaker
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.runlog.sqlite_store import TransitionLogStore
from aios_orchestration_core.states.po import POState


class POCircuitBreaker(LoopCircuitBreaker[POState]):
    """PO-specific circuit breaker that escalates to PO_NEEDS_HUMAN."""

    def __init__(self, retry_policy: RetryPolicy, log_store: TransitionLogStore) -> None:
        super().__init__(
            retry_policy=retry_policy,
            log_store=log_store,
            escalation_state=POState.PO_NEEDS_HUMAN,
            loop_id="po",
        )
