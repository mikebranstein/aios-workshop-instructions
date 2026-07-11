from dataclasses import asdict
from datetime import datetime, timezone
from uuid import uuid4

from aios_orchestration_core.artifacts.strategic_opportunity import MarketSizeEstimate, StrategicOpportunityArtifact
from aios_orchestration_core.events.pm import PMEvent
from aios_orchestration_core.github.pm_gateway import PMGitHubGateway
from aios_orchestration_core.labels.pm_labels import PM_CANONICAL_LABEL_BY_STATE
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.states.pm import PMState
from aios_orchestration_core.transitions.pm import get_next_pm_state


class PMPhase2DecisionNode:
    def __init__(self, adapter: JudgmentLLMAdapter, gateway: PMGitHubGateway):
        self.adapter = adapter
        self.gateway = gateway

    def run(self, issue_number: int, synthesis_summary: str, synthesis_confidence: float) -> PMState:
        issue = self.gateway.get_issue(issue_number)
        result = self.adapter.invoke_json(
            "pm_phase2",
            {
                "issue_number": issue_number,
                "title": issue.title,
                "synthesis_summary": synthesis_summary,
                "synthesis_confidence": synthesis_confidence,
            },
        )

        decision = result.payload["decision"]
        event = {
            "CHAMPION": PMEvent.PHASE2_CHAMPION,
            "DEFER": PMEvent.PHASE2_DEFER,
            "BLOCK": PMEvent.PHASE2_BLOCK,
            "ESCALATE": PMEvent.PHASE2_ESCALATE,
        }[decision]

        next_state = get_next_pm_state(PMState.PM_PHASE2_VALIDATING, event)

        if decision == "CHAMPION":
            artifact = StrategicOpportunityArtifact(
                artifact_version="1.0.0",
                artifact_type="strategic_opportunity",
                artifact_id=f"so-{uuid4()}",
                source_pm_issue_number=issue_number,
                title=issue.title,
                strategic_thesis=result.payload["reason"],
                customer_problem=issue.body or "No customer problem text provided",
                market_size_estimate=MarketSizeEstimate(
                    method="qualitative_signal_synthesis",
                    confidence=float(result.payload["confidence_score"]),
                    value=None,
                    unit=None,
                ),
                decision=decision,
                confidence_score=float(result.payload["confidence_score"]),
                produced_at=datetime.now(timezone.utc).isoformat(),
            )
            artifact.validate()
            self.gateway.publish_strategic_opportunity_artifact(issue_number, asdict(artifact))

        self.gateway.add_labels(issue_number, [PM_CANONICAL_LABEL_BY_STATE[next_state]])

        if next_state in {
            PMState.PM_OUTPUT_PUBLISHED,
            PMState.PM_DEFERRED,
            PMState.PM_BLOCKED,
            PMState.PM_ESCALATED,
        }:
            self.gateway.close_issue(issue_number, "completed" if decision == "CHAMPION" else "not planned")

        return next_state
