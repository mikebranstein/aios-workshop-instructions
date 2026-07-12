from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class TraceMetadata:
    run_id: str
    model: str
    prompt_version: str

    def validate(self) -> None:
        if not self.run_id.strip():
            raise ValueError("trace.run_id is required")
        if not self.model.strip():
            raise ValueError("trace.model is required")
        if not self.prompt_version.strip():
            raise ValueError("trace.prompt_version is required")


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
    decision_rationale: str
    evidence_refs: list[str]
    research_item_ids: list[int]
    handoff_contract_version: str
    trace: TraceMetadata
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
        if not self.decision_rationale.strip():
            raise ValueError("decision_rationale is required")
        if not self.handoff_contract_version.strip():
            raise ValueError("handoff_contract_version is required")
        for ref in self.evidence_refs:
            if not ref.strip():
                raise ValueError("evidence_refs entries must be non-empty")
        for issue_number in self.research_item_ids:
            if issue_number <= 0:
                raise ValueError("research_item_ids must contain positive issue numbers")
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("confidence_score must be between 0 and 1")
        self.market_size_estimate.validate()
        self.trace.validate()
        datetime.fromisoformat(self.produced_at)
