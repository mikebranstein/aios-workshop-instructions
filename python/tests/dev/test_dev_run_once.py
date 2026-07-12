import tempfile
import unittest

from aios_orchestration_core.github.dev_gateway import DevGitHubGateway, DevIssue
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from dev_orchestrator.run_once import DevRunOnceOrchestrator, DevRunRegistry


class _A:
    def __init__(self, payload):
        self.payload = payload

    @property
    def adapter_source(self):
        return "stub"

    def invoke_json(self, *a, **kw):
        return type("R", (), {"payload": self.payload, "model": "t"})()


def _orch(gateway, tmp, *, intake, design, build, qa, policy, **kw):
    return DevRunOnceOrchestrator(
        gateway=gateway,
        log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
        run_registry=DevRunRegistry(),
        intake_adapter=_A(intake),
        design_adapter=_A(design),
        build_adapter=_A(build),
        qa_adapter=_A(qa),
        policy_adapter=_A(policy),
        **kw,
    )


_OK = {"decision": "APPROVED", "reason": "ok"}
_COMPLETE = {"decision": "COMPLETE", "reason": "done"}
_PASSED = {"decision": "PASSED", "reason": "green"}


class DevRunOnceTests(unittest.TestCase):
    def test_full_pipeline_happy_path(self) -> None:
        gw = DevGitHubGateway({1: DevIssue(1, "F", "b", labels={"dev:intake"})})
        with tempfile.TemporaryDirectory() as tmp:
            run = _orch(gw, tmp, intake=_OK, design=_OK, build=_COMPLETE, qa=_PASSED, policy=_OK).run_once(1)
        self.assertIsNotNone(run.ended_at_utc)
        self.assertIn("dev:released", gw.get_issue(1).labels)
        self.assertFalse(gw.get_issue(1).open)

    def test_intake_blocked_short_circuits(self) -> None:
        gw = DevGitHubGateway({1: DevIssue(1, "F", "b", labels={"dev:intake"})})
        with tempfile.TemporaryDirectory() as tmp:
            _orch(gw, tmp, intake={"decision": "BLOCKED", "reason": "dep"},
                  design=_OK, build=_COMPLETE, qa=_PASSED, policy=_OK).run_once(1)
        self.assertIn("dev:blocked", gw.get_issue(1).labels)

    def test_design_revise_feedback_loop_completes(self) -> None:
        # First design call returns REVISE, second returns APPROVED
        calls = {"n": 0}

        class _DesignAdapter:
            @property
            def adapter_source(self):
                return "stub"

            def invoke_json(self, *a, **kw):
                calls["n"] += 1
                d = "REVISE" if calls["n"] == 1 else "APPROVED"
                return type("R", (), {"payload": {"decision": d, "reason": "ok"}})()

        gw = DevGitHubGateway({1: DevIssue(1, "F", "b", labels={"dev:intake"})})
        with tempfile.TemporaryDirectory() as tmp:
            orch = DevRunOnceOrchestrator(
                gateway=gw,
                log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
                run_registry=DevRunRegistry(),
                intake_adapter=_A(_OK),
                design_adapter=_DesignAdapter(),
                build_adapter=_A(_COMPLETE),
                qa_adapter=_A(_PASSED),
                policy_adapter=_A(_OK),
                max_cycles=5,
            )
            orch.run_once(1)
        self.assertIn("dev:released", gw.get_issue(1).labels)

    def test_circuit_breaker_escalates(self) -> None:
        class _Fail:
            @property
            def adapter_source(self):
                return "stub"

            def invoke_json(self, *a, **kw):
                raise RuntimeError("fail")

        gw = DevGitHubGateway({1: DevIssue(1, "F", "b", labels={"dev:intake"})})
        with tempfile.TemporaryDirectory() as tmp:
            DevRunOnceOrchestrator(
                gateway=gw,
                log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
                run_registry=DevRunRegistry(),
                intake_adapter=_Fail(),
                design_adapter=_Fail(),
                build_adapter=_Fail(),
                qa_adapter=_Fail(),
                policy_adapter=_Fail(),
                retry_policy=RetryPolicy(max_attempts=1),
            ).run_once(1)
        self.assertIn("dev:needs-human", gw.get_issue(1).labels)

    def test_resumes_from_mid_pipeline_state(self) -> None:
        gw = DevGitHubGateway({1: DevIssue(1, "F", "b", labels={"dev:qa"})})
        with tempfile.TemporaryDirectory() as tmp:
            _orch(gw, tmp, intake=_OK, design=_OK, build=_COMPLETE, qa=_PASSED, policy=_OK).run_once(1)
        self.assertIn("dev:released", gw.get_issue(1).labels)

    def test_idempotent_on_terminal_state(self) -> None:
        gw = DevGitHubGateway({1: DevIssue(1, "F", "b", labels={"dev:released"})})
        with tempfile.TemporaryDirectory() as tmp:
            orch = _orch(gw, tmp, intake=_OK, design=_OK, build=_COMPLETE, qa=_PASSED, policy=_OK)
            orch.run_once(1)
            comment_count_1 = len(gw.get_issue(1).comments)
            orch.run_once(1)
            comment_count_2 = len(gw.get_issue(1).comments)
        self.assertEqual(comment_count_1, comment_count_2)


if __name__ == "__main__":
    unittest.main()
