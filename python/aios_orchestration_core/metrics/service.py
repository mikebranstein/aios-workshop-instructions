"""Thread-safe metrics service for AIOS orchestration.

Usage pattern
-------------
Create one MetricsService per run, wrap your LLM adapter with
InstrumentedLLMAdapter, then use span() context managers at each level of
work you want timed::

    metrics = MetricsService()
    adapter = InstrumentedLLMAdapter(raw_adapter, metrics)

    with metrics.span("pass:1", type="pass", pass_index=1):
        with metrics.span("issue:44:pass:1", type="issue", issue_number=44):
            # ... do work, LLM calls auto-recorded to active span ...
            pass
        metrics.log_summary("Issue #44", span_keys=["issue:44:pass:1"])
    metrics.log_summary("Pass 1", tag_filter={"type": "issue", "pass_index": 1})

Span attribution
----------------
LLM calls are attributed to the innermost active span on the *calling thread*.
Worker threads using ThreadPoolExecutor automatically get their own span stacks
via threading.local(), so parallel workers are tracked independently.

Roll-up logging
---------------
log_summary() accepts either explicit span_keys or a tag_filter dict.  It
aggregates all matching spans and emits one summary block to the logger.
"""

from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional

from aios_orchestration_core.llm.base import JudgmentLLMAdapter, LLMInvocationResult
from aios_orchestration_core.metrics.models import (
    LLMCallRecord,
    LLMUsage,
    MetricsSummary,
    SpanRecord,
)

logger = logging.getLogger(__name__)


class MetricsService:
    """Thread-safe, in-memory metrics collector.

    One instance is created per orchestrator run and shared across all threads.
    Span stacks are thread-local so parallel workers track their own spans.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._spans: Dict[str, SpanRecord] = {}
        self._tl: threading.local = threading.local()

    # ------------------------------------------------------------------
    # Span lifecycle
    # ------------------------------------------------------------------

    def push_span(self, key: str, **tags: Any) -> None:
        """Open a new span and make it the active span on this thread."""
        span = SpanRecord(key=key, started_at=time.monotonic(), tags=dict(tags))
        with self._lock:
            self._spans[key] = span
        self._stack().append(key)

    def pop_span(self) -> Optional[SpanRecord]:
        """Close and return the innermost active span on this thread."""
        stack = self._stack()
        if not stack:
            return None
        key = stack.pop()
        with self._lock:
            span = self._spans.get(key)
            if span and span.ended_at is None:
                span.ended_at = time.monotonic()
        return span

    @contextmanager
    def span(self, key: str, **tags: Any) -> Iterator[None]:
        """Context manager that opens and closes a span around a block of work."""
        self.push_span(key, **tags)
        try:
            yield
        finally:
            self.pop_span()

    # ------------------------------------------------------------------
    # LLM call recording
    # ------------------------------------------------------------------

    def record_llm_call(
        self,
        task_type: str,
        model: str,
        duration_s: float,
        usage: Optional[LLMUsage] = None,
    ) -> None:
        """Append an LLM call record to the innermost active span on this thread."""
        stack = self._stack()
        if not stack:
            return
        span_key = stack[-1]
        record = LLMCallRecord(task_type=task_type, model=model, duration_s=duration_s, usage=usage)
        with self._lock:
            span = self._spans.get(span_key)
            if span:
                span.llm_calls.append(record)

    # ------------------------------------------------------------------
    # Roll-up and logging
    # ------------------------------------------------------------------

    def get_span(self, key: str) -> Optional[SpanRecord]:
        with self._lock:
            return self._spans.get(key)

    def get_spans_by_keys(self, keys: List[str]) -> List[SpanRecord]:
        with self._lock:
            return [self._spans[k] for k in keys if k in self._spans]

    def get_spans_by_tags(self, **tag_filter: Any) -> List[SpanRecord]:
        """Return all completed spans whose tags are a superset of tag_filter."""
        with self._lock:
            return [
                s for s in self._spans.values()
                if all(s.tags.get(k) == v for k, v in tag_filter.items())
            ]

    def summarize(
        self,
        label: str,
        span_keys: Optional[List[str]] = None,
        tag_filter: Optional[Dict[str, Any]] = None,
        include_call_breakdown: bool = True,
    ) -> MetricsSummary:
        """Aggregate spans into a MetricsSummary.

        Provide either *span_keys* (explicit list) or *tag_filter* (dict match).
        """
        if span_keys is not None:
            spans = self.get_spans_by_keys(span_keys)
        elif tag_filter is not None:
            spans = self.get_spans_by_tags(**tag_filter)
        else:
            with self._lock:
                spans = list(self._spans.values())

        total_elapsed = sum(s.duration_s for s in spans)
        all_calls: List[LLMCallRecord] = []
        for s in spans:
            all_calls.extend(s.llm_calls)

        llm_duration = sum(c.duration_s for c in all_calls)

        in_tok_vals = [c.usage.input_tokens for c in all_calls if c.usage and c.usage.input_tokens is not None]
        out_tok_vals = [c.usage.output_tokens for c in all_calls if c.usage and c.usage.output_tokens is not None]
        nano_aiu_vals = [c.usage.nano_aiu for c in all_calls if c.usage and c.usage.nano_aiu is not None]

        in_sum = sum(in_tok_vals) if in_tok_vals else None
        out_sum = sum(out_tok_vals) if out_tok_vals else None
        total_sum = (in_sum or 0) + (out_sum or 0) if (in_sum is not None or out_sum is not None) else None

        breakdown = [str(c) for c in all_calls] if include_call_breakdown else []

        return MetricsSummary(
            label=label,
            span_count=len(spans),
            elapsed_s=total_elapsed,
            llm_calls=len(all_calls),
            llm_duration_s=llm_duration,
            input_tokens=in_sum,
            output_tokens=out_sum,
            total_tokens=total_sum,
            nano_aiu=sum(nano_aiu_vals) if nano_aiu_vals else None,
            per_call_breakdown=breakdown,
        )

    def log_summary(
        self,
        label: str,
        span_keys: Optional[List[str]] = None,
        tag_filter: Optional[Dict[str, Any]] = None,
        include_call_breakdown: bool = False,
    ) -> MetricsSummary:
        """Compute and log a summary. Returns the MetricsSummary for further use."""
        summary = self.summarize(label, span_keys=span_keys, tag_filter=tag_filter, include_call_breakdown=include_call_breakdown)
        for line in summary.log_lines():
            logger.info(line)
        return summary

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _stack(self) -> List[str]:
        if not hasattr(self._tl, "stack"):
            self._tl.stack = []
        return self._tl.stack  # type: ignore[return-value]


class InstrumentedLLMAdapter(JudgmentLLMAdapter):
    """Transparent adapter wrapper that records timing and usage to MetricsService.

    Wrap any JudgmentLLMAdapter with this before passing it to orchestrator
    components. Every invoke_json call is automatically timed and attributed to
    the innermost active span on the calling thread::

        raw_adapter = CopilotSDKAdapter(...)
        adapter = InstrumentedLLMAdapter(raw_adapter, metrics)
    """

    def __init__(self, inner: JudgmentLLMAdapter, metrics: MetricsService) -> None:
        self._inner = inner
        self._metrics = metrics

    @property
    def adapter_source(self) -> str:
        return self._inner.adapter_source

    def invoke_json(
        self,
        task_type: str,
        prompt_vars: Dict[str, Any],
        model_hint: str = "",
    ) -> LLMInvocationResult:
        start = time.monotonic()
        result = self._inner.invoke_json(task_type, prompt_vars, model_hint)
        duration_s = time.monotonic() - start

        self._metrics.record_llm_call(
            task_type=task_type,
            model=result.model,
            duration_s=duration_s,
            usage=result.usage,
        )
        return result
