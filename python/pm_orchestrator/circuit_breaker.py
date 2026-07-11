from dataclasses import dataclass
from datetime import datetime, timezone

from aios_orchestration_core.policies.retry import RetryPolicy, RetryState
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.runlog.sqlite_store import TransitionLogStore
from aios_orchestration_core.states.pm import PMState


@dataclass(frozen=True)
class PMBlockContext:
    blocked_stage: str
    reason_code: str
    reason_detail: str
    last_error_class: str


class PMCircuitBreaker:
    def __init__(self, retry_policy: RetryPolicy, log_store: TransitionLogStore):
        self.retry_policy = retry_policy
        self.log_store = log_store

    def handle_failure(
        self,
        run_id: str,
        issue_number: int,
        from_state: PMState,
        retry_state: RetryState,
        context: PMBlockContext,
    ) -> PMState:
        retry_state.increment()
        if retry_state.exceeded(self.retry_policy):
            entry = TransitionLogEntry(
                run_id=run_id,
                issue_number=issue_number,
                from_state=from_state.value,
                to_state=PMState.PM_NEEDS_HUMAN.value,
                trigger_event="RETRY_THRESHOLD_EXCEEDED",
                blocked_stage=context.blocked_stage,
                reason_code=context.reason_code,
                reason_detail=(
                    f"{context.reason_detail}; "
                    f"last_error_class={context.last_error_class}; attempts={retry_state.attempts}"
                ),
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            )
            self.log_store.append(entry)
            return PMState.PM_NEEDS_HUMAN
        return from_state
