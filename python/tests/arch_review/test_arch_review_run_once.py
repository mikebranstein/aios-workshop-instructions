import tempfile
import unittest

from aios_orchestration_core.github.arch_review_gateway import ArchReviewGitHubGateway, ArchReviewIssue
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.arch_review import ArchReviewState
from arch_review_orchestrator.run_once import ArchReviewRunOnceOrchestrator, ArchReviewRunRegistry


class _S:
    def __init__(self, *payloads):
        self._payloads = list(payloads)
        self._idx = 0

    @property
    def adapter_source(self):
        return "stub"

    def invoke_json(self, *a, **kw):
        p = self._payloads[min(self._idx, len(self._payloads) - 1)]
        self._idx += 1
        return type("R", (), {"payload": p, "model": "t"})()


def _orch(gw, tmp, review, planner, **kw):
    return ArchReviewRunOnceOrchestrator(
        gateway=gw,
        log_store=TransitionLogStore(f"{tmp}/r.sqlite"),
        run_registry=ArchReviewRunRegistry(),
        review_adapter=_S(*review) if isinstance(review, list) else _S(review),
        planner_adapter=_S(*planner) if isinstance(planner, list) else _S(planner),
        **kw,
    )


class ArchReviewRunOnceTests(unittest.TestCase):
    def test_no_action_path(self) -> None:
        gw = ArchReviewGitHubGateway({1: ArchReviewIssue(1, "Review", "body", labels={"arch:review-pending"})})
        with tempfile.TemporaryDirectory() as tmp:
            _orch(gw, tmp, {"decision": "NO_ACTION", "reason": "all good"}, {"decision": "DEFER", "reason": "-"}).run_once(1)
        self.assertIn("arch:no-action", gw.get_issue(1).labels)
        self.assertFalse(gw.get_issue(1).open)

    def test_warn_creates_refactor_requests(self) -> None:
        gw = ArchReviewGitHubGateway({1: ArchReviewIssue(1, "Review", "body", labels={"arch:review-pending"})})
        with tempfile.TemporaryDirectory() as tmp:
            run = _orch(
                gw, tmp,
                {"decision": "CREATE_REFACTOR_PLAN", "reason": "tech debt"},
                {"decision": "CREATE_REFACTOR_REQUESTS", "reason": "3 items", "refactor_requests": [
                    {"title": "Refactor A", "body": "do it"},
                    {"title": "Refactor B", "body": "also do it"},
                ]},
            ).run_once(1)
        self.assertIn("arch:refactor-created", gw.get_issue(1).labels)
        self.assertEqual(len(run.created_refactor_request_numbers), 2)
        for nr in run.created_refactor_request_numbers:
            self.assertIn("refactor-request", gw.get_issue(nr).labels)

    def test_critical_escalates(self) -> None:
        gw = ArchReviewGitHubGateway({1: ArchReviewIssue(1, "Review", "body", labels={"arch:review-pending"})})
        with tempfile.TemporaryDirectory() as tmp:
            _orch(gw, tmp, {"decision": "ESCALATE", "reason": "critical"}, {"decision": "DEFER", "reason": "-"}).run_once(1)
        self.assertIn("arch:review-escalated", gw.get_issue(1).labels)

    def test_circuit_breaker_escalates(self) -> None:
        class _Fail:
            def invoke_json(self, *a, **kw): raise RuntimeError("fail")

        gw = ArchReviewGitHubGateway({1: ArchReviewIssue(1, "Review", "body", labels={"arch:review-pending"})})
        with tempfile.TemporaryDirectory() as tmp:
            ArchReviewRunOnceOrchestrator(
                gateway=gw, log_store=TransitionLogStore(f"{tmp}/r.sqlite"),
                run_registry=ArchReviewRunRegistry(),
                review_adapter=_Fail(), planner_adapter=_Fail(),
                retry_policy=RetryPolicy(max_attempts=1),
            ).run_once(1)
        self.assertIn("arch:needs-human", gw.get_issue(1).labels)

    def test_debt_upsert_creates_issue(self) -> None:
        gw = ArchReviewGitHubGateway({})
        n = gw.upsert_debt_issue("Complexity hotspot in module X", "Evidence: ...")
        self.assertIn("architecture-debt", gw.get_issue(n).labels)
        # Upsert same title: returns same number
        n2 = gw.upsert_debt_issue("Complexity hotspot in module X", "Updated evidence")
        self.assertEqual(n, n2)


if __name__ == "__main__":
    unittest.main()
