import subprocess
import tempfile
import unittest
from pathlib import Path

from aios_orchestration_core.wiki.github_wiki_manager import GitHubWikiManager
from aios_orchestration_core.wiki.llm_wiki_manager import slugify


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

    def test_apply_changes_raises_on_system_managed_page_path(self) -> None:
        for bad_path in ("Content-Index.md", "Home.md", "foundation/Content-Index.md"):
            with self.assertRaises(ValueError, msg=f"Should reject system path: {bad_path}"):
                self.manager.apply_changes(
                    page_path=bad_path,
                    page_content="# Oops\n\nThis must not overwrite a system file.\n",
                    page_moves=[],
                    index_issue_number=1,
                    index_summary="bad",
                    commit_message="should not reach git",
                )

    def test_apply_changes_silently_skips_move_to_system_managed_path(self) -> None:
        self.manager.apply_changes(
            page_path="foundation/Page.md",
            page_content="# Page\n\n## Summary\nOK page.\n",
            page_moves=[],
            index_issue_number=1,
            index_summary="ok",
            commit_message="add page",
        )
        # A move targeting a system file must be silently dropped.
        self.manager.apply_changes(
            page_path="foundation/Other.md",
            page_content="# Other\n\n## Summary\nAnother page.\n",
            page_moves=[{"from_path": "foundation/Page.md", "to_path": "Home.md"}],
            index_issue_number=2,
            index_summary="other",
            commit_message="bad move should be skipped",
        )
        # The original page must still exist (the move was silently dropped).
        self.assertIn("foundation/Page", self.manager.read_page("Home.md"))

    def test_get_snapshot_excludes_system_managed_pages(self) -> None:
        self.manager.apply_changes(
            page_path="foundation/Research.md",
            page_content="# Research\n\n## Summary\nFindings.\n",
            page_moves=[],
            index_issue_number=5,
            index_summary="Findings",
            commit_message="add research",
        )
        snapshot = self.manager.get_snapshot()
        paths = [entry["path"] for entry in snapshot]
        self.assertNotIn("Home.md", paths, "Home.md must not appear in snapshot")
        self.assertNotIn("Content-Index.md", paths, "Content-Index.md must not appear in snapshot")
        self.assertIn("foundation/Research.md", paths)


class SlugifyTests(unittest.TestCase):
    def test_basic_lowercasing_and_dash_replacement(self) -> None:
        self.assertEqual(slugify("Runtime and Language"), "runtime-and-language")

    def test_special_characters_removed(self) -> None:
        self.assertEqual(slugify("Choose: PostgreSQL (v14)!"), "choose-postgresql-v14")

    def test_leading_trailing_dashes_stripped(self) -> None:
        self.assertEqual(slugify("  --hello--  "), "hello")

    def test_fallback_used_for_empty_input(self) -> None:
        self.assertEqual(slugify("", fallback="fallback"), "fallback")
        self.assertEqual(slugify("   ", fallback="fb"), "fb")

    def test_max_len_truncates_at_word_boundary(self) -> None:
        long_title = "Architecture Style and Topology for the Shared Application Foundation"
        result = slugify(long_title, max_len=50)
        self.assertLessEqual(len(result), 50)
        self.assertFalse(result.endswith("-"), "slug must not end with a dash after truncation")

    def test_max_len_none_does_not_truncate(self) -> None:
        long_title = "A" * 100
        result = slugify(long_title, max_len=None)
        self.assertEqual(len(result), 100)

    def test_max_len_exact_fit_is_not_truncated(self) -> None:
        value = "a" * 50
        self.assertEqual(slugify(value, max_len=50), value)

    def test_max_len_applied_in_foundation_runner_slugify(self) -> None:
        """_slugify in foundation_runner caps at 50 chars."""
        import foundation_runner
        long_value = "Choose the right runtime and language stack for the entire project foundation"
        result = foundation_runner._slugify(long_value)
        self.assertLessEqual(len(result), 50)
        self.assertFalse(result.endswith("-"))


class WikiWriteLockTests(unittest.TestCase):
    """Tests that the module-level write lock serialises concurrent apply_changes calls."""

    def setUp(self) -> None:
        self._root = Path(tempfile.mkdtemp(prefix="wiki-lock-test-"))
        self._bare = self._root / "remote.wiki.git"
        subprocess.run(["git", "init", "--bare", "-q", str(self._bare)], check=True)

    def _manager(self) -> "_LocalWikiManager":
        return _LocalWikiManager(str(self._bare))

    def test_concurrent_writers_both_land_with_complete_home_index(self) -> None:
        """Two threads calling apply_changes at the same time must both succeed and
        the final Home index must list both pages."""
        import threading

        mgr = self._manager()
        errors: list = []

        def write_page(page_path: str, title: str, issue: int) -> None:
            try:
                mgr.apply_changes(
                    page_path=page_path,
                    page_content=f"# {title}\n\n## Summary\nContent for {title}.\n",
                    page_moves=[],
                    index_issue_number=issue,
                    index_summary=f"Summary of {title}",
                    commit_message=f"foundation: add {title}",
                )
            except Exception as exc:
                errors.append(exc)

        t1 = threading.Thread(target=write_page, args=("foundation/Page-A.md", "Page A", 1))
        t2 = threading.Thread(target=write_page, args=("foundation/Page-B.md", "Page B", 2))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(errors, [], f"Writer threads raised errors: {errors}")

        home = self._manager().read_page("Home.md")
        self.assertIn("[Page A](foundation/Page-A)", home, "Page A missing from index")
        self.assertIn("[Page B](foundation/Page-B)", home, "Page B missing from index")


class NormalizeWikiPagePathTests(unittest.TestCase):
    """Tests for normalize_wiki_page_path in llm_wiki_manager."""

    def setUp(self) -> None:
        from aios_orchestration_core.wiki.llm_wiki_manager import normalize_wiki_page_path
        self._normalize = normalize_wiki_page_path

    def test_adds_md_extension(self) -> None:
        self.assertEqual(self._normalize("foundation/auth", "fallback.md"), "foundation/auth.md")

    def test_preserves_existing_md_extension(self) -> None:
        self.assertEqual(self._normalize("foundation/auth.md", "fallback.md"), "foundation/auth.md")

    def test_normalizes_backslashes(self) -> None:
        self.assertEqual(self._normalize("foundation\\auth", "fallback.md"), "foundation/auth.md")

    def test_collapses_double_slashes(self) -> None:
        self.assertEqual(self._normalize("foundation//auth", "fallback.md"), "foundation/auth.md")

    def test_strips_leading_slash(self) -> None:
        self.assertEqual(self._normalize("/foundation/auth", "fallback.md"), "foundation/auth.md")

    def test_slugifies_filename_stem_spaces(self) -> None:
        result = self._normalize("foundation/Authentication Model", "fallback.md")
        self.assertNotIn(" ", result, "Spaces must be replaced in filename")
        self.assertIn("foundation/", result)
        self.assertTrue(result.endswith(".md"))

    def test_slugifies_filename_stem_special_chars(self) -> None:
        result = self._normalize("foundation/Auth: Model (v2)!", "fallback.md")
        self.assertNotIn(" ", result)
        self.assertNotIn(":", result)
        self.assertNotIn("(", result)

    def test_redirects_content_index_to_default(self) -> None:
        result = self._normalize("Content-Index.md", "foundation/fallback.md")
        self.assertNotEqual(result.lower(), "content-index.md")
        self.assertEqual(result, "foundation/fallback.md")

    def test_redirects_home_to_default(self) -> None:
        result = self._normalize("Home.md", "foundation/fallback.md")
        self.assertNotEqual(result.lower(), "home.md")
        self.assertEqual(result, "foundation/fallback.md")

    def test_redirects_nested_content_index_to_default(self) -> None:
        result = self._normalize("foundation/Content-Index.md", "foundation/fallback.md")
        self.assertNotIn("content-index", result.lower())

    def test_empty_value_uses_default(self) -> None:
        self.assertEqual(self._normalize("", "foundation/fallback.md"), "foundation/fallback.md")


if __name__ == "__main__":
    unittest.main()
