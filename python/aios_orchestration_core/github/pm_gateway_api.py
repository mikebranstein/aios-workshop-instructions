import json
import re
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from aios_orchestration_core.github.pm_gateway import PMIssue
from aios_orchestration_core.wiki.github_wiki_manager import GitHubWikiManager


@dataclass
class GitHubApiConfig:
    repo: str


class GitHubApiPMGateway:
    """GitHub CLI-backed PM gateway for disposable-repo and staging validation."""

    def __init__(self, config: GitHubApiConfig):
        self.config = config
        self.published_artifacts: Dict[int, Dict[str, object]] = {}
        self._research_issue_cache: Dict[Tuple[int, str], int] = {}
        self._wiki = GitHubWikiManager(repo=self.config.repo, temp_prefix="aios-pm-wiki-")

    def _gh(self, args: List[str]) -> str:
        cmd = ["gh", "-R", self.config.repo] + args
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return completed.stdout.strip()

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

    def get_issue(self, issue_number: int) -> PMIssue:
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
        linked = self._list_linked_research_issue_numbers(issue_number)
        return PMIssue(
            number=obj["number"],
            title=obj.get("title", ""),
            body=obj.get("body", ""),
            labels={l["name"] for l in obj.get("labels", [])},
            open=obj.get("state", "OPEN").upper() == "OPEN",
            linked_research_issue_numbers=linked,
        )

    def list_open_issues_with_any_label(self, labels: Sequence[str]) -> List[PMIssue]:
        raw = self._gh(["issue", "list", "--state", "open", "--limit", "200", "--json", "number,title,body,state,labels"])
        all_issues = json.loads(raw)
        label_set = set(labels)
        result = []
        for item in all_issues:
            issue_labels = {l["name"] for l in item.get("labels", [])}
            if issue_labels.intersection(label_set):
                result.append(
                    PMIssue(
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

    def are_linked_research_issues_closed(self, issue_number: int) -> bool:
        return len(self._list_open_linked_research_issue_numbers(issue_number)) == 0

    def count_closed_linked_research_issues(self, issue_number: int) -> int:
        linked = self._list_linked_research_issue_numbers(issue_number)
        open_linked = set(self._list_open_linked_research_issue_numbers(issue_number))
        return len([n for n in linked if n not in open_linked])

    def publish_strategic_opportunity_artifact(self, issue_number: int, artifact: Dict[str, object]) -> None:
        self.published_artifacts[issue_number] = artifact
        artifact_id = str(artifact.get("artifact_id", f"so-{issue_number}"))
        page_path = f"pm/strategic-opportunities/{artifact_id}.md"
        title = str(artifact.get("title", f"Strategic Opportunity #{issue_number}"))
        thesis = str(artifact.get("strategic_thesis", ""))
        decision = str(artifact.get("decision", ""))
        confidence = artifact.get("confidence_score", "")
        content = (
            f"# {title}\n\n"
            f"## Summary\n\n{thesis}\n\n"
            f"## Decision\n\n{decision}\n\n"
            f"## Confidence\n\n{confidence}\n\n"
            f"## Traceability\n\n"
            f"- Source issue: #{issue_number}\n"
            f"- Artifact ID: {artifact_id}\n"
        )
        self._wiki.apply_changes(
            page_path=page_path,
            page_content=content,
            page_moves=[],
            index_issue_number=issue_number,
            index_summary="PM strategic opportunity artifact",
            commit_message=f"pm: publish strategic opportunity artifact #{issue_number}",
        )
        self.post_comment(issue_number, f"Strategic Opportunity Artifact Published: {artifact.get('artifact_id', 'unknown')}")

    def ensure_research_issue(self, pm_issue_number: int, title: str, body: str, labels: Sequence[str]) -> int:
        cache_key = (pm_issue_number, title)
        if cache_key in self._research_issue_cache:
            return self._research_issue_cache[cache_key]

        trace_label = f"pm-idea-{pm_issue_number}"
        raw = self._gh(
            [
                "issue",
                "list",
                "--state",
                "open",
                "--label",
                "research",
                "--label",
                trace_label,
                "--limit",
                "200",
                "--json",
                "number,title,labels",
            ]
        )
        for item in json.loads(raw):
            if item.get("title") == title:
                number = int(item["number"])
                self._research_issue_cache[cache_key] = number
                return number

        create_cmd = ["issue", "create", "--title", title, "--body", body]
        self._ensure_labels(labels)
        for label in labels:
            create_cmd += ["--label", label]
        output = self._gh(create_cmd)
        match = re.search(r"/issues/(\d+)", output)
        if not match:
            raise RuntimeError(f"Unable to parse issue number from gh output: {output}")
        number = int(match.group(1))
        self._research_issue_cache[cache_key] = number
        return number

    def _list_linked_research_issue_numbers(self, issue_number: int) -> List[int]:
        trace_label = f"pm-idea-{issue_number}"
        raw = self._gh(
            [
                "issue",
                "list",
                "--label",
                "research",
                "--label",
                trace_label,
                "--limit",
                "200",
                "--json",
                "number",
            ]
        )
        return [int(i["number"]) for i in json.loads(raw)]

    def _list_open_linked_research_issue_numbers(self, issue_number: int) -> List[int]:
        trace_label = f"pm-idea-{issue_number}"
        raw = self._gh(
            [
                "issue",
                "list",
                "--state",
                "open",
                "--label",
                "research",
                "--label",
                trace_label,
                "--limit",
                "200",
                "--json",
                "number",
            ]
        )
        return [int(i["number"]) for i in json.loads(raw)]
