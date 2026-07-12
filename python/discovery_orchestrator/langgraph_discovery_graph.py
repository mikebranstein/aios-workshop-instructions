"""LangGraph StateGraph for Discovery orchestration loop.

This module wraps the Discovery orchestration logic in a LangGraph StateGraph using conditional_edges.
Nodes focus on business logic and return updated state (dict).
Routing functions check current_state and return next node name (string) or END.
This maintains the non-negotiable constraint: _DISCOVERY_TABLE remains the single source of truth.
"""

from typing import Optional, TypedDict
from typing_extensions import Literal
from datetime import datetime, timezone
from dataclasses import field

from langgraph.graph import StateGraph, START, END

from aios_orchestration_core.events.discovery import DiscoveryEvent
from aios_orchestration_core.states.discovery import DiscoveryState, TERMINAL_DISCOVERY_STATES
from aios_orchestration_core.transitions.discovery import get_next_discovery_state
from aios_orchestration_core.labels.discovery_labels import (
    normalize_discovery_state_from_labels,
    DISCOVERY_CANONICAL_LABEL_BY_STATE,
    DISCOVERY_CANONICAL_STATE_LABELS,
)
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.runlog.models import TransitionLogEntry
from discovery_orchestrator.context import DiscoveryContext, DiscoveryRunResult
from discovery_orchestrator.nodes.idea_scout import IdeaScoutNode
from discovery_orchestrator.idea_scout_adapter import IdeaScoutAdapter


class DiscoveryRunState(TypedDict, total=False):
    """State dictionary passed through LangGraph nodes.

    total=False means all fields are optional.
    Nodes update only the fields they affect.
    """

    run_id: str
    current_state: DiscoveryState
    created_pm_idea_numbers: list = field(default_factory=list)
    deferred_count: int = 0
    dropped_count: int = 0
    halted_reason: Optional[str] = None


class DiscoveryGraphOrchestrator:
    """Manages Discovery loop orchestration via LangGraph StateGraph with conditional_edges routing."""

    def __init__(
        self,
        context: DiscoveryContext,
        idea_scout_adapter: IdeaScoutAdapter,
        pm_idea_store: "PMIdeaIssueStore",
        log_store: Optional[TransitionLogStore] = None,
    ):
        """Initialize orchestrator with dependencies."""
        self.context = context
        self.idea_scout_adapter = idea_scout_adapter
        self.pm_idea_store = pm_idea_store
        self.log_store = log_store

        # Initialize node instances
        self.idea_scout_node = IdeaScoutNode(idea_scout_adapter, pm_idea_store)

        # Build the graph
        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build and compile the Discovery StateGraph with conditional_edges routing.
        
        Routing is determined by TransitionTable, the single source of truth.
        Conditional edges consult routing functions that use TransitionTable
        to determine the next node. Nodes focus on business logic only.
        
        Nodes:
        - check_preconditions: Verify foundation gate and focus file
        - idea_scout: Wrapper around IdeaScoutNode
        """
        builder = StateGraph(DiscoveryRunState)

        # Add nodes (business logic only, routing handled by conditional_edges)
        builder.add_node("check_preconditions", self._node_check_preconditions)
        builder.add_node("idea_scout", self._node_idea_scout_wrapper)

        # Entry point
        builder.add_edge(START, "check_preconditions")
        
        # Conditional edges: routing determined by TransitionTable
        builder.add_conditional_edges(
            "check_preconditions",
            self._route_check_preconditions,
        )
        
        builder.add_edge("idea_scout", END)

        return builder.compile()

    def _node_check_preconditions(self, state: DiscoveryRunState) -> DiscoveryRunState:
        """Check foundation gate and focus file preconditions. Update state."""
        # Transition to RUNNING
        current_state = DiscoveryState.DISCOVERY_IDLE
        next_state = get_next_discovery_state(
            current_state, DiscoveryEvent.RUN_TRIGGERED
        )

        # Check foundation gate
        if not self.context.foundation_gate_passed:
            terminal_state = get_next_discovery_state(
                next_state, DiscoveryEvent.GATE_MISSING
            )
            self._log_transition(
                state,
                next_state,
                terminal_state,
                DiscoveryEvent.GATE_MISSING,
                "GATE_MISSING",
                "Foundation gate not passed",
            )
            return {
                **state,
                "current_state": terminal_state,
                "halted_reason": "Foundation gate not passed",
            }

        # Check focus file
        if not self.context.focus_file_exists or not self.context.focus_file_populated:
            terminal_state = get_next_discovery_state(
                next_state, DiscoveryEvent.FOCUS_MISSING
            )
            self._log_transition(
                state,
                next_state,
                terminal_state,
                DiscoveryEvent.FOCUS_MISSING,
                "FOCUS_MISSING",
                "docs/discovery-focus.md missing or empty",
            )
            return {
                **state,
                "current_state": terminal_state,
                "halted_reason": "docs/discovery-focus.md missing or empty",
            }

        # Preconditions passed
        return {
            **state,
            "current_state": next_state,
        }

    def _route_check_preconditions(self, state: DiscoveryRunState) -> str:
        """Route from check_preconditions using TransitionTable."""
        current_state = state.get("current_state")
        if current_state in TERMINAL_DISCOVERY_STATES:
            return END
        elif current_state == DiscoveryState.DISCOVERY_RUNNING:
            return "idea_scout"
        else:
            return END

    def _node_idea_scout_wrapper(self, state: DiscoveryRunState) -> DiscoveryRunState:
        """Wrapper around IdeaScoutNode. Update state with result."""
        final_state, created, deferred, dropped = self.idea_scout_node.run(
            creation_cap=self.context.creation_cap,
            context_summary="discovery run",
        )

        # Log transition
        self._log_transition(
            state,
            DiscoveryState.DISCOVERY_RUNNING,
            final_state,
            DiscoveryEvent.IDEA_SCOUT_COMPLETED,
            "IDEA_SCOUT_COMPLETED",
            f"Created {len(created)} PM-ideas, deferred {deferred}, dropped {dropped}",
        )

        return {
            **state,
            "current_state": final_state,
            "created_pm_idea_numbers": created,
            "deferred_count": deferred,
            "dropped_count": dropped,
        }

    def _log_transition(
        self,
        state: DiscoveryRunState,
        from_state: DiscoveryState,
        to_state: DiscoveryState,
        event: DiscoveryEvent,
        reason_code: str,
        reason_detail: str,
    ) -> None:
        """Log a transition if log_store is available."""
        if not self.log_store:
            return

        entry = TransitionLogEntry(
            loop_id="discovery",
            run_id=state.get("run_id", ""),
            issue_number=0,  # Discovery loop does not target specific issues
            from_state=from_state.value,
            to_state=to_state.value,
            trigger_event=event.value,
            reason_code=reason_code,
            reason_detail=reason_detail,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )
        self.log_store.append(entry)

    def invoke(self, initial_state: DiscoveryRunState) -> DiscoveryRunState:
        """Invoke the graph with an initial state.

        Args:
            initial_state: DiscoveryRunState dict with run_id, etc.

        Returns:
            Final state dict after graph execution.
        """
        return self._graph.invoke(initial_state)