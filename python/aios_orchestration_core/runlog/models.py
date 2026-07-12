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
    adapter_source: str  # REQUIRED: "copilot" or "stub" — must be explicitly set by all callers
    loop_id: str = "pm"
    actor: str = "orchestrator"
    blocked_stage: Optional[str] = None

    def to_comment(self) -> str:
        blocked = f" blocked_stage={self.blocked_stage}" if self.blocked_stage else ""
        adapter_note = f" adapter_source={self.adapter_source}" if self.adapter_source != "copilot" else ""
        return (
            f"[{self.loop_id.upper()} Transition] "
            f"run_id={self.run_id} "
            f"from={self.from_state} to={self.to_state} "
            f"event={self.trigger_event} "
            f"reason_code={self.reason_code}{blocked}{adapter_note} "
            f"detail={self.reason_detail}"
        )

    def to_markdown_row(self) -> str:
        """Return a markdown table row for this transition."""
        blocked = f" [{self.blocked_stage}]" if self.blocked_stage else ""
        adapter_flag = " [STUB]" if self.adapter_source == "stub" else ""
        return (
            f"| {self.loop_id} | {self.run_id[:8]}... | {self.issue_number} | "
            f"{self.from_state} | {self.to_state} | {self.trigger_event} | "
            f"{self.reason_code}{blocked}{adapter_flag} | {self.timestamp_utc} |"
        )

    def to_stdout(self) -> str:
        """Return a human-readable one-liner for console output."""
        blocked = f" [BLOCKED: {self.blocked_stage}]" if self.blocked_stage else ""
        adapter_flag = " [STUB RESPONSE]" if self.adapter_source == "stub" else ""
        return (
            f"[{self.timestamp_utc}] [{self.loop_id}] issue={self.issue_number} "
            f"{self.from_state} -> {self.to_state} "
            f"({self.trigger_event}, {self.reason_code}){blocked}{adapter_flag}"
        )
