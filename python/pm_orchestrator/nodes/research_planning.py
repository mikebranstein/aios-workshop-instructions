from dataclasses import dataclass
from typing import List

from aios_orchestration_core.github.pm_gateway import PMGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter


@dataclass(frozen=True)
class ResearchTask:
    topic: str
    persona: str


class PMResearchPlanningNode:
    def __init__(self, adapter: JudgmentLLMAdapter, gateway: PMGateway):
        self.adapter = adapter
        self.gateway = gateway

    def run(self, issue_number: int) -> List[ResearchTask]:
        issue = self.gateway.get_issue(issue_number)
        result = self.adapter.invoke_json(
            "pm_research_task_plan",
            {"issue_number": issue.number, "title": issue.title, "body": issue.body},
        )
        tasks = [ResearchTask(topic=t["topic"], persona=t["persona"]) for t in result.payload["tasks"]]

        for task in tasks:
            self.gateway.ensure_research_issue(
                pm_issue_number=issue_number,
                title=f"[research]: {task.persona} - {task.topic}",
                body=f"Research topic: {task.topic}",
                labels=["research", f"pm-idea-{issue_number}"],
            )

        return tasks
