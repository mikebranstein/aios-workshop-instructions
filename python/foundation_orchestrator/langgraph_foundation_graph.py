"""LangGraph StateGraph for Foundation orchestration loop.

This module wraps the Foundation orchestration logic in a LangGraph StateGraph using conditional_edges.
Nodes focus on business logic and return updated state (dict).
Routing functions check current_state and return next node name (string) or END.
This maintains the non-negotiable constraint: _FOUNDATION_TABLE remains the single source of truth.
"""

import logging
from typing import Optional, TypedDict
from datetime import datetime, timezone

from langgraph.graph import StateGraph, START, END

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
    """Manages Foundation loop orchestration via LangGraph StateGraph with conditional_edges routing."""

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
        self._logger = logging.getLogger(__name__)

        # Initialize node instances
        self.research_node = FoundationResearchNode(research_adapter, gateway, log_store)
        self.gate_node = FoundationGateNode(gate_adapter, gateway, log_store)

        # Build the graph
        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build and compile the Foundation StateGraph with conditional_edges routing.
        
        Routing is determined by TransitionTable, the single source of truth.
        Conditional edges consult routing functions that use TransitionTable
        to determine the next node. Nodes focus on business logic only.
        
        Uses bounded single-pass routing per invocation. Feedback outcomes
        (e.g. NEEDS_MORE/REVISE) are persisted as state and picked up on the
        next orchestrator run instead of looping indefinitely in-process.
        
        Nodes:
        - normalize_and_route: Entry point
        - needed_to_in_progress: Auto-transition from NEEDED to IN_PROGRESS
        - research: Wrapper around FoundationResearchNode
        - gate: Wrapper around FoundationGateNode
        """
        builder = StateGraph(FoundationRunState)

        # Add nodes (business logic only, routing handled by conditional_edges)
        builder.add_node("normalize_and_route", self._node_normalize_and_route)
        builder.add_node("needed_to_in_progress", self._node_needed_to_in_progress)
        builder.add_node("research", self._node_research_wrapper)
        builder.add_node("gate", self._node_gate_wrapper)

        # Entry point
        builder.add_edge(START, "normalize_and_route")
        
        # Conditional edges: routing determined by TransitionTable
        builder.add_conditional_edges(
            "normalize_and_route",
            self._route_normalize_and_route,
        )
        builder.add_conditional_edges(
            "needed_to_in_progress",
            self._route_needed_to_in_progress,
        )
        builder.add_conditional_edges(
            "research",
            self._route_research,
        )
        builder.add_conditional_edges(
            "gate",
            self._route_gate,
        )

        return builder.compile()

    def _node_normalize_and_route(self, state: FoundationRunState) -> FoundationRunState:
        """Entry point: normalize state from GitHub labels."""
        issue = self.gateway.get_issue(state["source_issue_number"])
        normalized = normalize_foundation_state_from_labels(issue.labels)
        current_state = normalized.state or FoundationState.FOUNDATION_NEEDED
        self._logger.info(
            f"  Issue #{state['source_issue_number']}: graph node=normalize_and_route, "
            f"state={current_state.value}"
        )
        return {
            **state,
            "current_state": current_state,
        }

    def _route_normalize_and_route(self, state: FoundationRunState) -> str:
        """Route from normalize_and_route using TransitionTable."""
        current_state = state.get("current_state")
        if current_state in TERMINAL_FOUNDATION_STATES:
            return END
        elif current_state == FoundationState.FOUNDATION_NEEDED:
            return "needed_to_in_progress"
        elif current_state == FoundationState.FOUNDATION_IN_PROGRESS:
            return "research"
        elif current_state == FoundationState.FOUNDATION_REVIEW:
            return "gate"
        else:
            return END

    def _node_needed_to_in_progress(self, state: FoundationRunState) -> FoundationRunState:
        """Auto-transition from FOUNDATION_NEEDED to FOUNDATION_IN_PROGRESS."""
        if state["current_state"] == FoundationState.FOUNDATION_NEEDED:
            next_state = get_next_foundation_state(
                FoundationState.FOUNDATION_NEEDED,
                FoundationEvent.FOUNDATION_STARTED,
            )
            self._logger.info(
                f"  Issue #{state['source_issue_number']}: graph node=needed_to_in_progress, "
                f"auto-transitioning needed → {next_state.value}"
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
                adapter_source="system",  # Auto-transition, no LLM
            )
            self.log_store.append(entry)
            self.gateway.post_comment(state["source_issue_number"], entry.to_comment())
        else:
            next_state = state["current_state"]

        return {
            **state,
            "current_state": next_state,
        }

    def _route_needed_to_in_progress(self, state: FoundationRunState) -> str:
        """Route from needed_to_in_progress using TransitionTable."""
        current_state = state.get("current_state")
        if current_state in TERMINAL_FOUNDATION_STATES:
            return END
        elif current_state == FoundationState.FOUNDATION_IN_PROGRESS:
            return "research"
        else:
            return END

    def _node_research_wrapper(self, state: FoundationRunState) -> FoundationRunState:
        """Wrapper around FoundationResearchNode. Update state with result."""
        self._logger.info(
            f"  Issue #{state['source_issue_number']}: graph node=research"
        )
        next_state = self.research_node.run(state["run_id"], state["source_issue_number"])

        return {
            **state,
            "current_state": next_state,
        }

    def _route_research(self, state: FoundationRunState) -> str:
        """Route from research using bounded single-pass semantics."""
        current_state = state.get("current_state")
        if current_state in TERMINAL_FOUNDATION_STATES:
            return END
        elif current_state == FoundationState.FOUNDATION_IN_PROGRESS:
            return END
        elif current_state == FoundationState.FOUNDATION_REVIEW:
            return "gate"  # RECOMMEND advances
        else:
            return END

    def _node_gate_wrapper(self, state: FoundationRunState) -> FoundationRunState:
        """Wrapper around FoundationGateNode. Update state with result."""
        self._logger.info(
            f"  Issue #{state['source_issue_number']}: graph node=gate"
        )
        next_state = self.gate_node.run(state["run_id"], state["source_issue_number"])

        return {
            **state,
            "current_state": next_state,
        }

    def _route_gate(self, state: FoundationRunState) -> str:
        """Route from gate using bounded single-pass semantics."""
        current_state = state.get("current_state")
        if current_state in TERMINAL_FOUNDATION_STATES:
            return END
        else:
            return END

    def invoke(self, initial_state: FoundationRunState, recursion_limit: int | None = None) -> FoundationRunState:
        """Invoke the graph with an initial state.
        
        Args:
            initial_state: FoundationRunState dict with run_id, source_issue_number, etc.
        
        Returns:
            Final state dict after graph execution.
        """
        if recursion_limit is None:
            return self._graph.invoke(initial_state)
        return self._graph.invoke(initial_state, config={"recursion_limit": recursion_limit})