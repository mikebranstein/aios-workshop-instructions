"""Test LangGraph conditional edges and routing for PM loop."""

import unittest
from typing import Dict, Any

from aios_orchestration_core.github.pm_gateway import PMGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter, LLMInvocationResult
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.pm import PMState, TERMINAL_PM_STATES
from pm_orchestrator.langgraph_pm_graph import PMGraphOrchestrator, PMRunState
from langgraph.graph import END


class MockGateway(PMGateway):
    """Mock gateway for testing."""

    def __init__(self):
        self.issues: Dict[int, Any] = {}

    def get_issue(self, issue_number: int) -> Any:
        from dataclasses import dataclass

        @dataclass
        class MockIssue:
            number: int
            title: str
            body: str
            labels: list

        if issue_number not in self.issues:
            self.issues[issue_number] = MockIssue(
                number=issue_number, title="Test", body="Body", labels=[]
            )
        return self.issues[issue_number]

    def set_state_labels(self, issue_number: int, labels_to_remove: list, labels_to_add: list) -> None:
        pass

    def post_comment(self, issue_number: int, comment: str) -> None:
        pass

    def ensure_research_issue(self, pm_issue_number: int, title: str, body: str, labels: list) -> None:
        pass

    def count_closed_linked_research_issues(self, pm_issue_number: int) -> int:
        return 0

    def close_issue(self, issue_number: int, reason: str) -> None:
        pass


class MockAdapter(JudgmentLLMAdapter):
    def invoke_json(self, task_type: str, prompt_vars: Dict, model_hint: str = None) -> LLMInvocationResult:
        return LLMInvocationResult(payload={"decision": "PROVISIONAL_CHAMPION"}, model="copilot-standard", request_id="mock-req")


class LangGraphConditionalEdgesTests(unittest.TestCase):
    """Test routing logic via conditional edges."""

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

    def test_route_foundation_gate_returns_end_for_terminal_states(self):
        """Verify router returns END for all terminal states."""
        for terminal_state in TERMINAL_PM_STATES:
            state: PMRunState = {
                "source_issue_number": 1,
                "current_state": terminal_state,
            }
            result = self.orchestrator._route_foundation_gate(state)
            self.assertEqual(result, END, f"Failed for terminal state: {terminal_state}")

    def test_route_foundation_gate_to_phase1(self):
        """Verify router routes to phase1 when in PHASE1_VALIDATING."""
        state: PMRunState = {
            "source_issue_number": 1,
            "current_state": PMState.PM_PHASE1_VALIDATING,
        }
        result = self.orchestrator._route_foundation_gate(state)
        self.assertEqual(result, "phase1")

    def test_route_phase1_to_research_planning(self):
        """Verify router routes to research_planning when in RESEARCH_PLANNING."""
        state: PMRunState = {
            "source_issue_number": 1,
            "current_state": PMState.PM_RESEARCH_PLANNING,
        }
        result = self.orchestrator._route_phase1(state)
        self.assertEqual(result, "research_planning")

    def test_route_research_planning_to_closure_gate(self):
        """Verify router routes to research_closure_gate when in RESEARCH_WAITING."""
        state: PMRunState = {
            "source_issue_number": 1,
            "current_state": PMState.PM_RESEARCH_WAITING,
        }
        result = self.orchestrator._route_research_planning(state)
        self.assertEqual(result, "research_closure_gate")

    def test_route_research_closure_gate_synthesis(self):
        """Verify router routes to synthesis when in RESEARCH_SYNTHESIZING (gate passed)."""
        state: PMRunState = {
            "source_issue_number": 1,
            "current_state": PMState.PM_RESEARCH_SYNTHESIZING,
        }
        result = self.orchestrator._route_research_closure_gate(state)
        self.assertEqual(result, "synthesis")

    def test_route_research_closure_gate_loop_back(self):
        """Verify router routes back to research_planning when in RESEARCH_WAITING (gate not passed)."""
        state: PMRunState = {
            "source_issue_number": 1,
            "current_state": PMState.PM_RESEARCH_WAITING,
        }
        result = self.orchestrator._route_research_closure_gate(state)
        self.assertEqual(result, "research_planning")

    def test_route_synthesis_to_phase2(self):
        """Verify router routes to phase2 when in PHASE2_VALIDATING."""
        state: PMRunState = {
            "source_issue_number": 1,
            "current_state": PMState.PM_PHASE2_VALIDATING,
        }
        result = self.orchestrator._route_synthesis(state)
        self.assertEqual(result, "phase2")

    def test_route_normalize_queued_to_foundation_gate(self):
        """Verify router from normalize directs to foundation_gate for QUEUED state."""
        state: PMRunState = {
            "current_state": PMState.PM_QUEUED,
        }
        result = self.orchestrator._route_normalize_and_route(state)
        self.assertEqual(result, "foundation_gate")

    def test_route_normalize_returns_end_for_terminal(self):
        """Verify router from normalize returns END for terminal states."""
        for terminal_state in TERMINAL_PM_STATES:
            state: PMRunState = {
                "current_state": terminal_state,
            }
            result = self.orchestrator._route_normalize_and_route(state)
            self.assertEqual(result, END, f"Failed for terminal state: {terminal_state}")

    def test_router_respects_transition_table(self):
        """Verify router delegates to transition table semantics."""
        # Phase1 can transition to:
        # - RESEARCH_PLANNING (via PHASE1_PROVISIONAL_CHAMPION)
        # - DEFERRED (via PHASE1_DEFER)
        # - BLOCKED (via PHASE1_BLOCK)
        # All of which are valid next nodes or END

        # Test routing from normalize_and_route entry point
        test_cases = [
            (PMState.PM_RESEARCH_PLANNING, "research_planning"),
            (PMState.PM_DEFERRED, END),
            (PMState.PM_BLOCKED, END),
        ]
        
        for state_value, expected_result in test_cases:
            state: PMRunState = {
                "current_state": state_value,
            }
            result = self.orchestrator._route_normalize_and_route(state)
            self.assertEqual(
                result,
                expected_result,
                f"Router returned {result} for state {state_value}, expected {expected_result}",
            )


if __name__ == "__main__":
    unittest.main()
