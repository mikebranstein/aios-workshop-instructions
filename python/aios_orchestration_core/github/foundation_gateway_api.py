import json
import re
import subprocess
import base64
import shutil
import tempfile
from typing import List, Sequence
from pathlib import Path

from aios_orchestration_core.github.foundation_gateway import (
    FoundationIssue,
    LinkedFoundationIssue,
)
from aios_orchestration_core.github.pm_gateway_api import GitHubApiConfig


class GitHubApiFoundationGateway:
    """GitHub CLI-backed Foundation gateway."""

    def __init__(self, config: GitHubApiConfig):
        self.config = config

    def _gh(self, args: List[str]) -> str:
        cmd = ["gh", "-R", self.config.repo] + args
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return completed.stdout.strip()

    def _gh_api(self, path: str, jq: str | None = None) -> subprocess.CompletedProcess:
        cmd = ["gh", "api", path]
        if jq is not None:
            cmd += ["--jq", jq]
        return subprocess.run(cmd, check=False, capture_output=True, text=True)

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

    def _run_git(self, cwd: Path, args: List[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
            cwd=str(cwd),
        )

    def _wiki_workspace(self) -> tuple[Path, Path]:
        workspace = Path(tempfile.mkdtemp(prefix="aios-foundation-wiki-", dir=tempfile.gettempdir()))
        wiki_dir = workspace / "wiki"
        self._run_git(workspace, ["clone", f"https://github.com/{self.config.repo}.wiki.git", str(wiki_dir)])
        return workspace, wiki_dir

    def _cleanup_workspace(self, workspace: Path) -> None:
        shutil.rmtree(workspace, ignore_errors=True)

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
        self._gh(["issue", "comment", str(issue_number), "--body", body])

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
        trace_label = f"foundation-source-{foundation_issue_number}"
        raw = self._gh(
            [
                "issue",
                "list",
                "--state",
                "open",
                "--label",
                "foundation:research",
                "--label",
                trace_label,
                "--limit",
                "200",
                "--json",
                "number,title",
            ]
        )
        for item in json.loads(raw):
            if item.get("title") == title:
                return int(item["number"])

        create_labels = list(labels) + ["foundation:research", trace_label]
        self._ensure_labels(create_labels)
        create_cmd = ["issue", "create", "--title", title, "--body", body]
        for label in create_labels:
            create_cmd += ["--label", label]
        output = self._gh(create_cmd)
        match = re.search(r"/issues/(\d+)", output)
        if not match:
            raise RuntimeError(f"Unable to parse issue number from gh output: {output}")
        return int(match.group(1))

    def list_linked_research_issues(self, foundation_issue_number: int) -> List[LinkedFoundationIssue]:
        trace_label = f"foundation-source-{foundation_issue_number}"
        raw = self._gh(
            [
                "issue",
                "list",
                "--state",
                "all",
                "--label",
                "foundation:research",
                "--label",
                trace_label,
                "--limit",
                "200",
                "--json",
                "number,title,body,state",
            ]
        )
        result: List[LinkedFoundationIssue] = []
        for item in json.loads(raw):
            result.append(
                LinkedFoundationIssue(
                    number=int(item["number"]),
                    title=item.get("title", ""),
                    body=item.get("body", ""),
                    open=item.get("state", "OPEN").upper() == "OPEN",
                )
            )
        return result

    def count_open_linked_research_issues(self, foundation_issue_number: int) -> int:
        return len([i for i in self.list_linked_research_issues(foundation_issue_number) if i.open])

    def count_closed_linked_research_issues(self, foundation_issue_number: int) -> int:
        return len([i for i in self.list_linked_research_issues(foundation_issue_number) if not i.open])

    def list_wiki_pages(self) -> List[str]:
        workspace, wiki_dir = self._wiki_workspace()
        try:
            pages = []
            for path in wiki_dir.rglob("*.md"):
                pages.append(path.relative_to(wiki_dir).as_posix())
            return sorted(pages)
        finally:
            self._cleanup_workspace(workspace)

    def get_wiki_snapshot(self, limit: int = 50, excerpt_chars: int = 1200) -> List[dict]:
        workspace, wiki_dir = self._wiki_workspace()
        try:
            pages = sorted(path.relative_to(wiki_dir).as_posix() for path in wiki_dir.rglob("*.md"))
            out = []
            for page in pages[:limit]:
                content = (wiki_dir / Path(page)).read_text(encoding="utf-8")
                out.append({"path": page, "content_excerpt": content[:excerpt_chars]})
            return out
        finally:
            self._cleanup_workspace(workspace)

    def read_wiki_page(self, page_path: str) -> str:
        workspace, wiki_dir = self._wiki_workspace()
        try:
            target = wiki_dir / Path(page_path)
            if not target.exists():
                return ""
            return target.read_text(encoding="utf-8")
        finally:
            self._cleanup_workspace(workspace)

    def write_wiki_page(self, page_path: str, content: str, commit_message: str) -> bool:
        workspace, wiki_dir = self._wiki_workspace()
        try:
            target = wiki_dir / Path(page_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            original = target.read_text(encoding="utf-8") if target.exists() else None
            if original == content:
                return False
            target.write_text(content, encoding="utf-8")
            self._run_git(wiki_dir, ["add", page_path])
            self._run_git(wiki_dir, ["commit", "-m", commit_message])
            self._run_git(wiki_dir, ["push"])
            return True
        finally:
            self._cleanup_workspace(workspace)

    def move_wiki_page(self, from_path: str, to_path: str, commit_message: str) -> bool:
        workspace, wiki_dir = self._wiki_workspace()
        try:
            source = wiki_dir / Path(from_path)
            target = wiki_dir / Path(to_path)
            if not source.exists():
                return False
            target.parent.mkdir(parents=True, exist_ok=True)
            source.replace(target)
            self._run_git(wiki_dir, ["add", from_path, to_path])
            self._run_git(wiki_dir, ["commit", "-m", commit_message])
            self._run_git(wiki_dir, ["push"])
            return True
        finally:
            self._cleanup_workspace(workspace)

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
        workspace, wiki_dir = self._wiki_workspace()
        try:
            changed = False
            for move in page_moves:
                from_path = str(move.get("from_path", ""))
                to_path = str(move.get("to_path", ""))
                if not from_path or not to_path or from_path == to_path:
                    continue
                source = wiki_dir / Path(from_path)
                target = wiki_dir / Path(to_path)
                if not source.exists():
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                source.replace(target)
                changed = True

            target = wiki_dir / Path(page_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            original = target.read_text(encoding="utf-8") if target.exists() else None
            if original != page_content:
                target.write_text(page_content, encoding="utf-8")
                changed = True

            index_path = wiki_dir / "Content-Index.md"
            existing_index = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
            rendered_index = self._render_content_index(existing_index, page_path, index_issue_number, index_summary)
            if existing_index != rendered_index:
                index_path.write_text(rendered_index, encoding="utf-8")
                changed = True

            if not changed:
                return False

            self._run_git(wiki_dir, ["add", "-A"])
            self._run_git(wiki_dir, ["commit", "-m", commit_message])
            self._run_git(wiki_dir, ["push"])
            return True
        finally:
            self._cleanup_workspace(workspace)

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
