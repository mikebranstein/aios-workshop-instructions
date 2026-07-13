import json
import re
import subprocess
import base64
from typing import List, Optional, Sequence

from aios_orchestration_core.github.comment_formatter import (
    CommentFormatter,
    NullCommentFormatter,
)
from aios_orchestration_core.github.foundation_gateway import (
    FoundationIssue,
    LinkedFoundationIssue,
)
from aios_orchestration_core.github.pm_gateway_api import GitHubApiConfig
from aios_orchestration_core.wiki.github_wiki_manager import GitHubWikiManager


class GitHubApiFoundationGateway:
    """GitHub CLI-backed Foundation gateway."""

    def __init__(self, config: GitHubApiConfig, comment_formatter: Optional[CommentFormatter] = None):
        self.config = config
        self.comment_formatter: CommentFormatter = comment_formatter or NullCommentFormatter()
        self._wiki = GitHubWikiManager(repo=self.config.repo, temp_prefix="aios-foundation-wiki-")
        self._wiki_initialized = False

    def _gh(self, args: List[str]) -> str:
        cmd = ["gh", "-R", self.config.repo] + args
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return completed.stdout.strip()

    def _gh_api(self, path: str, jq: str | None = None) -> subprocess.CompletedProcess:
        cmd = ["gh", "api", path]
        if jq is not None:
            cmd += ["--jq", jq]
        return subprocess.run(cmd, check=False, capture_output=True, text=True)

    def _ensure_wiki_exists(self) -> None:
        """Ensure the wiki backing repo exists; bootstrap with a home page if needed.
        
        Raises:
            RuntimeError: If wiki initialization fails.
        """
        if self._wiki_initialized:
            return

        # Check if the wiki backing repo exists via gh api
        result = self._gh_api(f"repos/{self.config.repo}/contents", jq=".")
        if result.returncode != 0:
            # Repo lookup failed; can't proceed
            return

        # Try to check if the wiki backing repo has been initialized
        # by attempting a minimal operation. If the wiki has no pages, cloning fails
        # with exit 128. Bootstrap it with a Home page.
        try:
            pages = self._wiki.list_pages()
            # Wiki exists and has pages (or is empty but accessible)
            if pages and "Home.md" in pages:
                # Wiki is fully initialized
                self._wiki_initialized = True
                return
            # Wiki exists but needs Home page
            home_content = self._wiki.read_page("Home.md")
            if home_content:
                # Home page already exists
                self._wiki_initialized = True
                return
        except Exception as e:
            # Clone/access failed; wiki not yet initialized
            pass

        # Bootstrap wiki with a Home page if not already present
        try:
            success = self._wiki.write_page(
                "Home.md",
                "# Wiki\n\nInitialized by Foundation Orchestrator.\n",
                "wiki: bootstrap home page",
            )
            if not success:
                # write_page returned False (content already existed as-is)
                pass
        except Exception as e:
            raise RuntimeError(
                f"Failed to bootstrap wiki for {self.config.repo}: {e}"
            ) from e

        # Verify the Home page now exists
        try:
            home_content = self._wiki.read_page("Home.md")
            if not home_content:
                raise RuntimeError(
                    f"Wiki Home.md page not created or empty after bootstrap for {self.config.repo}"
                )
        except Exception as e:
            raise RuntimeError(
                f"Failed to verify wiki initialization for {self.config.repo}: {e}"
            ) from e

        self._wiki_initialized = True

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

    def _file_exists(self, path: str) -> bool:
        result = self._gh_api(f"repos/{self.config.repo}/contents/{path}", ".type")
        return result.returncode == 0

    def _read_repo_file(self, path: str) -> str:
        result = self._gh_api(f"repos/{self.config.repo}/contents/{path}")
        if result.returncode != 0:
            return ""
        payload = json.loads(result.stdout)
        encoded = (payload.get("content") or "").replace("\n", "")
        if not encoded:
            return ""
        return base64.b64decode(encoded).decode("utf-8", errors="replace")

    def get_issue(self, issue_number: int) -> FoundationIssue:
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
        return FoundationIssue(
            number=obj["number"],
            title=obj.get("title", ""),
            body=obj.get("body", ""),
            labels={l["name"] for l in obj.get("labels", [])},
            open=obj.get("state", "OPEN").upper() == "OPEN",
        )

    def list_open_issues_with_any_label(self, labels: Sequence[str]) -> List[FoundationIssue]:
        raw = self._gh(["issue", "list", "--state", "open", "--limit", "200", "--json", "number,title,body,state,labels"])
        all_issues = json.loads(raw)
        label_set = set(labels)
        result: List[FoundationIssue] = []
        for item in all_issues:
            issue_labels = {l["name"] for l in item.get("labels", [])}
            if issue_labels.intersection(label_set):
                result.append(
                    FoundationIssue(
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
        issue = self.get_issue(issue_number)
        removable = [label for label in labels if label in issue.labels]
        if not removable:
            return
        self._gh(["issue", "edit", str(issue_number), "--remove-label", ",".join(removable)])

    def set_state_labels(self, issue_number: int, labels_to_remove: Sequence[str], labels_to_add: Sequence[str]) -> None:
        # Add first, then remove old labels; this avoids no-state windows.
        self.add_labels(issue_number, labels_to_add)
        remove_after_add = [label for label in labels_to_remove if label not in set(labels_to_add)]
        self.remove_labels(issue_number, remove_after_add)

    def post_comment(self, issue_number: int, body: str) -> None:
        self._gh(["issue", "comment", str(issue_number), "--body", self.comment_formatter.format(body)])

    def close_issue(self, issue_number: int, reason: str) -> None:
        self._gh(["issue", "close", str(issue_number), "--reason", reason])

    def foundation_markdown_exists(self) -> bool:
        return self._file_exists("FOUNDATION.md")

    def read_foundation_markdown(self) -> str:
        return self._read_repo_file("FOUNDATION.md")

    def get_issue_comments(self, issue_number: int) -> List[str]:
        raw = self._gh(
            [
                "issue",
                "view",
                str(issue_number),
                "--json",
                "comments",
            ]
        )
        obj = json.loads(raw)
        return [comment.get("body", "") for comment in obj.get("comments", [])]

    def ensure_research_issue(
        self,
        foundation_issue_number: int,
        title: str,
        body: str,
        labels: Sequence[str],
    ) -> int:
        for child in self._list_sub_issues(foundation_issue_number):
            if child.get("title") == title and self._has_research_label(child):
                return int(child["number"])

        create_labels = list(labels) + ["foundation:research"]
        self._ensure_labels(create_labels)
        create_cmd = ["issue", "create", "--title", title, "--body", body]
        for label in create_labels:
            create_cmd += ["--label", label]
        output = self._gh(create_cmd)
        match = re.search(r"/issues/(\d+)", output)
        if not match:
            raise RuntimeError(f"Unable to parse issue number from gh output: {output}")
        child_number = int(match.group(1))
        self._link_sub_issue(foundation_issue_number, child_number)
        return child_number

    def list_linked_research_issues(self, foundation_issue_number: int) -> List[LinkedFoundationIssue]:
        result: List[LinkedFoundationIssue] = []
        for child in self._list_sub_issues(foundation_issue_number):
            if not self._has_research_label(child):
                continue
            result.append(
                LinkedFoundationIssue(
                    number=int(child["number"]),
                    title=child.get("title", ""),
                    body=child.get("body", "") or "",
                    open=str(child.get("state", "open")).lower() == "open",
                )
            )
        return result

    @staticmethod
    def _has_research_label(issue: dict) -> bool:
        for label in issue.get("labels", []) or []:
            name = label.get("name") if isinstance(label, dict) else label
            if name == "foundation:research":
                return True
        return False

    def _list_sub_issues(self, foundation_issue_number: int) -> List[dict]:
        result = self._gh_api(
            f"repos/{self.config.repo}/issues/{foundation_issue_number}/sub_issues"
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []
        return data if isinstance(data, list) else []

    def _issue_db_id(self, issue_number: int) -> int:
        result = self._gh_api(
            f"repos/{self.config.repo}/issues/{issue_number}", jq=".id"
        )
        if result.returncode != 0 or not result.stdout.strip():
            raise RuntimeError(
                f"Unable to resolve database id for issue #{issue_number}: {result.stderr.strip()}"
            )
        return int(result.stdout.strip())

    def _link_sub_issue(self, foundation_issue_number: int, child_issue_number: int) -> None:
        child_id = self._issue_db_id(child_issue_number)
        subprocess.run(
            [
                "gh",
                "api",
                "--method",
                "POST",
                f"repos/{self.config.repo}/issues/{foundation_issue_number}/sub_issues",
                "-F",
                f"sub_issue_id={child_id}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    def count_open_linked_research_issues(self, foundation_issue_number: int) -> int:
        return len([i for i in self.list_linked_research_issues(foundation_issue_number) if i.open])

    def count_closed_linked_research_issues(self, foundation_issue_number: int) -> int:
        return len([i for i in self.list_linked_research_issues(foundation_issue_number) if not i.open])

    def list_wiki_pages(self) -> List[str]:
        return self._wiki.list_pages()

    def get_wiki_snapshot(self, limit: int = 50, excerpt_chars: int = 1200) -> List[dict]:
        return self._wiki.get_snapshot(limit=limit, excerpt_chars=excerpt_chars)

    def read_wiki_page(self, page_path: str) -> str:
        return self._wiki.read_page(page_path)

    def write_wiki_page(self, page_path: str, content: str, commit_message: str) -> bool:
        return self._wiki.write_page(page_path, content, commit_message)

    def move_wiki_page(self, from_path: str, to_path: str, commit_message: str) -> bool:
        return self._wiki.move_page(from_path, to_path, commit_message)

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
        return self._wiki.apply_changes(
            page_path=page_path,
            page_content=page_content,
            page_moves=page_moves,
            index_issue_number=index_issue_number,
            index_summary=index_summary,
            commit_message=commit_message,
        )

    def create_foundation_issue(self, title: str, body: str) -> int:
        self._ensure_labels(["foundation:needed"])
        output = self._gh(
            [
                "issue",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--label",
                "foundation:needed",
            ]
        )
        match = re.search(r"/issues/(\d+)", output)
        if not match:
            raise RuntimeError(f"Unable to parse issue number from gh output: {output}")
        return int(match.group(1))
