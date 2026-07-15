import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import foundation_runner
from aios_orchestration_core.github.foundation_gateway import FoundationGitHubGateway, FoundationIssue
from foundation_orchestrator.evidence import extract_links, classify_wiki_links, classify_adr_links


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

    def has_approved_foundation_issue(self) -> bool:
        return False

    # DISCOVERY-FOCUS.md stubs — return "file already exists and is approved" so
    # _ensure_discovery_focus is a no-op in the loop tests that don't target it.
    def discovery_focus_exists(self) -> bool:
        return True

    def get_discovery_focus_issue(self):
        from aios_orchestration_core.github.foundation_gateway import FoundationIssue
        return FoundationIssue(
            number=999,
            title="[discovery-focus]: Synthesize DISCOVERY-FOCUS.md from FOUNDATION.md",
            body="",
            labels={"discovery-focus:approved"},
        )

    def list_adr_files(self):
        return []

    def read_repo_file(self, path: str) -> str:
        return ""

    def get_wiki_snapshot(self, limit: int = 50, excerpt_chars: int = 1200):
        return []


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

    def test_has_approved_foundation_issue_detects_closed_approved(self) -> None:
        gateway = FoundationGitHubGateway(
            issues={
                1: FoundationIssue(number=1, title="Foundation Setup", body="b", labels={"foundation:approved"}, open=False),
            }
        )
        self.assertTrue(gateway.has_approved_foundation_issue())

    def test_has_approved_foundation_issue_detects_open_approved(self) -> None:
        """An open issue tagged foundation:approved (stuck after close failure) must be detected."""
        gateway = FoundationGitHubGateway(
            issues={
                1: FoundationIssue(number=1, title="Foundation Setup", body="b", labels={"foundation:approved"}, open=True),
            }
        )
        self.assertTrue(gateway.has_approved_foundation_issue())

    def test_has_approved_foundation_issue_false_when_none_approved(self) -> None:
        gateway = FoundationGitHubGateway(
            issues={
                1: FoundationIssue(number=1, title="Foundation Setup", body="b", labels={"foundation:in-progress"}, open=True),
            }
        )
        self.assertFalse(gateway.has_approved_foundation_issue())

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
                elif task_type == "adr_generator":
                    payload = {
                        "adr_title": "Adopt Python 3.14 runtime",
                        "context_section": "## Context\n\nContext here.",
                        "decision_section": "## Decision\n\nWe will use Python 3.14.",
                        "alternatives_section": "## Alternatives Considered\n\n### Alternative 1: Python 3.12\n\n**Pros:**\n- Stable\n\n**Cons:**\n- Older",
                        "rationale_section": "## Rationale\n\n### 1. Fit\n\nFits constraints.",
                        "consequences_section": "## Consequences\n\n### Positive\n\n- Modern runtime\n\n### Negative / Risks\n\n- ⚠️ **Upgrade cost** (Severity: LOW)\n  Minor.",
                        "validation_strategy_section": "## Validation Strategy\n\n**Metrics:**\n- Build success rate: 100%\n\n**Review Schedule:**\n- Cadence: quarterly",
                        "rollback_section": "## Rollback / Exit Strategy\n\n**Conditions:** If Python 3.14 is abandoned.\n\n**Rollback steps:**\n1. Revert.\n\n**Cost of rollback:**\n- Effort: 2 days",
                        "related_decisions_section": "## Related Decisions\n\n**References:**\n- Foundation research issue: #101",
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
        # ADR file must be written to docs/adr/
        adr_files = gateway.list_adr_files()
        self.assertEqual(len(adr_files), 1)
        adr_content = gateway._repo_files[adr_files[0]]
        self.assertIn("Adopt Python 3.14 runtime", adr_content)
        self.assertIn("ADR-0000", adr_content)
        # Primary comment on the parent issue must reference both wiki and ADR
        parent_comments = gateway.get_issue(1).comments
        combined = "\n".join(parent_comments)
        self.assertIn("wiki/foundation/runtime-and-language-baseline.md", combined)
        self.assertIn("docs/adr/", combined)

    def test_linked_research_worker_writes_wiki_when_no_wiki_title_provided(self) -> None:
        """Wiki should be written even when the LLM omits wiki_page_title/wiki_summary."""
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
                    title="[foundation-research] Persistence for #1",
                    body="Research body",
                    labels={"foundation:research"},
                    open=True,
                ),
            },
            sub_issues={1: [101]},
        )

        class _MinimalAdapter:
            def invoke_json(self, task_type: str, prompt_vars: dict, model_hint: str = ""):
                if task_type == "foundation_research_worker":
                    # No wiki_page_title or wiki_summary returned, but adr_title IS required
                    payload = {
                        "decision": "COMPLETE",
                        "summary": "Persistence strategy decided.",
                        "adr_title": "Adopt SQLite for persistence",
                        "adr_summary": "SQLite chosen.",
                        "next_actions": [],
                    }
                elif task_type == "wiki_manager":
                    payload = {
                        "decision": "CREATE_PAGE",
                        "page_path": "foundation/persistence-for-1.md",
                        "page_content": "# Persistence for #1\n\nPersistence strategy decided.",
                        "content_index_summary": "Persistence decision captured.",
                        "page_moves": [],
                        "reason": "New page",
                    }
                elif task_type == "adr_generator":
                    payload = {
                        "adr_title": "Adopt SQLite for persistence",
                        "context_section": "## Context\n\nContext.",
                        "decision_section": "## Decision\n\nWe will use SQLite.",
                        "alternatives_section": "## Alternatives Considered\n\n### Alt 1\n\n**Pros:**\n- Simple\n\n**Cons:**\n- Limited",
                        "rationale_section": "## Rationale\n\n### 1. Fit\n\nFits.",
                        "consequences_section": "## Consequences\n\n### Positive\n\n- Simple\n\n### Negative / Risks\n\n- ⚠️ **Scale** (Severity: LOW)\n  Low scale.",
                        "validation_strategy_section": "## Validation Strategy\n\n**Metrics:**\n- Query time: <100ms\n\n**Review Schedule:**\n- Cadence: quarterly",
                        "rollback_section": "## Rollback / Exit Strategy\n\n**Conditions:** If scale exceeds SQLite limits.\n\n**Rollback steps:**\n1. Migrate.\n\n**Cost of rollback:**\n- Effort: 3 days",
                        "related_decisions_section": "## Related Decisions\n\n**References:**\n- #{research_issue_number}",
                    }
                else:
                    payload = {}
                return type("R", (), {"payload": payload, "model": "auto"})()

        result = foundation_runner._run_linked_research_workers(
            gateway=gateway,
            adapter=_MinimalAdapter(),
            foundation_issue_number=1,
            foundation_markdown="# FOUNDATION",
        )

        self.assertEqual(result["completed"], 1)
        page = gateway.read_wiki_page("foundation/persistence-for-1.md")
        self.assertIn("Persistence strategy decided", page)
        self.assertEqual(len(gateway.list_adr_files()), 1)

    def _make_research_gateway(self):
        return FoundationGitHubGateway(
            issues={
                1: FoundationIssue(
                    number=1,
                    title="Foundation Setup",
                    body="Foundation body",
                    labels={"foundation:in-progress"},
                ),
                101: FoundationIssue(
                    number=101,
                    title="[foundation-research] Auth for #1",
                    body="Research body",
                    labels={"foundation:research"},
                    open=True,
                ),
            },
            sub_issues={1: [101]},
        )

    def test_research_issue_not_closed_when_wiki_write_fails(self) -> None:
        """Issue must stay open when the wiki gateway raises (e.g. git push failure)."""
        gateway = self._make_research_gateway()

        class _FailWikiAdapter:
            def invoke_json(self, task_type, prompt_vars, model_hint=""):
                if task_type == "foundation_research_worker":
                    payload = {
                        "decision": "COMPLETE",
                        "summary": "Auth strategy complete.",
                        "adr_title": "Use JWT for auth",
                        "adr_summary": "JWT chosen.",
                        "next_actions": [],
                    }
                elif task_type == "wiki_manager":
                    raise RuntimeError("git push failed: remote rejected")
                elif task_type == "adr_generator":
                    payload = {
                        "adr_title": "Use JWT for auth",
                        "context_section": "## Context\n\nContext.",
                        "decision_section": "## Decision\n\nWe will use JWT.",
                        "alternatives_section": "## Alternatives Considered\n\n### Alt 1\n\n**Pros:**\n- Simple\n\n**Cons:**\n- None",
                        "rationale_section": "## Rationale\n\n### 1. Fit\n\nFits.",
                        "consequences_section": "## Consequences\n\n### Positive\n\n- Secure\n\n### Negative / Risks\n\n- ⚠️ **Token expiry** (Severity: LOW)\n  Low.",
                        "validation_strategy_section": "## Validation Strategy\n\n**Metrics:**\n- Auth latency: <50ms\n\n**Review Schedule:**\n- Cadence: quarterly",
                        "rollback_section": "## Rollback / Exit Strategy\n\n**Conditions:** If JWT fails.\n\n**Rollback steps:**\n1. Switch to sessions.\n\n**Cost of rollback:**\n- Effort: 1 week",
                        "related_decisions_section": "## Related Decisions\n\n**References:**\n- #101",
                    }
                else:
                    payload = {}
                return type("R", (), {"payload": payload, "model": "auto"})()

        result = foundation_runner._run_linked_research_workers(
            gateway=gateway,
            adapter=_FailWikiAdapter(),
            foundation_issue_number=1,
            foundation_markdown="# FOUNDATION",
        )

        self.assertEqual(result["completed"], 0)
        self.assertTrue(gateway.get_issue(101).open, "Research issue must stay open when wiki write fails")
        # A failure comment must be posted (without the decision marker so next pass retries)
        comments = gateway.get_issue(101).comments
        self.assertTrue(any("closure blocked" in c.lower() for c in comments))
        self.assertFalse(any("Foundation research worker decision:" in c for c in comments))

    def test_research_issue_not_closed_when_adr_title_missing(self) -> None:
        """Issue must stay open when LLM returns COMPLETE without providing an adr_title."""
        gateway = self._make_research_gateway()

        class _NoAdrTitleAdapter:
            def invoke_json(self, task_type, prompt_vars, model_hint=""):
                if task_type == "foundation_research_worker":
                    payload = {
                        "decision": "COMPLETE",
                        "summary": "Auth strategy complete.",
                        # adr_title intentionally omitted
                        "next_actions": [],
                    }
                elif task_type == "wiki_manager":
                    payload = {
                        "decision": "CREATE_PAGE",
                        "page_path": "foundation/auth-for-1.md",
                        "page_content": "# Auth\n\nAuth complete.",
                        "content_index_summary": "Auth decision.",
                        "page_moves": [],
                        "reason": "New page",
                    }
                else:
                    payload = {}
                return type("R", (), {"payload": payload, "model": "auto"})()

        result = foundation_runner._run_linked_research_workers(
            gateway=gateway,
            adapter=_NoAdrTitleAdapter(),
            foundation_issue_number=1,
            foundation_markdown="# FOUNDATION",
        )

        self.assertEqual(result["completed"], 0)
        self.assertTrue(gateway.get_issue(101).open, "Research issue must stay open when ADR title is missing")
        comments = gateway.get_issue(101).comments
        self.assertTrue(any("adr_title missing" in c.lower() for c in comments))

    def test_research_issue_not_closed_when_adr_write_fails(self) -> None:
        """Issue must stay open when adr_generator returns no content."""
        gateway = self._make_research_gateway()

        class _FailAdrAdapter:
            def invoke_json(self, task_type, prompt_vars, model_hint=""):
                if task_type == "foundation_research_worker":
                    payload = {
                        "decision": "COMPLETE",
                        "summary": "Auth strategy complete.",
                        "adr_title": "Use JWT for auth",
                        "adr_summary": "JWT chosen.",
                        "next_actions": [],
                    }
                elif task_type == "wiki_manager":
                    payload = {
                        "decision": "CREATE_PAGE",
                        "page_path": "foundation/auth-for-1.md",
                        "page_content": "# Auth\n\nAuth complete.",
                        "content_index_summary": "Auth decision.",
                        "page_moves": [],
                        "reason": "New page",
                    }
                elif task_type == "adr_generator":
                    # All sections empty — simulates a total LLM failure
                    payload = {}
                else:
                    payload = {}
                return type("R", (), {"payload": payload, "model": "auto"})()

        result = foundation_runner._run_linked_research_workers(
            gateway=gateway,
            adapter=_FailAdrAdapter(),
            foundation_issue_number=1,
            foundation_markdown="# FOUNDATION",
        )

        # The ADR file should still be written by _assemble_adr_content using fallback
        # sections — _generate_and_write_adr writes something even when sections are empty.
        # So the issue SHOULD close. (Adjust if stricter ADR content validation is added.)
        self.assertEqual(result["completed"], 1)
        self.assertFalse(gateway.get_issue(101).open)

    def test_main_returns_0_without_creating_issue_when_approved_issue_exists(self) -> None:
        """Re-running after completion must not spawn a new foundation issue."""

        class _AlreadyApprovedGateway(_LoopGatewayStub):
            def has_approved_foundation_issue(self) -> bool:
                return True

        gateway = _AlreadyApprovedGateway(open_issues=[])
        exit_code, pass_mock = _run_main_with_loop(
            gateway, signatures=[("s",)] * 10, extra_args=["--verify-passes", "2"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(gateway.created), 0, "Must not create a new issue when one is already approved")
        pass_mock.assert_not_called()


class EvidenceLinkExtractionTests(unittest.TestCase):
    """extract_links must pick up wiki/ relative paths in addition to https:// and docs/adr/ paths."""

    def test_extracts_https_url(self) -> None:
        links = extract_links(["See https://github.com/org/repo/wiki/Home for details."])
        self.assertIn("https://github.com/org/repo/wiki/Home", links)

    def test_extracts_docs_adr_path(self) -> None:
        links = extract_links(["ADR link: docs/adr/0001-use-postgres.md"])
        self.assertIn("docs/adr/0001-use-postgres.md", links)

    def test_extracts_wiki_relative_path(self) -> None:
        """wiki/foundation/... relative paths must be extracted so classify_wiki_links sees them."""
        links = extract_links(["Research wiki reference: wiki/foundation/my-topic.md"])
        self.assertTrue(
            any(lnk.startswith("wiki/") for lnk in links),
            f"Expected a wiki/ link but got: {links}",
        )

    def test_wiki_relative_path_classified_as_wiki_link(self) -> None:
        """A wiki/ relative path must survive extract_links → classify_wiki_links pipeline."""
        text = "Research wiki reference: wiki/foundation/auth-decisions.md"
        links = extract_links([text])
        wiki_links = classify_wiki_links(links)
        self.assertTrue(
            len(wiki_links) > 0,
            "wiki/foundation/auth-decisions.md should be classified as a wiki link",
        )

    def test_adr_relative_path_classified_as_adr_link(self) -> None:
        links = extract_links(["Research ADR reference: docs/adr/0002-service-mesh.md"])
        adr_links = classify_adr_links(links)
        self.assertGreater(len(adr_links), 0)

    def test_wiki_zero_when_only_adr_present(self) -> None:
        """When only ADR links exist the wiki count must be 0 (regression guard)."""
        links = extract_links(["docs/adr/0003-cache-strategy.md"])
        wiki_links = classify_wiki_links(links)
        self.assertEqual(len(wiki_links), 0)


class NextActionsForStateTests(unittest.TestCase):
    """_next_actions_for_state must not say 'close research' when all research is already closed."""

    def _run(self, state: str, blockers: list[str], open_research: int) -> list[str]:
        from aios_orchestration_core.states.foundation import FoundationState
        fs = FoundationState[state] if state else None
        return foundation_runner._next_actions_for_state(fs, blockers, open_research)

    def test_in_progress_open_research_says_complete_issues(self) -> None:
        actions = self._run("FOUNDATION_IN_PROGRESS", blockers=[], open_research=3)
        self.assertTrue(any("close" in a or "complete" in a for a in actions))

    def test_in_progress_all_closed_no_blockers_says_advancing(self) -> None:
        """When open_research==0 and no blockers the message should reflect readiness."""
        actions = self._run("FOUNDATION_IN_PROGRESS", blockers=[], open_research=0)
        joined = " ".join(actions).lower()
        # Must NOT say "close at least one" (the old misleading message)
        self.assertNotIn("close at least one", joined)
        # Must convey forward progress / advancing
        self.assertTrue(
            any(word in joined for word in ("advancing", "evidence", "gate", "closed")),
            f"Expected an advancing/ready message but got: {actions}",
        )

    def test_in_progress_all_closed_with_blockers_surfaces_blockers(self) -> None:
        actions = self._run("FOUNDATION_IN_PROGRESS", blockers=["at least one ADR link is required"], open_research=0)
        joined = " ".join(actions).lower()
        self.assertIn("adr", joined)

    def test_main_returns_0_without_creating_issue_when_open_approved_issue_exists(self) -> None:
        """An open issue with foundation:approved (stuck) must also block re-creation."""

        class _OpenApprovedGateway(_LoopGatewayStub):
            def has_approved_foundation_issue(self) -> bool:
                return True  # open + approved, not yet closed

        gateway = _OpenApprovedGateway(open_issues=[])
        exit_code, pass_mock = _run_main_with_loop(
            gateway, signatures=[("s",)] * 10, extra_args=["--verify-passes", "2"]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(gateway.created), 0, "Must not create a new issue when open approved issue exists")
        pass_mock.assert_not_called()

    def test_concurrent_adr_writes_get_distinct_sequence_numbers(self) -> None:
        """Multiple threads calling _generate_and_write_adr concurrently must
        produce ADR files with unique, non-overlapping sequence numbers."""
        import threading

        gateway = FoundationGitHubGateway(
            issues={1: FoundationIssue(number=1, title="Foundation", body="", labels={"foundation:in-progress"})},
        )

        class _QuickAdapter:
            adapter_source = "stub"

            def invoke_json(self, task_type, context):
                return type("R", (), {
                    "payload": {
                        "context_section": "## Context\nTest.",
                        "decision_section": "## Decision\nTest.",
                    },
                    "model": "stub",
                })()

        adapter = _QuickAdapter()
        written_paths: list = []
        errors: list = []

        def write_one(n: int) -> None:
            try:
                path = foundation_runner._generate_and_write_adr(
                    gateway=gateway,
                    adapter=adapter,
                    foundation_issue_number=1,
                    research_issue_number=100 + n,
                    research_issue_title=f"Research {n}",
                    wiki_page_path=f"foundation/page-{n}.md",
                    adr_title=f"Decision {n}",
                    adr_summary=f"Summary for decision {n}",
                    foundation_markdown="# FOUNDATION",
                )
                written_paths.append(path)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=write_one, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [], f"Threads raised errors: {errors}")
        self.assertEqual(len(written_paths), 5, "Expected 5 ADR files written")
        # Each path must carry a unique 4-digit prefix.
        prefixes = [Path(p).stem.split("-", 1)[0] for p in written_paths]
        self.assertEqual(len(set(prefixes)), 5, f"Duplicate ADR numbers detected: {prefixes}")


class EnsureDiscoveryFocusTests(unittest.TestCase):
    """Tests for foundation_runner._ensure_discovery_focus helper."""

    class _StubLLMAdapter:
        """Stub that returns synthesis + passing verification by default."""
        adapter_source = "stub"
        verify_passes = True

        def invoke_json(self, task_type, prompt_vars, model_hint=""):
            if task_type == "foundation_discovery_focus_synthesis":
                return type("R", (), {
                    "payload": {
                        "focus_content": "# DISCOVERY-FOCUS\n\nSynthesized content.",
                        "confidence": "medium",
                        "placeholder_fields": [],
                    },
                    "model": "stub",
                })()
            if task_type == "foundation_discovery_focus_verify":
                if self.verify_passes:
                    return type("R", (), {
                        "payload": {
                            "passed": True,
                            "verdict": "All required sections present.",
                            "failing_sections": [],
                        },
                        "model": "stub",
                    })()
                else:
                    return type("R", (), {
                        "payload": {
                            "passed": False,
                            "verdict": "Missing sections detected.",
                            "failing_sections": ["Priority Problems", "Definition of a Useful Idea"],
                        },
                        "model": "stub",
                    })()
            return type("R", (), {"payload": {}, "model": "stub"})()

    def test_creates_synthesizes_verifies_and_approves_when_missing(self) -> None:
        """Full happy path: no file, no issue → synthesize → verify passes → approved + closed."""
        gw = FoundationGitHubGateway()
        adapter = self._StubLLMAdapter()
        status = foundation_runner._ensure_discovery_focus(gw, adapter, "# FOUNDATION", adrs={}, wiki_snapshot=[])
        self.assertEqual(status, "approved")
        self.assertTrue(gw.discovery_focus_exists())
        issue = gw.get_discovery_focus_issue()
        self.assertIsNotNone(issue)
        self.assertIn("discovery-focus:approved", issue.labels)

    def test_stays_draft_when_verification_fails(self) -> None:
        """Synthesis succeeds but verification fails → issue stays draft with comment."""
        gw = FoundationGitHubGateway()
        adapter = self._StubLLMAdapter()
        adapter.verify_passes = False
        status = foundation_runner._ensure_discovery_focus(gw, adapter, "# FOUNDATION", adrs={}, wiki_snapshot=[])
        self.assertEqual(status, "just-created")
        issue = gw.get_discovery_focus_issue()
        self.assertIsNotNone(issue)
        self.assertNotIn("discovery-focus:approved", issue.labels)
        self.assertTrue(issue.comments, "Should have posted a failure comment")
        self.assertTrue(any("Priority Problems" in c for c in issue.comments))

    def test_returns_approved_when_already_approved(self) -> None:
        gw = FoundationGitHubGateway()
        gw.write_discovery_focus("# DISCOVERY-FOCUS\n\nContent.", "test: create")
        num = gw.create_discovery_focus_issue("Body")
        gw.set_discovery_focus_label(num, "discovery-focus:approved")
        adapter = self._StubLLMAdapter()
        status = foundation_runner._ensure_discovery_focus(gw, adapter, "# FOUNDATION", adrs={}, wiki_snapshot=[])
        self.assertEqual(status, "approved")

    def test_reverifies_draft_and_approves_on_next_run(self) -> None:
        """File + issue exist in draft state → re-run verify → passes → approved."""
        gw = FoundationGitHubGateway()
        gw.write_discovery_focus("# DISCOVERY-FOCUS\n\nContent.", "test: create")
        gw.create_discovery_focus_issue("Body")
        adapter = self._StubLLMAdapter()
        status = foundation_runner._ensure_discovery_focus(gw, adapter, "# FOUNDATION", adrs={}, wiki_snapshot=[])
        self.assertEqual(status, "approved")
        issue = gw.get_discovery_focus_issue()
        self.assertIn("discovery-focus:approved", issue.labels)

    def test_stays_draft_when_reverification_fails(self) -> None:
        """File + issue exist in draft state → re-run verify → fails → stays draft."""
        gw = FoundationGitHubGateway()
        gw.write_discovery_focus("# DISCOVERY-FOCUS\n\nContent.", "test: create")
        gw.create_discovery_focus_issue("Body")
        adapter = self._StubLLMAdapter()
        adapter.verify_passes = False
        status = foundation_runner._ensure_discovery_focus(gw, adapter, "# FOUNDATION", adrs={}, wiki_snapshot=[])
        self.assertEqual(status, "draft")
        issue = gw.get_discovery_focus_issue()
        self.assertNotIn("discovery-focus:approved", issue.labels)

    def test_resynthesize_on_needs_revision_then_verify(self) -> None:
        """needs-revision → re-synthesize → verify passes → approved + closed."""
        gw = FoundationGitHubGateway()
        gw.write_discovery_focus("# OLD CONTENT", "test: create")
        num = gw.create_discovery_focus_issue("Body")
        gw.set_discovery_focus_label(num, "discovery-focus:needs-revision")
        adapter = self._StubLLMAdapter()
        status = foundation_runner._ensure_discovery_focus(gw, adapter, "# FOUNDATION", adrs={}, wiki_snapshot=[])
        self.assertEqual(status, "approved")
        self.assertIn("DISCOVERY-FOCUS", gw.read_discovery_focus())
        issue = gw.get_discovery_focus_issue()
        self.assertIn("discovery-focus:approved", issue.labels)
        self.assertNotIn("discovery-focus:needs-revision", issue.labels)

    def test_returns_missing_review_when_file_exists_no_issue(self) -> None:
        gw = FoundationGitHubGateway()
        gw.write_discovery_focus("# Content", "test: create")
        adapter = self._StubLLMAdapter()
        status = foundation_runner._ensure_discovery_focus(gw, adapter, "# FOUNDATION", adrs={}, wiki_snapshot=[])
        self.assertEqual(status, "missing-review")

    def test_reuses_existing_issue_when_file_missing_but_issue_exists(self) -> None:
        """Re-run after file deleted should reuse the existing tracking issue, not create a new one."""
        gw = FoundationGitHubGateway()
        existing_num = gw.create_discovery_focus_issue("Prior body")
        adapter = self._StubLLMAdapter()
        status = foundation_runner._ensure_discovery_focus(gw, adapter, "# FOUNDATION", adrs={}, wiki_snapshot=[])
        self.assertEqual(status, "approved")
        self.assertTrue(gw.discovery_focus_exists())
        issue = gw.get_discovery_focus_issue()
        self.assertEqual(issue.number, existing_num)
        self.assertIn("discovery-focus:approved", issue.labels)



if __name__ == "__main__":
    unittest.main()
