from dataclasses import dataclass
from enum import Enum


class PMPhase1Decision(str, Enum):
    PROVISIONAL_CHAMPION = "PROVISIONAL_CHAMPION"
    DEFER = "DEFER"
    BLOCK = "BLOCK"


class PMPhase2Decision(str, Enum):
    CHAMPION = "CHAMPION"
    DEFER = "DEFER"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"


@dataclass(frozen=True)
class PMResearchSynthesis:
    summary: str
    confidence_score: float
    closed_linked_research_count: int

    def validate(self, min_confidence_score: float, min_research_count: int) -> None:
        if not self.summary.strip():
            raise ValueError("Research synthesis summary must be non-empty")
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("confidence_score must be between 0 and 1")
        if self.closed_linked_research_count < 0:
            raise ValueError("closed_linked_research_count must be non-negative")
        if self.confidence_score < min_confidence_score:
            raise ValueError("confidence_score below configured gate")
        if self.closed_linked_research_count < min_research_count:
            raise ValueError("closed_linked_research_count below configured gate")
