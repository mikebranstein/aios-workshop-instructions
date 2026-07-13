"""Metrics data models for the AIOS orchestration core.

These are pure data classes — no side effects, no I/O.
``LLMUsage`` is defined in ``aios_orchestration_core.llm.base`` and re-exported
here for convenience so callers can import everything from one place.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from aios_orchestration_core.llm.base import LLMUsage  # canonical definition

__all__ = ["LLMUsage", "LLMCallRecord", "SpanRecord", "MetricsSummary"]


@dataclass
class LLMCallRecord:
    """Record of a single invoke_json call."""

    task_type: str
    model: str
    duration_s: float
    usage: Optional[LLMUsage] = None

    def __str__(self) -> str:
        parts = [f"{self.task_type} ({self.duration_s:.1f}s)"]
        if self.usage:
            if self.usage.input_tokens is not None:
                total = (self.usage.input_tokens or 0) + (self.usage.output_tokens or 0)
                parts.append(
                    f"tokens=in:{self.usage.input_tokens} "
                    f"out:{self.usage.output_tokens} "
                    f"total:{total}"
                )
            if self.usage.nano_aiu is not None:
                parts.append(f"nanoAIU:{self.usage.nano_aiu:.0f}")
        return " ".join(parts)


@dataclass
class SpanRecord:
    """A timed unit of work, optionally carrying child LLM call records.

    Spans are created by MetricsService and should not be constructed directly
    by callers.
    """

    key: str
    started_at: float  # time.monotonic()
    ended_at: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    llm_calls: List[LLMCallRecord] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Derived properties
    # ------------------------------------------------------------------

    @property
    def duration_s(self) -> float:
        """Wall-clock seconds. Returns live elapsed time if span is still open."""
        end = self.ended_at if self.ended_at is not None else time.monotonic()
        return end - self.started_at

    @property
    def llm_count(self) -> int:
        return len(self.llm_calls)

    @property
    def llm_duration_s(self) -> float:
        return sum(c.duration_s for c in self.llm_calls)

    @property
    def input_tokens(self) -> Optional[int]:
        vals = [c.usage.input_tokens for c in self.llm_calls if c.usage and c.usage.input_tokens is not None]
        return sum(vals) if vals else None

    @property
    def output_tokens(self) -> Optional[int]:
        vals = [c.usage.output_tokens for c in self.llm_calls if c.usage and c.usage.output_tokens is not None]
        return sum(vals) if vals else None

    @property
    def total_tokens(self) -> Optional[int]:
        ins = self.input_tokens
        outs = self.output_tokens
        if ins is not None or outs is not None:
            return (ins or 0) + (outs or 0)
        return None

    @property
    def nano_aiu(self) -> Optional[float]:
        vals = [c.usage.nano_aiu for c in self.llm_calls if c.usage and c.usage.nano_aiu is not None]
        return sum(vals) if vals else None


@dataclass
class MetricsSummary:
    """Aggregated metrics across one or more spans, suitable for logging."""

    label: str
    span_count: int
    elapsed_s: float
    llm_calls: int
    llm_duration_s: float
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    total_tokens: Optional[int]
    nano_aiu: Optional[float]
    per_call_breakdown: List[str] = field(default_factory=list)

    def log_lines(self) -> List[str]:
        """Return human-readable log lines for this summary."""
        token_str = ""
        if self.total_tokens is not None:
            token_str = (
                f", tokens=in:{self.input_tokens} "
                f"out:{self.output_tokens} "
                f"total:{self.total_tokens}"
            )
        aiu_str = f", nanoAIU:{self.nano_aiu:.0f}" if self.nano_aiu is not None else ""
        lines = [
            f"[METRICS] {self.label}: "
            f"elapsed={self.elapsed_s:.1f}s, "
            f"llm_calls={self.llm_calls}, "
            f"llm_time={self.llm_duration_s:.1f}s"
            f"{token_str}"
            f"{aiu_str}"
        ]
        for call_str in self.per_call_breakdown:
            lines.append(f"[METRICS]   {call_str}")
        return lines
