from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from aios_orchestration_core.policies.retry import RetryPolicy, RetryState
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore

S = TypeVar("S")


def _state_str(s: Any) -> str:
    """Coerce a state value to a clean string.

    For ``str``-based Enum members, ``str(member)`` returns
    ``"ClassName.MEMBER"`` rather than the underlying value.
    Using ``.value`` when available produces the clean form.
    """
    return s.value if hasattr(s, "value") else str(s)


@dataclass(frozen=True)
class BlockContext:
    """Diagnostic payload captured at failure time."""

    blocked_stage: str
    reason_code: str
    reason_detail: str
    last_error_class: str


class LoopCircuitBreaker(Generic[S]):
    """Generic circuit-breaker that escalates to a configurable state.

    Each loop instantiates this with its own ``escalation_state``
    (e.g. ``PMState.PM_NEEDS_HUMAN``) and ``loop_id`` (e.g. ``"pm"``).
    After ``retry_policy.max_attempts`` failures the breaker writes a
    ``TransitionLogEntry`` and returns the escalation state.
    """

    def __init__(
        self,
        retry_policy: RetryPolicy,
        log_store: TransitionLogStore,
        escalation_state: S,
        loop_id: str,
    ) -> None:
        self.retry_policy = retry_policy
        self.log_store = log_store
        self.escalation_state = escalation_state
        self.loop_id = loop_id

    def handle_failure(
        self,
        run_id: str,
        issue_number: int,
        from_state: S,
        retry_state: RetryState,
        context: BlockContext,
    ) -> S:
        """Increment retry counter; escalate if threshold exceeded."""
        retry_state.increment()
        if retry_state.exceeded(self.retry_policy):
            entry = TransitionLogEntry(
                loop_id=self.loop_id,
                run_id=run_id,
                issue_number=issue_number,
                from_state=_state_str(from_state),
                to_state=_state_str(self.escalation_state),
                trigger_event="RETRY_THRESHOLD_EXCEEDED",
                blocked_stage=context.blocked_stage,
                reason_code=context.reason_code,
                reason_detail=(
                    f"{context.reason_detail}; "
                    f"last_error_class={context.last_error_class}; "
                    f"attempts={retry_state.attempts}"
                ),
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                adapter_source="system",  # Circuit breaker escalation (not adapter decision)
            )
            self.log_store.append(entry)
            return self.escalation_state
        return from_state
