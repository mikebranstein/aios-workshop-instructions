import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Sequence


class GitHubWikiManager:
    def __init__(self, repo: str, temp_prefix: str = "aios-wiki-") -> None:
        self.repo = repo
        self.temp_prefix = temp_prefix

    def _run_git(self, cwd: Path, args: List[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
            cwd=str(cwd),
        )

    def _wiki_workspace(self) -> tuple[Path, Path]:
        workspace = Path(tempfile.mkdtemp(prefix=self.temp_prefix, dir=tempfile.gettempdir()))
        wiki_dir = workspace / "wiki"
        self._run_git(workspace, ["clone", f"https://github.com/{self.repo}.wiki.git", str(wiki_dir)])
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

    def list_pages(self) -> List[str]:
        workspace, wiki_dir = self._wiki_workspace()
        try:
            pages = []
            for path in wiki_dir.rglob("*.md"):
                pages.append(path.relative_to(wiki_dir).as_posix())
            return sorted(pages)
        finally:
            self._cleanup_workspace(workspace)

    def get_snapshot(self, limit: int = 50, excerpt_chars: int = 1200) -> List[dict]:
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

    def read_page(self, page_path: str) -> str:
        workspace, wiki_dir = self._wiki_workspace()
        try:
            target = wiki_dir / Path(page_path)
            if not target.exists():
                return ""
            return target.read_text(encoding="utf-8")
        finally:
            self._cleanup_workspace(workspace)

    def write_page(self, page_path: str, content: str, commit_message: str) -> bool:
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

    def move_page(self, from_path: str, to_path: str, commit_message: str) -> bool:
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

    def apply_changes(
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

