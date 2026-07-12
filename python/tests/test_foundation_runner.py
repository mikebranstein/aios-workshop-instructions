import io
import unittest
from unittest.mock import patch

import foundation_runner


class _GatewayMissingFoundation:
    def foundation_markdown_exists(self) -> bool:
        return False

    def list_open_issues_with_any_label(self, labels):
        raise AssertionError("Runner should fail before scanning issues when FOUNDATION.md is missing")

    def create_foundation_issue(self, title, body):
        raise AssertionError("Runner should fail before creating issues when FOUNDATION.md is missing")


class _ContextStub:
    def __init__(self, gateway):
        self._gateway = gateway

    def create_foundation_gateway(self):
        return self._gateway

    def __str__(self) -> str:
        return "GitHub: owner/repo"


class FoundationRunnerTests(unittest.TestCase):
    def test_main_returns_1_when_foundation_markdown_missing(self) -> None:
        gateway = _GatewayMissingFoundation()
        context = _ContextStub(gateway)

        stderr = io.StringIO()
        with patch("sys.argv", ["foundation_runner.py", "owner/repo"]), patch(
            "foundation_runner.RepoContext.from_string", return_value=context
        ), patch("sys.stderr", stderr):
            exit_code = foundation_runner.main()

        self.assertEqual(exit_code, 1)
        self.assertIn("FOUNDATION.md not found", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
