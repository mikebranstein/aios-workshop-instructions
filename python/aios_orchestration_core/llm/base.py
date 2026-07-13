from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class LLMUsage:
    """Token and cost usage for a single LLM invocation.

    Populated from the Copilot SDK ``assistant.usage`` event when available.
    All fields are optional — the event is documented as ephemeral and may not
    fire on every backend path.
    """

    # Standard token counts (input == prompt, output == completion)
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cache_read_tokens: Optional[int] = None
    cache_write_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None

    # Cost signals from copilot_usage
    nano_aiu: Optional[float] = None   # totalNanoAiu — Copilot billing unit
    cost: Optional[float] = None       # raw cost float when present


@dataclass(frozen=True)
class LLMInvocationResult:
    payload: Dict[str, Any]
    model: str
    request_id: str
    usage: Optional[LLMUsage] = None


class JudgmentLLMAdapter(ABC):
    """Adapter for structured judgment node calls."""

    @property
    def adapter_source(self) -> str:
        """
        Return the source of this adapter ("copilot", "stub", etc.).
        Used to tag TransitionLogEntry for auditability.
        Subclasses should override this if needed.
        """
        return "copilot"  # Default assumption

    @abstractmethod
    def invoke_json(self, task_type: str, prompt_vars: Dict[str, Any], model_hint: str = "") -> LLMInvocationResult:
        raise NotImplementedError
