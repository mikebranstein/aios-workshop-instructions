from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from aios_orchestration_core.llm.base import JudgmentLLMAdapter, LLMInvocationResult
from aios_orchestration_core.llm.exceptions import (
    CapabilityProbeFailed,
    ForcedToolCallMissing,
    ToolSchemaValidationError,
)
from aios_orchestration_core.llm.schema_validation import validate_json_schema
from aios_orchestration_core.llm.task_tools import TASK_TOOL_MAP, ToolSpec


class CopilotSDKClient(Protocol):
    def supports_forced_tool_calls(self) -> bool:
        ...

    def chat(self, *, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], tool_choice: Dict[str, Any], model: str) -> Dict[str, Any]:
        ...


@dataclass
class CopilotAdapterConfig:
    model_default: str = "copilot-standard"
    allow_unforced_json_fallback: bool = False


class CopilotSDKAdapter(JudgmentLLMAdapter):
    """Fail-closed adapter that requires forced tool-call support."""

    def __init__(self, client: CopilotSDKClient, config: Optional[CopilotAdapterConfig] = None):
        self.client = client
        self.config = config or CopilotAdapterConfig()
        if not self.client.supports_forced_tool_calls():
            raise CapabilityProbeFailed(
                "Copilot SDK forced tool-call capability is required for invoke_json reliability"
            )

    def invoke_json(self, task_type: str, prompt_vars: Dict[str, Any], model_hint: str = "") -> LLMInvocationResult:
        if task_type not in TASK_TOOL_MAP:
            raise ValueError(f"Unknown task_type={task_type}")

        tool = TASK_TOOL_MAP[task_type]
        model = model_hint or self.config.model_default
        response = self.client.chat(
            messages=[{"role": "user", "content": str(prompt_vars)}],
            tools=[self._tool_to_sdk_dict(tool)],
            tool_choice={"type": "tool", "name": tool.name},
            model=model,
        )

        tool_payload = self._extract_forced_tool_payload(response, tool)
        errors = validate_json_schema(tool_payload, tool.parameters_schema)
        if errors:
            raise ToolSchemaValidationError("; ".join(errors))

        return LLMInvocationResult(
            payload=tool_payload,
            model=response.get("model", model),
            request_id=response.get("request_id", "unknown"),
        )

    @staticmethod
    def _tool_to_sdk_dict(tool: ToolSpec) -> Dict[str, Any]:
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters_schema,
        }

    @staticmethod
    def _extract_forced_tool_payload(response: Dict[str, Any], tool: ToolSpec) -> Dict[str, Any]:
        tool_calls = response.get("tool_calls", [])
        if not tool_calls:
            raise ForcedToolCallMissing("Response contained no tool_calls")

        for call in tool_calls:
            if call.get("name") == tool.name:
                args = call.get("arguments")
                if not isinstance(args, dict):
                    raise ForcedToolCallMissing("Tool call arguments must be an object")
                return args

        raise ForcedToolCallMissing(
            f"Response tool_calls missing forced tool name={tool.name}"
        )
