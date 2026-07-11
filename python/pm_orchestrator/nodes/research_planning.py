from dataclasses import dataclass
from typing import List

from aios_orchestration_core.github.pm_gateway import PMGitHubGateway, PMIssue
from aios_orchestration_core.llm.base import JudgmentLLMAdapter


@dataclass(frozen=True)
class ResearchTask:
    topic: str
    persona: str


class PMResearchPlanningNode:
    def __init__(self, adapter: JudgmentLLMAdapter, gateway: PMGitHubGateway):
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
            new_number = max(self.gateway.issues.keys()) + 1 if self.gateway.issues else 1
            research_issue = PMIssue(
                number=new_number,
                title=f"[research]: {task.persona} - {task.topic}",
                body=f"Research topic: {task.topic}",
                labels={"research", f"pm-idea-{issue_number}"},
                open=True,
            )
            self.gateway.issues[new_number] = research_issue
            issue.linked_research_issue_numbers.append(new_number)

        return tasks
