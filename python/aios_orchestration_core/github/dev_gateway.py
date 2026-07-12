from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Sequence, Set

from aios_orchestration_core.core.gateway import BaseGateway


@dataclass
class DevIssue:
    number: int
    title: str
    body: str
    labels: Set[str] = field(default_factory=set)
    open: bool = True
    comments: List[str] = field(default_factory=list)


class DevGateway(BaseGateway, Protocol):
    """Dev-loop gateway: extends BaseGateway for feature-request issues."""

    def get_issue(self, issue_number: int) -> DevIssue:
        ...

    def list_open_issues_with_any_label(self, labels: Sequence[str]) -> List[DevIssue]:
        ...


class DevGitHubGateway:
    """In-memory deterministic Dev gateway used by orchestrator nodes and tests."""

    def __init__(self, issues: Optional[Dict[int, DevIssue]] = None) -> None:
        self.issues: Dict[int, DevIssue] = issues or {}

    def get_issue(self, issue_number: int) -> DevIssue:
        return self.issues[issue_number]

    def list_open_issues_with_any_label(self, labels: Sequence[str]) -> List[DevIssue]:
        label_set = set(labels)
        return [i for i in self.issues.values() if i.open and i.labels.intersection(label_set)]

    def add_labels(self, issue_number: int, labels: Sequence[str]) -> None:
        self.issues[issue_number].labels.update(labels)

    def remove_labels(self, issue_number: int, labels: Sequence[str]) -> None:
        for label in labels:
            self.issues[issue_number].labels.discard(label)

    def set_state_labels(
        self,
        issue_number: int,
        labels_to_remove: Sequence[str],
        labels_to_add: Sequence[str],
    ) -> None:
        self.remove_labels(issue_number, labels_to_remove)
        self.add_labels(issue_number, labels_to_add)

    def post_comment(self, issue_number: int, body: str) -> None:
        self.issues[issue_number].comments.append(body)

    def close_issue(self, issue_number: int, reason: str) -> None:
        issue = self.issues[issue_number]
        issue.open = False
        issue.comments.append(f"Closed: {reason}")
