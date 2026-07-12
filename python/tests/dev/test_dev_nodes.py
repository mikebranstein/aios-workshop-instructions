import tempfile
import unittest

from aios_orchestration_core.github.dev_gateway import DevGitHubGateway, DevIssue
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.dev import DevState
from dev_orchestrator.nodes.build import DevBuildNode
from dev_orchestrator.nodes.design import DevDesignNode
from dev_orchestrator.nodes.intake import DevIntakeNode
from dev_orchestrator.nodes.policy import DevPolicyNode
from dev_orchestrator.nodes.qa import DevQANode


class _A:
    def __init__(self, decision):
        self.decision = decision

    @property
    def adapter_source(self):
        return "stub"

    def invoke_json(self, task_type, prompt_vars, model_hint=""):
        return type("R", (), {"payload": {"decision": self.decision, "reason": "test"}})()


class DevNodesTests(unittest.TestCase):
    def _gw(self, labels):
        return DevGitHubGateway({1: DevIssue(1, "F", "b", labels=set(labels))})

    def _store(self, tmp):
        return TransitionLogStore(f"{tmp}/runlog.sqlite")

    def test_intake_approved_transitions_to_design(self) -> None:
        gw = self._gw({"dev:intake"})
        with tempfile.TemporaryDirectory() as tmp:
            state = DevIntakeNode(_A("APPROVED"), gw, self._store(tmp)).run("r", 1)
        self.assertEqual(state, DevState.DEV_DESIGN)
        self.assertIn("dev:design", gw.get_issue(1).labels)

    def test_intake_blocked_closes_issue(self) -> None:
        gw = self._gw({"dev:intake"})
        with tempfile.TemporaryDirectory() as tmp:
            state = DevIntakeNode(_A("BLOCKED"), gw, self._store(tmp)).run("r", 1)
        self.assertEqual(state, DevState.DEV_BLOCKED)
        self.assertFalse(gw.get_issue(1).open)

    def test_design_revise_loops_to_intake(self) -> None:
        gw = self._gw({"dev:design"})
        with tempfile.TemporaryDirectory() as tmp:
            state = DevDesignNode(_A("REVISE"), gw, self._store(tmp)).run("r", 1)
        self.assertEqual(state, DevState.DEV_INTAKE)

    def test_build_complete_to_qa(self) -> None:
        gw = self._gw({"dev:build"})
        with tempfile.TemporaryDirectory() as tmp:
            state = DevBuildNode(_A("COMPLETE"), gw, self._store(tmp)).run("r", 1)
        self.assertEqual(state, DevState.DEV_QA)

    def test_qa_failed_loops_to_design(self) -> None:
        gw = self._gw({"dev:qa"})
        with tempfile.TemporaryDirectory() as tmp:
            state = DevQANode(_A("FAILED"), gw, self._store(tmp)).run("r", 1)
        self.assertEqual(state, DevState.DEV_DESIGN)

    def test_policy_approved_releases(self) -> None:
        gw = self._gw({"dev:policy"})
        with tempfile.TemporaryDirectory() as tmp:
            state = DevPolicyNode(_A("APPROVED"), gw, self._store(tmp)).run("r", 1)
        self.assertEqual(state, DevState.DEV_RELEASED)
        self.assertFalse(gw.get_issue(1).open)

    def test_policy_review_required_needs_human(self) -> None:
        gw = self._gw({"dev:policy"})
        with tempfile.TemporaryDirectory() as tmp:
            state = DevPolicyNode(_A("REVIEW_REQUIRED"), gw, self._store(tmp)).run("r", 1)
        self.assertEqual(state, DevState.DEV_NEEDS_HUMAN)

    def test_node_posts_dev_transition_comment(self) -> None:
        gw = self._gw({"dev:intake"})
        with tempfile.TemporaryDirectory() as tmp:
            DevIntakeNode(_A("APPROVED"), gw, self._store(tmp)).run("r", 1)
        self.assertTrue(any("[DEV Transition]" in c for c in gw.get_issue(1).comments))


if __name__ == "__main__":
    unittest.main()
