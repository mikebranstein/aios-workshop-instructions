import asyncio
from typing import Any, Dict, List, Optional

from copilot import CopilotClient
from copilot.session_events import AssistantMessageData, AssistantUsageData
from copilot.tools import define_tool

from aios_orchestration_core.llm.base import LLMUsage
from aios_orchestration_core.llm.schema_validation import validate_json_schema


class CopilotRuntimeClient:
    """Sync wrapper over the async Copilot SDK session API for single-tool calls."""

    def supports_forced_tool_calls(self) -> bool:
        # The Python SDK does not expose a direct forced-tool-choice flag.
        return False

    def chat(
        self,
        *,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_choice: Dict[str, Any],
        model: str,
    ) -> Dict[str, Any]:
        return asyncio.run(
            self._chat_async(
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                model=model,
            )
        )

    async def _chat_async(
        self,
        *,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_choice: Dict[str, Any],
        model: str,
    ) -> Dict[str, Any]:
        if len(tools) != 1:
            raise ValueError("CopilotRuntimeClient only supports a single tool per call")

        tool_decl = tools[0]
        tool_name = str(tool_choice.get("name") or tool_decl.get("name"))
        tool_schema = tool_decl.get("parameters") or {}
        if not tool_name:
            raise ValueError("tool_choice.name is required")

        tool_calls: List[Dict[str, Any]] = []
        attempted_calls: List[Dict[str, Any]] = []
        last_usage_data: Optional[AssistantUsageData] = None

        @define_tool(
            name=tool_name,
            description=str(tool_decl.get("description") or "runtime tool"),
            skip_permission=True,
        )
        def _runtime_tool(arguments):
            args = arguments if isinstance(arguments, dict) else {"value": str(arguments)}
            attempted_calls.append({"name": tool_name, "arguments": args})
            errors = validate_json_schema(args, tool_schema)
            if errors:
                raise ValueError("; ".join(errors))
            tool_calls.append({"name": tool_name, "arguments": args})
            return {"ok": True}

        joined_prompt = self._messages_to_prompt(messages, tool_name, tool_decl.get("parameters"))

        async with CopilotClient() as client:
            try:
                session = await client.create_session(
                    model=model,
                    tools=[_runtime_tool],
                    enable_skills=False,
                    skip_custom_instructions=True,
                )
            except Exception as ex:
                # Some local runtimes do not expose aliases like "auto".
                # Retry once using runtime default model selection.
                if "not available" not in str(ex):
                    raise
                session = await client.create_session(
                    tools=[_runtime_tool],
                    enable_skills=False,
                    skip_custom_instructions=True,
                )

            # Capture assistant.usage events — these fire on the same stream as
            # assistant.message but are not returned by send_and_wait, so we
            # subscribe before sending. The event is documented as ephemeral and
            # may not fire on every backend/model path.
            def _usage_handler(event: Any) -> None:
                nonlocal last_usage_data
                if isinstance(event.data, AssistantUsageData):
                    last_usage_data = event.data

            session.on(_usage_handler)

            event = await session.send_and_wait(joined_prompt, timeout=90.0)

            assistant_content = None
            if event is not None and isinstance(event.data, AssistantMessageData):
                assistant_content = event.data.content

            calls_for_adapter = tool_calls if tool_calls else attempted_calls

            return {
                "model": model,
                "request_id": getattr(session, "session_id", "unknown"),
                "tool_calls": calls_for_adapter,
                "assistant_content": assistant_content,
                "usage": _extract_usage(last_usage_data),
            }

    @staticmethod
    def _messages_to_prompt(
        messages: List[Dict[str, Any]],
        tool_name: str,
        tool_schema: Any,
    ) -> str:
        lines = [
            f"You must call tool {tool_name} exactly once.",
            "Do not answer in plain text before calling the tool.",
            "Return schema-valid arguments for the tool.",
            f"Tool schema: {tool_schema}",
            "Conversation:",
        ]
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)


def _extract_usage(data: Optional[AssistantUsageData]) -> Optional[LLMUsage]:
    """Convert an SDK AssistantUsageData event to our LLMUsage model.

    Returns None if no data was captured (event is ephemeral).
    """
    if data is None:
        return None
    nano_aiu: Optional[float] = None
    if data.copilot_usage is not None:
        nano_aiu = data.copilot_usage.total_nano_aiu
    return LLMUsage(
        input_tokens=data.input_tokens,
        output_tokens=data.output_tokens,
        cache_read_tokens=data.cache_read_tokens,
        cache_write_tokens=data.cache_write_tokens,
        reasoning_tokens=data.reasoning_tokens,
        nano_aiu=nano_aiu,
        cost=data.cost,
    )
