from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class LLMInvocationResult:
    payload: Dict[str, Any]
    model: str
    request_id: str


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
