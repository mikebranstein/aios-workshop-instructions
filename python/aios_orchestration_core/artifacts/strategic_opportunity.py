from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class MarketSizeEstimate:
    method: str
    confidence: float
    value: Optional[float] = None
    unit: Optional[str] = None

    def validate(self) -> None:
        if not self.method.strip():
            raise ValueError("market_size_estimate.method is required")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("market_size_estimate.confidence must be between 0 and 1")
        if self.value is not None and self.value < 0:
            raise ValueError("market_size_estimate.value cannot be negative")


@dataclass(frozen=True)
class StrategicOpportunityArtifact:
    artifact_version: str
    artifact_type: str
    artifact_id: str
    source_pm_issue_number: int
    title: str
    strategic_thesis: str
    customer_problem: str
    market_size_estimate: MarketSizeEstimate
    decision: str
    confidence_score: float
    produced_at: str

    def validate(self) -> None:
        if self.artifact_type != "strategic_opportunity":
            raise ValueError("artifact_type must be strategic_opportunity")
        if self.source_pm_issue_number <= 0:
            raise ValueError("source_pm_issue_number must be positive")
        if not self.title.strip():
            raise ValueError("title is required")
        if not self.strategic_thesis.strip():
            raise ValueError("strategic_thesis is required")
        if not self.customer_problem.strip():
            raise ValueError("customer_problem is required")
        if self.decision not in {"CHAMPION", "DEFER", "BLOCK", "ESCALATE"}:
            raise ValueError("decision has invalid value")
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("confidence_score must be between 0 and 1")
        self.market_size_estimate.validate()
        datetime.fromisoformat(self.produced_at)
