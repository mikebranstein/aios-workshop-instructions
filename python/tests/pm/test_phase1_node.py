import tempfile
import unittest

from aios_orchestration_core.github.pm_gateway import PMGitHubGateway, PMIssue
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.pm import PMState
from pm_orchestrator.nodes.phase1 import PMPhase1Node, Phase1Config


class StubAdapter:
    @property
    def adapter_source(self):
        return "stub"

    def invoke_json(self, task_type, prompt_vars, model_hint=""):
        return type("Result", (), {"payload": {"decision": "PROVISIONAL_CHAMPION", "reason": "signal"}})()


class Phase5Phase1NodeTests(unittest.TestCase):
    def test_phase1_node_applies_transition(self) -> None:
        gateway = PMGitHubGateway({1: PMIssue(1, "idea", "body", labels={"pm:phase1-validating"})})
        with tempfile.TemporaryDirectory() as tmp:
            node = PMPhase1Node(StubAdapter(), gateway, TransitionLogStore(f"{tmp}/runlog.sqlite"), Phase1Config())
            state = node.run("run-1", 1)
            self.assertEqual(state, PMState.PM_RESEARCH_PLANNING)
            self.assertIn("pm:research-planning", gateway.get_issue(1).labels)


if __name__ == "__main__":
    unittest.main()
