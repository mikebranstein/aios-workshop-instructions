"""Test LangGraph node wrappers for PM loop."""

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
        self.comments: Dict[int, list] = {}

    def get_issue(self, issue_number: int) -> Any:
        @dataclass
        class MockIssue:
            number: int
            title: str
            body: str
            labels: list
            linked_research_issue_numbers: list = None

        if issue_number not in self.issues:
            self.issues[issue_number] = MockIssue(
                number=issue_number, title="Test", body="Body", labels=[], linked_research_issue_numbers=[]
            )
        return self.issues[issue_number]

    def set_state_labels(self, issue_number: int, labels_to_remove: list, labels_to_add: list) -> None:
        pass

    def post_comment(self, issue_number: int, comment: str) -> None:
        if issue_number not in self.comments:
            self.comments[issue_number] = []
        self.comments[issue_number].append(comment)

    def ensure_research_issue(self, pm_issue_number: int, title: str, body: str, labels: list) -> None:
        pass

    def count_closed_linked_research_issues(self, pm_issue_number: int) -> int:
        return 0

    def close_issue(self, issue_number: int, reason: str) -> None:
        pass


class MockAdapter(JudgmentLLMAdapter):
    """Mock LLM adapter for testing."""

    def invoke_json(self, task_type: str, prompt_vars: Dict, model_hint: str = None) -> LLMInvocationResult:
        if task_type == "pm_phase1":
            return LLMInvocationResult(
                payload={"decision": "PROVISIONAL_CHAMPION"}, model="auto", request_id="mock-req-1"
            )
        elif task_type == "pm_research_task_plan":
            return LLMInvocationResult(
                payload={"tasks": [{"topic": "Topic 1", "persona": "Persona 1"}]},
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
        elif task_type == "pm_phase2":
            return LLMInvocationResult(
                payload={
                    "decision": "CHAMPION",
                    "reason": "This is a good opportunity",
                    "confidence_score": 0.85,
                },
                model="auto",
                request_id="mock-req-4",
            )
        return LLMInvocationResult(payload={"decision": "PROVISIONAL_CHAMPION"}, model="auto", request_id="mock-req-default")


class LangGraphNodeWrapperTests(unittest.TestCase):
    """Test individual node wrappers."""

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

    def test_phase1_wrapper_transitions_state(self):
        """Verify Phase1 node wrapper transitions to next state."""
        initial_state: PMRunState = {
            "source_issue_number": 1,
            "run_id": "test-run",
            "current_state": PMState.PM_PHASE1_VALIDATING,
        }

        result = self.orchestrator._node_phase1_wrapper(initial_state)

        self.assertEqual(result["current_state"], PMState.PM_RESEARCH_PLANNING)

    def test_research_planning_wrapper_transitions_state(self):
        """Verify research planning node wrapper transitions state."""
        initial_state: PMRunState = {
            "source_issue_number": 1,
            "run_id": "test-run",
            "current_state": PMState.PM_RESEARCH_PLANNING,
        }

        result = self.orchestrator._node_research_planning_wrapper(initial_state)

        self.assertEqual(result["current_state"], PMState.PM_RESEARCH_WAITING)

    def test_research_closure_gate_wrapper_stays_waiting(self):
        """Verify research closure gate keeps state if not ready."""
        initial_state: PMRunState = {
            "source_issue_number": 1,
            "run_id": "test-run",
            "current_state": PMState.PM_RESEARCH_WAITING,
        }

        result = self.orchestrator._node_research_closure_gate_wrapper(initial_state)

        # With 0 closed research issues (mock), gate is not ready
        self.assertEqual(result["current_state"], PMState.PM_RESEARCH_WAITING)

    def test_synthesis_wrapper_stores_synthesis_data(self):
        """Verify synthesis node wrapper stores summary and confidence."""
        initial_state: PMRunState = {
            "source_issue_number": 1,
            "run_id": "test-run",
            "current_state": PMState.PM_RESEARCH_SYNTHESIZING,
        }

        result = self.orchestrator._node_synthesis_wrapper(initial_state)

        self.assertIn("synthesis_summary", result)
        self.assertIn("synthesis_confidence", result)
        self.assertEqual(result["synthesis_summary"], "Test summary")
        self.assertEqual(result["synthesis_confidence"], 0.9)

    def test_phase2_wrapper_transitions_to_published(self):
        """Verify Phase2 node wrapper transitions to terminal state."""
        initial_state: PMRunState = {
            "source_issue_number": 1,
            "run_id": "test-run",
            "current_state": PMState.PM_PHASE2_VALIDATING,
            "synthesis_summary": "Test summary",
            "synthesis_confidence": 0.9,
        }

        result = self.orchestrator._node_phase2_wrapper(initial_state)

        self.assertEqual(result["current_state"], PMState.PM_OUTPUT_PUBLISHED)

    def test_node_wrapper_preserves_run_id(self):
        """Verify node wrappers preserve run_id through state."""
        initial_state: PMRunState = {
            "source_issue_number": 1,
            "run_id": "specific-run-id",
            "current_state": PMState.PM_PHASE1_VALIDATING,
        }

        result = self.orchestrator._node_phase1_wrapper(initial_state)

        self.assertEqual(result["run_id"], "specific-run-id")


if __name__ == "__main__":
    unittest.main()
