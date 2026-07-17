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


def _gw_no_prior_research(labels):
    """Gateway with no pre-existing research issues and a decision pack with TODO sections.

    Used to test the initial research planning flow where backlog_build_create must invoke
    the LLM and spawn research sub-issues.
    """
    return FoundationGitHubGateway(
        {
            1: FoundationIssue(
                1,
                "Foundation",
                "See docs/adr/0001-runtime.md and https://github.com/owner/repo/wiki/Foundation-Research",
                labels=set(labels),
            ),
        },
        repo_files={
            "docs/foundation-decision-pack.md": (
                "# Foundation Decision Pack\n\n"
                "## 1. Project Overview\nTest project.\n\n"
                "### 2.1 Architecture Topology\n"
                "<!-- TODO: needs research — which topology fits? -->\n"
            )
        },
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
                # research_adapter handles: backlog_build_verify (RECOMMEND) then handoff_pack_verify (passed).
                # backlog_build_create skips re-planning because the test gateway has closed research issues
                # but no decision-pack TODO sections (file doesn't exist in test).
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
                # backlog_build_create skips re-planning both passes because the test gateway has
                # closed research issues but no decision-pack TODO sections (file doesn't exist in test).
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

    def test_backlog_create_invokes_research_plan_when_decision_pack_has_todos(self) -> None:
        """_plan_and_sync_research_areas calls foundation_research_plan when decision pack has TODO sections.

        Validates that:
        - When no research issues exist and the decision pack has TODO sections, the research plan
          LLM is invoked and sub-issues are created.
        - When all research issues are closed but the decision pack has no TODOs, planning is skipped.
        - When there are open research issues, planning is skipped.
        """
        import tempfile as _tf
        from foundation_orchestrator.langgraph_foundation_graph import FoundationGraphOrchestrator

        decision_pack_with_todos = (
            "# Foundation Decision Pack\n\n"
            "## 1. Project Overview\nTest project.\n\n"
            "### 2.1 Architecture Topology\n"
            "<!-- TODO: needs research — which topology fits? -->\n"
        )

        # Case 1: no prior issues, decision pack has TODOs → research plan MUST be invoked
        gw1 = FoundationGitHubGateway(
            {1: FoundationIssue(1, "Foundation", "body", labels={"foundation:needed"})},
        )
        stub = _S({"research_areas": ["Which topology best fits the project?"]})
        with _tf.TemporaryDirectory() as tmp:
            orch = FoundationGraphOrchestrator(
                gw1, TransitionLogStore(f"{tmp}/r.sqlite"), stub, stub
            )
            orch._plan_and_sync_research_areas(1, gw1.get_issue(1), "# FOUNDATION", decision_pack_with_todos)
        self.assertEqual(stub._idx, 1, "research plan LLM should have been called exactly once")
        # A new research issue should have been created
        self.assertGreater(len(gw1.list_linked_research_issues(1)), 0)

        # Case 2: existing research issues are closed, decision pack has no TODOs → skip
        gw2 = FoundationGitHubGateway(
            {
                1: FoundationIssue(1, "Foundation", "body", labels={"foundation:needed"}),
                2: FoundationIssue(2, "research", "body", labels={"foundation:research"}, open=False),
            },
            sub_issues={1: [2]},
        )
        stub2 = _S({"research_areas": ["should not be called"]})
        with _tf.TemporaryDirectory() as tmp:
            orch2 = FoundationGraphOrchestrator(
                gw2, TransitionLogStore(f"{tmp}/r.sqlite"), stub2, stub2
            )
            orch2._plan_and_sync_research_areas(1, gw2.get_issue(1), "# FOUNDATION", "# no todos here")
        self.assertEqual(stub2._idx, 0, "research plan LLM should NOT have been called when no TODOs")

        # Case 3: existing research issues are open → skip (in-flight)
        gw3 = FoundationGitHubGateway(
            {
                1: FoundationIssue(1, "Foundation", "body", labels={"foundation:needed"}),
                2: FoundationIssue(2, "research", "body", labels={"foundation:research"}, open=True),
            },
            sub_issues={1: [2]},
        )
        stub3 = _S({"research_areas": ["should not be called"]})
        with _tf.TemporaryDirectory() as tmp:
            orch3 = FoundationGraphOrchestrator(
                gw3, TransitionLogStore(f"{tmp}/r.sqlite"), stub3, stub3
            )
            orch3._plan_and_sync_research_areas(1, gw3.get_issue(1), "# FOUNDATION", decision_pack_with_todos)
        self.assertEqual(stub3._idx, 0, "research plan LLM should NOT have been called when open issues exist")


if __name__ == "__main__":
    unittest.main()
