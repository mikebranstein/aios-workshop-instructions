from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Sequence, Set

from aios_orchestration_core.core.gateway import BaseGateway


@dataclass
class PMIssue:
    number: int
    title: str
    body: str
    labels: Set[str] = field(default_factory=set)
    open: bool = True
    comments: List[str] = field(default_factory=list)
    linked_research_issue_numbers: List[int] = field(default_factory=list)


class PMGateway(BaseGateway, Protocol):
    """PM-loop gateway: extends BaseGateway with PM-specific operations."""

    def get_issue(self, issue_number: int) -> PMIssue:
        ...

    def list_open_issues_with_any_label(self, labels: Sequence[str]) -> List[PMIssue]:
        ...

    def add_labels(self, issue_number: int, labels: Sequence[str]) -> None:
        ...

    def remove_labels(self, issue_number: int, labels: Sequence[str]) -> None:
        ...

    def set_state_labels(self, issue_number: int, labels_to_remove: Sequence[str], labels_to_add: Sequence[str]) -> None:
        ...

    def post_comment(self, issue_number: int, body: str) -> None:
        ...

    def close_issue(self, issue_number: int, reason: str) -> None:
        ...

    def are_linked_research_issues_closed(self, issue_number: int) -> bool:
        ...

    def count_closed_linked_research_issues(self, issue_number: int) -> int:
        ...

    def publish_strategic_opportunity_artifact(self, issue_number: int, artifact: Dict[str, object]) -> None:
        ...

    def ensure_research_issue(self, pm_issue_number: int, title: str, body: str, labels: Sequence[str]) -> int:
        ...


class PMGitHubGateway:
    """In-memory deterministic PM issue operations used by orchestrator nodes."""

    def __init__(self, issues: Optional[Dict[int, PMIssue]] = None):
        self.issues: Dict[int, PMIssue] = issues or {}
        self.published_artifacts: Dict[int, Dict[str, object]] = {}
        self.wiki_pages: Dict[str, str] = {}

    @staticmethod
    def _render_content_index(existing: str, page_path: str, issue_number: int, summary: str) -> str:
        marker = f"| `{page_path}` | #{issue_number} |"
        header = (
            "# Content-Index\n\n"
            "| Wiki Page | Source Issue | Summary |\n"
            "|---|---|---|"
        )
        lines = existing.strip().splitlines() if existing.strip() else header.splitlines()
        if marker in "\n".join(lines):
            updated = []
            for line in lines:
                if line.startswith(marker):
                    updated.append(f"{marker} {summary} |")
                else:
                    updated.append(line)
            return "\n".join(updated).strip() + "\n"
        return ("\n".join(lines).strip() + f"\n{marker} {summary} |\n")

    def get_issue(self, issue_number: int) -> PMIssue:
        return self.issues[issue_number]

    def list_open_issues_with_any_label(self, labels: Sequence[str]) -> List[PMIssue]:
        label_set = set(labels)
        return [
            issue for issue in self.issues.values() if issue.open and issue.labels.intersection(label_set)
        ]

    def add_labels(self, issue_number: int, labels: Sequence[str]) -> None:
        self.issues[issue_number].labels.update(labels)

    def remove_labels(self, issue_number: int, labels: Sequence[str]) -> None:
        for label in labels:
            self.issues[issue_number].labels.discard(label)

    def set_state_labels(self, issue_number: int, labels_to_remove: Sequence[str], labels_to_add: Sequence[str]) -> None:
        self.remove_labels(issue_number, labels_to_remove)
        self.add_labels(issue_number, labels_to_add)

    def post_comment(self, issue_number: int, body: str) -> None:
        self.issues[issue_number].comments.append(body)

    def close_issue(self, issue_number: int, reason: str) -> None:
        issue = self.issues[issue_number]
        issue.open = False
        issue.comments.append(f"Closed: {reason}")

    def are_linked_research_issues_closed(self, issue_number: int) -> bool:
        issue = self.issues[issue_number]
        for linked_number in issue.linked_research_issue_numbers:
            linked = self.issues.get(linked_number)
            if linked is not None and linked.open:
                return False
        return True

    def count_closed_linked_research_issues(self, issue_number: int) -> int:
        issue = self.issues[issue_number]
        count = 0
        for linked_number in issue.linked_research_issue_numbers:
            linked = self.issues.get(linked_number)
            if linked is not None and not linked.open:
                count += 1
        return count

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
        self.wiki_pages[page_path] = content
        existing = self.wiki_pages.get("Content-Index.md", "")
        self.wiki_pages["Content-Index.md"] = self._render_content_index(
            existing,
            page_path,
            issue_number,
            "PM strategic opportunity artifact",
        )
        self.post_comment(issue_number, f"Strategic Opportunity Artifact Published: {artifact.get('artifact_id', 'unknown')}")

    def ensure_research_issue(self, pm_issue_number: int, title: str, body: str, labels: Sequence[str]) -> int:
        label_set = set(labels)
        for number, issue in self.issues.items():
            if title == issue.title and label_set.issubset(issue.labels):
                if number not in self.issues[pm_issue_number].linked_research_issue_numbers:
                    self.issues[pm_issue_number].linked_research_issue_numbers.append(number)
                return number

        new_number = max(self.issues.keys()) + 1 if self.issues else 1
        self.issues[new_number] = PMIssue(
            number=new_number,
            title=title,
            body=body,
            labels=set(labels),
            open=True,
        )
        if new_number not in self.issues[pm_issue_number].linked_research_issue_numbers:
            self.issues[pm_issue_number].linked_research_issue_numbers.append(new_number)
        return new_number
