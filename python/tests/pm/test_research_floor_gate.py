import unittest

from aios_orchestration_core.github.pm_gateway import PMGitHubGateway, PMIssue
from pm_orchestrator.nodes.research_closure_gate import evaluate_research_closure_gate


class Phase6ResearchGateTests(unittest.TestCase):
    def test_floor_gate_requires_all_closed_and_min_count(self) -> None:
        gateway = PMGitHubGateway(
            {
                1: PMIssue(1, "idea", "body", linked_research_issue_numbers=[2, 3]),
                2: PMIssue(2, "r1", "", open=False),
                3: PMIssue(3, "r2", "", open=False),
            }
        )
        result = evaluate_research_closure_gate(gateway, 1, min_closed_linked_research_items=2)
        self.assertTrue(result.passed)

    def test_floor_gate_fails_if_open_exists(self) -> None:
        gateway = PMGitHubGateway(
            {
                1: PMIssue(1, "idea", "body", linked_research_issue_numbers=[2]),
                2: PMIssue(2, "r1", "", open=True),
            }
        )
        result = evaluate_research_closure_gate(gateway, 1, min_closed_linked_research_items=1)
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
