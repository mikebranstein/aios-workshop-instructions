import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from aios_orchestration_core.github.arch_review_gateway_api import GitHubApiArchReviewGateway
from aios_orchestration_core.github.discovery_gateway_api import GitHubApiDiscoveryGateway
from aios_orchestration_core.github.foundation_gateway_api import GitHubApiFoundationGateway
from aios_orchestration_core.github.pm_gateway_api import GitHubApiConfig


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

        with patch("aios_orchestration_core.github.foundation_gateway_api.subprocess.run", side_effect=fake_run):
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

        with patch("aios_orchestration_core.github.foundation_gateway_api.subprocess.run", side_effect=fake_run):
            changed = gateway.write_wiki_page(
                "foundation/new-page.md",
                "# New Page\n\nBody",
                "foundation: update wiki page",
            )

        self.assertTrue(changed)
        commands = [cmd for cmd, _ in seen]
        self.assertIn(["git", "commit", "-m", "foundation: update wiki page"], commands)
        self.assertIn(["git", "push"], commands)

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

        with patch("aios_orchestration_core.github.foundation_gateway_api.subprocess.run", side_effect=fake_run):
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


if __name__ == "__main__":
    unittest.main()
