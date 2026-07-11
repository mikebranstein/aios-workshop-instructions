from dataclasses import dataclass

from aios_orchestration_core.artifacts.pm_decisions import PMResearchSynthesis
from aios_orchestration_core.llm.base import JudgmentLLMAdapter


@dataclass
class SynthesisGateConfig:
    min_confidence_score: float
    min_closed_linked_research_count: int


class PMResearchSynthesisNode:
    def __init__(self, adapter: JudgmentLLMAdapter, config: SynthesisGateConfig):
        self.adapter = adapter
        self.config = config

    def run(self, issue_number: int, closed_linked_research_count: int) -> PMResearchSynthesis:
        result = self.adapter.invoke_json(
            "pm_research_synthesis",
            {
                "issue_number": issue_number,
                "closed_linked_research_count": closed_linked_research_count,
            },
        )
        synthesis = PMResearchSynthesis(
            summary=result.payload["summary"],
            confidence_score=float(result.payload["confidence_score"]),
            closed_linked_research_count=int(result.payload["closed_linked_research_count"]),
        )
        synthesis.validate(
            min_confidence_score=self.config.min_confidence_score,
            min_research_count=self.config.min_closed_linked_research_count,
        )
        return synthesis
