import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from aios_orchestration_core.github.arch_review_gateway_api import GitHubApiArchReviewGateway
from aios_orchestration_core.github.discovery_gateway_api import GitHubApiDiscoveryGateway
from aios_orchestration_core.github.foundation_gateway_api import GitHubApiFoundationGateway
from aios_orchestration_core.github.pm_gateway_api import GitHubApiConfig, GitHubApiPMGateway


def _cp(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")


class GitHubApiFoundationGatewayTests(unittest.TestCase):
    def test_foundation_markdown_exists_checks_repo_root_file(self) -> None:
        cfg = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiFoundationGateway(cfg)

        def fake_run(cmd, check, capture_output, text):
            if cmd[:2] == ["gh", "api"]:
                path = cmd[2]
                jq = cmd[4] if len(cmd) >= 5 and cmd[3] == "--jq" else ""
                if path.endswith("/FOUNDATION.md") and jq == ".type":
                    return _cp("file")
                return _cp("", returncode=1)
            return _cp("")

        with patch("aios_orchestration_core.github.foundation_gateway_api.subprocess.run", side_effect=fake_run):
            exists = gateway.foundation_markdown_exists()

        self.assertTrue(exists)

    def test_read_foundation_markdown_decodes_content(self) -> None:
        cfg = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiFoundationGateway(cfg)

        def fake_run(cmd, check, capture_output, text):
            if cmd[:2] == ["gh", "api"]:
                path = cmd[2]
                if path.endswith("/FOUNDATION.md"):
                    return _cp(json.dumps({"content": "IyBUZXN0IEZPVU5EQVRJT04K"}))
                return _cp("", returncode=1)
            return _cp("")

        with patch("aios_orchestration_core.github.foundation_gateway_api.subprocess.run", side_effect=fake_run):
            content = gateway.read_foundation_markdown()

        self.assertEqual(content, "# Test FOUNDATION\n")

    def test_create_foundation_issue_returns_created_number(self) -> None:
        cfg = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiFoundationGateway(cfg)

        def fake_run(cmd, check, capture_output, text):
            gh_args = cmd[3:] if cmd[:2] == ["gh", "-R"] else []
            if gh_args[:3] == ["label", "create", "foundation:needed"]:
                return _cp("")
            if gh_args[:2] == ["issue", "create"]:
                return _cp("https://github.com/owner/repo/issues/44")
            return _cp("")

        with patch("aios_orchestration_core.github.foundation_gateway_api.subprocess.run", side_effect=fake_run):
            issue_number = gateway.create_foundation_issue("Foundation Setup", "Body")

        self.assertEqual(issue_number, 44)

    def test_ensure_research_issue_creates_and_links_sub_issue(self) -> None:
        cfg = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiFoundationGateway(cfg)
        posted = []

        def fake_run(cmd, check, capture_output, text):
            # Parent has no existing sub-issues yet.
            if cmd[:2] == ["gh", "api"] and cmd[2].endswith("/issues/4/sub_issues") and "--method" not in cmd:
                return _cp("[]")
            # Resolve child DB id.
            if cmd[:2] == ["gh", "api"] and cmd[2].endswith("/issues/50") and "--jq" in cmd:
                return _cp("9999")
            # Link sub-issue (POST).
            if cmd[:2] == ["gh", "api"] and "--method" in cmd and "POST" in cmd:
                posted.append(cmd)
                return _cp("{}")
            gh_args = cmd[3:] if cmd[:2] == ["gh", "-R"] else []
            if gh_args[:2] == ["label", "create"]:
                return _cp("")
            if gh_args[:2] == ["issue", "create"]:
                return _cp("https://github.com/owner/repo/issues/50")
            return _cp("")

        with patch("aios_orchestration_core.github.foundation_gateway_api.subprocess.run", side_effect=fake_run):
            number = gateway.ensure_research_issue(4, "Research topic", "Body", labels=[])

        self.assertEqual(number, 50)
        self.assertTrue(posted, "expected a sub_issues POST to link the child")
        self.assertIn("sub_issue_id=9999", posted[0])

    def test_ensure_research_issue_dedupes_on_existing_sub_issue(self) -> None:
        cfg = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiFoundationGateway(cfg)
        created = []

        def fake_run(cmd, check, capture_output, text):
            if cmd[:2] == ["gh", "api"] and cmd[2].endswith("/issues/4/sub_issues"):
                return _cp(json.dumps([
                    {"number": 51, "title": "Research topic", "state": "open",
                     "labels": [{"name": "foundation:research"}]}
                ]))
            gh_args = cmd[3:] if cmd[:2] == ["gh", "-R"] else []
            if gh_args[:2] == ["issue", "create"]:
                created.append(cmd)
                return _cp("https://github.com/owner/repo/issues/99")
            return _cp("")

        with patch("aios_orchestration_core.github.foundation_gateway_api.subprocess.run", side_effect=fake_run):
            number = gateway.ensure_research_issue(4, "Research topic", "Body", labels=[])

        self.assertEqual(number, 51)
        self.assertFalse(created, "should not create a new issue when one already exists")

    def test_list_linked_research_issues_reads_sub_issues(self) -> None:
        cfg = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiFoundationGateway(cfg)

        def fake_run(cmd, check, capture_output, text):
            if cmd[:2] == ["gh", "api"] and cmd[2].endswith("/issues/4/sub_issues"):
                return _cp(json.dumps([
                    {"number": 51, "title": "Open one", "body": "b1", "state": "open",
                     "labels": [{"name": "foundation:research"}]},
                    {"number": 52, "title": "Closed one", "body": "b2", "state": "closed",
                     "labels": [{"name": "foundation:research"}]},
                    {"number": 53, "title": "Not research", "body": "b3", "state": "open",
                     "labels": [{"name": "something-else"}]},
                ]))
            return _cp("")

        with patch("aios_orchestration_core.github.foundation_gateway_api.subprocess.run", side_effect=fake_run):
            linked = gateway.list_linked_research_issues(4)
            open_count = gateway.count_open_linked_research_issues(4)
            closed_count = gateway.count_closed_linked_research_issues(4)

        self.assertEqual([i.number for i in linked], [51, 52])
        self.assertEqual(open_count, 1)
        self.assertEqual(closed_count, 1)

    def test_pm_publish_strategic_artifact_writes_wiki(self) -> None:
        cfg = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiPMGateway(cfg)
        seen = []

        def fake_run(cmd, check, capture_output, text, cwd=None):
            seen.append((cmd, cwd))
            gh_args = cmd[3:] if cmd[:2] == ["gh", "-R"] else []
            if gh_args[:2] == ["issue", "comment"]:
                return _cp("")
            if cmd[:2] == ["git", "clone"]:
                target = Path(cmd[3])
                target.mkdir(parents=True, exist_ok=True)
                return _cp("")
            if cmd[:1] == ["git"]:
                return _cp("")
            return _cp("")

        with patch("aios_orchestration_core.github.pm_gateway_api.subprocess.run", side_effect=fake_run), patch(
            "aios_orchestration_core.wiki.github_wiki_manager.subprocess.run", side_effect=fake_run
        ):
            gateway.publish_strategic_opportunity_artifact(
                issue_number=42,
                artifact={
                    "artifact_id": "so-42",
                    "title": "Strategic Opportunity",
                    "strategic_thesis": "Thesis",
                    "decision": "CHAMPION",
                    "confidence_score": 0.9,
                },
            )

        commands = [cmd for cmd, _ in seen]
        self.assertIn(["git", "commit", "-m", "pm: publish strategic opportunity artifact #42"], commands)
        self.assertIn(["git", "push", "-u", "origin", "master"], commands)

    def test_list_wiki_pages_clones_in_temp_and_returns_markdown_paths(self) -> None:
        cfg = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiFoundationGateway(cfg)
        seen = []

        def fake_run(cmd, check, capture_output, text, cwd=None):
            seen.append((cmd, cwd))
            if cmd[:2] == ["git", "clone"]:
                target = Path(cmd[3])
                target.mkdir(parents=True, exist_ok=True)
                (target / "Home.md").write_text("# Home\n", encoding="utf-8")
                (target / "foundation").mkdir(parents=True, exist_ok=True)
                (target / "foundation" / "runtime.md").write_text("# Runtime\n", encoding="utf-8")
            return _cp("")

        with patch("aios_orchestration_core.wiki.github_wiki_manager.subprocess.run", side_effect=fake_run):
            pages = gateway.list_wiki_pages()

        self.assertEqual(pages, ["Home.md", "foundation/runtime.md"])
        self.assertTrue(any(cmd[:2] == ["git", "clone"] for cmd, _ in seen))

    def test_write_wiki_page_commits_changes(self) -> None:
        cfg = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiFoundationGateway(cfg)
        seen = []

        def fake_run(cmd, check, capture_output, text, cwd=None):
            seen.append((cmd, cwd))
            if cmd[:2] == ["git", "clone"]:
                target = Path(cmd[3])
                target.mkdir(parents=True, exist_ok=True)
            return _cp("")

        with patch("aios_orchestration_core.wiki.github_wiki_manager.subprocess.run", side_effect=fake_run):
            changed = gateway.write_wiki_page(
                "foundation/new-page.md",
                "# New Page\n\nBody",
                "foundation: update wiki page",
            )

        self.assertTrue(changed)
        commands = [cmd for cmd, _ in seen]
        self.assertIn(["git", "commit", "-m", "foundation: update wiki page"], commands)
        self.assertIn(["git", "push", "-u", "origin", "master"], commands)

    def test_apply_wiki_manager_changes_uses_single_clone_and_commit(self) -> None:
        cfg = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiFoundationGateway(cfg)
        seen = []

        def fake_run(cmd, check, capture_output, text, cwd=None):
            seen.append((cmd, cwd))
            if cmd[:2] == ["git", "clone"]:
                target = Path(cmd[3])
                target.mkdir(parents=True, exist_ok=True)
                (target / "old").mkdir(parents=True, exist_ok=True)
                (target / "old" / "runtime.md").write_text("# Runtime\n", encoding="utf-8")
            return _cp("")

        with patch("aios_orchestration_core.wiki.github_wiki_manager.subprocess.run", side_effect=fake_run):
            changed = gateway.apply_wiki_manager_changes(
                page_path="foundation/runtime.md",
                page_content="# Runtime\n\nUpdated",
                page_moves=[{"from_path": "old/runtime.md", "to_path": "foundation/runtime.md"}],
                index_issue_number=42,
                index_summary="Runtime baseline selected.",
                commit_message="foundation: update wiki for issue #42",
            )

        self.assertTrue(changed)
        commands = [cmd for cmd, _ in seen]
        clone_calls = [cmd for cmd in commands if cmd[:2] == ["git", "clone"]]
        commit_calls = [cmd for cmd in commands if cmd[:2] == ["git", "commit"]]
        push_calls = [cmd for cmd in commands if cmd[:2] == ["git", "push"]]
        self.assertEqual(len(clone_calls), 1)
        self.assertEqual(len(commit_calls), 1)
        self.assertEqual(len(push_calls), 1)


class GitHubApiArchReviewGatewayTests(unittest.TestCase):
    def test_upsert_debt_updates_existing_open_issue(self) -> None:
        cfg = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiArchReviewGateway(cfg)

        def fake_run(cmd, check, capture_output, text):
            gh_args = cmd[3:] if cmd[:2] == ["gh", "-R"] else []
            if gh_args[:3] == ["label", "create", "architecture-debt"]:
                return _cp("")
            if gh_args[:3] == ["label", "create", "debt:new"]:
                return _cp("")
            if gh_args[:2] == ["issue", "list"]:
                return _cp(json.dumps([{"number": 77, "title": "Debt hotspot"}]))
            if gh_args[:2] == ["issue", "edit"]:
                return _cp("")
            return _cp("")

        with patch("aios_orchestration_core.github.arch_review_gateway_api.subprocess.run", side_effect=fake_run):
            issue_number = gateway.upsert_debt_issue("Debt hotspot", "Updated details")

        self.assertEqual(issue_number, 77)

    def test_create_arch_review_issue_returns_created_number(self) -> None:
        cfg = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiArchReviewGateway(cfg)

        def fake_run(cmd, check, capture_output, text):
            gh_args = cmd[3:] if cmd[:2] == ["gh", "-R"] else []
            if gh_args[:3] == ["label", "create", "arch:review-pending"]:
                return _cp("")
            if gh_args[:2] == ["issue", "create"]:
                return _cp("https://github.com/owner/repo/issues/88")
            return _cp("")

        with patch("aios_orchestration_core.github.arch_review_gateway_api.subprocess.run", side_effect=fake_run):
            issue_number = gateway.create_arch_review_issue("Architecture Review", "Body")

        self.assertEqual(issue_number, 88)


class GitHubApiDiscoveryGatewayTests(unittest.TestCase):
    def test_get_context_and_create_pm_idea(self) -> None:
        cfg = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiDiscoveryGateway(cfg)

        def fake_run(cmd, check, capture_output, text):
            if cmd[:2] == ["gh", "api"]:
                path = cmd[2]
                jq = cmd[4] if len(cmd) >= 5 and cmd[3] == "--jq" else ""
                if path.endswith("/docs/discovery-focus.md") and jq == ".type":
                    return _cp("file")
                if path.endswith("/docs/discovery-focus.md") and jq == ".size":
                    return _cp("256")
                return _cp("", returncode=1)

            gh_args = cmd[3:] if cmd[:2] == ["gh", "-R"] else []
            if gh_args[:2] == ["issue", "list"]:
                return _cp(json.dumps([{"number": 9}]))
            if gh_args[:3] == ["label", "create", "pm-idea"]:
                return _cp("")
            if gh_args[:3] == ["label", "create", "pm-idea-auto"]:
                return _cp("")
            if gh_args[:2] == ["issue", "create"]:
                return _cp("https://github.com/owner/repo/issues/123")
            return _cp("")

        with patch("aios_orchestration_core.github.discovery_gateway_api.subprocess.run", side_effect=fake_run):
            context = gateway.get_context()
            issue_number = gateway.create("New strategic idea", "Details")

        self.assertTrue(context.foundation_gate_passed)
        self.assertTrue(context.focus_file_exists)
        self.assertTrue(context.focus_file_populated)
        self.assertEqual(issue_number, 123)

    def test_publish_discovery_run_artifact_writes_wiki(self) -> None:
        cfg = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiDiscoveryGateway(cfg)
        seen = []

        def fake_run(cmd, check, capture_output, text, cwd=None):
            seen.append((cmd, cwd))
            if cmd[:2] == ["git", "clone"]:
                target = Path(cmd[3])
                target.mkdir(parents=True, exist_ok=True)
            return _cp("")

        with patch("aios_orchestration_core.wiki.github_wiki_manager.subprocess.run", side_effect=fake_run):
            gateway.publish_discovery_run_artifact(
                state="DISCOVERY_COMPLETE",
                created_pm_idea_numbers=[11, 12],
                deferred_count=1,
                dropped_count=0,
            )

        commands = [cmd for cmd, _ in seen]
        self.assertIn(["git", "commit", "-m", "discovery: publish run summary"], commands)
        self.assertIn(["git", "push", "-u", "origin", "master"], commands)


if __name__ == "__main__":
    unittest.main()
