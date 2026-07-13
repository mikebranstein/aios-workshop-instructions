import json
import re
import subprocess
from datetime import datetime, timezone
from typing import List

from aios_orchestration_core.github.pm_gateway_api import GitHubApiConfig
from aios_orchestration_core.wiki.github_wiki_manager import GitHubWikiManager
from discovery_orchestrator.context import DiscoveryContext


class GitHubApiDiscoveryGateway:
    """GitHub CLI-backed Discovery gateway for context loading and PM-idea creation."""

    def __init__(self, config: GitHubApiConfig):
        self.config = config
        self._wiki = GitHubWikiManager(repo=self.config.repo, temp_prefix="aios-discovery-wiki-")

    def _gh(self, args: List[str]) -> str:
        cmd = ["gh", "-R", self.config.repo] + args
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return (completed.stdout or "").strip()

    def _gh_api(self, path: str, jq: str | None = None) -> subprocess.CompletedProcess:
        cmd = ["gh", "api", path]
        if jq is not None:
            cmd += ["--jq", jq]
        return subprocess.run(cmd, check=False, capture_output=True, text=True)

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

    def get_context(self) -> DiscoveryContext:
        focus_path = "docs/discovery-focus.md"
        return DiscoveryContext(
            foundation_gate_passed=self._is_foundation_approved(),
            focus_file_exists=self._file_exists(focus_path),
            focus_file_populated=self._file_is_populated(focus_path),
        )

    def create(self, title: str, body: str) -> int:
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
        content = (
            "# Discovery Run Summary\n\n"
            f"## Run State\n\n{state}\n\n"
            f"## Created PM Ideas\n\n{created_list}\n\n"
            f"## Deferred Count\n\n{deferred_count}\n\n"
            f"## Dropped Count\n\n{dropped_count}\n\n"
            "## Traceability\n\n"
            f"- Generated at: {stamp}\n"
        )
        self._wiki.apply_changes(
            page_path="discovery/discovery-run-summary.md",
            page_content=content,
            page_moves=[],
            index_issue_number=0,
            index_summary="Discovery run summary",
            commit_message="discovery: publish run summary",
        )
