import json
import re
import subprocess
from typing import List, Sequence

from aios_orchestration_core.github.foundation_gateway import (
    FoundationArtifactState,
    FoundationIssue,
)
from aios_orchestration_core.github.pm_gateway_api import GitHubApiConfig


class GitHubApiFoundationGateway:
    """GitHub CLI-backed Foundation gateway."""

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

    def _ensure_labels(self, labels: Sequence[str]) -> None:
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

    def get_issue(self, issue_number: int) -> FoundationIssue:
        raw = self._gh(
            [
                "issue",
                "view",
                str(issue_number),
                "--json",
                "number,title,body,state,labels",
            ]
        )
        obj = json.loads(raw)
        return FoundationIssue(
            number=obj["number"],
            title=obj.get("title", ""),
            body=obj.get("body", ""),
            labels={l["name"] for l in obj.get("labels", [])},
            open=obj.get("state", "OPEN").upper() == "OPEN",
        )

    def list_open_issues_with_any_label(self, labels: Sequence[str]) -> List[FoundationIssue]:
        raw = self._gh(["issue", "list", "--state", "open", "--limit", "200", "--json", "number,title,body,state,labels"])
        all_issues = json.loads(raw)
        label_set = set(labels)
        result: List[FoundationIssue] = []
        for item in all_issues:
            issue_labels = {l["name"] for l in item.get("labels", [])}
            if issue_labels.intersection(label_set):
                result.append(
                    FoundationIssue(
                        number=item["number"],
                        title=item.get("title", ""),
                        body=item.get("body", ""),
                        labels=issue_labels,
                        open=True,
                    )
                )
        return result

    def add_labels(self, issue_number: int, labels: Sequence[str]) -> None:
        if not labels:
            return
        self._ensure_labels(labels)
        self._gh(["issue", "edit", str(issue_number), "--add-label", ",".join(labels)])

    def remove_labels(self, issue_number: int, labels: Sequence[str]) -> None:
        if not labels:
            return
        self._gh(["issue", "edit", str(issue_number), "--remove-label", ",".join(labels)])

    def set_state_labels(self, issue_number: int, labels_to_remove: Sequence[str], labels_to_add: Sequence[str]) -> None:
        self.remove_labels(issue_number, labels_to_remove)
        self.add_labels(issue_number, labels_to_add)

    def post_comment(self, issue_number: int, body: str) -> None:
        self._gh(["issue", "comment", str(issue_number), "--body", body])

    def close_issue(self, issue_number: int, reason: str) -> None:
        self._gh(["issue", "close", str(issue_number), "--reason", reason])

    def get_artifact_state(self) -> FoundationArtifactState:
        focus_path = "docs/discovery-focus.md"
        return FoundationArtifactState(
            decision_pack_exists=self._file_exists("docs/foundation-decision-pack.md"),
            adr_template_exists=self._file_exists("docs/adr/0000-template.md"),
            discovery_focus_exists=self._file_exists(focus_path),
            discovery_focus_populated=self._file_is_populated(focus_path),
        )

    def foundation_markdown_exists(self) -> bool:
        return self._file_exists("FOUNDATION.md")

    def create_foundation_issue(self, title: str, body: str) -> int:
        self._ensure_labels(["foundation:needed"])
        output = self._gh(
            [
                "issue",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--label",
                "foundation:needed",
            ]
        )
        match = re.search(r"/issues/(\d+)", output)
        if not match:
            raise RuntimeError(f"Unable to parse issue number from gh output: {output}")
        return int(match.group(1))
