import unittest

from aios_orchestration_core.github.pm_gateway import PMGitHubGateway, PMIssue
from aios_orchestration_core.states.pm import PMState
from pm_orchestrator.nodes.phase2_decision import PMPhase2DecisionNode


class StubPhase2Adapter:
    def invoke_json(self, task_type, prompt_vars, model_hint=""):
        return type(
            "Result",
            (),
            {
                "payload": {
                    "decision": "CHAMPION",
                    "reason": "Strong validated strategic upside",
                    "confidence_score": 0.88,
                },
                "model": "test-model",
            },
        )()


class Phase8Phase2PublishTests(unittest.TestCase):
    def test_champion_publishes_artifact_and_closes(self) -> None:
        gateway = PMGitHubGateway({9: PMIssue(9, "Title", "Customer problem", labels={"pm:phase2-validating"})})
        node = PMPhase2DecisionNode(StubPhase2Adapter(), gateway)
        state = node.run(
            run_id="run-9",
            issue_number=9,
            synthesis_summary="summary",
            synthesis_confidence=0.88,
            prompt_version="pm-v1",
            handoff_contract_version="1.0.0",
        )
        self.assertEqual(state, PMState.PM_OUTPUT_PUBLISHED)
        self.assertFalse(gateway.get_issue(9).open)
        self.assertIn(9, gateway.published_artifacts)
        self.assertIn("pm:output-published", gateway.get_issue(9).labels)


if __name__ == "__main__":
    unittest.main()
