import tempfile
import unittest

from aios_orchestration_core.github.po_gateway import POGitHubGateway, POIssue
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.po import POState
from po_orchestrator.run_once import PORunOnceOrchestrator, PORunRegistry


class _StaticAdapter:
    def __init__(self, payload):
        self.payload = payload

    def invoke_json(self, task_type, prompt_vars, model_hint=""):
        return type("R", (), {"payload": self.payload, "model": "test"})()


class PORunOnceTests(unittest.TestCase):
    def _orchestrator(self, gateway, tmp, prioritize_payload, create_payload, **kwargs):
        return PORunOnceOrchestrator(
            gateway=gateway,
            log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
            run_registry=PORunRegistry(),
            prioritize_adapter=_StaticAdapter(prioritize_payload),
            create_features_adapter=_StaticAdapter(create_payload),
            **kwargs,
        )

    def test_full_path_queued_to_feature_requests_created(self) -> None:
        gateway = POGitHubGateway({1: POIssue(1, "Op", "body", labels={"po:queued"})})
        with tempfile.TemporaryDirectory() as tmp:
            run = self._orchestrator(
                gateway, tmp,
                {"decision": "CREATE_FEATURE_REQUESTS", "reason": "good"},
                {"feature_requests": [{"title": "FR", "body": "do it", "priority_score": 55}]},
            ).run_once(1)
        self.assertIsNotNone(run.ended_at_utc)
        self.assertIn("po:feature-requests-created", gateway.get_issue(1).labels)

    def test_defer_path_closes_opportunity(self) -> None:
        gateway = POGitHubGateway({1: POIssue(1, "Op", "body", labels={"po:queued"})})
        with tempfile.TemporaryDirectory() as tmp:
            self._orchestrator(
                gateway, tmp,
                {"decision": "DEFER", "reason": "later"},
                {"feature_requests": []},
            ).run_once(1)
        self.assertIn("po:deferred", gateway.get_issue(1).labels)
        self.assertFalse(gateway.get_issue(1).open)

    def test_reject_path_closes_opportunity(self) -> None:
        gateway = POGitHubGateway({1: POIssue(1, "Op", "body", labels={"po:queued"})})
        with tempfile.TemporaryDirectory() as tmp:
            self._orchestrator(
                gateway, tmp,
                {"decision": "REJECT", "reason": "not viable"},
                {"feature_requests": []},
            ).run_once(1)
        self.assertIn("po:rejected", gateway.get_issue(1).labels)

    def test_idempotent_when_already_in_creating_features(self) -> None:
        gateway = POGitHubGateway({1: POIssue(1, "Op", "body", labels={"po:creating-features"})})
        with tempfile.TemporaryDirectory() as tmp:
            orch = self._orchestrator(
                gateway, tmp,
                {"decision": "CREATE_FEATURE_REQUESTS", "reason": "good"},
                {"feature_requests": [{"title": "FR", "body": "do it", "priority_score": 40}]},
            )
            orch.run_once(1)
            first_count = len(gateway.list_created_feature_request_numbers(1))
            # Re-running after terminal state should be a no-op.
            orch.run_once(1)
            second_count = len(gateway.list_created_feature_request_numbers(1))
        self.assertEqual(first_count, 1)
        self.assertEqual(second_count, 1)

    def test_circuit_breaker_escalates_to_needs_human(self) -> None:
        class _FailingAdapter:
            def invoke_json(self, task_type, prompt_vars, model_hint=""):
                raise RuntimeError("simulated")

        from aios_orchestration_core.policies.retry import RetryPolicy

        gateway = POGitHubGateway({1: POIssue(1, "Op", "body", labels={"po:queued"})})
        with tempfile.TemporaryDirectory() as tmp:
            PORunOnceOrchestrator(
                gateway=gateway,
                log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
                run_registry=PORunRegistry(),
                prioritize_adapter=_FailingAdapter(),
                create_features_adapter=_FailingAdapter(),
                retry_policy=RetryPolicy(max_attempts=1),
            ).run_once(1)
        self.assertIn("po:needs-human", gateway.get_issue(1).labels)

    def test_transition_log_written_for_each_step(self) -> None:
        gateway = POGitHubGateway({1: POIssue(1, "Op", "body", labels={"po:queued"})})
        with tempfile.TemporaryDirectory() as tmp:
            orch = self._orchestrator(
                gateway, tmp,
                {"decision": "DEFER", "reason": "no"},
                {"feature_requests": []},
            )
            orch.run_once(1)
            # Verify transitions were logged
            entries = orch.log_store.all()
        self.assertTrue(len(entries) > 0, "Expected at least one transition logged")
        self.assertTrue(all(e.loop_id == "po" for e in entries), "All entries should be from po loop")
        states_visited = [e.from_state for e in entries]
        self.assertIn("PO_QUEUED", states_visited, "PO_QUEUED should be visited")


if __name__ == "__main__":
    unittest.main()
