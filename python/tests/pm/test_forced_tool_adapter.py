import unittest

from aios_orchestration_core.llm.copilot_sdk_adapter import CopilotSDKAdapter
from aios_orchestration_core.llm.exceptions import (
    ForcedToolCallMissing,
    ToolSchemaValidationError,
)


class FakeClient:
    def __init__(self, supports_tools: bool, response):
        self._supports_tools = supports_tools
        if isinstance(response, list):
            self._responses = response
        else:
            self._responses = [response]
        self.calls = 0

    def supports_forced_tool_calls(self) -> bool:
        return self._supports_tools

    def chat(self, **kwargs):
        idx = min(self.calls, len(self._responses) - 1)
        self.calls += 1
        return self._responses[idx]


class Phase2ForcedToolAdapterTests(unittest.TestCase):
    def test_no_startup_block_when_capability_probe_is_false(self) -> None:
        adapter = CopilotSDKAdapter(
            FakeClient(
                False,
                {
                    "tool_calls": [
                        {
                            "name": "submit_pm_phase1_decision",
                            "arguments": {
                                "decision": "PROVISIONAL_CHAMPION",
                                "reason": "Strong signal and strategic fit.",
                            },
                        }
                    ]
                },
            )
        )
        result = adapter.invoke_json("pm_phase1", {"issue": 42})
        self.assertEqual(result.payload["decision"], "PROVISIONAL_CHAMPION")

    def test_invoke_json_accepts_forced_tool_payload(self) -> None:
        adapter = CopilotSDKAdapter(
            FakeClient(
                True,
                {
                    "request_id": "r1",
                    "model": "auto",
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

    def test_invoke_json_retries_once_then_succeeds(self) -> None:
        fake = FakeClient(
            True,
            [
                {"tool_calls": []},
                {
                    "tool_calls": [
                        {
                            "name": "submit_pm_phase1_decision",
                            "arguments": {
                                "decision": "PROVISIONAL_CHAMPION",
                                "reason": "corrected",
                            },
                        }
                    ]
                },
            ],
        )
        adapter = CopilotSDKAdapter(fake)
        result = adapter.invoke_json("pm_phase1", {"issue": 42})
        self.assertEqual(result.payload["reason"], "corrected")
        self.assertEqual(fake.calls, 2)

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
