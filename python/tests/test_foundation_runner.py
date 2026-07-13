import io
import unittest
from unittest.mock import patch

import foundation_runner
from aios_orchestration_core.github.foundation_gateway import FoundationGitHubGateway, FoundationIssue


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

    def test_supporting_research_issue_detection_true_for_foundation_research_label(self) -> None:
        issue = FoundationIssue(
            number=1,
            title="Research",
            body="body",
            labels={"foundation:research", "foundation:in-progress", "foundation-source-2"},
        )
        self.assertTrue(foundation_runner._is_supporting_research_issue(issue))

    def test_supporting_research_issue_detection_false_for_primary_foundation_issue(self) -> None:
        issue = FoundationIssue(
            number=2,
            title="Foundation Setup",
            body="body",
            labels={"foundation:in-progress"},
        )
        self.assertFalse(foundation_runner._is_supporting_research_issue(issue))

    def test_linked_research_worker_writes_wiki_and_content_index(self) -> None:
        gateway = FoundationGitHubGateway(
            issues={
                1: FoundationIssue(
                    number=1,
                    title="Foundation Setup",
                    body="Foundation body",
                    labels={"foundation:in-progress"},
                ),
                101: FoundationIssue(
                    number=101,
                    title="[foundation-research] Runtime and Language for #1",
                    body="Research body",
                    labels={"foundation:research", "foundation-source-1"},
                    open=True,
                ),
            }
        )

        class _Adapter:
            def invoke_json(self, task_type: str, prompt_vars: dict, model_hint: str = ""):
                if task_type == "foundation_research_worker":
                    payload = {
                        "decision": "COMPLETE",
                        "summary": "Runtime selection complete.",
                        "wiki_page_title": "Runtime and Language Baseline",
                        "wiki_summary": "Python 3.14 selected with rationale.",
                        "adr_title": "Adopt Python 3.14 runtime",
                        "adr_summary": "Tradeoffs documented.",
                        "next_actions": ["Proceed to review"],
                    }
                elif task_type == "wiki_manager":
                    payload = {
                        "decision": "CREATE_PAGE",
                        "page_path": "foundation/runtime-and-language-baseline.md",
                        "page_content": "# Runtime and Language Baseline\n\nPython 3.14 selected.",
                        "content_index_summary": "Runtime baseline approved.",
                        "page_moves": [],
                        "reason": "New foundation topic page",
                    }
                else:
                    payload = {}
                return type("R", (), {"payload": payload, "model": "auto"})()

        result = foundation_runner._run_linked_research_workers(
            gateway=gateway,
            adapter=_Adapter(),
            foundation_issue_number=1,
            foundation_markdown="# FOUNDATION",
        )

        self.assertEqual(result["completed"], 1)
        self.assertFalse(gateway.get_issue(101).open)
        page = gateway.read_wiki_page("foundation/runtime-and-language-baseline.md")
        self.assertIn("Python 3.14 selected", page)
        index = gateway.read_wiki_page("Content-Index.md")
        self.assertIn("foundation/runtime-and-language-baseline.md", index)
        self.assertIn("#101", index)


if __name__ == "__main__":
    unittest.main()
