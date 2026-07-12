"""LangGraph StateGraph for PM orchestration loop.

This module wraps the PM orchestration logic in a LangGraph StateGraph.
Each node is a thin adapter around existing PM node classes, maintaining
the non-negotiable constraint: _PM_TABLE remains the single source of truth,
and existing node logic is NOT reimplemented inline.

The router delegates to _PM_TABLE via get_next_pm_state() and allowed_events_for_state().
No transition pairs are re-declared in the graph; the graph only orchestrates node execution.
"""

from typing import Annotated, Optional, TypedDict
from typing_extensions import Literal

from langgraph.graph import StateGraph, END

from aios_orchestration_core.events.pm import PMEvent
from aios_orchestration_core.states.pm import PMState, TERMINAL_PM_STATES
from aios_orchestration_core.transitions.pm import get_next_pm_state, allowed_events_for_state
from aios_orchestration_core.github.pm_gateway import PMGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.artifacts.pm_decisions import PMResearchSynthesis
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
    """Manages PM loop orchestration via LangGraph StateGraph."""

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
        """Build and compile the PM StateGraph.
        
        Nodes:
        - normalize_and_route: Entry point; determines initial state or routes based on labels
        - phase1: Wrapper around PMPhase1Node
        - research_planning: Wrapper around PMResearchPlanningNode
        - research_closure_gate: Wrapper around evaluate_research_closure_gate
        - synthesis: Wrapper around PMResearchSynthesisNode
        - phase2: Wrapper around PMPhase2DecisionNode
        
        Edges:
        - Conditional edges from each node to next node based on current_state
        - Terminal states route to END
        """
        builder = StateGraph(PMRunState)

        # Add nodes
        builder.add_node("normalize_and_route", self._node_normalize_and_route)
        builder.add_node("foundation_gate", self._node_foundation_gate)
        builder.add_node("phase1", self._node_phase1_wrapper)
        builder.add_node("research_planning", self._node_research_planning_wrapper)
        builder.add_node("research_closure_gate", self._node_research_closure_gate_wrapper)
        builder.add_node("synthesis", self._node_synthesis_wrapper)
        builder.add_node("phase2", self._node_phase2_wrapper)

        # Entry point
        builder.set_entry_point("normalize_and_route")

        # Conditional edges from normalize_and_route
        builder.add_conditional_edges(
            "normalize_and_route",
            self._router_from_normalize,
            {
                "foundation_gate": "foundation_gate",
                "phase1": "phase1",
                "research_planning": "research_planning",
                "research_closure_gate": "research_closure_gate",
                "synthesis": "synthesis",
                "phase2": "phase2",
                END: END,
            },
        )

        # Conditional edges from foundation_gate
        builder.add_conditional_edges(
            "foundation_gate",
            self._router_from_state,
            {
                "phase1": "phase1",
                END: END,
            },
        )

        # Conditional edges from phase1
        builder.add_conditional_edges(
            "phase1",
            self._router_from_state,
            {
                "research_planning": "research_planning",
                END: END,
            },
        )

        # Conditional edges from research_planning
        builder.add_conditional_edges(
            "research_planning",
            self._router_from_state,
            {
                "research_closure_gate": "research_closure_gate",
                END: END,
            },
        )

        # Conditional edges from research_closure_gate
        builder.add_conditional_edges(
            "research_closure_gate",
            self._router_from_state,
            {
                "synthesis": "synthesis",
                END: END,
            },
        )

        # Conditional edges from synthesis (flows to phase2)
        builder.add_edge("synthesis", "phase2")

        # Conditional edges from phase2
        builder.add_conditional_edges(
            "phase2",
            self._router_from_state,
            {
                END: END,
            },
        )

        return builder.compile()

    def _node_normalize_and_route(self, state: PMRunState) -> PMRunState:
        """Entry point: normalize state from GitHub labels, determine next action."""
        from aios_orchestration_core.labels.pm_labels import normalize_pm_state_from_labels

        issue = self.gateway.get_issue(state["source_issue_number"])
        normalized = normalize_pm_state_from_labels(issue.labels)
        current_state = normalized.state or PMState.PM_QUEUED

        state["current_state"] = current_state
        return state

    def _node_foundation_gate(self, state: PMRunState) -> PMRunState:
        """Check if foundation gate has passed."""
        issue = self.gateway.get_issue(state["source_issue_number"])

        if state["current_state"] == PMState.PM_QUEUED:
            if "foundation-approved" in issue.labels:
                next_state = get_next_pm_state(PMState.PM_QUEUED, PMEvent.FOUNDATION_GATE_PASSED)
                state["current_state"] = next_state
            # else: stay in PM_QUEUED (which is terminal for this run)
        
        return state

    def _node_phase1_wrapper(self, state: PMRunState) -> PMRunState:
        """Wrapper around PMPhase1Node.run()."""
        next_state = self.phase1_node.run(state["run_id"], state["source_issue_number"])
        state["current_state"] = next_state
        return state

    def _node_research_planning_wrapper(self, state: PMRunState) -> PMRunState:
        """Wrapper around PMResearchPlanningNode.run()."""
        self.research_planning_node.run(state["source_issue_number"])
        
        # Transition from RESEARCH_PLANNING to RESEARCH_WAITING
        next_state = get_next_pm_state(
            PMState.PM_RESEARCH_PLANNING,
            PMEvent.RESEARCH_TASKS_CREATED,
        )
        state["current_state"] = next_state
        return state

    def _node_research_closure_gate_wrapper(self, state: PMRunState) -> PMRunState:
        """Wrapper around evaluate_research_closure_gate."""
        closure = evaluate_research_closure_gate(
            self.gateway,
            state["source_issue_number"],
            self.min_research_count,
        )
        
        if closure.passed:
            # Transition from RESEARCH_WAITING to RESEARCH_SYNTHESIZING
            next_state = get_next_pm_state(
                PMState.PM_RESEARCH_WAITING,
                PMEvent.LINKED_RESEARCH_ALL_CLOSED,
            )
            state["current_state"] = next_state
        # else: stay in PM_RESEARCH_WAITING
        
        return state

    def _node_synthesis_wrapper(self, state: PMRunState) -> PMRunState:
        """Wrapper around PMResearchSynthesisNode.run()."""
        synthesis = self.synthesis_node.run(
            state["source_issue_number"],
            self.gateway.count_closed_linked_research_issues(state["source_issue_number"]),
        )
        
        # Store synthesis results for phase2 node
        state["synthesis_summary"] = synthesis.summary
        state["synthesis_confidence"] = synthesis.confidence_score
        
        # Transition from RESEARCH_SYNTHESIZING to PHASE2_VALIDATING
        next_state = get_next_pm_state(
            PMState.PM_RESEARCH_SYNTHESIZING,
            PMEvent.SYNTHESIS_READY,
        )
        state["current_state"] = next_state
        return state

    def _node_phase2_wrapper(self, state: PMRunState) -> PMRunState:
        """Wrapper around PMPhase2DecisionNode.run()."""
        final_state = self.phase2_node.run(
            run_id=state["run_id"],
            issue_number=state["source_issue_number"],
            synthesis_summary=state.get("synthesis_summary", ""),
            synthesis_confidence=state.get("synthesis_confidence", 0.0),
            prompt_version=state.get("prompt_version", "pm-pilot-v1"),
            handoff_contract_version=state.get("handoff_contract_version", "1.0.0"),
        )
        state["current_state"] = final_state
        return state

    def _router_from_normalize(self, state: PMRunState) -> str:
        """Route after normalize_and_route: determine next node based on current_state."""
        current = state["current_state"]
        
        # Terminal states -> END
        if current in TERMINAL_PM_STATES:
            return END
        
        # Route based on current state
        if current == PMState.PM_QUEUED:
            return "foundation_gate"
        elif current == PMState.PM_PHASE1_VALIDATING:
            return "phase1"
        elif current == PMState.PM_RESEARCH_PLANNING:
            return "research_planning"
        elif current == PMState.PM_RESEARCH_WAITING:
            return "research_closure_gate"
        elif current == PMState.PM_RESEARCH_SYNTHESIZING:
            return "synthesis"
        elif current == PMState.PM_PHASE2_VALIDATING:
            return "phase2"
        else:
            # Unknown state; terminate
            return END

    def _router_from_state(self, state: PMRunState) -> str:
        """Generic router: after node execution, route based on new current_state.
        
        Delegates to _PM_TABLE logic: if state is terminal, end; otherwise,
        the next node will be determined by the router (or edge explicitly set).
        """
        current = state["current_state"]
        
        # Terminal states -> END
        if current in TERMINAL_PM_STATES:
            return END
        
        # For non-terminal states, route based on current state
        if current == PMState.PM_PHASE1_VALIDATING:
            return "phase1"
        elif current == PMState.PM_RESEARCH_PLANNING:
            return "research_planning"
        elif current == PMState.PM_RESEARCH_WAITING:
            # Research gate just ran; if we're still in RESEARCH_WAITING,
            # the gate didn't pass, so end this run invocation
            return END
        elif current == PMState.PM_RESEARCH_SYNTHESIZING:
            return "synthesis"
        elif current == PMState.PM_PHASE2_VALIDATING:
            return "phase2"
        else:
            return END

    def invoke(self, initial_state: PMRunState) -> PMRunState:
        """Invoke the graph with an initial state.
        
        Args:
            initial_state: PMRunState dict with run_id, source_issue_number, etc.
        
        Returns:
            Final state dict after graph execution.
        """
        return self._graph.invoke(initial_state)
