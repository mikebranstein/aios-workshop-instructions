import tempfile
import unittest

from aios_orchestration_core.github.foundation_gateway import (
    FoundationGitHubGateway,
    FoundationIssue,
)
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.foundation import FoundationState
from foundation_orchestrator.run_once import FoundationRunOnceOrchestrator, FoundationRunRegistry


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


def _gw(labels):
    return FoundationGitHubGateway(
        {
            1: FoundationIssue(
                1,
                "Foundation",
                "See docs/adr/0001-runtime.md and https://github.com/owner/repo/wiki/Foundation-Research",
                labels=set(labels),
            ),
            2: FoundationIssue(
                2,
                "[foundation-research] closed evidence",
                "Evidence captured",
                labels={"foundation:research", "foundation-source-1"},
                open=False,
            ),
        },
    )


class FoundationRunOnceTests(unittest.TestCase):
    def test_full_happy_path_approved(self) -> None:
        gw = _gw({"foundation:needed"})
        with tempfile.TemporaryDirectory() as tmp:
            FoundationRunOnceOrchestrator(
                gateway=gw, log_store=TransitionLogStore(f"{tmp}/r.sqlite"),
                run_registry=FoundationRunRegistry(),
                research_adapter=_S({"decision": "RECOMMEND", "reason": "ok"}),
                gate_adapter=_S({"decision": "APPROVE_FOUNDATION", "reason": "ok"}),
            ).run_once(1)
        self.assertIn("foundation:approved", gw.get_issue(1).labels)

    def test_research_blocked_terminates(self) -> None:
        gw = _gw({"foundation:needed"})
        with tempfile.TemporaryDirectory() as tmp:
            FoundationRunOnceOrchestrator(
                gateway=gw, log_store=TransitionLogStore(f"{tmp}/r.sqlite"),
                run_registry=FoundationRunRegistry(),
                research_adapter=_S({"decision": "BLOCKED", "reason": "issue"}),
                gate_adapter=_S({"decision": "APPROVE_FOUNDATION", "reason": "ok"}),
            ).run_once(1)
        self.assertIn("foundation:blocked", gw.get_issue(1).labels)

    def test_revise_then_approve(self) -> None:
        gw = _gw({"foundation:needed"})
        with tempfile.TemporaryDirectory() as tmp:
            FoundationRunOnceOrchestrator(
                gateway=gw, log_store=TransitionLogStore(f"{tmp}/r.sqlite"),
                run_registry=FoundationRunRegistry(),
                research_adapter=_S({"decision": "RECOMMEND", "reason": "ok"}),
                gate_adapter=_S(
                    {"decision": "REVISE_FOUNDATION", "reason": "gaps"},
                    {"decision": "APPROVE_FOUNDATION", "reason": "ok now"},
                ),
                max_cycles=5,
            ).run_once(1)
        self.assertIn("foundation:approved", gw.get_issue(1).labels)

    def test_circuit_breaker_escalates(self) -> None:
        class _Fail:
            def invoke_json(self, *a, **kw): raise RuntimeError("fail")

        gw = _gw({"foundation:needed"})
        with tempfile.TemporaryDirectory() as tmp:
            FoundationRunOnceOrchestrator(
                gateway=gw, log_store=TransitionLogStore(f"{tmp}/r.sqlite"),
                run_registry=FoundationRunRegistry(),
                research_adapter=_Fail(), gate_adapter=_Fail(),
                retry_policy=RetryPolicy(max_attempts=1),
            ).run_once(1)
        self.assertIn("foundation:needs-human", gw.get_issue(1).labels)


if __name__ == "__main__":
    unittest.main()
