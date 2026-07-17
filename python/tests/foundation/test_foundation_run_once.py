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
    """Sequential stub adapter. Cycles through payloads in order, repeating the last."""

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
                "## Decision Area\nruntime/language\n\n## Evidence\nDocumented.",
                labels={"foundation:research"},
                open=False,
            ),
        },
        sub_issues={1: [2]},
    )


class FoundationRunOnceTests(unittest.TestCase):
    def test_full_happy_path_approved(self) -> None:
        """Full run from NEEDED → APPROVED through all 10 phases."""
        gw = _gw({"foundation:needed"})
        with tempfile.TemporaryDirectory() as tmp:
            FoundationRunOnceOrchestrator(
                gateway=gw,
                log_store=TransitionLogStore(f"{tmp}/r.sqlite"),
                run_registry=FoundationRunRegistry(),
                # research_adapter handles: backlog_build_verify (RECOMMEND) then handoff_pack_verify (passed)
                research_adapter=_S(
                    {"decision": "RECOMMEND", "reason": "all closed"},
                    {"passed": True, "verdict": "DISCOVERY-FOCUS.md looks complete"},
                ),
                # gate_adapter handles: intent_capture_verify, shell_design_verify, readiness_assess_verify
                gate_adapter=_S({"decision": "APPROVE_FOUNDATION", "reason": "ok"}),
            ).run_once(1)
        self.assertIn("foundation:approved", gw.get_issue(1).labels)

    def test_research_blocked_terminates(self) -> None:
        """BLOCKED decision at backlog_build_verify should leave issue in foundation:blocked."""
        gw = _gw({"foundation:needed"})
        with tempfile.TemporaryDirectory() as tmp:
            FoundationRunOnceOrchestrator(
                gateway=gw,
                log_store=TransitionLogStore(f"{tmp}/r.sqlite"),
                run_registry=FoundationRunRegistry(),
                research_adapter=_S({"decision": "BLOCKED", "reason": "unresolvable gap"}),
                gate_adapter=_S({"decision": "APPROVE_FOUNDATION", "reason": "ok"}),
            ).run_once(1)
        self.assertIn("foundation:blocked", gw.get_issue(1).labels)

    def test_backlog_revise_then_approve(self) -> None:
        """backlog_build_verify NEEDS_MORE_RESEARCH cycles back to backlog_build_create,
        then RECOMMEND advances to readiness_assess and eventually APPROVED."""
        gw = _gw({"foundation:needed"})
        with tempfile.TemporaryDirectory() as tmp:
            FoundationRunOnceOrchestrator(
                gateway=gw,
                log_store=TransitionLogStore(f"{tmp}/r.sqlite"),
                run_registry=FoundationRunRegistry(),
                # first research call → revise (NEEDS_MORE_RESEARCH), second → approve (RECOMMEND)
                research_adapter=_S(
                    {"decision": "NEEDS_MORE_RESEARCH", "reason": "needs more evidence"},
                    {"decision": "RECOMMEND", "reason": "all good now"},
                    {"passed": True, "verdict": "ok"},
                ),
                gate_adapter=_S({"decision": "APPROVE_FOUNDATION", "reason": "ok"}),
                max_cycles=10,
            ).run_once(1)
        self.assertIn("foundation:approved", gw.get_issue(1).labels)

    def test_circuit_breaker_escalates(self) -> None:
        """Adapter failures should escalate to foundation:needs-human via circuit breaker."""
        class _Fail:
            adapter_source = "stub"
            def invoke_json(self, *a, **kw): raise RuntimeError("fail")

        gw = _gw({"foundation:needed"})
        with tempfile.TemporaryDirectory() as tmp:
            FoundationRunOnceOrchestrator(
                gateway=gw,
                log_store=TransitionLogStore(f"{tmp}/r.sqlite"),
                run_registry=FoundationRunRegistry(),
                research_adapter=_Fail(),
                gate_adapter=_Fail(),
                retry_policy=RetryPolicy(max_attempts=1),
            ).run_once(1)
        self.assertIn("foundation:needs-human", gw.get_issue(1).labels)


if __name__ == "__main__":
    unittest.main()
