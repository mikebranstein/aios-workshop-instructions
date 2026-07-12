from typing import Any, List, Protocol, Sequence, runtime_checkable


@runtime_checkable
class BaseGateway(Protocol):
    """Minimal issue-operation interface shared by all loop gateways.

    Every loop gateway (PM, PO, Dev, Foundation, …) satisfies this
    protocol.  Loop-specific operations are declared in loop-scoped
    sub-protocols that extend this base.
    """

    def get_issue(self, issue_number: int) -> Any:
        ...

    def list_open_issues_with_any_label(self, labels: Sequence[str]) -> List[Any]:
        ...

    def add_labels(self, issue_number: int, labels: Sequence[str]) -> None:
        ...

    def remove_labels(self, issue_number: int, labels: Sequence[str]) -> None:
        ...

    def set_state_labels(
        self,
        issue_number: int,
        labels_to_remove: Sequence[str],
        labels_to_add: Sequence[str],
    ) -> None:
        ...

    def post_comment(self, issue_number: int, body: str) -> None:
        ...

    def close_issue(self, issue_number: int, reason: str) -> None:
        ...
