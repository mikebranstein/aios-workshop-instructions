from dataclasses import dataclass

from aios_orchestration_core.github.pm_gateway import PMGitHubGateway


@dataclass(frozen=True)
class ResearchClosureGateResult:
    passed: bool
    closed_count: int
    reason: str


def evaluate_research_closure_gate(
    gateway: PMGitHubGateway,
    issue_number: int,
    min_closed_linked_research_items: int,
) -> ResearchClosureGateResult:
    closed_count = gateway.count_closed_linked_research_issues(issue_number)
    if not gateway.are_linked_research_issues_closed(issue_number):
        return ResearchClosureGateResult(False, closed_count, "Linked research issues are still open")
    if closed_count < min_closed_linked_research_items:
        return ResearchClosureGateResult(
            False,
            closed_count,
            "Closed linked research count below configured floor",
        )
    return ResearchClosureGateResult(True, closed_count, "Research closure floor passed")
