import base64
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from aios_orchestration_core.github.pm_gateway_api import GitHubApiConfig
from aios_orchestration_core.wiki.github_wiki_manager import GitHubWikiManager
from discovery_orchestrator.context import DiscoveryContext

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates" / "discovery"


def _render_template(name: str, **vars: str) -> str:
    """Load a Markdown template from templates/discovery/ and render it.

    Variable placeholders use the ``{{VARIABLE_NAME}}`` convention.
    """
    content = (_TEMPLATES_DIR / name).read_text(encoding="utf-8")
    for key, value in vars.items():
        content = content.replace("{{" + key + "}}", value)
    return content.rstrip("\n")


class GitHubApiDiscoveryGateway:
    """GitHub CLI-backed Discovery gateway for context loading and PM-idea creation."""

    def __init__(self, config: GitHubApiConfig):
        self.config = config
        self._wiki = GitHubWikiManager(repo=self.config.repo, temp_prefix="aios-discovery-wiki-")

    def _gh(self, args: List[str]) -> str:
        cmd = ["gh", "-R", self.config.repo] + args
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        return (completed.stdout or "").strip()

    def _gh_api(self, path: str, jq: str | None = None) -> subprocess.CompletedProcess:
        cmd = ["gh", "api", path]
        if jq is not None:
            cmd += ["--jq", jq]
        return subprocess.run(cmd, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace")

    def _ensure_labels(self, labels: List[str]) -> None:
        for label in labels:
            subprocess.run(
                [
                    "gh",
                    "-R",
                    self.config.repo,
                    "label",
                    "create",
                    label,
                    "--color",
                    "1D76DB",
                    "--description",
                    "AIOS managed label",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

    def _file_exists(self, path: str) -> bool:
        result = self._gh_api(f"repos/{self.config.repo}/contents/{path}", ".type")
        return result.returncode == 0

    def _file_is_populated(self, path: str) -> bool:
        result = self._gh_api(f"repos/{self.config.repo}/contents/{path}", ".size")
        if result.returncode != 0:
            return False
        return int(result.stdout.strip() or "0") > 0

    def _is_foundation_approved(self) -> bool:
        raw = self._gh(
            [
                "issue",
                "list",
                "--state",
                "all",
                "--label",
                "foundation:approved",
                "--limit",
                "1",
                "--json",
                "number",
            ]
        )
        return len(json.loads(raw)) > 0

    def _is_discovery_focus_approved(self) -> bool:
        raw = self._gh(
            [
                "issue",
                "list",
                "--state",
                "all",
                "--label",
                "discovery-focus:approved",
                "--limit",
                "1",
                "--json",
                "number",
            ]
        )
        return len(json.loads(raw)) > 0

    def get_context(self) -> DiscoveryContext:
        focus_path = "DISCOVERY-FOCUS.md"
        return DiscoveryContext(
            foundation_gate_passed=self._is_foundation_approved(),
            focus_file_exists=self._file_exists(focus_path),
            focus_file_populated=self._file_is_populated(focus_path),
            discovery_focus_approved=self._is_discovery_focus_approved(),
        )

    def read_focus_file(self) -> str:
        """Return the decoded content of DISCOVERY-FOCUS.md."""
        result = self._gh_api("repos/{repo}/contents/DISCOVERY-FOCUS.md".format(repo=self.config.repo))
        if result.returncode != 0:
            return ""
        try:
            data = json.loads(result.stdout or "{}")
            raw = data.get("content", "")
            # GitHub API returns base64-encoded content with newlines
            return base64.b64decode(raw.replace("\n", "")).decode("utf-8", errors="replace")
        except Exception:
            return ""

    def create_pm_idea_issue(self, title: str, body: str) -> int:
        labels = ["pm-idea", "pm-idea-auto"]
        self._ensure_labels(labels)
        output = self._gh(
            [
                "issue",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--label",
                "pm-idea",
                "--label",
                "pm-idea-auto",
            ]
        )
        match = re.search(r"/issues/(\d+)", output)
        if not match:
            raise RuntimeError(f"Unable to parse issue number from gh output: {output}")
        return int(match.group(1))

    def append_deferred_candidates(self, candidates: List[dict]) -> bool:
        """Append deferred candidates to the Discovery-Deferred-Candidates wiki page."""
        if not candidates:
            return True
        stamp = datetime.now(timezone.utc).isoformat()
        section_header = _render_template("deferred-candidates-section.md", TIMESTAMP=stamp)
        lines = [f"\n{section_header}\n"]
        for c in candidates:
            title = c.get("title", "(no title)")
            body = c.get("body", "")
            lines.append(_render_template("deferred-candidate-entry.md", TITLE=title, BODY=body) + "\n")
        new_content = "\n".join(lines)

        try:
            existing = self._wiki.read_page("Discovery-Deferred-Candidates.md") or ""
        except Exception:
            existing = ""

        combined = (existing.rstrip() + "\n" + new_content).strip() + "\n"
        self._wiki.apply_changes(
            page_path="Discovery-Deferred-Candidates.md",
            page_content=combined,
            page_moves=[],
            index_issue_number=0,
            index_summary="Discovery deferred candidates",
            commit_message="discovery: append deferred candidates",
        )
        return True

    def publish_discovery_run_artifact(
        self,
        *,
        state: str,
        created_pm_idea_numbers: List[int],
        deferred_count: int,
        dropped_count: int,
    ) -> None:
        stamp = datetime.now(timezone.utc).isoformat()
        created_list = ", ".join([f"#{n}" for n in created_pm_idea_numbers]) if created_pm_idea_numbers else "(none)"
        content = _render_template(
            "discovery-run-summary.md",
            STATE=state,
            CREATED_LIST=created_list,
            DEFERRED_COUNT=str(deferred_count),
            DROPPED_COUNT=str(dropped_count),
            TIMESTAMP=stamp,
        ) + "\n"
        self._wiki.apply_changes(
            page_path="discovery/discovery-run-summary.md",
            page_content=content,
            page_moves=[],
            index_issue_number=0,
            index_summary="Discovery run summary",
            commit_message="discovery: publish run summary",
        )
