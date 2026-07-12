from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from aios_orchestration_core.llm.base import JudgmentLLMAdapter, LLMInvocationResult
from aios_orchestration_core.llm.exceptions import (
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
    max_non_tool_retries: int = 1
    strict_tool_instruction: str = (
        "You must call the provided tool exactly once. "
        "Do not answer in plain text. "
        "The tool parameters must satisfy the declared schema."
    )


class CopilotSDKAdapter(JudgmentLLMAdapter):
    """Single-tool constrained adapter with retry-on-non-tool enforcement."""

    def __init__(self, client: CopilotSDKClient, config: Optional[CopilotAdapterConfig] = None):
        self.client = client
        self.config = config or CopilotAdapterConfig()
        self.forced_tool_capability = self.client.supports_forced_tool_calls()

    def invoke_json(self, task_type: str, prompt_vars: Dict[str, Any], model_hint: str = "") -> LLMInvocationResult:
        if task_type not in TASK_TOOL_MAP:
            raise ValueError(f"Unknown task_type={task_type}")

        tool = TASK_TOOL_MAP[task_type]
        model = model_hint or self.config.model_default
        corrections = 0

        while True:
            messages = [
                {"role": "system", "content": self.config.strict_tool_instruction},
                {"role": "user", "content": str(prompt_vars)},
            ]
            if corrections > 0:
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "Previous response did not return the required tool call. "
                            f"Call tool {tool.name} now with schema-valid arguments."
                        ),
                    }
                )

            response = self.client.chat(
                messages=messages,
                tools=[self._tool_to_sdk_dict(tool)],
                tool_choice={"type": "tool", "name": tool.name},
                model=model,
            )

            try:
                tool_payload = self._extract_forced_tool_payload(response, tool)
            except ForcedToolCallMissing:
                if corrections >= self.config.max_non_tool_retries:
                    raise
                corrections += 1
                continue

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
