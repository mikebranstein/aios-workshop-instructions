import unittest

from aios_orchestration_core.llm.copilot_sdk_adapter import CopilotSDKAdapter
from aios_orchestration_core.llm.exceptions import (
    CapabilityProbeFailed,
    ForcedToolCallMissing,
    ToolSchemaValidationError,
)


class FakeClient:
    def __init__(self, supports_tools: bool, response):
        self._supports_tools = supports_tools
        self._response = response

    def supports_forced_tool_calls(self) -> bool:
        return self._supports_tools

    def chat(self, **kwargs):
        return self._response


class Phase2ForcedToolAdapterTests(unittest.TestCase):
    def test_capability_probe_fails_closed(self) -> None:
        with self.assertRaises(CapabilityProbeFailed):
            CopilotSDKAdapter(FakeClient(False, {}))

    def test_invoke_json_accepts_forced_tool_payload(self) -> None:
        adapter = CopilotSDKAdapter(
            FakeClient(
                True,
                {
                    "request_id": "r1",
                    "model": "copilot-standard",
                    "tool_calls": [
                        {
                            "name": "submit_pm_phase1_decision",
                            "arguments": {
                                "decision": "PROVISIONAL_CHAMPION",
                                "reason": "Strong signal and strategic fit.",
                            },
                        }
                    ],
                },
            )
        )

        result = adapter.invoke_json("pm_phase1", {"issue": 42})
        self.assertEqual(result.payload["decision"], "PROVISIONAL_CHAMPION")

    def test_invoke_json_rejects_missing_tool_call(self) -> None:
        adapter = CopilotSDKAdapter(FakeClient(True, {"tool_calls": []}))
        with self.assertRaises(ForcedToolCallMissing):
            adapter.invoke_json("pm_phase1", {"issue": 42})

    def test_invoke_json_rejects_schema_mismatch(self) -> None:
        adapter = CopilotSDKAdapter(
            FakeClient(
                True,
                {
                    "tool_calls": [
                        {
                            "name": "submit_pm_phase1_decision",
                            "arguments": {"decision": "PROVISIONAL_CHAMPION"},
                        }
                    ]
                },
            )
        )

        with self.assertRaises(ToolSchemaValidationError):
            adapter.invoke_json("pm_phase1", {"issue": 42})


if __name__ == "__main__":
    unittest.main()
