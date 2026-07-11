from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set


@dataclass
class PMIssue:
    number: int
    title: str
    body: str
    labels: Set[str] = field(default_factory=set)
    open: bool = True
    comments: List[str] = field(default_factory=list)
    linked_research_issue_numbers: List[int] = field(default_factory=list)


class PMGitHubGateway:
    """Deterministic PM issue operations used by orchestrator nodes."""

    def __init__(self, issues: Optional[Dict[int, PMIssue]] = None):
        self.issues: Dict[int, PMIssue] = issues or {}
        self.published_artifacts: Dict[int, Dict[str, object]] = {}

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
        self.post_comment(issue_number, f"Strategic Opportunity Artifact Published: {artifact.get('artifact_id', 'unknown')}")
