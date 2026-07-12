from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Sequence, Set

from aios_orchestration_core.core.gateway import BaseGateway


@dataclass
class ArchReviewIssue:
    number: int
    title: str
    body: str
    labels: Set[str] = field(default_factory=set)
    open: bool = True
    comments: List[str] = field(default_factory=list)


class ArchReviewGateway(BaseGateway, Protocol):
    def get_issue(self, issue_number: int) -> ArchReviewIssue: ...
    def list_open_issues_with_any_label(self, labels: Sequence[str]) -> List[ArchReviewIssue]: ...
    def create_refactor_request(self, title: str, body: str, source_review_number: int) -> int: ...
    def upsert_debt_issue(self, title: str, body: str) -> int: ...


class ArchReviewGitHubGateway:
    def __init__(self, issues: Optional[Dict[int, ArchReviewIssue]] = None) -> None:
        self.issues: Dict[int, ArchReviewIssue] = issues or {}
        self._next = max(self.issues.keys(), default=0) + 100

    def get_issue(self, issue_number: int) -> ArchReviewIssue:
        return self.issues[issue_number]

    def list_open_issues_with_any_label(self, labels: Sequence[str]) -> List[ArchReviewIssue]:
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
        self.issues[issue_number].open = False
        self.issues[issue_number].comments.append(f"Closed: {reason}")

    def create_refactor_request(self, title: str, body: str, source_review_number: int) -> int:
        self._next += 1
        self.issues[self._next] = ArchReviewIssue(self._next, title, body, labels={"feature-request", "refactor-request"})
        return self._next

    def upsert_debt_issue(self, title: str, body: str) -> int:
        # Check for existing open debt issue with same title; upsert if found.
        for issue in self.issues.values():
            if issue.open and "architecture-debt" in issue.labels and issue.title == title:
                issue.body = body
                return issue.number
        self._next += 1
        self.issues[self._next] = ArchReviewIssue(self._next, title, body, labels={"architecture-debt", "debt:new"})
        return self._next
