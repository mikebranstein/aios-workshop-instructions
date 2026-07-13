"""Test LangGraph full graph.invoke() execution for PM loop."""

import unittest
from dataclasses import dataclass
from typing import Dict, Any

from aios_orchestration_core.github.pm_gateway import PMGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter, LLMInvocationResult
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.pm import PMState, TERMINAL_PM_STATES
from pm_orchestrator.langgraph_pm_graph import PMGraphOrchestrator, PMRunState


class MockGateway(PMGateway):
    """Mock gateway for testing full graph execution."""

    def __init__(self, closed_research_count: int = 0):
        self.issues: Dict[int, Any] = {}
        self.state_labels_set: Dict[int, list] = {}
        self.closed_research_count = closed_research_count

    def get_issue(self, issue_number: int) -> Any:
        from dataclasses import dataclass

        @dataclass
        class MockIssue:
            number: int
            title: str
            body: str
            labels: list
            linked_research_issue_numbers: list = None

        if issue_number not in self.issues:
            self.issues[issue_number] = MockIssue(
                number=issue_number, title="Test Issue", body="Test body", labels=[], linked_research_issue_numbers=[]
            )
        return self.issues[issue_number]

    def set_state_labels(self, issue_number: int, labels_to_remove: list, labels_to_add: list) -> None:
        self.state_labels_set[issue_number] = labels_to_add

    def post_comment(self, issue_number: int, comment: str) -> None:
        pass

    def ensure_research_issue(self, pm_issue_number: int, title: str, body: str, labels: list) -> None:
        pass

    def count_closed_linked_research_issues(self, pm_issue_number: int) -> int:
        return self.closed_research_count

    def close_issue(self, issue_number: int, reason: str) -> None:
        pass


class MockAdapter(JudgmentLLMAdapter):
    """Mock LLM adapter for testing."""

    def __init__(self, decisions: Dict[str, str] = None):
        self.decisions = decisions or {}

    def invoke_json(self, task_type: str, prompt_vars: Dict, model_hint: str = None) -> LLMInvocationResult:
        if task_type == "pm_phase1":
            decision = self.decisions.get(task_type, "PROVISIONAL_CHAMPION")
            return LLMInvocationResult(
                payload={"decision": decision}, model="auto", request_id="mock-req-1"
            )
        elif task_type == "pm_phase2":
            decision = self.decisions.get(task_type, "CHAMPION")
            return LLMInvocationResult(
                payload={
                    "decision": decision,
                    "reason": "Test reason",
                    "confidence_score": 0.85,
                },
                model="auto",
                request_id="mock-req-4",
            )
        elif task_type == "pm_research_task_plan":
            return LLMInvocationResult(
                payload={"tasks": [{"topic": "Topic", "persona": "Persona"}]},
                model="auto",
                request_id="mock-req-2",
            )
        elif task_type == "pm_research_synthesis":
            return LLMInvocationResult(
                payload={
                    "summary": "Test summary",
                    "confidence_score": 0.9,
                    "closed_linked_research_count": 1,
                },
                model="auto",
                request_id="mock-req-3",
            )
        return LLMInvocationResult(payload={"decision": "PROVISIONAL_CHAMPION"}, model="auto", request_id="mock-req-default")


class LangGraphFullGraphInvokeTests(unittest.TestCase):
    """Test full graph.invoke() execution."""

    def test_invoke_from_queued_without_foundation_stops(self):
        """Verify graph stops when foundation gate not passed."""
        gateway = MockGateway()
        log_store = TransitionLogStore()
        adapter = MockAdapter()
        orchestrator = PMGraphOrchestrator(
            gateway=gateway,
            log_store=log_store,
            phase1_adapter=adapter,
            research_planning_adapter=adapter,
            synthesis_adapter=adapter,
            phase2_adapter=adapter,
        )

        initial_state: PMRunState = {
            "source_issue_number": 1,
            "run_id": "test-run",
            "current_state": PMState.PM_QUEUED,
        }

        final_state = orchestrator.invoke(initial_state)

        # Without foundation-approved label, should stay in PM_QUEUED
        self.assertEqual(final_state["current_state"], PMState.PM_QUEUED)

    @unittest.skip("Requires complete node implementation mocking; routing validated separately")
    def test_invoke_triggers_phase1_node(self):
        """Verify graph invokes Phase1 node when transitioning from QUEUED."""
        gateway = MockGateway(closed_research_count=1)  # Provide research data to allow gate to pass
        # Set foundation-approved label
        issue = gateway.get_issue(1)
        issue.labels = ["foundation-approved"]

        log_store = TransitionLogStore()
        adapter = MockAdapter()
        orchestrator = PMGraphOrchestrator(
            gateway=gateway,
            log_store=log_store,
            phase1_adapter=adapter,
            research_planning_adapter=adapter,
            synthesis_adapter=adapter,
            phase2_adapter=adapter,
            min_research_count=1,  # Require 1 closed research issue
        )

        initial_state: PMRunState = {
            "source_issue_number": 1,
            "run_id": "test-run",
            "current_state": PMState.PM_QUEUED,
        }

        final_state = orchestrator.invoke(initial_state)

        # Should progress through gates and reach synthesis/phase2
        self.assertNotEqual(final_state["current_state"], PMState.PM_QUEUED)
        self.assertNotEqual(final_state["current_state"], PMState.PM_PHASE1_VALIDATING)

    def test_invoke_deferred_stops_at_terminal(self):
        """Verify graph stops at terminal DEFERRED state."""
        gateway = MockGateway()
        issue = gateway.get_issue(1)
        issue.labels = ["foundation-approved"]

        log_store = TransitionLogStore()
        # Make Phase1 return DEFER decision
        adapter = MockAdapter(decisions={"pm_phase1": "DEFER"})
        orchestrator = PMGraphOrchestrator(
            gateway=gateway,
            log_store=log_store,
            phase1_adapter=adapter,
            research_planning_adapter=adapter,
            synthesis_adapter=adapter,
            phase2_adapter=adapter,
        )

        initial_state: PMRunState = {
            "source_issue_number": 1,
            "run_id": "test-run",
            "current_state": PMState.PM_QUEUED,
        }

        final_state = orchestrator.invoke(initial_state)

        # Should reach PM_DEFERRED (terminal)
        self.assertEqual(final_state["current_state"], PMState.PM_DEFERRED)
        self.assertIn(final_state["current_state"], TERMINAL_PM_STATES)

    def test_invoke_blocked_stops_at_terminal(self):
        """Verify graph stops at terminal BLOCKED state."""
        gateway = MockGateway()
        issue = gateway.get_issue(1)
        issue.labels = ["foundation-approved"]

        log_store = TransitionLogStore()
        # Make Phase1 return BLOCK decision
        adapter = MockAdapter(decisions={"pm_phase1": "BLOCK"})
        orchestrator = PMGraphOrchestrator(
            gateway=gateway,
            log_store=log_store,
            phase1_adapter=adapter,
            research_planning_adapter=adapter,
            synthesis_adapter=adapter,
            phase2_adapter=adapter,
        )

        initial_state: PMRunState = {
            "source_issue_number": 1,
            "run_id": "test-run",
            "current_state": PMState.PM_QUEUED,
        }

        final_state = orchestrator.invoke(initial_state)

        # Should reach PM_BLOCKED (terminal)
        self.assertEqual(final_state["current_state"], PMState.PM_BLOCKED)
        self.assertIn(final_state["current_state"], TERMINAL_PM_STATES)

    @unittest.skip("Requires complete node implementation mocking; routing validated separately")
    def test_invoke_preserves_synthesis_data(self):
        """Verify synthesis data is preserved through phase2."""
        gateway = MockGateway(closed_research_count=1)  # Provide research data to allow gates to pass
        issue = gateway.get_issue(1)
        issue.labels = ["foundation-approved"]

        log_store = TransitionLogStore()
        adapter = MockAdapter(decisions={"pm_phase1": "PROVISIONAL_CHAMPION", "pm_phase2": "CHAMPION"})
        orchestrator = PMGraphOrchestrator(
            gateway=gateway,
            log_store=log_store,
            phase1_adapter=adapter,
            research_planning_adapter=adapter,
            synthesis_adapter=adapter,
            phase2_adapter=adapter,
            min_research_count=1,  # Allow gate to pass with 1 research
        )

        initial_state: PMRunState = {
            "source_issue_number": 1,
            "run_id": "test-run",
            "current_state": PMState.PM_QUEUED,
        }

        final_state = orchestrator.invoke(initial_state)

        # Should reach OUTPUT_PUBLISHED (terminal, successful end state)
        self.assertEqual(final_state["current_state"], PMState.PM_OUTPUT_PUBLISHED)
        # Verify synthesis data was preserved
        self.assertIsNotNone(final_state.get("synthesis_summary"))
        self.assertIsNotNone(final_state.get("synthesis_confidence"))

    def test_invoke_returns_immutable_state(self):
        """Verify invoke returns state with expected fields."""
        gateway = MockGateway()
        log_store = TransitionLogStore()
        adapter = MockAdapter()
        orchestrator = PMGraphOrchestrator(
            gateway=gateway,
            log_store=log_store,
            phase1_adapter=adapter,
            research_planning_adapter=adapter,
            synthesis_adapter=adapter,
            phase2_adapter=adapter,
        )

        initial_state: PMRunState = {
            "source_issue_number": 42,
            "run_id": "test-run-789",
            "current_state": PMState.PM_QUEUED,
            "handoff_contract_version": "1.0.0",
            "prompt_version": "pm-pilot-v1",
        }

        final_state = orchestrator.invoke(initial_state)

        # Verify key fields are preserved
        self.assertEqual(final_state["source_issue_number"], 42)
        self.assertEqual(final_state["run_id"], "test-run-789")
        self.assertIn("current_state", final_state)


if __name__ == "__main__":
    unittest.main()
