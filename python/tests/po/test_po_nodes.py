import tempfile
import unittest

from aios_orchestration_core.github.po_gateway import POGitHubGateway, POIssue
from aios_orchestration_core.runlog.sqlite_store import TransitionLogStore
from aios_orchestration_core.states.po import POState
from po_orchestrator.nodes.create_features import POCreateFeaturesNode
from po_orchestrator.nodes.prioritize import POPrioritizeNode


class StubPrioritizeAdapter:
    def __init__(self, decision: str):
        self.decision = decision

    def invoke_json(self, task_type, prompt_vars, model_hint=""):
        return type("R", (), {"payload": {"decision": self.decision, "reason": "test"}})()


class StubCreateFeaturesAdapter:
    def __init__(self, specs):
        self.specs = specs

    def invoke_json(self, task_type, prompt_vars, model_hint=""):
        return type("R", (), {"payload": {"feature_requests": self.specs}})()


class POPrioritizeNodeTests(unittest.TestCase):
    def _make_gateway(self, labels):
        return POGitHubGateway({1: POIssue(1, "Op", "body", labels=set(labels))})

    def test_create_decision_transitions_to_creating_features(self) -> None:
        gateway = self._make_gateway({"po:prioritizing"})
        with tempfile.TemporaryDirectory() as tmp:
            node = POPrioritizeNode(
                StubPrioritizeAdapter("CREATE_FEATURE_REQUESTS"),
                gateway,
                TransitionLogStore(f"{tmp}/runlog.sqlite"),
            )
            state = node.run("run-1", 1)
        self.assertEqual(state, POState.PO_CREATING_FEATURES)
        self.assertIn("po:creating-features", gateway.get_issue(1).labels)

    def test_defer_decision_closes_issue(self) -> None:
        gateway = self._make_gateway({"po:prioritizing"})
        with tempfile.TemporaryDirectory() as tmp:
            node = POPrioritizeNode(
                StubPrioritizeAdapter("DEFER"),
                gateway,
                TransitionLogStore(f"{tmp}/runlog.sqlite"),
            )
            state = node.run("run-1", 1)
        self.assertEqual(state, POState.PO_DEFERRED)
        self.assertFalse(gateway.get_issue(1).open)

    def test_reject_decision_closes_issue(self) -> None:
        gateway = self._make_gateway({"po:prioritizing"})
        with tempfile.TemporaryDirectory() as tmp:
            node = POPrioritizeNode(
                StubPrioritizeAdapter("REJECT"),
                gateway,
                TransitionLogStore(f"{tmp}/runlog.sqlite"),
            )
            state = node.run("run-1", 1)
        self.assertEqual(state, POState.PO_REJECTED)
        self.assertFalse(gateway.get_issue(1).open)

    def test_node_posts_transition_comment(self) -> None:
        gateway = self._make_gateway({"po:prioritizing"})
        with tempfile.TemporaryDirectory() as tmp:
            node = POPrioritizeNode(
                StubPrioritizeAdapter("CREATE_FEATURE_REQUESTS"),
                gateway,
                TransitionLogStore(f"{tmp}/runlog.sqlite"),
            )
            node.run("run-1", 1)
        comments = gateway.get_issue(1).comments
        self.assertTrue(any("[PO Transition]" in c for c in comments))


class POCreateFeaturesNodeTests(unittest.TestCase):
    def test_creates_feature_requests_and_transitions(self) -> None:
        gateway = POGitHubGateway({1: POIssue(1, "Op", "body", labels={"po:creating-features"})})
        specs = [
            {"title": "FR1", "body": "do it", "priority_score": 70},
            {"title": "FR2", "body": "do it too", "priority_score": 50},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            node = POCreateFeaturesNode(
                StubCreateFeaturesAdapter(specs),
                gateway,
                TransitionLogStore(f"{tmp}/runlog.sqlite"),
            )
            state = node.run("run-1", 1)
        self.assertEqual(state, POState.PO_FEATURE_REQUESTS_CREATED)
        self.assertIn("po:feature-requests-created", gateway.get_issue(1).labels)
        self.assertFalse(gateway.get_issue(1).open)
        self.assertEqual(len(gateway.list_created_feature_request_numbers(1)), 2)

    def test_empty_feature_request_list_still_transitions(self) -> None:
        gateway = POGitHubGateway({1: POIssue(1, "Op", "body", labels={"po:creating-features"})})
        with tempfile.TemporaryDirectory() as tmp:
            node = POCreateFeaturesNode(
                StubCreateFeaturesAdapter([]),
                gateway,
                TransitionLogStore(f"{tmp}/runlog.sqlite"),
            )
            state = node.run("run-1", 1)
        self.assertEqual(state, POState.PO_FEATURE_REQUESTS_CREATED)


if __name__ == "__main__":
    unittest.main()
