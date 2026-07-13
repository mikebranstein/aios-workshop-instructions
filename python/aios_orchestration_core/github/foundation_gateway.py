from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Sequence, Set

from aios_orchestration_core.core.gateway import BaseGateway


@dataclass
class FoundationIssue:
    number: int
    title: str
    body: str
    labels: Set[str] = field(default_factory=set)
    open: bool = True
    comments: List[str] = field(default_factory=list)


@dataclass
class LinkedFoundationIssue:
    number: int
    title: str
    body: str
    open: bool = True


class FoundationGateway(BaseGateway, Protocol):
    def get_issue(self, issue_number: int) -> FoundationIssue: ...
    def list_open_issues_with_any_label(self, labels: Sequence[str]) -> List[FoundationIssue]: ...
    def foundation_markdown_exists(self) -> bool: ...
    def read_foundation_markdown(self) -> str: ...
    def get_issue_comments(self, issue_number: int) -> List[str]: ...
    def ensure_research_issue(self, foundation_issue_number: int, title: str, body: str, labels: Sequence[str]) -> int: ...
    def list_linked_research_issues(self, foundation_issue_number: int) -> List[LinkedFoundationIssue]: ...
    def count_open_linked_research_issues(self, foundation_issue_number: int) -> int: ...
    def count_closed_linked_research_issues(self, foundation_issue_number: int) -> int: ...
    def create_foundation_issue(self, title: str, body: str) -> int: ...


class FoundationGitHubGateway:
    def __init__(
        self,
        issues: Optional[Dict[int, FoundationIssue]] = None,
    ) -> None:
        self.issues: Dict[int, FoundationIssue] = issues or {}
        self._next = max(self.issues.keys(), default=0) + 100
        self._research_issue_cache: Dict[int, int] = {}

    def get_issue(self, issue_number: int) -> FoundationIssue:
        return self.issues[issue_number]

    def list_open_issues_with_any_label(self, labels: Sequence[str]) -> List[FoundationIssue]:
        label_set = set(labels)
        return [i for i in self.issues.values() if i.open and i.labels.intersection(label_set)]

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

    def foundation_markdown_exists(self) -> bool:
        return True

    def read_foundation_markdown(self) -> str:
        return "# FOUNDATION\n"

    def get_issue_comments(self, issue_number: int) -> List[str]:
        return list(self.issues[issue_number].comments)

    def ensure_research_issue(self, foundation_issue_number: int, title: str, body: str, labels: Sequence[str]) -> int:
        if foundation_issue_number in self._research_issue_cache:
            return self._research_issue_cache[foundation_issue_number]
        self._next += 1
        issue = FoundationIssue(
            number=self._next,
            title=title,
            body=body,
            labels=set(labels) | {"foundation:research", f"foundation-source-{foundation_issue_number}"},
        )
        self.issues[self._next] = issue
        self._research_issue_cache[foundation_issue_number] = self._next
        return self._next

    def list_linked_research_issues(self, foundation_issue_number: int) -> List[LinkedFoundationIssue]:
        trace_label = f"foundation-source-{foundation_issue_number}"
        result: List[LinkedFoundationIssue] = []
        for issue in self.issues.values():
            if "foundation:research" in issue.labels and trace_label in issue.labels:
                result.append(
                    LinkedFoundationIssue(
                        number=issue.number,
                        title=issue.title,
                        body=issue.body,
                        open=issue.open,
                    )
                )
        return result

    def count_open_linked_research_issues(self, foundation_issue_number: int) -> int:
        return len([i for i in self.list_linked_research_issues(foundation_issue_number) if i.open])

    def count_closed_linked_research_issues(self, foundation_issue_number: int) -> int:
        return len([i for i in self.list_linked_research_issues(foundation_issue_number) if not i.open])

    def create_foundation_issue(self, title: str, body: str) -> int:
        self._next += 1
        self.issues[self._next] = FoundationIssue(
            number=self._next,
            title=title,
            body=body,
            labels={"foundation:needed"},
        )
        return self._next
