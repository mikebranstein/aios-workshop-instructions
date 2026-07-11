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

    @abstractmethod
    def invoke_json(self, task_type: str, prompt_vars: Dict[str, Any], model_hint: str = "") -> LLMInvocationResult:
        raise NotImplementedError
