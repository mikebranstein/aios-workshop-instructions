"""LangGraph StateGraph for Dev orchestration loop.

This module wraps the Dev orchestration logic in a LangGraph StateGraph using conditional_edges.
Nodes focus on business logic and return updated state (dict).
Routing functions check current_state and return next node name (string) or END.
This maintains the non-negotiable constraint: _DEV_TABLE remains the single source of truth.
Supports feedback loops: DESIGN_REVISE->INTAKE, QA_FAILED->DESIGN.
"""

from typing import Optional, TypedDict

from langgraph.graph import StateGraph, START, END

from aios_orchestration_core.events.dev import DevEvent
from aios_orchestration_core.states.dev import DevState, TERMINAL_DEV_STATES
from aios_orchestration_core.transitions.dev import get_next_dev_state
from aios_orchestration_core.github.dev_gateway import DevGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.labels.dev_labels import (
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
    """Manages Dev loop orchestration via LangGraph StateGraph with conditional_edges routing."""

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
        """Build and compile the Dev StateGraph with conditional_edges routing.
        
        Routing is determined by TransitionTable, the single source of truth.
        Conditional edges consult routing functions that use TransitionTable
        to determine the next node. Nodes focus on business logic only.
        
        Supports feedback loops:
        - DESIGN_REVISE -> intake
        - QA_FAILED -> design
        
        Nodes:
        - normalize_and_route: Entry point
        - intake, design, build, qa, policy: Node wrappers
        """
        builder = StateGraph(DevRunState)

        # Add nodes (business logic only, routing handled by conditional_edges)
        builder.add_node("normalize_and_route", self._node_normalize_and_route)
        builder.add_node("intake", self._node_intake_wrapper)
        builder.add_node("design", self._node_design_wrapper)
        builder.add_node("build", self._node_build_wrapper)
        builder.add_node("qa", self._node_qa_wrapper)
        builder.add_node("policy", self._node_policy_wrapper)

        # Entry point
        builder.add_edge(START, "normalize_and_route")
        
        # Conditional edges: routing determined by TransitionTable
        builder.add_conditional_edges(
            "normalize_and_route",
            self._route_normalize_and_route,
        )
        builder.add_conditional_edges(
            "intake",
            self._route_intake,
        )
        builder.add_conditional_edges(
            "design",
            self._route_design,
        )
        builder.add_conditional_edges(
            "build",
            self._route_build,
        )
        builder.add_conditional_edges(
            "qa",
            self._route_qa,
        )
        builder.add_edge("policy", END)

        return builder.compile()

    def _node_normalize_and_route(self, state: DevRunState) -> DevRunState:
        """Entry point: normalize state from GitHub labels."""
        issue = self.gateway.get_issue(state["source_issue_number"])
        normalized = normalize_dev_state_from_labels(issue.labels)
        current_state = normalized.state or DevState.DEV_INTAKE

        return {
            **state,
            "current_state": current_state,
        }

    def _route_normalize_and_route(self, state: DevRunState) -> str:
        """Route from normalize_and_route using TransitionTable."""
        current_state = state.get("current_state")
        if current_state in TERMINAL_DEV_STATES:
            return END
        elif current_state == DevState.DEV_INTAKE:
            return "intake"
        elif current_state == DevState.DEV_DESIGN:
            return "design"
        elif current_state == DevState.DEV_BUILD:
            return "build"
        elif current_state == DevState.DEV_QA:
            return "qa"
        elif current_state == DevState.DEV_POLICY:
            return "policy"
        else:
            return END

    def _node_intake_wrapper(self, state: DevRunState) -> DevRunState:
        """Wrapper around DevIntakeNode. Update state with result."""
        next_state = self.intake_node.run(state["run_id"], state["source_issue_number"])

        return {
            **state,
            "current_state": next_state,
        }

    def _route_intake(self, state: DevRunState) -> str:
        """Route from intake using TransitionTable."""
        current_state = state.get("current_state")
        if current_state in TERMINAL_DEV_STATES:
            return END
        elif current_state == DevState.DEV_DESIGN:
            return "design"
        else:
            return END

    def _node_design_wrapper(self, state: DevRunState) -> DevRunState:
        """Wrapper around DevDesignNode. Update state with result."""
        next_state = self.design_node.run(state["run_id"], state["source_issue_number"])

        return {
            **state,
            "current_state": next_state,
        }

    def _route_design(self, state: DevRunState) -> str:
        """Route from design using TransitionTable, supporting feedback loops."""
        current_state = state.get("current_state")
        if current_state in TERMINAL_DEV_STATES:
            return END
        elif current_state == DevState.DEV_INTAKE:
            return "intake"  # DESIGN_REVISE loops back
        elif current_state == DevState.DEV_BUILD:
            return "build"  # APPROVED advances
        else:
            return END

    def _node_build_wrapper(self, state: DevRunState) -> DevRunState:
        """Wrapper around DevBuildNode. Update state with result."""
        next_state = self.build_node.run(state["run_id"], state["source_issue_number"])

        return {
            **state,
            "current_state": next_state,
        }

    def _route_build(self, state: DevRunState) -> str:
        """Route from build using TransitionTable."""
        current_state = state.get("current_state")
        if current_state in TERMINAL_DEV_STATES:
            return END
        elif current_state == DevState.DEV_QA:
            return "qa"
        else:
            return END

    def _node_qa_wrapper(self, state: DevRunState) -> DevRunState:
        """Wrapper around DevQANode. Update state with result."""
        next_state = self.qa_node.run(state["run_id"], state["source_issue_number"])

        return {
            **state,
            "current_state": next_state,
        }

    def _route_qa(self, state: DevRunState) -> str:
        """Route from qa using TransitionTable, supporting feedback loops."""
        current_state = state.get("current_state")
        if current_state in TERMINAL_DEV_STATES:
            return END
        elif current_state == DevState.DEV_DESIGN:
            return "design"  # QA_FAILED loops back
        elif current_state == DevState.DEV_POLICY:
            return "policy"  # PASSED advances
        else:
            return END

    def _node_policy_wrapper(self, state: DevRunState) -> DevRunState:
        """Wrapper around DevPolicyNode. Update state with result."""
        next_state = self.policy_node.run(state["run_id"], state["source_issue_number"])

        return {
            **state,
            "current_state": next_state,
        }

    def invoke(self, initial_state: DevRunState) -> DevRunState:
        """Invoke the graph with an initial state.
        
        Args:
            initial_state: DevRunState dict with run_id, source_issue_number, etc.
        
        Returns:
            Final state dict after graph execution.
        """
        return self._graph.invoke(initial_state)