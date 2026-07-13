import os
import unittest
from unittest import mock

from aios_orchestration_core.github.comment_formatter import (
    FORMAT_ISSUE_COMMENT_TASK,
    LLMCommentFormatter,
    NullCommentFormatter,
    build_comment_formatter,
    formatting_enabled,
)


class _Result:
    def __init__(self, payload):
        self.payload = payload


class _FakeAdapter:
    def __init__(self, payload=None, raises=None):
        self._payload = payload or {}
        self._raises = raises
        self.calls = []

    def invoke_json(self, task_type, prompt_vars, model_hint=""):
        self.calls.append((task_type, prompt_vars, model_hint))
        if self._raises is not None:
            raise self._raises
        return _Result(self._payload)


class NullCommentFormatterTests(unittest.TestCase):
    def test_returns_body_unchanged(self):
        fmt = NullCommentFormatter()
        self.assertEqual(fmt.format("hello **world**"), "hello **world**")


class LLMCommentFormatterTests(unittest.TestCase):
    def test_success_returns_formatted_markdown(self):
        adapter = _FakeAdapter(payload={"formatted_markdown": "# Title\n\nBody"})
        fmt = LLMCommentFormatter(adapter, model_hint="gpt-x")
        out = fmt.format("title\nbody")
        self.assertEqual(out, "# Title\n\nBody")
        self.assertEqual(adapter.calls[0][0], FORMAT_ISSUE_COMMENT_TASK)
        self.assertEqual(adapter.calls[0][1], {"raw_comment": "title\nbody"})
        self.assertEqual(adapter.calls[0][2], "gpt-x")

    def test_blank_body_skips_adapter(self):
        adapter = _FakeAdapter(payload={"formatted_markdown": "should not be used"})
        fmt = LLMCommentFormatter(adapter)
        self.assertEqual(fmt.format("   "), "   ")
        self.assertEqual(adapter.calls, [])

    def test_empty_payload_falls_back_to_original(self):
        adapter = _FakeAdapter(payload={})
        fmt = LLMCommentFormatter(adapter)
        self.assertEqual(fmt.format("original"), "original")

    def test_blank_formatted_falls_back_to_original(self):
        adapter = _FakeAdapter(payload={"formatted_markdown": "   "})
        fmt = LLMCommentFormatter(adapter)
        self.assertEqual(fmt.format("original"), "original")

    def test_non_string_formatted_falls_back_to_original(self):
        adapter = _FakeAdapter(payload={"formatted_markdown": 123})
        fmt = LLMCommentFormatter(adapter)
        self.assertEqual(fmt.format("original"), "original")

    def test_adapter_exception_fails_open(self):
        adapter = _FakeAdapter(raises=RuntimeError("boom"))
        fmt = LLMCommentFormatter(adapter)
        self.assertEqual(fmt.format("original"), "original")


class BuildCommentFormatterTests(unittest.TestCase):
    def test_none_adapter_returns_null(self):
        self.assertIsInstance(build_comment_formatter(None), NullCommentFormatter)

    def test_adapter_returns_llm_formatter(self):
        self.assertIsInstance(
            build_comment_formatter(_FakeAdapter()), LLMCommentFormatter
        )

    def test_disabled_env_returns_null(self):
        with mock.patch.dict(os.environ, {"AIOS_FORMAT_COMMENTS": "0"}):
            self.assertIsInstance(
                build_comment_formatter(_FakeAdapter()), NullCommentFormatter
            )

    def test_enabled_env_returns_llm_formatter(self):
        with mock.patch.dict(os.environ, {"AIOS_FORMAT_COMMENTS": "1"}):
            self.assertIsInstance(
                build_comment_formatter(_FakeAdapter()), LLMCommentFormatter
            )


class FormattingEnabledTests(unittest.TestCase):
    def test_default_enabled(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertTrue(formatting_enabled())

    def test_disabled_values(self):
        for value in ("0", "false", "no", "off", "OFF", " False "):
            with mock.patch.dict(os.environ, {"AIOS_FORMAT_COMMENTS": value}):
                self.assertFalse(formatting_enabled(), value)


class GatewayRoutingTests(unittest.TestCase):
    def test_foundation_gateway_post_comment_routes_through_formatter(self):
        from aios_orchestration_core.github.foundation_gateway_api import (
            GitHubApiFoundationGateway,
        )
        from aios_orchestration_core.github.pm_gateway_api import GitHubApiConfig

        class _UpperFormatter:
            def format(self, body: str) -> str:
                return body.upper()

        gateway = GitHubApiFoundationGateway(
            GitHubApiConfig(repo="owner/repo"), comment_formatter=_UpperFormatter()
        )
        captured = {}
        gateway._gh = lambda args: captured.setdefault("args", args) or ""
        gateway.post_comment(7, "hello world")
        self.assertIn("HELLO WORLD", captured["args"])
        self.assertNotIn("hello world", captured["args"])

    def test_foundation_gateway_defaults_to_null_formatter(self):
        from aios_orchestration_core.github.foundation_gateway_api import (
            GitHubApiFoundationGateway,
        )
        from aios_orchestration_core.github.pm_gateway_api import GitHubApiConfig

        gateway = GitHubApiFoundationGateway(GitHubApiConfig(repo="owner/repo"))
        self.assertIsInstance(gateway.comment_formatter, NullCommentFormatter)
        captured = {}
        gateway._gh = lambda args: captured.setdefault("args", args) or ""
        gateway.post_comment(7, "hello world")
        self.assertIn("hello world", captured["args"])


if __name__ == "__main__":
    unittest.main()
