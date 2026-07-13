"""Tests for wiki initialization verification in Foundation Gateway."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from aios_orchestration_core.github.foundation_gateway_api import GitHubApiFoundationGateway
from aios_orchestration_core.github.pm_gateway_api import GitHubApiConfig
from aios_orchestration_core.wiki.github_wiki_manager import GitHubWikiManager


class _LocalWikiManager(GitHubWikiManager):
    """Wiki manager whose remote is a local bare repo, so tests need no network."""

    def __init__(self, remote_url: str) -> None:
        super().__init__("owner/repo")
        self._local_remote = remote_url

    @property
    def _remote_url(self) -> str:
        return self._local_remote


class WikiInitializationVerificationTests(unittest.TestCase):
    """Test that wiki initialization actually verifies the wiki was created."""

    def setUp(self) -> None:
        self._root = Path(tempfile.mkdtemp(prefix="wiki-init-test-"))
        self._bare = self._root / "remote.wiki.git"
        subprocess.run(["git", "init", "--bare", "-q", str(self._bare)], check=True)

    def test_ensure_wiki_exists_raises_when_not_initialized(self) -> None:
        """Test that _ensure_wiki_exists raises with clear instructions if wiki not initialized."""
        # Create a gateway with a local wiki manager
        config = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiFoundationGateway(config)
        
        # Replace the wiki manager with one that uses our local remote
        gateway._wiki = _LocalWikiManager(str(self._bare))
        gateway._wiki_initialized = False
        
        # Verify the wiki doesn't exist yet
        pages_before = gateway._wiki.list_pages()
        self.assertEqual(pages_before, [])
        
        # Call _ensure_wiki_exists with a mocked _gh_api that succeeds
        with patch.object(gateway, '_gh_api') as mock_gh_api:
            mock_result = MagicMock()
            mock_result.returncode = 0  # Repo lookup succeeds
            mock_gh_api.return_value = mock_result
            
            # Should raise RuntimeError with instructions
            with self.assertRaises(RuntimeError) as ctx:
                gateway._ensure_wiki_exists()
            
            error_msg = str(ctx.exception)
            self.assertIn("not initialized", error_msg)
            self.assertIn("create the first wiki page manually", error_msg)
            self.assertIn("https://github.com/owner/repo/wiki", error_msg)
            self.assertIn("Click 'New Page'", error_msg)

    def test_ensure_wiki_exists_with_existing_home_page(self) -> None:
        """Test that _ensure_wiki_exists skips bootstrap if wiki already has pages."""
        config = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiFoundationGateway(config)
        gateway._wiki = _LocalWikiManager(str(self._bare))
        gateway._wiki_initialized = False
        
        # Create a page first to simulate an existing wiki
        gateway._wiki.write_page(
            "existing-page.md",
            "# Existing Page\n\nThis page was already here.\n",
            "initial page"
        )
        
        # Verify pages exist
        pages_before = gateway._wiki.list_pages()
        self.assertIn("existing-page.md", pages_before)
        
        # Call _ensure_wiki_exists - it should detect the wiki exists and not try to bootstrap
        with patch.object(gateway, '_gh_api') as mock_gh_api:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_gh_api.return_value = mock_result
            
            # This should not raise - wiki already exists
            gateway._ensure_wiki_exists()
        
        # Verify the wiki is marked as initialized
        self.assertTrue(gateway._wiki_initialized)
        
        # Verify the original page still exists
        pages_after = gateway._wiki.list_pages()
        self.assertIn("existing-page.md", pages_after)

    def test_ensure_wiki_exists_raises_on_bootstrap_failure(self) -> None:
        """Test that _ensure_wiki_exists raises with clear message if wiki doesn't exist."""
        config = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiFoundationGateway(config)
        
        # Use a wiki manager with a non-existent remote (simulates uninitialized wiki)
        gateway._wiki = _LocalWikiManager("/nonexistent/remote.git")
        gateway._wiki_initialized = False
        
        with patch.object(gateway, '_gh_api') as mock_gh_api:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_gh_api.return_value = mock_result
            
            # Should raise with instructions for manual wiki creation
            with self.assertRaises(RuntimeError) as ctx:
                gateway._ensure_wiki_exists()
            
            error_msg = str(ctx.exception)
            self.assertIn("not initialized", error_msg)
            self.assertIn("create the first wiki page manually", error_msg)

    def test_ensure_wiki_exists_idempotent(self) -> None:
        """Test that calling _ensure_wiki_exists multiple times is safe."""
        config = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiFoundationGateway(config)
        gateway._wiki = _LocalWikiManager(str(self._bare))
        gateway._wiki_initialized = False
        
        # Create a page so wiki appears initialized
        gateway._wiki.write_page(
            "Test.md",
            "# Test Page\n\nFor testing.",
            "test page"
        )
        
        with patch.object(gateway, '_gh_api') as mock_gh_api:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_gh_api.return_value = mock_result
            
            # First call should recognize wiki exists
            gateway._ensure_wiki_exists()
            self.assertTrue(gateway._wiki_initialized)
            
            # Second call returns early without doing anything
            gateway._ensure_wiki_exists()
            self.assertTrue(gateway._wiki_initialized)
            
            # Pages should still exist
            pages = gateway._wiki.list_pages()
            self.assertIn("Test.md", pages)


if __name__ == "__main__":
    unittest.main()
