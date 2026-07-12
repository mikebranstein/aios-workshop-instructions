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
class FoundationArtifactState:
    """Injectable artifact-existence state used by the orchestrator pre-check."""
    decision_pack_exists: bool = False
    adr_template_exists: bool = False
    discovery_focus_exists: bool = False
    discovery_focus_populated: bool = False


class FoundationGateway(BaseGateway, Protocol):
    def get_issue(self, issue_number: int) -> FoundationIssue: ...
    def list_open_issues_with_any_label(self, labels: Sequence[str]) -> List[FoundationIssue]: ...
    def get_artifact_state(self) -> FoundationArtifactState: ...
    def create_foundation_issue(self, title: str, body: str) -> int: ...


class FoundationGitHubGateway:
    def __init__(
        self,
        issues: Optional[Dict[int, FoundationIssue]] = None,
        artifact_state: Optional[FoundationArtifactState] = None,
    ) -> None:
        self.issues: Dict[int, FoundationIssue] = issues or {}
        self._next = max(self.issues.keys(), default=0) + 100
        self._artifact_state = artifact_state or FoundationArtifactState()

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

    def get_artifact_state(self) -> FoundationArtifactState:
        return self._artifact_state

    def create_foundation_issue(self, title: str, body: str) -> int:
        self._next += 1
        self.issues[self._next] = FoundationIssue(
            number=self._next,
            title=title,
            body=body,
            labels={"foundation:needed"},
        )
        return self._next
