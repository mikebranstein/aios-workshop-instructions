import tempfile
import unittest

from aios_orchestration_core.github.arch_review_gateway import ArchReviewGitHubGateway, ArchReviewIssue
from aios_orchestration_core.github.dev_gateway import DevGitHubGateway, DevIssue
from aios_orchestration_core.github.discovery_gateway import DiscoveryInMemoryGateway
from aios_orchestration_core.github.foundation_gateway import FoundationGitHubGateway, FoundationIssue
from aios_orchestration_core.github.pm_gateway import PMGitHubGateway, PMIssue
from aios_orchestration_core.github.po_gateway import POGitHubGateway, POIssue
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from arch_review_orchestrator.run_once import ArchReviewRunOnceOrchestrator, ArchReviewRunRegistry
from dev_orchestrator.run_once import DevRunOnceOrchestrator, DevRunRegistry
from discovery_orchestrator.context import DiscoveryContext
from discovery_orchestrator.run_once import DiscoveryRunOnceOrchestrator, DiscoveryRunRegistry
from foundation_orchestrator.run_once import FoundationRunOnceOrchestrator, FoundationRunRegistry
from pm_orchestrator.run_once import PMRunOnceOrchestrator, PMRunRegistry
from po_orchestrator.run_once import PORunOnceOrchestrator, PORunRegistry


class _FailingAdapter:
    def __init__(self, message: str):
        self._message = message

    @property
    def adapter_source(self) -> str:
        return "stub"

    def invoke_json(self, task_type, prompt_vars, model_hint=""):
        raise RuntimeError(self._message)


class LoopExceptionEscalationTests(unittest.TestCase):
    def _assert_retry_threshold_entry(self, store: TransitionLogStore, loop_id: str, expected_error_fragment: str) -> None:
        entries = [e for e in store.all() if e.loop_id == loop_id]
        self.assertTrue(entries, f"Expected at least one transition entry for loop={loop_id}")
        last = entries[-1]
        self.assertIn("RUN_ONCE", last.reason_code)
        self.assertIn(expected_error_fragment, last.reason_detail)
        self.assertIn("last_error_class=RuntimeError", last.reason_detail)

    def test_pm_node_exception_escalates_with_logged_reason(self) -> None:
        gateway = PMGitHubGateway({1: PMIssue(1, "Idea", "body", labels={"pm:phase1-validating"})})
        with tempfile.TemporaryDirectory() as tmp:
            store = TransitionLogStore(f"{tmp}/pm.sqlite")
            PMRunOnceOrchestrator(
                gateway=gateway,
                log_store=store,
                run_registry=PMRunRegistry(),
                phase1_adapter=_FailingAdapter("pm generic node failure"),
                research_planning_adapter=_FailingAdapter("unused"),
                synthesis_adapter=_FailingAdapter("unused"),
                phase2_adapter=_FailingAdapter("unused"),
                retry_policy=RetryPolicy(max_attempts=1),
            ).run_once(1)
        self.assertIn("pm:needs-human", gateway.get_issue(1).labels)
        self._assert_retry_threshold_entry(store, "pm", "pm generic node failure")

    def test_po_node_exception_escalates_with_logged_reason(self) -> None:
        gateway = POGitHubGateway({1: POIssue(1, "Opportunity", "body", labels={"po:prioritizing"})})
        with tempfile.TemporaryDirectory() as tmp:
            store = TransitionLogStore(f"{tmp}/po.sqlite")
            PORunOnceOrchestrator(
                gateway=gateway,
                log_store=store,
                run_registry=PORunRegistry(),
                prioritize_adapter=_FailingAdapter("po generic node failure"),
                create_features_adapter=_FailingAdapter("unused"),
                retry_policy=RetryPolicy(max_attempts=1),
            ).run_once(1)
        self.assertIn("po:needs-human", gateway.get_issue(1).labels)
        self._assert_retry_threshold_entry(store, "po", "po generic node failure")

    def test_dev_node_exception_escalates_with_logged_reason(self) -> None:
        gateway = DevGitHubGateway({1: DevIssue(1, "Feature", "body", labels={"dev:design"})})
        with tempfile.TemporaryDirectory() as tmp:
            store = TransitionLogStore(f"{tmp}/dev.sqlite")
            DevRunOnceOrchestrator(
                gateway=gateway,
                log_store=store,
                run_registry=DevRunRegistry(),
                intake_adapter=_FailingAdapter("unused"),
                design_adapter=_FailingAdapter("dev generic node failure"),
                build_adapter=_FailingAdapter("unused"),
                qa_adapter=_FailingAdapter("unused"),
                policy_adapter=_FailingAdapter("unused"),
                retry_policy=RetryPolicy(max_attempts=1),
            ).run_once(1)
        self.assertIn("dev:needs-human", gateway.get_issue(1).labels)
        self._assert_retry_threshold_entry(store, "dev", "dev generic node failure")

    def test_foundation_node_exception_escalates_with_logged_reason(self) -> None:
        gateway = FoundationGitHubGateway({1: FoundationIssue(1, "Foundation", "body", labels={"foundation:review"})})
        with tempfile.TemporaryDirectory() as tmp:
            store = TransitionLogStore(f"{tmp}/foundation.sqlite")
            FoundationRunOnceOrchestrator(
                gateway=gateway,
                log_store=store,
                run_registry=FoundationRunRegistry(),
                research_adapter=_FailingAdapter("unused"),
                gate_adapter=_FailingAdapter("foundation generic node failure"),
                retry_policy=RetryPolicy(max_attempts=1),
            ).run_once(1)
        self.assertIn("foundation:needs-human", gateway.get_issue(1).labels)
        self._assert_retry_threshold_entry(store, "foundation", "foundation generic node failure")

    def test_arch_review_node_exception_escalates_with_logged_reason(self) -> None:
        gateway = ArchReviewGitHubGateway({1: ArchReviewIssue(1, "Arch", "body", labels={"arch:review-in-progress"})})
        with tempfile.TemporaryDirectory() as tmp:
            store = TransitionLogStore(f"{tmp}/arch.sqlite")
            ArchReviewRunOnceOrchestrator(
                gateway=gateway,
                log_store=store,
                run_registry=ArchReviewRunRegistry(),
                review_adapter=_FailingAdapter("arch generic node failure"),
                planner_adapter=_FailingAdapter("unused"),
                retry_policy=RetryPolicy(max_attempts=1),
            ).run_once(1)
        self.assertIn("arch:needs-human", gateway.get_issue(1).labels)
        self._assert_retry_threshold_entry(store, "arch_review", "arch generic node failure")

    def test_discovery_node_exception_halts_with_logged_reason(self) -> None:
        context = DiscoveryContext(
            foundation_gate_passed=True,
            focus_file_exists=True,
            focus_file_populated=True,
            discovery_focus_approved=True,
        )
        gateway = DiscoveryInMemoryGateway(context=context, focus_content="# Focus")
        failing_llm = _FailingAdapter("discovery generic node failure")
        with tempfile.TemporaryDirectory() as tmp:
            store = TransitionLogStore(f"{tmp}/discovery.sqlite")
            result = DiscoveryRunOnceOrchestrator(
                gateway=gateway,
                llm_adapter=failing_llm,
                run_registry=DiscoveryRunRegistry(),
                log_store=store,
                retry_policy=RetryPolicy(max_attempts=1),
            ).run()
        self.assertIn(result.state, {"DISCOVERY_HALTED_NEEDS_HUMAN", "DISCOVERY_HALTED_NO_GATE"})
        entries = [e for e in store.all() if e.loop_id == "discovery"]
        self.assertTrue(entries, "Expected discovery transition log entry on exception")
        last = entries[-1]
        self.assertEqual(last.reason_code, "RUN_ONCE_NODE_FAILURE")
        self.assertIn("discovery generic node failure", last.reason_detail)
        self.assertIn("last_error_class=RuntimeError", last.reason_detail)


if __name__ == "__main__":
    unittest.main()
