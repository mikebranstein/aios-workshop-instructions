import unittest

from aios_orchestration_core.llm.copilot_sdk_adapter import CopilotSDKAdapter
from aios_orchestration_core.llm.exceptions import ToolSchemaValidationError
from aios_orchestration_core.llm.schema_validation import validate_json_schema
from aios_orchestration_core.llm.task_tools import TASK_TOOL_MAP


def _example_for_schema(schema):
    if "enum" in schema and schema["enum"]:
        return schema["enum"][0]
    schema_type = schema.get("type")
    if schema_type == "string":
        return "value"
    if schema_type == "integer":
        return 1
    if schema_type == "number":
        return 0.7
    if schema_type == "boolean":
        return True
    if schema_type == "array":
        return [_example_for_schema(schema.get("items", {}))]
    if schema_type == "object":
        out = {}
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            out[key] = _example_for_schema(props.get(key, {}))
        return out
    return None


def _valid_payload(schema):
    payload = {}
    props = schema.get("properties", {})
    for key in schema.get("required", []):
        payload[key] = _example_for_schema(props[key])
    return payload


class _CapturingClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0
        self.last_kwargs = []

    def supports_forced_tool_calls(self):
        return False

    def chat(self, **kwargs):
        self.last_kwargs.append(kwargs)
        idx = min(self.calls, len(self.responses) - 1)
        self.calls += 1
        return self.responses[idx]


class CopilotSDKAdapterCrossTaskTests(unittest.TestCase):
    def test_all_task_types_accept_schema_valid_payload(self):
        for task_type, tool in TASK_TOOL_MAP.items():
            with self.subTest(task_type=task_type):
                payload = _valid_payload(tool.parameters_schema)
                adapter = CopilotSDKAdapter(
                    _CapturingClient(
                        [
                            {
                                "tool_calls": [
                                    {"name": tool.name, "arguments": payload}
                                ]
                            }
                        ]
                    )
                )
                result = adapter.invoke_json(task_type, {"ticket": 1, "notes": "x"})
                self.assertEqual(validate_json_schema(result.payload, tool.parameters_schema), [])

    def test_schema_failure_reprompt_includes_error_context(self):
        tool = TASK_TOOL_MAP["pm_phase1"]
        client = _CapturingClient(
            [
                {
                    "tool_calls": [
                        {
                            "name": tool.name,
                            "arguments": {"decision": "PROVISIONAL_CHAMPION"},
                        }
                    ]
                },
                {
                    "tool_calls": [
                        {
                            "name": tool.name,
                            "arguments": {
                                "decision": "PROVISIONAL_CHAMPION",
                                "reason": "fixed",
                            },
                        }
                    ]
                },
            ]
        )
        adapter = CopilotSDKAdapter(client)
        result = adapter.invoke_json("pm_phase1", {"ticket": 12})
        self.assertEqual(result.payload["reason"], "fixed")
        self.assertEqual(client.calls, 2)

        second_call_messages = client.last_kwargs[1]["messages"]
        merged = "\n".join(m["content"] for m in second_call_messages)
        self.assertIn("schema_validation", merged)
        self.assertIn("missing required property", merged)

    def test_normalizes_numeric_string_payloads(self):
        tool = TASK_TOOL_MAP["pm_research_synthesis"]
        adapter = CopilotSDKAdapter(
            _CapturingClient(
                [
                    {
                        "tool_calls": [
                            {
                                "name": tool.name,
                                "arguments": {
                                    "summary": "ok",
                                    "confidence_score": "0.9",
                                    "closed_linked_research_count": "2",
                                },
                            }
                        ]
                    }
                ]
            )
        )
        result = adapter.invoke_json("pm_research_synthesis", {"ticket": 1})
        self.assertEqual(result.payload["confidence_score"], 0.9)
        self.assertEqual(result.payload["closed_linked_research_count"], 2)

    def test_exhausts_retries_when_schema_never_valid(self):
        tool = TASK_TOOL_MAP["pm_phase1"]
        adapter = CopilotSDKAdapter(
            _CapturingClient(
                [
                    {
                        "tool_calls": [
                            {
                                "name": tool.name,
                                "arguments": {"decision": "PROVISIONAL_CHAMPION"},
                            }
                        ]
                    }
                ]
            )
        )
        with self.assertRaises(ToolSchemaValidationError):
            adapter.invoke_json("pm_phase1", {"ticket": 99})

    def test_missing_required_array_field_defaults_to_empty_array(self):
        tool = TASK_TOOL_MAP["pm_research_task_plan"]
        adapter = CopilotSDKAdapter(
            _CapturingClient(
                [
                    {
                        "tool_calls": [
                            {
                                "name": tool.name,
                                "arguments": {},
                            }
                        ]
                    }
                ]
            )
        )
        result = adapter.invoke_json("pm_research_task_plan", {"ticket": 55})
        self.assertEqual(result.payload["tasks"], [])
        self.assertEqual(validate_json_schema(result.payload, tool.parameters_schema), [])

    def test_foundation_wiki_manager_prompt_includes_strict_policy(self):
        tool = TASK_TOOL_MAP["wiki_manager"]
        prompt = CopilotSDKAdapter._build_tool_request_prompt("wiki_manager", tool, {"topic": "runtime"})
        self.assertIn("Task prompt template:", prompt)
        self.assertIn("Strict policy:", prompt)
        self.assertIn("Prefer updating an existing page", prompt)
        self.assertIn("required_sections", prompt)


if __name__ == "__main__":
    unittest.main()
