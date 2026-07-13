import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Sequence


class GitHubWikiManager:
    # Wiki pages that are generated/meta and must not appear as entries in the
    # auto-generated Home index.
    HOME_INDEX_FILE = "Home.md"
    EXCLUDED_INDEX_PAGES = {"Home.md", "_Sidebar.md", "_Footer.md", "Content-Index.md"}

    def __init__(self, repo: str, temp_prefix: str = "aios-wiki-") -> None:
        self.repo = repo
        self.temp_prefix = temp_prefix

    @property
    def _remote_url(self) -> str:
        return f"https://github.com/{self.repo}.wiki.git"

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
        clone = subprocess.run(
            ["git", "clone", self._remote_url, str(wiki_dir)],
            capture_output=True,
            text=True,
            cwd=str(workspace),
        )
        if clone.returncode != 0:
            # A GitHub wiki has no backing .wiki.git repository until it is
            # initialized with a first page, so cloning an empty/uninitialized
            # wiki fails with exit 128. Bootstrap a local repo instead: reads
            # return empty, and the first push creates the wiki remotely.
            wiki_dir.mkdir(parents=True, exist_ok=True)
            self._run_git(wiki_dir, ["init", "-q", "-b", "master"])
            self._run_git(wiki_dir, ["remote", "add", "origin", self._remote_url])
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

    @staticmethod
    def _humanize_stem(stem: str) -> str:
        text = re.sub(r"[-_]+", " ", stem).strip()
        return text or stem

    @classmethod
    def _derive_title(cls, content: str, page_path: str) -> str:
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
        return cls._humanize_stem(Path(page_path).stem)

    @staticmethod
    def _derive_description(content: str, max_len: int = 200) -> str:
        lines = content.splitlines()

        # Prefer the page's "Summary" section when present.
        collected: List[str] = []
        in_summary = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                if in_summary:
                    break
                heading = stripped.lstrip("#").strip().lower()
                in_summary = heading == "summary"
                continue
            if in_summary and stripped:
                collected.append(stripped)

        # Otherwise fall back to the first meaningful paragraph.
        if not collected:
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith(("#", "|", "-", "*", ">")):
                    continue
                collected.append(stripped)
                break

        text = re.sub(r"\s+", " ", " ".join(collected)).strip()
        if len(text) > max_len:
            text = text[:max_len].rstrip() + "…"
        return text

    @classmethod
    def _render_home_index(cls, entries: List[dict]) -> str:
        lines = [
            "# Wiki Index",
            "",
            "_Auto-generated navigation index. It lists every page in this wiki and is "
            "updated automatically as pages are added, updated, or reorganized._",
            "",
        ]
        if not entries:
            lines.append("_No wiki pages yet._")
            return "\n".join(lines).strip() + "\n"

        groups: dict[str, List[dict]] = {}
        for entry in sorted(entries, key=lambda item: item["path"].lower()):
            parent = Path(entry["path"]).parent.as_posix()
            group = "Top level" if parent == "." else parent
            groups.setdefault(group, []).append(entry)

        for group in sorted(groups, key=lambda name: (name == "Top level", name.lower())):
            lines.append(f"## {group}")
            lines.append("")
            lines.append("| Page | Description |")
            lines.append("|---|---|")
            for entry in groups[group]:
                path = entry["path"]
                link = path[:-3] if path.endswith(".md") else path
                title = entry["title"].replace("|", "\\|")
                description = entry["description"].replace("|", "\\|")
                lines.append(f"| [{title}]({link}) | {description} |")
            lines.append("")

        return "\n".join(lines).strip() + "\n"

    def _rebuild_home_index(self, wiki_dir: Path) -> bool:
        entries: List[dict] = []
        for path in wiki_dir.rglob("*.md"):
            rel = path.relative_to(wiki_dir).as_posix()
            if rel in self.EXCLUDED_INDEX_PAGES or path.name in self.EXCLUDED_INDEX_PAGES:
                continue
            content = path.read_text(encoding="utf-8")
            entries.append(
                {
                    "path": rel,
                    "title": self._derive_title(content, rel),
                    "description": self._derive_description(content),
                }
            )

        rendered = self._render_home_index(entries)
        home_path = wiki_dir / self.HOME_INDEX_FILE
        existing = home_path.read_text(encoding="utf-8") if home_path.exists() else ""
        if existing == rendered:
            return False
        home_path.write_text(rendered, encoding="utf-8")
        return True

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
            self._rebuild_home_index(wiki_dir)
            self._run_git(wiki_dir, ["add", "-A"])
            self._run_git(wiki_dir, ["commit", "-m", commit_message])
            self._run_git(wiki_dir, ["push", "-u", "origin", "HEAD"])
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
            self._rebuild_home_index(wiki_dir)
            self._run_git(wiki_dir, ["add", "-A"])
            self._run_git(wiki_dir, ["commit", "-m", commit_message])
            self._run_git(wiki_dir, ["push", "-u", "origin", "HEAD"])
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

            if self._rebuild_home_index(wiki_dir):
                changed = True

            if not changed:
                return False

            self._run_git(wiki_dir, ["add", "-A"])
            self._run_git(wiki_dir, ["commit", "-m", commit_message])
            self._run_git(wiki_dir, ["push", "-u", "origin", "HEAD"])
            return True
        finally:
            self._cleanup_workspace(workspace)

    def rebuild_index(self, commit_message: str = "wiki: rebuild Home index") -> bool:
        """Regenerate the Home index from the current wiki pages and push it.

        Useful for repairing an existing wiki whose Home index is missing or
        stale. Returns True if the index changed and was pushed.
        """
        workspace, wiki_dir = self._wiki_workspace()
        try:
            if not self._rebuild_home_index(wiki_dir):
                return False
            self._run_git(wiki_dir, ["add", "-A"])
            self._run_git(wiki_dir, ["commit", "-m", commit_message])
            self._run_git(wiki_dir, ["push", "-u", "origin", "HEAD"])
            return True
        finally:
            self._cleanup_workspace(workspace)

