import asyncio
from dataclasses import asdict

from pydantic import BaseModel, Field

from copilot import CopilotClient
from copilot.session_events import AssistantMessageData
from copilot.tools import define_tool


class ProbeParams(BaseModel):
    marker: str = Field(description="Marker string to echo")


tool_calls = []


@define_tool(
    name="emit_probe_marker",
    description="Echo a marker string for SDK live verification.",
    skip_permission=True,
)
def emit_probe_marker(params: ProbeParams):
    tool_calls.append(params.marker)
    return {"ok": True, "marker": params.marker}


async def main() -> int:
    prompt = (
        "Tool-call verification run. "
        "You must call emit_probe_marker exactly once with marker='SDK_LIVE_TOOL_PROOF'. "
        "Do not answer in plain text without calling the tool first."
    )

    print("LIVE_SDK_PROBE_START")
    try:
        async with CopilotClient() as client:
            session = await client.create_session(
                tools=[emit_probe_marker],
                enable_skills=False,
                skip_custom_instructions=True,
            )
            event = await session.send_and_wait(prompt, timeout=90.0)

            print(f"TOOL_CALL_COUNT={len(tool_calls)}")
            print(f"TOOL_CALL_VALUES={tool_calls}")

            if event is None:
                print("FINAL_EVENT=None")
                return 2

            print(f"FINAL_EVENT_DATA_CLASS={type(event.data).__name__}")
            if isinstance(event.data, AssistantMessageData):
                content = event.data.content
                print("ASSISTANT_CONTENT_START")
                print(content)
                print("ASSISTANT_CONTENT_END")

            if len(tool_calls) >= 1:
                print("SDK_TOOL_CALL_VERDICT=TOOL_CALLED")
                return 0

            print("SDK_TOOL_CALL_VERDICT=NO_TOOL_CALL")
            return 3

    except Exception as ex:
        print(f"LIVE_SDK_PROBE_ERROR={type(ex).__name__}: {ex}")
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
