"""LangGraph StateGraph for PO orchestration loop.

This module wraps the PO orchestration logic in a LangGraph StateGraph.
Each node is a thin adapter around existing PO node classes, maintaining
the non-negotiable constraint: _PO_TABLE remains the single source of truth.

The router delegates to _PO_TABLE via get_next_po_state().
No transition pairs are re-declared in the graph.
"""

from typing import Annotated, Optional, TypedDict
from typing_extensions import Literal
from datetime import datetime, timezone

from langgraph.graph import StateGraph, END

from aios_orchestration_core.events.po import POEvent
from aios_orchestration_core.states.po import POState, TERMINAL_PO_STATES
from aios_orchestration_core.transitions.po import get_next_po_state
from aios_orchestration_core.github.po_gateway import POGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.labels.po_labels import normalize_po_state_from_labels, PO_CANONICAL_LABEL_BY_STATE, PO_CANONICAL_STATE_LABELS
from po_orchestrator.nodes.prioritize import POPrioritizeNode
from po_orchestrator.nodes.create_features import POCreateFeaturesNode


class PORunState(TypedDict, total=False):
    """State dictionary passed through LangGraph nodes.
    
    total=False means all fields are optional.
    Nodes update only the fields they affect.
    """
    source_issue_number: int
    run_id: str
    current_state: POState


class POGraphOrchestrator:
    """Manages PO loop orchestration via LangGraph StateGraph."""

    def __init__(
        self,
        gateway: POGateway,
        log_store: TransitionLogStore,
        prioritize_adapter: JudgmentLLMAdapter,
        create_features_adapter: JudgmentLLMAdapter,
    ):
        """Initialize orchestrator with dependencies."""
        self.gateway = gateway
        self.log_store = log_store

        # Initialize node instances
        self.prioritize_node = POPrioritizeNode(prioritize_adapter, gateway, log_store)
        self.create_features_node = POCreateFeaturesNode(create_features_adapter, gateway, log_store)

        # Build the graph
        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build and compile the PO StateGraph.
        
        Nodes:
        - normalize_and_route: Entry point; determines initial state or routes based on labels
        - queued_to_prioritizing: Auto-transition from QUEUED to PRIORITIZING
        - prioritize: Wrapper around POPrioritizeNode
        - create_features: Wrapper around POCreateFeaturesNode
        
        Edges:
        - Conditional edges from each node based on current_state
        - Terminal states route to END
        """
        builder = StateGraph(PORunState)

        # Add nodes
        builder.add_node("normalize_and_route", self._node_normalize_and_route)
        builder.add_node("queued_to_prioritizing", self._node_queued_to_prioritizing)
        builder.add_node("prioritize", self._node_prioritize_wrapper)
        builder.add_node("create_features", self._node_create_features_wrapper)

        # Entry point
        builder.set_entry_point("normalize_and_route")

        # Conditional edges from normalize_and_route
        builder.add_conditional_edges(
            "normalize_and_route",
            self._router_from_normalize,
            {
                "queued_to_prioritizing": "queued_to_prioritizing",
                "prioritize": "prioritize",
                "create_features": "create_features",
                END: END,
            },
        )

        # Conditional edges from queued_to_prioritizing
        builder.add_conditional_edges(
            "queued_to_prioritizing",
            self._router_from_state,
            {
                "prioritize": "prioritize",
                END: END,
            },
        )

        # Conditional edges from prioritize
        builder.add_conditional_edges(
            "prioritize",
            self._router_from_state,
            {
                "create_features": "create_features",
                END: END,
            },
        )

        # Conditional edges from create_features
        builder.add_conditional_edges(
            "create_features",
            self._router_from_state,
            {
                END: END,
            },
        )

        return builder.compile()

    def _node_normalize_and_route(self, state: PORunState) -> PORunState:
        """Entry point: normalize state from GitHub labels, determine next action."""
        issue = self.gateway.get_issue(state["source_issue_number"])
        normalized = normalize_po_state_from_labels(issue.labels)
        current_state = normalized.state or POState.PO_QUEUED

        state["current_state"] = current_state
        return state

    def _node_queued_to_prioritizing(self, state: PORunState) -> PORunState:
        """Auto-transition from PO_QUEUED to PO_PRIORITIZING."""
        if state["current_state"] == POState.PO_QUEUED:
            next_state = get_next_po_state(POState.PO_QUEUED, POEvent.ENTERED_PRIORITIZATION)
            
            # Log the transition
            self.gateway.set_state_labels(
                state["source_issue_number"],
                list(PO_CANONICAL_STATE_LABELS),
                [PO_CANONICAL_LABEL_BY_STATE[next_state]],
            )
            entry = TransitionLogEntry(
                loop_id="po",
                run_id=state["run_id"],
                issue_number=state["source_issue_number"],
                from_state=POState.PO_QUEUED.value,
                to_state=next_state.value,
                trigger_event=POEvent.ENTERED_PRIORITIZATION.value,
                reason_code="ENTERED_PRIORITIZATION",
                reason_detail="Strategic opportunity entered PO prioritization",
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            )
            self.log_store.append(entry)
            self.gateway.post_comment(state["source_issue_number"], entry.to_comment())
            
            state["current_state"] = next_state
        return state


    def _node_prioritize_wrapper(self, state: PORunState) -> PORunState:
        """Wrapper around POPrioritizeNode.run()."""
        next_state = self.prioritize_node.run(state["run_id"], state["source_issue_number"])
        state["current_state"] = next_state
        return state

    def _node_create_features_wrapper(self, state: PORunState) -> PORunState:
        """Wrapper around POCreateFeaturesNode.run()."""
        next_state = self.create_features_node.run(state["run_id"], state["source_issue_number"])
        state["current_state"] = next_state
        return state

    def _router_from_normalize(self, state: PORunState) -> str:
        """Route after normalize_and_route: determine next node based on current_state."""
        current = state["current_state"]
        
        # Terminal states -> END
        if current in TERMINAL_PO_STATES:
            return END
        
        # Route based on current state
        if current == POState.PO_QUEUED:
            return "queued_to_prioritizing"
        elif current == POState.PO_PRIORITIZING:
            return "prioritize"
        elif current == POState.PO_CREATING_FEATURES:
            return "create_features"
        else:
            return END

    def _router_from_state(self, state: PORunState) -> str:
        """Generic router: after node execution, route based on new current_state.
        
        Delegates to _PO_TABLE logic: if state is terminal, end; otherwise,
        route to next node.
        """
        current = state["current_state"]
        
        # Terminal states -> END
        if current in TERMINAL_PO_STATES:
            return END
        
        # For non-terminal states, route based on current state
        if current == POState.PO_PRIORITIZING:
            return "prioritize"
        elif current == POState.PO_CREATING_FEATURES:
            return "create_features"
        else:
            return END

    def invoke(self, initial_state: PORunState) -> PORunState:
        """Invoke the graph with an initial state.
        
        Args:
            initial_state: PORunState dict with run_id, source_issue_number, etc.
        
        Returns:
            Final state dict after graph execution.
        """
        return self._graph.invoke(initial_state)
