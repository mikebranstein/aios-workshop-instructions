"""LangGraph StateGraph for ArchReview orchestration loop.

This module wraps the ArchReview orchestration logic in a LangGraph StateGraph using conditional_edges.
Nodes focus on business logic and return updated state (dict).
Routing functions check current_state and return next node name (string) or END.
This maintains the non-negotiable constraint: _ARCH_REVIEW_TABLE remains the single source of truth.
"""

from typing import Optional, TypedDict
from datetime import datetime, timezone

from langgraph.graph import StateGraph, START, END

from aios_orchestration_core.events.arch_review import ArchReviewEvent
from aios_orchestration_core.states.arch_review import (
    ArchReviewState,
    TERMINAL_ARCH_REVIEW_STATES,
)
from aios_orchestration_core.transitions.arch_review import get_next_arch_review_state
from aios_orchestration_core.labels.arch_review_labels import (
    normalize_arch_review_state_from_labels,
    ARCH_REVIEW_CANONICAL_LABEL_BY_STATE,
    ARCH_REVIEW_CANONICAL_STATE_LABELS,
)
from aios_orchestration_core.github.arch_review_gateway import ArchReviewGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.runlog.models import TransitionLogEntry
from arch_review_orchestrator.nodes.review import ArchReviewNode
from arch_review_orchestrator.nodes.planner import ArchRefactorPlannerNode


class ArchReviewRunState(TypedDict, total=False):
    """State dictionary passed through LangGraph nodes.

    total=False means all fields are optional.
    Nodes update only the fields they affect.
    """

    run_id: str
    source_issue_number: int
    current_state: ArchReviewState
    created_refactor_request_numbers: list = None


class ArchReviewGraphOrchestrator:
    """Manages ArchReview loop orchestration via LangGraph StateGraph with conditional_edges routing."""

    def __init__(
        self,
        gateway: ArchReviewGateway,
        log_store: TransitionLogStore,
        review_adapter: JudgmentLLMAdapter,
        planner_adapter: JudgmentLLMAdapter,
    ):
        """Initialize orchestrator with dependencies."""
        self.gateway = gateway
        self.log_store = log_store

        # Initialize node instances
        self.review_node = ArchReviewNode(review_adapter, gateway, log_store)
        self.planner_node = ArchRefactorPlannerNode(planner_adapter, gateway, log_store)

        # Build the graph
        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build and compile the ArchReview StateGraph with conditional_edges routing.
        
        Routing is determined by TransitionTable, the single source of truth.
        Conditional edges consult routing functions that use TransitionTable
        to determine the next node. Nodes focus on business logic only.
        
        Nodes:
        - normalize_and_route: Entry point
        - pending_to_in_progress: Auto-transition from PENDING to IN_PROGRESS
        - review: Wrapper around ArchReviewNode
        - planner: Wrapper around ArchRefactorPlannerNode
        - close_issue: Terminal handler to close the issue
        """
        builder = StateGraph(ArchReviewRunState)

        # Add nodes (business logic only, routing handled by conditional_edges)
        builder.add_node("normalize_and_route", self._node_normalize_and_route)
        builder.add_node("pending_to_in_progress", self._node_pending_to_in_progress)
        builder.add_node("review", self._node_review_wrapper)
        builder.add_node("planner", self._node_planner_wrapper)
        builder.add_node("close_issue", self._node_close_issue)

        # Entry point
        builder.add_edge(START, "normalize_and_route")
        
        # Conditional edges: routing determined by TransitionTable
        builder.add_conditional_edges(
            "normalize_and_route",
            self._route_normalize_and_route,
        )
        builder.add_conditional_edges(
            "pending_to_in_progress",
            self._route_pending_to_in_progress,
        )
        builder.add_conditional_edges(
            "review",
            self._route_review,
        )
        builder.add_conditional_edges(
            "planner",
            self._route_planner,
        )
        builder.add_edge("close_issue", END)

        return builder.compile()

    def _node_normalize_and_route(self, state: ArchReviewRunState) -> ArchReviewRunState:
        """Entry point: normalize state from GitHub labels."""
        issue = self.gateway.get_issue(state["source_issue_number"])
        normalized = normalize_arch_review_state_from_labels(issue.labels)
        current_state = (
            normalized.state or ArchReviewState.ARCH_REVIEW_PENDING
        )
        state["created_refactor_request_numbers"] = []

        return {
            **state,
            "current_state": current_state,
        }

    def _route_normalize_and_route(self, state: ArchReviewRunState) -> str:
        """Route from normalize_and_route using TransitionTable."""
        current_state = state.get("current_state")
        if current_state in TERMINAL_ARCH_REVIEW_STATES:
            return "close_issue"
        elif current_state == ArchReviewState.ARCH_REVIEW_PENDING:
            return "pending_to_in_progress"
        elif current_state == ArchReviewState.ARCH_REVIEW_IN_PROGRESS:
            return "review"
        elif current_state == ArchReviewState.ARCH_REFACTOR_PLANNED:
            return "planner"
        else:
            return "close_issue"

    def _node_pending_to_in_progress(self, state: ArchReviewRunState) -> ArchReviewRunState:
        """Auto-transition from PENDING to IN_PROGRESS. Update state."""
        if state["current_state"] == ArchReviewState.ARCH_REVIEW_PENDING:
            next_state = get_next_arch_review_state(
                ArchReviewState.ARCH_REVIEW_PENDING, ArchReviewEvent.EVALUATION_STARTED
            )

            # Set state label
            self.gateway.set_state_labels(
                state["source_issue_number"],
                list(ARCH_REVIEW_CANONICAL_STATE_LABELS),
                [ARCH_REVIEW_CANONICAL_LABEL_BY_STATE[next_state]],
            )

            # Log transition
            entry = TransitionLogEntry(
                loop_id="arch_review",
                run_id=state["run_id"],
                issue_number=state["source_issue_number"],
                from_state=ArchReviewState.ARCH_REVIEW_PENDING.value,
                to_state=next_state.value,
                trigger_event=ArchReviewEvent.EVALUATION_STARTED.value,
                reason_code="EVALUATION_STARTED",
                reason_detail="Starting architecture review",
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            )
            self.log_store.append(entry)
            self.gateway.post_comment(state["source_issue_number"], entry.to_comment())
        else:
            next_state = state["current_state"]

        return {
            **state,
            "current_state": next_state,
        }

    def _route_pending_to_in_progress(self, state: ArchReviewRunState) -> str:
        """Route from pending_to_in_progress using TransitionTable."""
        current_state = state.get("current_state")
        if current_state in TERMINAL_ARCH_REVIEW_STATES:
            return "close_issue"
        elif current_state == ArchReviewState.ARCH_REVIEW_IN_PROGRESS:
            return "review"
        else:
            return "close_issue"

    def _node_review_wrapper(self, state: ArchReviewRunState) -> ArchReviewRunState:
        """Wrapper around ArchReviewNode. Update state with result."""
        next_state = self.review_node.run(
            state["run_id"], state["source_issue_number"]
        )

        return {
            **state,
            "current_state": next_state,
        }

    def _route_review(self, state: ArchReviewRunState) -> str:
        """Route from review using TransitionTable."""
        current_state = state.get("current_state")
        if current_state in TERMINAL_ARCH_REVIEW_STATES:
            return "close_issue"
        elif current_state == ArchReviewState.ARCH_REFACTOR_PLANNED:
            return "planner"
        else:
            return "close_issue"

    def _node_planner_wrapper(self, state: ArchReviewRunState) -> ArchReviewRunState:
        """Wrapper around ArchRefactorPlannerNode. Update state with result."""
        next_state, created_numbers = self.planner_node.run(
            state["run_id"], state["source_issue_number"]
        )

        return {
            **state,
            "current_state": next_state,
            "created_refactor_request_numbers": created_numbers,
        }

    def _route_planner(self, state: ArchReviewRunState) -> str:
        """Route from planner using TransitionTable."""
        # Always go to close_issue after planner
        return "close_issue"

    def _node_close_issue(self, state: ArchReviewRunState) -> ArchReviewRunState:
        """Close the issue if in terminal state. Update state."""
        if state["current_state"] in TERMINAL_ARCH_REVIEW_STATES:
            self.gateway.close_issue(
                state["source_issue_number"], "arch review complete"
            )

        return state

    def invoke(self, initial_state: ArchReviewRunState) -> ArchReviewRunState:
        """Invoke the graph with an initial state.

        Args:
            initial_state: ArchReviewRunState dict with run_id, source_issue_number, etc.

        Returns:
            Final state dict after graph execution.
        """
        return self._graph.invoke(initial_state)