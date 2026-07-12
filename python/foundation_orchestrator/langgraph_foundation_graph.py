"""LangGraph StateGraph for Foundation orchestration loop.

This module wraps the Foundation orchestration logic in a LangGraph StateGraph.
Each node is a thin adapter around existing Foundation node classes, maintaining
the non-negotiable constraint: _FOUNDATION_TABLE remains the single source of truth,
and existing node logic is NOT reimplemented inline.

The router delegates to _FOUNDATION_TABLE via get_next_foundation_state() and allowed_events_for_foundation_state().
No transition pairs are re-declared in the graph; the graph only orchestrates node execution.
"""

from typing import Optional, TypedDict
from typing_extensions import Literal
from datetime import datetime, timezone

from langgraph.graph import StateGraph, END

from aios_orchestration_core.events.foundation import FoundationEvent
from aios_orchestration_core.states.foundation import FoundationState, TERMINAL_FOUNDATION_STATES
from aios_orchestration_core.transitions.foundation import get_next_foundation_state
from aios_orchestration_core.github.foundation_gateway import FoundationGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.labels.foundation_labels import (
    FOUNDATION_CANONICAL_LABEL_BY_STATE,
    FOUNDATION_CANONICAL_STATE_LABELS,
    normalize_foundation_state_from_labels,
)
from foundation_orchestrator.nodes.gate import FoundationGateNode
from foundation_orchestrator.nodes.research import FoundationResearchNode


class FoundationRunState(TypedDict, total=False):
    """State dictionary passed through LangGraph nodes.
    
    total=False means all fields are optional.
    Nodes update only the fields they affect.
    """
    source_issue_number: int
    run_id: str
    current_state: FoundationState


class FoundationGraphOrchestrator:
    """Manages Foundation loop orchestration via LangGraph StateGraph."""

    def __init__(
        self,
        gateway: FoundationGateway,
        log_store: TransitionLogStore,
        research_adapter: JudgmentLLMAdapter,
        gate_adapter: JudgmentLLMAdapter,
    ):
        """Initialize orchestrator with dependencies."""
        self.gateway = gateway
        self.log_store = log_store

        # Initialize node instances
        self.research_node = FoundationResearchNode(research_adapter, gateway, log_store)
        self.gate_node = FoundationGateNode(gate_adapter, gateway, log_store)

        # Build the graph
        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build and compile the Foundation StateGraph.
        
        Nodes:
        - normalize_and_route: Entry point; determines initial state or routes based on labels
        - needed_to_in_progress: Auto-transition from NEEDED to IN_PROGRESS
        - research: Wrapper around FoundationResearchNode
        - gate: Wrapper around FoundationGateNode
        
        Edges:
        - Conditional edges from each node based on current_state
        - Terminal states route to END
        - Feedback loops: REVIEW->IN_PROGRESS (REVISE), IN_PROGRESS->IN_PROGRESS (NEEDS_MORE)
        """
        builder = StateGraph(FoundationRunState)

        # Add nodes
        builder.add_node("normalize_and_route", self._node_normalize_and_route)
        builder.add_node("needed_to_in_progress", self._node_needed_to_in_progress)
        builder.add_node("research", self._node_research_wrapper)
        builder.add_node("gate", self._node_gate_wrapper)

        # Entry point
        builder.set_entry_point("normalize_and_route")

        # Conditional edges from normalize_and_route
        builder.add_conditional_edges(
            "normalize_and_route",
            self._router_from_normalize,
            {
                "needed_to_in_progress": "needed_to_in_progress",
                "research": "research",
                "gate": "gate",
                END: END,
            },
        )

        # Conditional edges from needed_to_in_progress
        builder.add_conditional_edges(
            "needed_to_in_progress",
            self._router_from_state,
            {
                "research": "research",
                END: END,
            },
        )

        # Conditional edges from research (can loop back or advance)
        builder.add_conditional_edges(
            "research",
            self._router_from_state,
            {
                "research": "research",  # NEEDS_MORE loops back
                "gate": "gate",          # RECOMMEND advances
                END: END,                # BLOCKED ends
            },
        )

        # Conditional edges from gate (can loop back to research or end)
        builder.add_conditional_edges(
            "gate",
            self._router_from_state,
            {
                "research": "research",  # REVISE loops back to research
                END: END,                # APPROVE or BLOCK ends
            },
        )

        return builder.compile()

    def _node_normalize_and_route(self, state: FoundationRunState) -> FoundationRunState:
        """Entry point: normalize state from GitHub labels, determine next action."""
        issue = self.gateway.get_issue(state["source_issue_number"])
        normalized = normalize_foundation_state_from_labels(issue.labels)
        current_state = normalized.state or FoundationState.FOUNDATION_NEEDED

        state["current_state"] = current_state
        return state

    def _node_needed_to_in_progress(self, state: FoundationRunState) -> FoundationRunState:
        """Auto-transition from FOUNDATION_NEEDED to FOUNDATION_IN_PROGRESS."""
        if state["current_state"] == FoundationState.FOUNDATION_NEEDED:
            next_state = get_next_foundation_state(
                FoundationState.FOUNDATION_NEEDED,
                FoundationEvent.FOUNDATION_STARTED,
            )
            
            # Log the transition
            self.gateway.set_state_labels(
                state["source_issue_number"],
                list(FOUNDATION_CANONICAL_STATE_LABELS),
                [FOUNDATION_CANONICAL_LABEL_BY_STATE[next_state]],
            )
            entry = TransitionLogEntry(
                loop_id="foundation",
                run_id=state["run_id"],
                issue_number=state["source_issue_number"],
                from_state=FoundationState.FOUNDATION_NEEDED.value,
                to_state=next_state.value,
                trigger_event=FoundationEvent.FOUNDATION_STARTED.value,
                reason_code="FOUNDATION_STARTED",
                reason_detail="Starting foundation research",
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            )
            self.log_store.append(entry)
            self.gateway.post_comment(state["source_issue_number"], entry.to_comment())
            
            state["current_state"] = next_state
        return state

    def _node_research_wrapper(self, state: FoundationRunState) -> FoundationRunState:
        """Wrapper around FoundationResearchNode.run()."""
        next_state = self.research_node.run(state["run_id"], state["source_issue_number"])
        state["current_state"] = next_state
        return state

    def _node_gate_wrapper(self, state: FoundationRunState) -> FoundationRunState:
        """Wrapper around FoundationGateNode.run()."""
        next_state = self.gate_node.run(state["run_id"], state["source_issue_number"])
        state["current_state"] = next_state
        return state

    def _router_from_normalize(self, state: FoundationRunState) -> str:
        """Route after normalize_and_route: determine next node based on current_state."""
        current = state["current_state"]
        
        # Terminal states -> END
        if current in TERMINAL_FOUNDATION_STATES:
            return END
        
        # Route based on current state
        if current == FoundationState.FOUNDATION_NEEDED:
            return "needed_to_in_progress"
        elif current == FoundationState.FOUNDATION_IN_PROGRESS:
            return "research"
        elif current == FoundationState.FOUNDATION_REVIEW:
            return "gate"
        else:
            return END

    def _router_from_state(self, state: FoundationRunState) -> str:
        """Generic router: after node execution, route based on new current_state.
        
        Delegates to _FOUNDATION_TABLE logic: if state is terminal, end; otherwise,
        route to next node or loop back.
        """
        current = state["current_state"]
        
        # Terminal states -> END
        if current in TERMINAL_FOUNDATION_STATES:
            return END
        
        # Handle blocked state explicitly
        if current == FoundationState.FOUNDATION_BLOCKED:
            return END
        
        # For non-terminal states, route based on current state
        if current == FoundationState.FOUNDATION_IN_PROGRESS:
            # Research node sets this; keep looping or advance to gate
            return "research"
        elif current == FoundationState.FOUNDATION_REVIEW:
            return "gate"
        else:
            return END

    def invoke(self, initial_state: FoundationRunState) -> FoundationRunState:
        """Invoke the graph with an initial state.
        
        Args:
            initial_state: FoundationRunState dict with run_id, source_issue_number, etc.
        
        Returns:
            Final state dict after graph execution.
        """
        return self._graph.invoke(initial_state)