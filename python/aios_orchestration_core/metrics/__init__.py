"""Metrics subsystem for AIOS orchestration core.

Public API::

    from aios_orchestration_core.metrics import MetricsService, InstrumentedLLMAdapter
    from aios_orchestration_core.metrics.models import LLMCallRecord, SpanRecord, MetricsSummary
    from aios_orchestration_core.llm.base import LLMUsage
"""

from aios_orchestration_core.llm.base import LLMUsage  # canonical location; re-exported for convenience
from aios_orchestration_core.metrics.models import (
    LLMCallRecord,
    MetricsSummary,
    SpanRecord,
)
from aios_orchestration_core.metrics.service import InstrumentedLLMAdapter, MetricsService

__all__ = [
    "InstrumentedLLMAdapter",
    "LLMCallRecord",
    "LLMUsage",
    "MetricsSummary",
    "MetricsService",
    "SpanRecord",
]
