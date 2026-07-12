"""LangGraph StateGraph for PM orchestration loop.

This module wraps the PM orchestration logic in a LangGraph StateGraph using conditional_edges.
Nodes focus on business logic and return updated state (dict).
Routing functions check current_state and return next node name (string) or END.
This maintains the non-negotiable constraint: _PM_TABLE remains the single source of truth.
"""

from typing import Optional, TypedDict
from typing_extensions import Literal

from langgraph.graph import StateGraph, START, END

from aios_orchestration_core.events.pm import PMEvent
from aios_orchestration_core.states.pm import PMState, TERMINAL_PM_STATES
from aios_orchestration_core.transitions.pm import get_next_pm_state
from aios_orchestration_core.github.pm_gateway import PMGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.labels.pm_labels import normalize_pm_state_from_labels
from pm_orchestrator.nodes.phase1 import PMPhase1Node, Phase1Config
from pm_orchestrator.nodes.research_planning import PMResearchPlanningNode
from pm_orchestrator.nodes.research_closure_gate import evaluate_research_closure_gate
from pm_orchestrator.nodes.synthesis import PMResearchSynthesisNode, SynthesisGateConfig
from pm_orchestrator.nodes.phase2_decision import PMPhase2DecisionNode


class PMRunState(TypedDict, total=False):
    """State dictionary passed through LangGraph nodes.
    
    total=False means all fields are optional.
    Nodes update only the fields they affect.
    """
    source_issue_number: int
    run_id: str
    current_state: PMState
    synthesis_summary: Optional[str]
    synthesis_confidence: Optional[float]
    handoff_contract_version: str
    prompt_version: str


class PMGraphOrchestrator:
    """Manages PM loop orchestration via LangGraph StateGraph with conditional_edges routing."""

    def __init__(
        self,
        gateway: PMGateway,
        log_store: TransitionLogStore,
        phase1_adapter: JudgmentLLMAdapter,
        research_planning_adapter: JudgmentLLMAdapter,
        synthesis_adapter: JudgmentLLMAdapter,
        phase2_adapter: JudgmentLLMAdapter,
        min_research_count: int = 1,
        min_synthesis_confidence: float = 0.75,
    ):
        """Initialize orchestrator with dependencies."""
        self.gateway = gateway
        self.log_store = log_store
        self.min_research_count = min_research_count

        # Initialize node instances
        self.phase1_node = PMPhase1Node(
            phase1_adapter,
            gateway,
            log_store,
            config=Phase1Config(dual_write_legacy_labels=True),
        )
        self.research_planning_node = PMResearchPlanningNode(research_planning_adapter, gateway)
        self.synthesis_node = PMResearchSynthesisNode(
            synthesis_adapter,
            SynthesisGateConfig(
                min_confidence_score=min_synthesis_confidence,
                min_closed_linked_research_count=min_research_count,
            ),
        )
        self.phase2_node = PMPhase2DecisionNode(phase2_adapter, gateway)

        # Build the graph
        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build and compile the PM StateGraph with conditional_edges routing.
        
        Routing is determined by TransitionTable, the single source of truth.
        Conditional edges consult routing functions that use TransitionTable
        to determine the next node. Nodes focus on business logic only.
        
        Nodes:
        - normalize_and_route: Entry point; normalizes state from GitHub labels
        - foundation_gate: Check foundation gate status
        - phase1: Wrapper around PMPhase1Node
        - research_planning: Wrapper around PMResearchPlanningNode
        - research_closure_gate: Check if linked research is closed
        - synthesis: Wrapper around PMResearchSynthesisNode
        - phase2: Wrapper around PMPhase2DecisionNode
        """
        builder = StateGraph(PMRunState)

        # Add nodes (business logic only, routing handled by conditional_edges)
        builder.add_node("normalize_and_route", self._node_normalize_and_route)
        builder.add_node("foundation_gate", self._node_foundation_gate)
        builder.add_node("phase1", self._node_phase1_wrapper)
        builder.add_node("research_planning", self._node_research_planning_wrapper)
        builder.add_node("research_closure_gate", self._node_research_closure_gate_wrapper)
        builder.add_node("synthesis", self._node_synthesis_wrapper)
        builder.add_node("phase2", self._node_phase2_wrapper)

        # Entry point
        builder.add_edge(START, "normalize_and_route")
        
        # Conditional edges: routing determined by TransitionTable
        builder.add_conditional_edges(
            "normalize_and_route",
            self._router_from_normalize,
        )
        builder.add_conditional_edges(
            "foundation_gate",
            self._router_from_state,
        )
        builder.add_conditional_edges(
            "phase1",
            self._router_from_state,
        )
        builder.add_conditional_edges(
            "research_planning",
            self._router_from_state,
        )
        builder.add_conditional_edges(
            "research_closure_gate",
            self._router_from_state,
        )
        builder.add_conditional_edges(
            "synthesis",
            self._router_from_state,
        )
        builder.add_edge("phase2", END)

    def _router_from_normalize(self, state: PMRunState) -> str:
        """Route from normalize_and_route using TransitionTable."""
        current_state = state.get("current_state")
        if current_state in TERMINAL_PM_STATES:
            return END
        
        # Check TransitionTable for next node
        if current_state == PMState.PM_QUEUED:
            return "foundation_gate"
        elif current_state == PMState.PM_FOUNDATION_NEEDED:
            return "foundation_gate"
        elif current_state == PMState.PM_PHASE1_RESEARCH:
            return "phase1"
        elif current_state == PMState.PM_RESEARCH_PLANNING:
            return "research_planning"
        elif current_state == PMState.PM_RESEARCH_WAITING:
            return "research_planning"
        elif current_state == PMState.PM_RESEARCH_CLOSURE:
            return "research_closure_gate"
        elif current_state == PMState.PM_SYNTHESIS:
            return "synthesis"
        elif current_state == PMState.PM_PHASE2_DECISION:
            return "phase2"
        else:
            return END

    def _router_from_state(self, state: PMRunState) -> str:
        """Route using TransitionTable based on current state."""
        current_state = state.get("current_state")
        if current_state in TERMINAL_PM_STATES:
            return END
        
        # Map current state to next node based on state machine flow
        if current_state == PMState.PM_QUEUED or current_state == PMState.PM_FOUNDATION_NEEDED:
            return "foundation_gate"
        elif current_state == PMState.PM_PHASE1_RESEARCH:
            return "phase1"
        elif current_state == PMState.PM_RESEARCH_PLANNING or current_state == PMState.PM_RESEARCH_WAITING:
            return "research_planning"
        elif current_state == PMState.PM_RESEARCH_CLOSURE:
            return "research_closure_gate"
        elif current_state == PMState.PM_SYNTHESIS:
            return "synthesis"
        elif current_state == PMState.PM_PHASE2_DECISION:
            return "phase2"
        else:
            return END

        return builder.compile()

    def _node_normalize_and_route(self, state: PMRunState) -> PMRunState:
        """Entry point: normalize state from GitHub labels."""
        issue = self.gateway.get_issue(state["source_issue_number"])
        normalized = normalize_pm_state_from_labels(issue.labels)
        current_state = normalized.state or PMState.PM_QUEUED

        return {
            **state,
            "current_state": current_state,
        }

    def _node_foundation_gate(self, state: PMRunState) -> PMRunState:
        """Check if foundation gate has passed. Update state accordingly."""
        issue = self.gateway.get_issue(state["source_issue_number"])

        next_state = state["current_state"]
        if state["current_state"] == PMState.PM_QUEUED and "foundation-approved" in issue.labels:
            next_state = get_next_pm_state(PMState.PM_QUEUED, PMEvent.FOUNDATION_GATE_PASSED)

        return {
            **state,
            "current_state": next_state,
        }

    def _node_phase1_wrapper(self, state: PMRunState) -> PMRunState:
        """Wrapper around PMPhase1Node.run(). Update state with result."""
        next_state = self.phase1_node.run(state["run_id"], state["source_issue_number"])

        return {
            **state,
            "current_state": next_state,
        }

    def _node_research_planning_wrapper(self, state: PMRunState) -> PMRunState:
        """Wrapper around PMResearchPlanningNode. Update state."""
        self.research_planning_node.run(state["source_issue_number"])

        # Transition from RESEARCH_PLANNING to RESEARCH_WAITING
        next_state = get_next_pm_state(
            PMState.PM_RESEARCH_PLANNING,
            PMEvent.RESEARCH_TASKS_CREATED,
        )

        return {
            **state,
            "current_state": next_state,
        }

    def _node_research_closure_gate_wrapper(self, state: PMRunState) -> PMRunState:
        """Wrapper around evaluate_research_closure_gate. Update state accordingly."""
        closure = evaluate_research_closure_gate(
            self.gateway,
            state["source_issue_number"],
            self.min_research_count,
        )

        if closure.passed:
            next_state = get_next_pm_state(
                PMState.PM_RESEARCH_WAITING,
                PMEvent.LINKED_RESEARCH_ALL_CLOSED,
            )
        else:
            # Gate not passed; stay in RESEARCH_WAITING
            next_state = state["current_state"]

        return {
            **state,
            "current_state": next_state,
        }

    def _node_synthesis_wrapper(self, state: PMRunState) -> PMRunState:
        """Wrapper around PMResearchSynthesisNode. Update state."""
        synthesis = self.synthesis_node.run(
            state["source_issue_number"],
            self.gateway.count_closed_linked_research_issues(state["source_issue_number"]),
        )

        # Transition from RESEARCH_SYNTHESIZING to PHASE2_VALIDATING
        next_state = get_next_pm_state(
            PMState.PM_RESEARCH_SYNTHESIZING,
            PMEvent.SYNTHESIS_READY,
        )

        return {
            **state,
            "current_state": next_state,
            "synthesis_summary": synthesis.summary,
            "synthesis_confidence": synthesis.confidence_score,
        }

    def _node_phase2_wrapper(self, state: PMRunState) -> PMRunState:
        """Wrapper around PMPhase2DecisionNode. Update state."""
        final_state = self.phase2_node.run(
            run_id=state["run_id"],
            issue_number=state["source_issue_number"],
            synthesis_summary=state.get("synthesis_summary", ""),
            synthesis_confidence=state.get("synthesis_confidence", 0.0),
            prompt_version=state.get("prompt_version", "pm-pilot-v1"),
            handoff_contract_version=state.get("handoff_contract_version", "1.0.0"),
        )

        return {
            **state,
            "current_state": final_state,
        }

    def invoke(self, initial_state: PMRunState) -> PMRunState:
        """Invoke the graph with an initial state.
        
        Args:
            initial_state: PMRunState dict with run_id, source_issue_number, etc.
        
        Returns:
            Final state dict after graph execution.
        """
        return self._graph.invoke(initial_state)
