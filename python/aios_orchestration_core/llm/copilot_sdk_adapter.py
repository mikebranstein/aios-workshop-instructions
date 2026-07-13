from dataclasses import dataclass
import json
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
    model_default: str = "auto"
    max_non_tool_retries: int = 2
    strict_tool_instruction: str = (
        "You must call the provided tool exactly once. "
        "Do not answer in plain text. "
        "The tool parameters must satisfy the declared schema. "
        "Never omit required fields."
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
        last_failure = ""
        last_error_detail = ""

        while True:
            messages = [
                {"role": "system", "content": self.config.strict_tool_instruction},
                {"role": "user", "content": self._build_tool_request_prompt(tool, prompt_vars)},
            ]
            if corrections > 0:
                correction_detail = f" Failure type: {last_failure}."
                if last_error_detail:
                    correction_detail += f" Validation errors: {last_error_detail}."
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "Previous response was invalid. "
                            f"Call tool {tool.name} now with schema-valid arguments."
                            f"{correction_detail}"
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
                last_failure = "missing_tool_call"
                last_error_detail = ""
                continue

            normalized_payload = self._normalize_payload(tool_payload, tool.parameters_schema)
            normalized_payload = self._apply_required_neutral_defaults(
                normalized_payload,
                tool.parameters_schema,
            )
            errors = validate_json_schema(tool_payload, tool.parameters_schema)
            if errors:
                errors = validate_json_schema(normalized_payload, tool.parameters_schema)
            if errors:
                if corrections >= self.config.max_non_tool_retries:
                    raise ToolSchemaValidationError("; ".join(errors))
                corrections += 1
                last_failure = "schema_validation"
                last_error_detail = "; ".join(errors)
                continue

            return LLMInvocationResult(
                payload=normalized_payload,
                model=response.get("model", model),
                request_id=response.get("request_id", "unknown"),
            )

    @staticmethod
    def _build_tool_request_prompt(tool: ToolSpec, prompt_vars: Dict[str, Any]) -> str:
        required = tool.parameters_schema.get("required", [])
        properties = tool.parameters_schema.get("properties", {})
        example: Dict[str, Any] = {}
        for field in required:
            field_schema = properties.get(field, {})
            example[field] = CopilotSDKAdapter._example_value_for_schema(field_schema)

        lines = [
            f"Task tool: {tool.name}",
            f"Description: {tool.description}",
            "You must call the tool exactly once.",
            "Return no plain-text answer before the tool call.",
            "Arguments must be valid JSON and must satisfy the schema.",
            "If a field is required, you must provide it even when context is sparse.",
            f"Required fields: {required}",
            f"Schema: {json.dumps(tool.parameters_schema, ensure_ascii=True)}",
            f"Valid example arguments: {json.dumps(example, ensure_ascii=True)}",
            f"Prompt variables: {json.dumps(prompt_vars, ensure_ascii=True)}",
        ]
        if "decision" in required and "reason" in required:
            decision_schema = properties.get("decision", {})
            if "enum" in decision_schema and decision_schema["enum"]:
                safe_decision = decision_schema["enum"][0]
                lines.append(
                    "If uncertain, still provide schema-valid arguments. "
                    f"Use decision={safe_decision} and reason='insufficient evidence in prompt vars' as fallback."
                )
        return "\n".join(lines)

    @staticmethod
    def _example_value_for_schema(schema: Dict[str, Any]) -> Any:
        if "enum" in schema and schema["enum"]:
            return schema["enum"][0]

        schema_type = schema.get("type")
        if schema_type == "string":
            return "example"
        if schema_type == "integer":
            minimum = schema.get("minimum")
            return minimum if isinstance(minimum, int) else 1
        if schema_type == "number":
            minimum = schema.get("minimum")
            return float(minimum) if isinstance(minimum, (int, float)) else 0.5
        if schema_type == "boolean":
            return True
        if schema_type == "array":
            item_schema = schema.get("items", {})
            return [CopilotSDKAdapter._example_value_for_schema(item_schema)]
        if schema_type == "object":
            obj: Dict[str, Any] = {}
            properties = schema.get("properties", {})
            for key in schema.get("required", []):
                obj[key] = CopilotSDKAdapter._example_value_for_schema(properties.get(key, {}))
            return obj
        return None

    @staticmethod
    def _normalize_payload(payload: Any, schema: Dict[str, Any]) -> Any:
        schema_type = schema.get("type")

        if schema_type == "object" and isinstance(payload, dict):
            properties = schema.get("properties", {})
            normalized: Dict[str, Any] = {}
            for key, value in payload.items():
                if key in properties:
                    normalized[key] = CopilotSDKAdapter._normalize_payload(value, properties[key])
            return normalized

        if schema_type == "array" and isinstance(payload, list):
            item_schema = schema.get("items", {})
            return [CopilotSDKAdapter._normalize_payload(item, item_schema) for item in payload]

        if schema_type == "string" and isinstance(payload, str):
            return payload.strip()

        if schema_type == "integer":
            if isinstance(payload, int):
                return payload
            if isinstance(payload, float) and payload.is_integer():
                return int(payload)
            if isinstance(payload, str):
                stripped = payload.strip()
                if stripped.lstrip("-").isdigit():
                    return int(stripped)

        if schema_type == "number":
            if isinstance(payload, (int, float)):
                return float(payload)
            if isinstance(payload, str):
                stripped = payload.strip()
                try:
                    return float(stripped)
                except ValueError:
                    return payload

        if schema_type == "boolean" and isinstance(payload, str):
            lowered = payload.strip().lower()
            if lowered == "true":
                return True
            if lowered == "false":
                return False

        return payload

    @staticmethod
    def _apply_required_neutral_defaults(payload: Any, schema: Dict[str, Any]) -> Any:
        if schema.get("type") != "object" or not isinstance(payload, dict):
            return payload

        required = schema.get("required", [])
        properties = schema.get("properties", {})
        amended = dict(payload)
        for key in required:
            if key in amended:
                continue
            field_schema = properties.get(key, {})
            # Neutral default only for arrays. This keeps behavior fail-closed for
            # scalar/object required fields where inference would be unsafe.
            if field_schema.get("type") == "array":
                amended[key] = []
        return amended

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
