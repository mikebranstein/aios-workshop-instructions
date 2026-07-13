import io
import tempfile
import unittest
from pathlib import Path
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

    def _ensure_wiki_exists(self) -> None:
        pass  # Won't be called since FOUNDATION.md check happens first


class _LoopGatewayStub:
    """Minimal gateway that satisfies main()'s bootstrap so the verification loop runs."""

    def __init__(self, open_issues):
        self._open_issues = open_issues
        self.created = []
        self.comment_formatter = None

    def foundation_markdown_exists(self) -> bool:
        return True

    def read_foundation_markdown(self) -> str:
        return "# FOUNDATION"

    def list_open_issues_with_any_label(self, labels):
        return list(self._open_issues)

    def create_foundation_issue(self, title, body):
        number = 100 + len(self.created)
        self.created.append(number)
        return number

    def _ensure_wiki_exists(self) -> None:
        """Stub: do nothing."""
        pass


class _ContextStub:
    def __init__(self, gateway):
        self._gateway = gateway

    def create_foundation_gateway(self):
        return self._gateway

    def __str__(self) -> str:
        return "GitHub: owner/repo"


def _run_main_with_loop(gateway, signatures, extra_args=None):
    """Run main() against a stub gateway, patching the per-pass work and signatures."""
    context = _ContextStub(gateway)
    with tempfile.TemporaryDirectory() as tmp:
        argv = ["foundation_runner.py", "owner/repo", "--stub", "--log-dir", tmp]
        if extra_args:
            argv.extend(extra_args)
        with patch("sys.argv", argv), patch(
            "foundation_runner.RepoContext.from_string", return_value=context
        ), patch(
            "foundation_runner._process_foundation_pass", return_value=([], [])
        ) as pass_mock, patch(
            "foundation_runner._world_signature", side_effect=list(signatures)
        ):
            exit_code = foundation_runner.main()
    return exit_code, pass_mock


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

    def test_verification_loop_confirms_idle_before_exiting(self) -> None:
        gateway = _LoopGatewayStub(open_issues=[FoundationIssue(number=1, title="F", body="b", labels={"foundation:needed"})])
        # Signature is queried before/after each pass and never changes -> every pass idle.
        exit_code, pass_mock = _run_main_with_loop(
            gateway, signatures=[("same",)] * 10, extra_args=["--verify-passes", "2"]
        )
        self.assertEqual(exit_code, 0)
        # verify-passes=2 consecutive idle passes -> exactly 2 passes.
        self.assertEqual(pass_mock.call_count, 2)

    def test_verification_loop_continues_while_progress_is_made(self) -> None:
        gateway = _LoopGatewayStub(open_issues=[FoundationIssue(number=1, title="F", body="b", labels={"foundation:needed"})])
        # pass1: before=A, after=B (progress, reset)
        # pass2: before=B, after=B (idle 1)
        # pass3: before=B, after=B (idle 2 -> stop)
        signatures = [("A",), ("B",), ("B",), ("B",), ("B",), ("B",)]
        exit_code, pass_mock = _run_main_with_loop(
            gateway, signatures=signatures, extra_args=["--verify-passes", "2"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(pass_mock.call_count, 3)

    def test_verification_loop_honors_max_passes_cap(self) -> None:
        gateway = _LoopGatewayStub(open_issues=[FoundationIssue(number=1, title="F", body="b", labels={"foundation:needed"})])
        # Signature always differs across before/after -> never idle; cap must stop it.
        exit_code, pass_mock = _run_main_with_loop(
            gateway,
            signatures=[(str(i),) for i in range(50)],
            extra_args=["--verify-passes", "2", "--max-passes", "3"],
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(pass_mock.call_count, 3)

    def test_bootstrap_creates_issue_only_once_when_none_open(self) -> None:
        gateway = _LoopGatewayStub(open_issues=[])
        exit_code, pass_mock = _run_main_with_loop(
            gateway, signatures=[("s",)] * 10, extra_args=["--verify-passes", "2"]
        )
        self.assertEqual(exit_code, 0)
        # Even across multiple passes, only one foundation issue is created.
        self.assertEqual(len(gateway.created), 1)

    def test_world_signature_reflects_state_and_research_counts(self) -> None:
        gateway = FoundationGitHubGateway(
            issues={
                1: FoundationIssue(number=1, title="Foundation Setup", body="b", labels={"foundation:in-progress"}, open=True),
                101: FoundationIssue(number=101, title="research", body="b", labels={"foundation:research"}, open=True),
            },
            sub_issues={1: [101]},
        )
        sig_before = foundation_runner._world_signature(gateway)
        gateway.close_issue(101, "completed")
        sig_after = foundation_runner._world_signature(gateway)
        self.assertNotEqual(sig_before, sig_after)

    def test_supporting_research_issue_detection_true_for_foundation_research_label(self) -> None:
        issue = FoundationIssue(
            number=1,
            title="Research",
            body="body",
            labels={"foundation:research", "foundation:in-progress"},
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
                    labels={"foundation:research"},
                    open=True,
                ),
            },
            sub_issues={1: [101]},
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
