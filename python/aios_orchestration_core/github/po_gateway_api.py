import json
import re
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from aios_orchestration_core.github.comment_formatter import (
    CommentFormatter,
    NullCommentFormatter,
)
from aios_orchestration_core.github.pm_gateway_api import GitHubApiConfig
from aios_orchestration_core.github.po_gateway import POIssue


class GitHubApiPOGateway:
    """GitHub CLI-backed PO gateway."""

    def __init__(self, config: GitHubApiConfig, comment_formatter: Optional[CommentFormatter] = None):
        self.config = config
        self.comment_formatter: CommentFormatter = comment_formatter or NullCommentFormatter()

    def _gh(self, args: List[str]) -> str:
        cmd = ["gh", "-R", self.config.repo] + args
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return (completed.stdout or "").strip()

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

    def get_issue(self, issue_number: int) -> POIssue:
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
        return POIssue(
            number=obj["number"],
            title=obj.get("title", ""),
            body=obj.get("body", ""),
            labels={l["name"] for l in obj.get("labels", [])},
            open=obj.get("state", "OPEN").upper() == "OPEN",
            created_feature_request_numbers=self.list_created_feature_request_numbers(issue_number),
        )

    def list_open_issues_with_any_label(self, labels: Sequence[str]) -> List[POIssue]:
        raw = self._gh(["issue", "list", "--state", "open", "--limit", "200", "--json", "number,title,body,state,labels"])
        all_issues = json.loads(raw)
        label_set = set(labels)
        result: List[POIssue] = []
        for item in all_issues:
            issue_labels = {l["name"] for l in item.get("labels", [])}
            if issue_labels.intersection(label_set):
                result.append(
                    POIssue(
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
        self._gh(["issue", "comment", str(issue_number), "--body", self.comment_formatter.format(body)])

    def close_issue(self, issue_number: int, reason: str) -> None:
        self._gh(["issue", "close", str(issue_number), "--reason", reason])

    def create_feature_request(
        self,
        source_opportunity_number: int,
        title: str,
        body: str,
        priority_score: int,
    ) -> int:
        source_label = f"source-opportunity-{source_opportunity_number}"
        labels = ["dev:intake", "feature-request", source_label]
        self._ensure_labels(labels)

        issue_body = f"{body}\n\n---\nPriority Score: {priority_score}\nSource Opportunity: #{source_opportunity_number}"
        create_cmd = ["issue", "create", "--title", title, "--body", issue_body]
        for label in labels:
            create_cmd += ["--label", label]

        output = self._gh(create_cmd)
        match = re.search(r"/issues/(\d+)", output)
        if not match:
            raise RuntimeError(f"Unable to parse issue number from gh output: {output}")
        return int(match.group(1))

    def list_created_feature_request_numbers(self, opportunity_number: int) -> List[int]:
        source_label = f"source-opportunity-{opportunity_number}"
        raw = self._gh(
            [
                "issue",
                "list",
                "--state",
                "all",
                "--label",
                source_label,
                "--limit",
                "200",
                "--json",
                "number",
            ]
        )
        return [int(i["number"]) for i in json.loads(raw)]
