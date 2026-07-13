import json
import re
import subprocess
import base64
from typing import List, Sequence

from aios_orchestration_core.github.foundation_gateway import (
    FoundationIssue,
    LinkedFoundationIssue,
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

    def _read_repo_file(self, path: str) -> str:
        result = self._gh_api(f"repos/{self.config.repo}/contents/{path}")
        if result.returncode != 0:
            return ""
        payload = json.loads(result.stdout)
        encoded = (payload.get("content") or "").replace("\n", "")
        if not encoded:
            return ""
        return base64.b64decode(encoded).decode("utf-8", errors="replace")

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
        issue = self.get_issue(issue_number)
        removable = [label for label in labels if label in issue.labels]
        if not removable:
            return
        self._gh(["issue", "edit", str(issue_number), "--remove-label", ",".join(removable)])

    def set_state_labels(self, issue_number: int, labels_to_remove: Sequence[str], labels_to_add: Sequence[str]) -> None:
        # Add first, then remove old labels; this avoids no-state windows.
        self.add_labels(issue_number, labels_to_add)
        remove_after_add = [label for label in labels_to_remove if label not in set(labels_to_add)]
        self.remove_labels(issue_number, remove_after_add)

    def post_comment(self, issue_number: int, body: str) -> None:
        self._gh(["issue", "comment", str(issue_number), "--body", body])

    def close_issue(self, issue_number: int, reason: str) -> None:
        self._gh(["issue", "close", str(issue_number), "--reason", reason])

    def foundation_markdown_exists(self) -> bool:
        return self._file_exists("FOUNDATION.md")

    def read_foundation_markdown(self) -> str:
        return self._read_repo_file("FOUNDATION.md")

    def get_issue_comments(self, issue_number: int) -> List[str]:
        raw = self._gh(
            [
                "issue",
                "view",
                str(issue_number),
                "--json",
                "comments",
            ]
        )
        obj = json.loads(raw)
        return [comment.get("body", "") for comment in obj.get("comments", [])]

    def ensure_research_issue(
        self,
        foundation_issue_number: int,
        title: str,
        body: str,
        labels: Sequence[str],
    ) -> int:
        trace_label = f"foundation-source-{foundation_issue_number}"
        raw = self._gh(
            [
                "issue",
                "list",
                "--state",
                "open",
                "--label",
                "foundation:research",
                "--label",
                trace_label,
                "--limit",
                "200",
                "--json",
                "number,title",
            ]
        )
        for item in json.loads(raw):
            if item.get("title") == title:
                return int(item["number"])

        create_labels = list(labels) + ["foundation:research", trace_label]
        self._ensure_labels(create_labels)
        create_cmd = ["issue", "create", "--title", title, "--body", body]
        for label in create_labels:
            create_cmd += ["--label", label]
        output = self._gh(create_cmd)
        match = re.search(r"/issues/(\d+)", output)
        if not match:
            raise RuntimeError(f"Unable to parse issue number from gh output: {output}")
        return int(match.group(1))

    def list_linked_research_issues(self, foundation_issue_number: int) -> List[LinkedFoundationIssue]:
        trace_label = f"foundation-source-{foundation_issue_number}"
        raw = self._gh(
            [
                "issue",
                "list",
                "--state",
                "all",
                "--label",
                "foundation:research",
                "--label",
                trace_label,
                "--limit",
                "200",
                "--json",
                "number,title,body,state",
            ]
        )
        result: List[LinkedFoundationIssue] = []
        for item in json.loads(raw):
            result.append(
                LinkedFoundationIssue(
                    number=int(item["number"]),
                    title=item.get("title", ""),
                    body=item.get("body", ""),
                    open=item.get("state", "OPEN").upper() == "OPEN",
                )
            )
        return result

    def count_open_linked_research_issues(self, foundation_issue_number: int) -> int:
        return len([i for i in self.list_linked_research_issues(foundation_issue_number) if i.open])

    def count_closed_linked_research_issues(self, foundation_issue_number: int) -> int:
        return len([i for i in self.list_linked_research_issues(foundation_issue_number) if not i.open])

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
