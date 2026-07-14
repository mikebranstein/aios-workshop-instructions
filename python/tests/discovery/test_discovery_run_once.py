import unittest

from aios_orchestration_core.events.discovery import DiscoveryEvent
from aios_orchestration_core.github.discovery_gateway import DiscoveryInMemoryGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter, LLMInvocationResult
from aios_orchestration_core.states.discovery import DiscoveryState, TERMINAL_DISCOVERY_STATES
from aios_orchestration_core.transitions.discovery import (
    DiscoveryTransitionError,
    allowed_events_for_discovery_state,
    get_next_discovery_state,
)
from discovery_orchestrator.context import DiscoveryContext
from discovery_orchestrator.run_once import DiscoveryRunOnceOrchestrator


# ---------------------------------------------------------------------------
# Stub LLM adapter for discovery tests
# ---------------------------------------------------------------------------

class StubDiscoveryLLMAdapter(JudgmentLLMAdapter):
    """Returns a fixed list of candidates for discovery_idea_scout invocations."""

    def __init__(self, candidates: list):
        self._candidates = candidates

    @property
    def adapter_source(self) -> str:
        return "stub"

    def invoke_json(self, task_type: str, prompt_vars: dict, model_hint: str = "") -> LLMInvocationResult:
        if task_type == "discovery_idea_scout":
            creation_cap = prompt_vars.get("creation_cap", 3)
            return LLMInvocationResult(
                payload={"candidates": self._candidates[:creation_cap]},
                model="stub",
                request_id="stub",
            )
        return LLMInvocationResult(payload={}, model="stub", request_id="stub")


def _make_gateway(*, gate: bool = True, focus: bool = True, focus_content: str = "# Focus") -> DiscoveryInMemoryGateway:
    ctx = DiscoveryContext(
        foundation_gate_passed=gate,
        focus_file_exists=focus,
        focus_file_populated=focus,
    )
    return DiscoveryInMemoryGateway(context=ctx, focus_content=focus_content if focus else "")


def _make_orchestrator(candidates: list, *, gate: bool = True, focus: bool = True, cap: int = 3) -> DiscoveryRunOnceOrchestrator:
    gateway = _make_gateway(gate=gate, focus=focus)
    adapter = StubDiscoveryLLMAdapter(candidates)
    return DiscoveryRunOnceOrchestrator(gateway=gateway, llm_adapter=adapter, creation_cap=cap)


# ---------------------------------------------------------------------------
# Contract tests (state machine)
# ---------------------------------------------------------------------------

class DiscoveryContractsTests(unittest.TestCase):
    def test_terminal_states_no_events(self) -> None:
        for state in TERMINAL_DISCOVERY_STATES:
            self.assertEqual(allowed_events_for_discovery_state(state), frozenset())

    def test_happy_path_transitions(self) -> None:
        s = get_next_discovery_state(DiscoveryState.DISCOVERY_IDLE, DiscoveryEvent.RUN_TRIGGERED)
        self.assertEqual(s, DiscoveryState.DISCOVERY_RUNNING)
        s = get_next_discovery_state(s, DiscoveryEvent.IDEA_SCOUT_COMPLETED)
        self.assertEqual(s, DiscoveryState.DISCOVERY_COMPLETE)

    def test_gate_missing_halts(self) -> None:
        s = get_next_discovery_state(DiscoveryState.DISCOVERY_RUNNING, DiscoveryEvent.GATE_MISSING)
        self.assertEqual(s, DiscoveryState.DISCOVERY_HALTED_NO_GATE)

    def test_focus_missing_halts(self) -> None:
        s = get_next_discovery_state(DiscoveryState.DISCOVERY_RUNNING, DiscoveryEvent.FOCUS_MISSING)
        self.assertEqual(s, DiscoveryState.DISCOVERY_HALTED_NO_FOCUS)

    def test_invalid_transition_raises(self) -> None:
        with self.assertRaises(DiscoveryTransitionError):
            get_next_discovery_state(DiscoveryState.DISCOVERY_IDLE, DiscoveryEvent.GATE_MISSING)

    def test_needs_human_is_terminal(self) -> None:
        self.assertIn(DiscoveryState.DISCOVERY_HALTED_NEEDS_HUMAN, TERMINAL_DISCOVERY_STATES)


# ---------------------------------------------------------------------------
# Orchestrator run tests
# ---------------------------------------------------------------------------

class DiscoveryRunOnceTests(unittest.TestCase):
    def test_happy_path_creates_ideas(self) -> None:
        candidates = [
            {"title": "Idea A", "body": "body a", "decision": "CREATE_PM_IDEA"},
            {"title": "Idea B", "body": "body b", "decision": "CREATE_PM_IDEA"},
        ]
        orch = _make_orchestrator(candidates)
        result = orch.run()
        self.assertEqual(result.state, "DISCOVERY_COMPLETE")
        self.assertEqual(len(result.created_pm_idea_numbers), 2)

    def test_creation_cap_enforced(self) -> None:
        candidates = [
            {"title": f"Idea {i}", "body": "b", "decision": "CREATE_PM_IDEA"} for i in range(5)
        ]
        orch = _make_orchestrator(candidates, cap=2)
        result = orch.run()
        self.assertEqual(len(result.created_pm_idea_numbers), 2)

    def test_gate_missing_halts(self) -> None:
        orch = _make_orchestrator([], gate=False)
        result = orch.run()
        self.assertEqual(result.state, "DISCOVERY_HALTED_NO_GATE")
        self.assertIsNotNone(result.halted_reason)

    def test_focus_missing_halts(self) -> None:
        orch = _make_orchestrator([], focus=False)
        result = orch.run()
        self.assertEqual(result.state, "DISCOVERY_HALTED_NO_FOCUS")

    def test_defer_and_drop_counted(self) -> None:
        candidates = [
            {"title": "A", "body": "b", "decision": "CREATE_PM_IDEA"},
            {"title": "B", "body": "b", "decision": "DEFER"},
            {"title": "C", "body": "b", "decision": "DROP"},
        ]
        orch = _make_orchestrator(candidates)
        result = orch.run()
        self.assertEqual(len(result.created_pm_idea_numbers), 1)
        self.assertEqual(result.deferred_count, 1)
        self.assertEqual(result.dropped_count, 1)

    def test_deferred_candidates_persisted_to_gateway(self) -> None:
        gateway = _make_gateway()
        candidates = [
            {"title": "Keep A", "body": "deferred body", "decision": "DEFER"},
        ]
        adapter = StubDiscoveryLLMAdapter(candidates)
        orch = DiscoveryRunOnceOrchestrator(gateway=gateway, llm_adapter=adapter)
        result = orch.run()
        self.assertEqual(result.deferred_count, 1)
        self.assertEqual(len(gateway.deferred_candidates), 1)
        self.assertEqual(gateway.deferred_candidates[0]["title"], "Keep A")

    def test_issues_written_to_gateway(self) -> None:
        gateway = _make_gateway()
        candidates = [
            {"title": "New Feature", "body": "body", "decision": "CREATE_PM_IDEA"},
        ]
        adapter = StubDiscoveryLLMAdapter(candidates)
        orch = DiscoveryRunOnceOrchestrator(gateway=gateway, llm_adapter=adapter)
        result = orch.run()
        self.assertEqual(len(result.created_pm_idea_numbers), 1)
        # Verify issue was written into the in-memory gateway
        number = result.created_pm_idea_numbers[0]
        self.assertIn(number, gateway._issues)
        self.assertEqual(gateway._issues[number]["title"], "New Feature")


if __name__ == "__main__":
    unittest.main()

