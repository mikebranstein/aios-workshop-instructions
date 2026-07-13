import subprocess
import tempfile
import unittest
from pathlib import Path

from aios_orchestration_core.wiki.github_wiki_manager import GitHubWikiManager


class _LocalWikiManager(GitHubWikiManager):
    """Wiki manager whose remote is a local bare repo, so tests need no network."""

    def __init__(self, remote_url: str) -> None:
        super().__init__("owner/repo")
        self._local_remote = remote_url

    @property
    def _remote_url(self) -> str:
        return self._local_remote


class GitHubWikiManagerHomeIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self._root = Path(tempfile.mkdtemp(prefix="wiki-test-"))
        self._bare = self._root / "remote.wiki.git"
        subprocess.run(["git", "init", "--bare", "-q", str(self._bare)], check=True)
        self.manager = _LocalWikiManager(str(self._bare))

    def test_bootstraps_empty_wiki_without_error(self) -> None:
        # An uninitialized wiki has no backing repo; reads must not raise.
        self.assertEqual(self.manager.get_snapshot(), [])
        self.assertEqual(self.manager.list_pages(), [])
        self.assertEqual(self.manager.read_page("Home.md"), "")

    def test_home_index_lists_pages_with_titles_and_descriptions(self) -> None:
        self.manager.write_page(
            "foundation/Auth-Model.md",
            "# Authentication Model\n\n## Summary\nJWT-based auth for all services.\n",
            "add auth",
        )
        self.manager.write_page(
            "Glossary.md",
            "Terms and definitions used across the project.\n",
            "add glossary",
        )

        home = self.manager.read_page("Home.md")
        self.assertIn("# Wiki Index", home)
        self.assertIn("[Authentication Model](foundation/Auth-Model)", home)
        self.assertIn("JWT-based auth for all services.", home)
        # Falls back to filename-derived title and first paragraph.
        self.assertIn("[Glossary](Glossary)", home)
        self.assertIn("Terms and definitions used across the project.", home)

    def test_home_index_updates_on_restructure(self) -> None:
        self.manager.write_page(
            "foundation/Data-Store.md",
            "# Data Store\n\n## Summary\nPostgres chosen for persistence.\n",
            "add datastore",
        )
        self.manager.move_page(
            "foundation/Data-Store.md",
            "foundation/persistence/Data-Store.md",
            "reorg",
        )

        home = self.manager.read_page("Home.md")
        self.assertIn("[Data Store](foundation/persistence/Data-Store)", home)
        self.assertNotIn("(foundation/Data-Store)", home)

    def test_generated_pages_excluded_from_index(self) -> None:
        self.manager.write_page(
            "foundation/Auth-Model.md",
            "# Authentication Model\n\n## Summary\nJWT auth.\n",
            "add auth",
        )
        self.manager.write_page("_Sidebar.md", "navigation", "add sidebar")

        home = self.manager.read_page("Home.md")
        self.assertNotIn("_Sidebar", home)
        self.assertNotIn("Content-Index", home)
        self.assertNotIn("[Home]", home)

    def test_apply_changes_rebuilds_home_index(self) -> None:
        self.manager.apply_changes(
            page_path="foundation/Topic.md",
            page_content="# Topic\n\n## Summary\nAn important research topic.\n",
            page_moves=[],
            index_issue_number=42,
            index_summary="Research on the topic",
            commit_message="foundation: add topic",
        )

        home = self.manager.read_page("Home.md")
        self.assertIn("[Topic](foundation/Topic)", home)
        self.assertIn("An important research topic.", home)


if __name__ == "__main__":
    unittest.main()
