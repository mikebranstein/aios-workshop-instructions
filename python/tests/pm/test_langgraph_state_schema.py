"""Test LangGraph StateGraph and node wrappers for PM loop."""

import unittest
from dataclasses import dataclass
from typing import Dict, Any

from aios_orchestration_core.github.pm_gateway import PMGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter, LLMInvocationResult
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.pm import PMState
from pm_orchestrator.langgraph_pm_graph import PMGraphOrchestrator, PMRunState


class MockGateway(PMGateway):
    """Mock gateway for testing."""

    def __init__(self):
        self.issues: Dict[int, Any] = {}

    def get_issue(self, issue_number: int) -> Any:
        """Return a mock issue."""
        from dataclasses import dataclass

        @dataclass
        class MockIssue:
            number: int
            title: str
            body: str
            labels: list

        if issue_number not in self.issues:
            self.issues[issue_number] = MockIssue(
                number=issue_number, title="Test Issue", body="Test body", labels=[]
            )
        return self.issues[issue_number]

    def set_state_labels(self, issue_number: int, labels_to_remove: list, labels_to_add: list) -> None:
        pass

    def post_comment(self, issue_number: int, comment: str) -> None:
        pass

    def ensure_research_issue(
        self, pm_issue_number: int, title: str, body: str, labels: list
    ) -> None:
        pass

    def count_closed_linked_research_issues(self, pm_issue_number: int) -> int:
        return 0

    def close_issue(self, issue_number: int, reason: str) -> None:
        pass


class MockAdapter(JudgmentLLMAdapter):
    """Mock LLM adapter for testing."""

    def invoke_json(
        self, task_type: str, prompt_vars: Dict, model_hint: str = None
    ) -> LLMInvocationResult:
        """Return a mock result with forced tool call."""
        if task_type == "pm_phase1":
            return LLMInvocationResult(
                payload={"decision": "PROVISIONAL_CHAMPION"}, model="copilot-standard", request_id="mock-req-1"
            )
        elif task_type == "pm_research_task_plan":
            return LLMInvocationResult(
                payload={"tasks": [{"topic": "Test Topic", "persona": "Test Persona"}]},
                model="copilot-standard",
                request_id="mock-req-2",
            )
        elif task_type == "pm_research_synthesis":
            return LLMInvocationResult(
                payload={
                    "summary": "Test summary",
                    "confidence_score": 0.9,
                    "closed_linked_research_count": 1,
                },
                model="copilot-standard",
                request_id="mock-req-3",
            )
        elif task_type == "pm_phase2_decision":
            return LLMInvocationResult(
                payload={"decision": "CHAMPION"}, model="copilot-standard", request_id="mock-req-4"
            )
        return LLMInvocationResult(payload={}, model="copilot-standard", request_id="mock-req-default")


class LangGraphGraphTests(unittest.TestCase):
    """Test LangGraph StateGraph structure and invocation."""

    def setUp(self):
        self.gateway = MockGateway()
        self.log_store = TransitionLogStore()
        self.adapter = MockAdapter()
        self.orchestrator = PMGraphOrchestrator(
            gateway=self.gateway,
            log_store=self.log_store,
            phase1_adapter=self.adapter,
            research_planning_adapter=self.adapter,
            synthesis_adapter=self.adapter,
            phase2_adapter=self.adapter,
        )

    def test_graph_exists(self):
        """Verify graph is created."""
        self.assertIsNotNone(self.orchestrator._graph)

    def test_invoke_returns_state_dict(self):
        """Verify graph.invoke() returns a state dict."""
        initial_state: PMRunState = {
            "source_issue_number": 1,
            "run_id": "test-run-123",
            "current_state": PMState.PM_QUEUED,
            "handoff_contract_version": "1.0.0",
            "prompt_version": "pm-pilot-v1",
        }

        final_state = self.orchestrator.invoke(initial_state)

        self.assertIsInstance(final_state, dict)
        self.assertIn("current_state", final_state)

    def test_invoke_preserves_issue_number(self):
        """Verify issue_number is preserved through graph."""
        initial_state: PMRunState = {
            "source_issue_number": 42,
            "run_id": "test-run-123",
            "current_state": PMState.PM_QUEUED,
        }

        final_state = self.orchestrator.invoke(initial_state)

        self.assertEqual(final_state.get("source_issue_number"), 42)

    def test_normalize_and_route_entry_point(self):
        """Verify entry point normalizes state correctly."""
        # Set up mock issue with foundation-approved label
        issue = self.gateway.get_issue(1)
        issue.labels = ["foundation-approved"]

        initial_state: PMRunState = {
            "source_issue_number": 1,
            "run_id": "test-run-123",
            "current_state": PMState.PM_QUEUED,
        }

        # Manually test the entry node
        state = self.orchestrator._node_normalize_and_route(initial_state)
        self.assertEqual(state["current_state"], PMState.PM_QUEUED)

    def test_router_returns_string_or_end(self):
        """Verify router returns valid node name or END."""
        from langgraph.graph import END

        # Test terminal state
        state_terminal: PMRunState = {
            "source_issue_number": 1,
            "run_id": "test-run-123",
            "current_state": PMState.PM_OUTPUT_PUBLISHED,
        }
        result = self.orchestrator._router_from_state(state_terminal)
        self.assertEqual(result, END)

        # Test active state
        state_active: PMRunState = {
            "source_issue_number": 1,
            "run_id": "test-run-123",
            "current_state": PMState.PM_PHASE1_VALIDATING,
        }
        result = self.orchestrator._router_from_state(state_active)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, END)


if __name__ == "__main__":
    unittest.main()
