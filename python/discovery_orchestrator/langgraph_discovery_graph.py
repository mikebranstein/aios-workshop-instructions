"""LangGraph StateGraph for Discovery orchestration loop.

This module wraps the Discovery orchestration logic in a LangGraph StateGraph.
Each node is a thin adapter around existing Discovery logic, maintaining the
non-negotiable constraint: _DISCOVERY_TABLE remains the single source of truth.

The router delegates to _DISCOVERY_TABLE via get_next_discovery_state() and
allowed_events_for_discovery_state(). No transition pairs are re-declared in
the graph; the graph only orchestrates node execution.
"""

from typing import Optional, TypedDict
from typing_extensions import Literal
from datetime import datetime, timezone
from dataclasses import field

from langgraph.graph import StateGraph, END

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
    """Manages Discovery loop orchestration via LangGraph StateGraph."""

    def __init__(
        self,
        context: DiscoveryContext,
        idea_scout_adapter: IdeaScoutAdapter,
        pm_idea_store: PMIdeaIssueStore,
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
        """Build and compile the Discovery StateGraph.

        Nodes:
        - check_preconditions: Verify foundation gate and focus file
        - idea_scout: Wrapper around IdeaScoutNode
        - complete: Terminal handler

        Edges:
        - Conditional edges based on precondition checks
        - Terminal states route to END
        """
        builder = StateGraph(DiscoveryRunState)

        # Add nodes
        builder.add_node("check_preconditions", self._node_check_preconditions)
        builder.add_node("idea_scout", self._node_idea_scout_wrapper)

        # Entry point
        builder.set_entry_point("check_preconditions")

        # Conditional edges from preconditions
        builder.add_conditional_edges(
            "check_preconditions",
            self._router_from_preconditions,
            {
                "idea_scout": "idea_scout",
                END: END,
            },
        )

        # Conditional edges from idea_scout
        builder.add_conditional_edges(
            "idea_scout",
            self._router_from_state,
            {
                END: END,
            },
        )

        return builder.compile()

    def _node_check_preconditions(self, state: DiscoveryRunState) -> DiscoveryRunState:
        """Check foundation gate and focus file preconditions."""
        # Transition to RUNNING
        current_state = DiscoveryState.DISCOVERY_IDLE
        next_state = get_next_discovery_state(
            current_state, DiscoveryEvent.RUN_TRIGGERED
        )
        state["current_state"] = next_state

        # Check foundation gate
        if not self.context.foundation_gate_passed:
            terminal_state = get_next_discovery_state(
                next_state, DiscoveryEvent.GATE_MISSING
            )
            state["current_state"] = terminal_state
            state["halted_reason"] = "Foundation gate not passed"
            self._log_transition(
                state,
                next_state,
                terminal_state,
                DiscoveryEvent.GATE_MISSING,
                "GATE_MISSING",
                "Foundation gate not passed",
            )
            return state

        # Check focus file
        if not self.context.focus_file_exists or not self.context.focus_file_populated:
            terminal_state = get_next_discovery_state(
                next_state, DiscoveryEvent.FOCUS_MISSING
            )
            state["current_state"] = terminal_state
            state["halted_reason"] = "docs/discovery-focus.md missing or empty"
            self._log_transition(
                state,
                next_state,
                terminal_state,
                DiscoveryEvent.FOCUS_MISSING,
                "FOCUS_MISSING",
                "docs/discovery-focus.md missing or empty",
            )
            return state

        # Preconditions passed, ready for idea scout
        state["current_state"] = next_state
        return state

    def _node_idea_scout_wrapper(self, state: DiscoveryRunState) -> DiscoveryRunState:
        """Wrapper around IdeaScoutNode.run()."""
        final_state, created, deferred, dropped = self.idea_scout_node.run(
            creation_cap=self.context.creation_cap,
            context_summary="discovery run",
        )

        state["current_state"] = final_state
        state["created_pm_idea_numbers"] = created
        state["deferred_count"] = deferred
        state["dropped_count"] = dropped

        # Log transition
        self._log_transition(
            state,
            DiscoveryState.DISCOVERY_RUNNING,
            final_state,
            DiscoveryEvent.IDEA_SCOUT_COMPLETED,
            "IDEA_SCOUT_COMPLETED",
            f"Created {len(created)} PM-ideas, deferred {deferred}, dropped {dropped}",
        )

        return state

    def _router_from_preconditions(self, state: DiscoveryRunState) -> str:
        """Route after precondition check: either proceed to idea_scout or end."""
        current = state["current_state"]

        # Terminal states (halted) -> END
        if current in TERMINAL_DISCOVERY_STATES:
            return END

        # DISCOVERY_RUNNING -> idea_scout
        if current == DiscoveryState.DISCOVERY_RUNNING:
            return "idea_scout"

        return END

    def _router_from_state(self, state: DiscoveryRunState) -> str:
        """Generic router: route based on current_state.

        Terminal states route to END; otherwise, route to next node.
        """
        current = state["current_state"]

        # Terminal states -> END
        if current in TERMINAL_DISCOVERY_STATES:
            return END

        return END

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