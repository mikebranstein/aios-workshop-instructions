from dataclasses import dataclass, field
from pathlib import Path
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
    def get_wiki_snapshot(self, limit: int = 50, excerpt_chars: int = 1200) -> List[dict]: ...
    def list_wiki_pages(self) -> List[str]: ...
    def read_wiki_page(self, page_path: str) -> str: ...
    def write_wiki_page(self, page_path: str, content: str, commit_message: str) -> bool: ...
    def move_wiki_page(self, from_path: str, to_path: str, commit_message: str) -> bool: ...
    def apply_wiki_manager_changes(
        self,
        *,
        page_path: str,
        page_content: str,
        page_moves: Sequence[dict],
        index_issue_number: int,
        index_summary: str,
        commit_message: str,
    ) -> bool: ...
    def list_adr_files(self) -> List[str]: ...
    def write_repo_file(self, path: str, content: str, commit_message: str) -> bool: ...
    def create_foundation_issue(self, title: str, body: str) -> int: ...
    def has_approved_foundation_issue(self) -> bool: ...


class FoundationGitHubGateway:
    def __init__(
        self,
        issues: Optional[Dict[int, FoundationIssue]] = None,
        wiki_pages: Optional[Dict[str, str]] = None,
        sub_issues: Optional[Dict[int, List[int]]] = None,
        repo_files: Optional[Dict[str, str]] = None,
    ) -> None:
        self.issues: Dict[int, FoundationIssue] = issues or {}
        self.wiki_pages: Dict[str, str] = dict(wiki_pages or {})
        self._repo_files: Dict[str, str] = dict(repo_files or {})
        self._next = max(self.issues.keys(), default=0) + 100
        self._research_issue_cache: Dict[int, int] = {}
        self._sub_issues: Dict[int, List[int]] = {
            parent: list(children) for parent, children in (sub_issues or {}).items()
        }

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
            labels=set(labels) | {"foundation:research"},
        )
        self.issues[self._next] = issue
        self._sub_issues.setdefault(foundation_issue_number, []).append(self._next)
        self._research_issue_cache[foundation_issue_number] = self._next
        return self._next

    def list_linked_research_issues(self, foundation_issue_number: int) -> List[LinkedFoundationIssue]:
        result: List[LinkedFoundationIssue] = []
        for child_number in self._sub_issues.get(foundation_issue_number, []):
            issue = self.issues.get(child_number)
            if issue is None or "foundation:research" not in issue.labels:
                continue
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

    def list_wiki_pages(self) -> List[str]:
        return sorted(self.wiki_pages.keys())

    def get_wiki_snapshot(self, limit: int = 50, excerpt_chars: int = 1200) -> List[dict]:
        pages = self.list_wiki_pages()[:limit]
        return [
            {"path": page, "content_excerpt": self.read_wiki_page(page)[:excerpt_chars]}
            for page in pages
        ]

    def read_wiki_page(self, page_path: str) -> str:
        return self.wiki_pages.get(page_path, "")

    def write_wiki_page(self, page_path: str, content: str, commit_message: str) -> bool:
        current = self.wiki_pages.get(page_path)
        if current == content:
            return False
        self.wiki_pages[page_path] = content
        return True

    def move_wiki_page(self, from_path: str, to_path: str, commit_message: str) -> bool:
        if from_path == to_path:
            return False
        if from_path not in self.wiki_pages:
            return False
        self.wiki_pages[to_path] = self.wiki_pages.pop(from_path)
        return True

    def apply_wiki_manager_changes(
        self,
        *,
        page_path: str,
        page_content: str,
        page_moves: Sequence[dict],
        index_issue_number: int,
        index_summary: str,
        commit_message: str,
    ) -> bool:
        changed = False
        for move in page_moves:
            from_path = str(move.get("from_path", ""))
            to_path = str(move.get("to_path", ""))
            if from_path and to_path:
                changed = self.move_wiki_page(from_path, to_path, commit_message) or changed

        changed = self.write_wiki_page(page_path, page_content, commit_message) or changed

        marker = f"| `{page_path}` | #{index_issue_number} |"
        existing = self.read_wiki_page("Content-Index.md").strip()
        header = (
            "# Content-Index\n\n"
            "| Wiki Page | Source Issue | Summary |\n"
            "|---|---|---|"
        )
        lines = existing.splitlines() if existing else header.splitlines()
        if marker in "\n".join(lines):
            updated = []
            for line in lines:
                if line.startswith(marker):
                    updated.append(f"{marker} {index_summary} |")
                else:
                    updated.append(line)
            content = "\n".join(updated).strip() + "\n"
        else:
            content = ("\n".join(lines).strip() + f"\n{marker} {index_summary} |\n")
        changed = self.write_wiki_page("Content-Index.md", content, commit_message) or changed
        return changed

    def list_adr_files(self) -> List[str]:
        return sorted(k for k in self._repo_files if k.startswith("docs/adr/") and k.endswith(".md"))

    def write_repo_file(self, path: str, content: str, commit_message: str) -> bool:
        current = self._repo_files.get(path)
        if current == content:
            return False
        self._repo_files[path] = content
        return True

    def create_foundation_issue(self, title: str, body: str) -> int:
        self._next += 1
        self.issues[self._next] = FoundationIssue(
            number=self._next,
            title=title,
            body=body,
            labels={"foundation:needed"},
        )
        return self._next

    def has_approved_foundation_issue(self) -> bool:
        return any(
            "foundation:approved" in i.labels
            for i in self.issues.values()
        )
