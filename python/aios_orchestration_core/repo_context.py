"""Repository context detection and gateway factory.

Supports running orchestrators against:
- GitHub repos via GitHub CLI: "owner/repo"
- Locally cloned repos: "/path/to/repo" or "./relative/path"

Usage:
    context = RepoContext.from_string("owner/repo")
    gateway = context.create_pm_gateway()
    
    # Or from environment:
    context = RepoContext.from_env(default="owner/repo")
"""

import os
from dataclasses import dataclass
from typing import Optional

from aios_orchestration_core.github.dev_gateway import DevGateway
from aios_orchestration_core.github.dev_gateway_api import GitHubApiDevGateway
from aios_orchestration_core.github.pm_gateway import PMGateway
from aios_orchestration_core.github.pm_gateway_api import GitHubApiConfig, GitHubApiPMGateway
from aios_orchestration_core.github.po_gateway import POGateway
from aios_orchestration_core.github.po_gateway_api import GitHubApiPOGateway


@dataclass
class RepoContext:
    """Encapsulates repository context (GitHub vs local)."""
    
    repo_ref: str  # Either "owner/repo" or local path
    is_github: bool  # True if GitHub API, False if local
    
    @staticmethod
    def from_string(repo_ref: str) -> "RepoContext":
        """Parse repo reference: 'owner/repo' for GitHub, './path' or '/path' for local."""
        is_github = "/" in repo_ref and not (repo_ref.startswith(".") or repo_ref.startswith("/"))
        return RepoContext(repo_ref=repo_ref, is_github=is_github)
    
    @staticmethod
    def from_env(env_var: str = "AIOS_TARGET_REPO", default: Optional[str] = None) -> "RepoContext":
        """Load repo context from environment variable, with optional default."""
        repo_ref = os.environ.get(env_var) or default
        if not repo_ref:
            raise ValueError(
                f"Repo context not specified. Set {env_var} environment variable or pass default.\n"
                f"Format: 'owner/repo' for GitHub, './path' or '/path' for local repo."
            )
        return RepoContext.from_string(repo_ref)
    
    def create_pm_gateway(self) -> PMGateway:
        """Create appropriate PM gateway for this repo context."""
        if self.is_github:
            return GitHubApiPMGateway(GitHubApiConfig(repo=self.repo_ref))
        else:
            raise NotImplementedError(
                f"Local repo support not yet implemented for PM gateway. "
                f"Please use GitHub format 'owner/repo' for now."
            )

    def create_po_gateway(self) -> POGateway:
        """Create appropriate PO gateway for this repo context."""
        if self.is_github:
            return GitHubApiPOGateway(GitHubApiConfig(repo=self.repo_ref))
        raise NotImplementedError(
            f"Local repo support not yet implemented for PO gateway. "
            f"Please use GitHub format 'owner/repo' for now."
        )

    def create_dev_gateway(self) -> DevGateway:
        """Create appropriate Dev gateway for this repo context."""
        if self.is_github:
            return GitHubApiDevGateway(GitHubApiConfig(repo=self.repo_ref))
        raise NotImplementedError(
            f"Local repo support not yet implemented for Dev gateway. "
            f"Please use GitHub format 'owner/repo' for now."
        )

    def create_foundation_gateway(self):
        raise NotImplementedError(
            "Foundation GitHub API gateway is not implemented in RepoContext yet."
        )

    def create_arch_review_gateway(self):
        raise NotImplementedError(
            "ArchReview GitHub API gateway is not implemented in RepoContext yet."
        )
    
    def __str__(self) -> str:
        return f"{'GitHub' if self.is_github else 'Local'}: {self.repo_ref}"
