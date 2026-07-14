from dataclasses import dataclass, field
from typing import Dict, List, Protocol

from discovery_orchestrator.context import DiscoveryContext


class DiscoveryGateway(Protocol):
    """Abstract gateway for all Discovery orchestrator external interactions."""

    def get_context(self) -> DiscoveryContext:
        """Load precondition context: foundation gate, focus file status."""
        ...

    def read_focus_file(self) -> str:
        """Return the full content of docs/discovery-focus.md."""
        ...

    def create_pm_idea_issue(self, title: str, body: str) -> int:
        """Create a pm-idea GitHub issue and return its number."""
        ...

    def append_deferred_candidates(self, candidates: List[dict]) -> bool:
        """Persist deferred candidates to the Discovery-Deferred-Candidates wiki page.

        Args:
            candidates: List of dicts with "title" and "body" keys.

        Returns:
            True if the wiki write succeeded, False otherwise.
        """
        ...


@dataclass
class DiscoveryInMemoryGateway:
    """In-memory gateway for testing — no GitHub calls."""

    context: DiscoveryContext = field(default_factory=DiscoveryContext)
    focus_content: str = ""
    _issues: Dict[int, Dict] = field(default_factory=dict)
    _next: int = 1000
    deferred_candidates: List[dict] = field(default_factory=list)

    def get_context(self) -> DiscoveryContext:
        return self.context

    def read_focus_file(self) -> str:
        return self.focus_content

    def create_pm_idea_issue(self, title: str, body: str) -> int:
        self._next += 1
        self._issues[self._next] = {
            "title": title,
            "body": body,
            "labels": {"pm-idea", "pm-idea-auto"},
        }
        return self._next

    def append_deferred_candidates(self, candidates: List[dict]) -> bool:
        self.deferred_candidates.extend(candidates)
        return True
