from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Sequence, Set

from aios_orchestration_core.core.gateway import BaseGateway


@dataclass
class POIssue:
    number: int
    title: str
    body: str
    labels: Set[str] = field(default_factory=set)
    open: bool = True
    comments: List[str] = field(default_factory=list)
    created_feature_request_numbers: List[int] = field(default_factory=list)


class POGateway(BaseGateway, Protocol):
    """PO-loop gateway: extends BaseGateway with PO-specific operations."""

    def get_issue(self, issue_number: int) -> POIssue:
        ...

    def list_open_issues_with_any_label(self, labels: Sequence[str]) -> List[POIssue]:
        ...

    def create_feature_request(
        self,
        source_opportunity_number: int,
        title: str,
        body: str,
        priority_score: int,
    ) -> int:
        ...

    def list_created_feature_request_numbers(self, opportunity_number: int) -> List[int]:
        ...


class POGitHubGateway:
    """In-memory deterministic PO gateway used by orchestrator nodes and tests."""

    def __init__(self, issues: Optional[Dict[int, POIssue]] = None) -> None:
        self.issues: Dict[int, POIssue] = issues or {}
        self._next_number: int = max(self.issues.keys(), default=0) + 100

    # ------------------------------------------------------------------
    # BaseGateway operations
    # ------------------------------------------------------------------

    def get_issue(self, issue_number: int) -> POIssue:
        return self.issues[issue_number]

    def list_open_issues_with_any_label(self, labels: Sequence[str]) -> List[POIssue]:
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

    # ------------------------------------------------------------------
    # PO-specific operations
    # ------------------------------------------------------------------

    def create_feature_request(
        self,
        source_opportunity_number: int,
        title: str,
        body: str,
        priority_score: int,
    ) -> int:
        self._next_number += 1
        number = self._next_number
        self.issues[number] = POIssue(
            number=number,
            title=title,
            body=body,
            labels={"feature-request"},
        )
        self.issues[source_opportunity_number].created_feature_request_numbers.append(number)
        return number

    def list_created_feature_request_numbers(self, opportunity_number: int) -> List[int]:
        return list(self.issues[opportunity_number].created_feature_request_numbers)
