from dataclasses import dataclass, field
from typing import List, Optional, Protocol


@dataclass
class IdeaCandidate:
    title: str
    body: str
    decision: str  # CREATE_PM_IDEA | DEFER | DROP


@dataclass
class IdeaScoutResult:
    candidates: List[IdeaCandidate] = field(default_factory=list)


class IdeaScoutAdapter(Protocol):
    """Abstraction for the idea-scout agent invocation."""

    def run(self, context_summary: str, creation_cap: int) -> IdeaScoutResult:
        ...


class StaticIdeaScoutAdapter:
    """In-memory adapter for testing: returns a fixed set of candidates."""

    def __init__(self, candidates: List[IdeaCandidate]) -> None:
        self._candidates = candidates

    def run(self, context_summary: str, creation_cap: int) -> IdeaScoutResult:
        return IdeaScoutResult(candidates=self._candidates[:creation_cap])
