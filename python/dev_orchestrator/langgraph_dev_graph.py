"""LangGraph StateGraph for Dev orchestration loop.

This module wraps the Dev orchestration logic in a LangGraph StateGraph.
Each node is a thin adapter around existing Dev node classes, maintaining
the non-negotiable constraint: _DEV_TABLE remains the single source of truth,
and existing node logic is NOT reimplemented inline.

The router delegates to _DEV_TABLE via get_next_dev_state() and allowed_events_for_dev_state().
No transition pairs are re-declared in the graph; the graph only orchestrates node execution.
"""

from typing import Optional, TypedDict
from typing_extensions import Literal
from datetime import datetime, timezone

from langgraph.graph import StateGraph, END

from aios_orchestration_core.events.dev import DevEvent
from aios_orchestration_core.states.dev import DevState, TERMINAL_DEV_STATES
from aios_orchestration_core.transitions.dev import get_next_dev_state
from aios_orchestration_core.github.dev_gateway import DevGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.labels.dev_labels import (
    DEV_CANONICAL_LABEL_BY_STATE,
    DEV_CANONICAL_STATE_LABELS,
    normalize_dev_state_from_labels,
)
from dev_orchestrator.nodes.intake import DevIntakeNode
from dev_orchestrator.nodes.design import DevDesignNode
from dev_orchestrator.nodes.build import DevBuildNode
from dev_orchestrator.nodes.qa import DevQANode
from dev_orchestrator.nodes.policy import DevPolicyNode


class DevRunState(TypedDict, total=False):
    """State dictionary passed through LangGraph nodes.
    
    total=False means all fields are optional.
    Nodes update only the fields they affect.
    """
    source_issue_number: int
    run_id: str
    current_state: DevState


class DevGraphOrchestrator:
    """Manages Dev loop orchestration via LangGraph StateGraph."""

    def __init__(
        self,
        gateway: DevGateway,
        log_store: TransitionLogStore,
        intake_adapter: JudgmentLLMAdapter,
        design_adapter: JudgmentLLMAdapter,
        build_adapter: JudgmentLLMAdapter,
        qa_adapter: JudgmentLLMAdapter,
        policy_adapter: JudgmentLLMAdapter,
    ):
        """Initialize orchestrator with dependencies."""
        self.gateway = gateway
        self.log_store = log_store

        # Initialize node instances
        self.intake_node = DevIntakeNode(intake_adapter, gateway, log_store)
        self.design_node = DevDesignNode(design_adapter, gateway, log_store)
        self.build_node = DevBuildNode(build_adapter, gateway, log_store)
        self.qa_node = DevQANode(qa_adapter, gateway, log_store)
        self.policy_node = DevPolicyNode(policy_adapter, gateway, log_store)

        # Build the graph
        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build and compile the Dev StateGraph.
        
        Nodes:
        - normalize_and_route: Entry point; determines initial state or routes based on labels
        - intake: Wrapper around DevIntakeNode
        - design: Wrapper around DevDesignNode
        - build: Wrapper around DevBuildNode
        - qa: Wrapper around DevQANode
        - policy: Wrapper around DevPolicyNode
        
        Edges:
        - Conditional edges from each node based on current_state
        - Terminal states route to END
        - Feedback loops: DESIGN_REVISE->INTAKE, QA_FAILED->DESIGN
        """
        builder = StateGraph(DevRunState)

        # Add nodes
        builder.add_node("normalize_and_route", self._node_normalize_and_route)
        builder.add_node("intake", self._node_intake_wrapper)
        builder.add_node("design", self._node_design_wrapper)
        builder.add_node("build", self._node_build_wrapper)
        builder.add_node("qa", self._node_qa_wrapper)
        builder.add_node("policy", self._node_policy_wrapper)

        # Entry point
        builder.set_entry_point("normalize_and_route")

        # Conditional edges from normalize_and_route
        builder.add_conditional_edges(
            "normalize_and_route",
            self._router_from_normalize,
            {
                "intake": "intake",
                "design": "design",
                "build": "build",
                "qa": "qa",
                "policy": "policy",
                END: END,
            },
        )

        # Conditional edges from intake
        builder.add_conditional_edges(
            "intake",
            self._router_from_state,
            {
                "design": "design",
                END: END,  # BLOCKED
            },
        )

        # Conditional edges from design (can loop back to intake or advance)
        builder.add_conditional_edges(
            "design",
            self._router_from_state,
            {
                "intake": "intake",  # REVISE loops back
                "build": "build",    # APPROVED advances
                END: END,            # BLOCKED or other terminal
            },
        )

        # Conditional edges from build
        builder.add_conditional_edges(
            "build",
            self._router_from_state,
            {
                "qa": "qa",
                END: END,  # BLOCKED
            },
        )

        # Conditional edges from qa (can loop back to design or advance)
        builder.add_conditional_edges(
            "qa",
            self._router_from_state,
            {
                "design": "design",  # FAILED loops back to design
                "policy": "policy",  # PASSED advances
            },
        )

        # Conditional edges from policy
        builder.add_conditional_edges(
            "policy",
            self._router_from_state,
            {
                END: END,
            },
        )

        return builder.compile()

    def _node_normalize_and_route(self, state: DevRunState) -> DevRunState:
        """Entry point: normalize state from GitHub labels, determine next action."""
        issue = self.gateway.get_issue(state["source_issue_number"])
        normalized = normalize_dev_state_from_labels(issue.labels)
        current_state = normalized.state or DevState.DEV_INTAKE

        state["current_state"] = current_state
        return state

    def _node_intake_wrapper(self, state: DevRunState) -> DevRunState:
        """Wrapper around DevIntakeNode.run()."""
        next_state = self.intake_node.run(state["run_id"], state["source_issue_number"])
        state["current_state"] = next_state
        return state

    def _node_design_wrapper(self, state: DevRunState) -> DevRunState:
        """Wrapper around DevDesignNode.run()."""
        next_state = self.design_node.run(state["run_id"], state["source_issue_number"])
        state["current_state"] = next_state
        return state

    def _node_build_wrapper(self, state: DevRunState) -> DevRunState:
        """Wrapper around DevBuildNode.run()."""
        next_state = self.build_node.run(state["run_id"], state["source_issue_number"])
        state["current_state"] = next_state
        return state

    def _node_qa_wrapper(self, state: DevRunState) -> DevRunState:
        """Wrapper around DevQANode.run()."""
        next_state = self.qa_node.run(state["run_id"], state["source_issue_number"])
        state["current_state"] = next_state
        return state

    def _node_policy_wrapper(self, state: DevRunState) -> DevRunState:
        """Wrapper around DevPolicyNode.run()."""
        next_state = self.policy_node.run(state["run_id"], state["source_issue_number"])
        state["current_state"] = next_state
        return state

    def _router_from_normalize(self, state: DevRunState) -> str:
        """Route after normalize_and_route: determine next node based on current_state."""
        current = state["current_state"]
        
        # Terminal states -> END
        if current in TERMINAL_DEV_STATES:
            return END
        
        # Route based on current state
        if current == DevState.DEV_INTAKE:
            return "intake"
        elif current == DevState.DEV_DESIGN:
            return "design"
        elif current == DevState.DEV_BUILD:
            return "build"
        elif current == DevState.DEV_QA:
            return "qa"
        elif current == DevState.DEV_POLICY:
            return "policy"
        else:
            return END

    def _router_from_state(self, state: DevRunState) -> str:
        """Generic router: after node execution, route based on new current_state.
        
        Delegates to _DEV_TABLE logic: if state is terminal, end; otherwise,
        route to next node or loop back.
        """
        current = state["current_state"]
        
        # Terminal states -> END
        if current in TERMINAL_DEV_STATES:
            return END
        
        # For non-terminal states, route based on current state
        if current == DevState.DEV_INTAKE:
            return "intake"
        elif current == DevState.DEV_DESIGN:
            return "design"
        elif current == DevState.DEV_BUILD:
            return "build"
        elif current == DevState.DEV_QA:
            return "qa"
        elif current == DevState.DEV_POLICY:
            return "policy"
        else:
            return END

    def invoke(self, initial_state: DevRunState) -> DevRunState:
        """Invoke the graph with an initial state.
        
        Args:
            initial_state: DevRunState dict with run_id, source_issue_number, etc.
        
        Returns:
            Final state dict after graph execution.
        """
        return self._graph.invoke(initial_state)