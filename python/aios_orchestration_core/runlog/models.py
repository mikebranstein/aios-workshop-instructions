from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TransitionLogEntry:
    run_id: str
    issue_number: int
    from_state: str
    to_state: str
    trigger_event: str
    reason_code: str
    reason_detail: str
    timestamp_utc: str
    actor: str = "orchestrator"
    blocked_stage: Optional[str] = None

    def to_comment(self) -> str:
        blocked = f" blocked_stage={self.blocked_stage}" if self.blocked_stage else ""
        return (
            "[PM Transition] "
            f"run_id={self.run_id} "
            f"from={self.from_state} to={self.to_state} "
            f"event={self.trigger_event} "
            f"reason_code={self.reason_code}{blocked} "
            f"detail={self.reason_detail}"
        )
