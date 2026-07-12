import json
import re
import subprocess
from typing import List

from aios_orchestration_core.github.pm_gateway_api import GitHubApiConfig
from discovery_orchestrator.context import DiscoveryContext


class GitHubApiDiscoveryGateway:
    """GitHub CLI-backed Discovery gateway for context loading and PM-idea creation."""

    def __init__(self, config: GitHubApiConfig):
        self.config = config

    def _gh(self, args: List[str]) -> str:
        cmd = ["gh", "-R", self.config.repo] + args
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return completed.stdout.strip()

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
