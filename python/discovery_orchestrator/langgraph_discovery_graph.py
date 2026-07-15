"""LangGraph StateGraph for Discovery orchestration loop.

This module wraps the Discovery orchestration logic in a LangGraph StateGraph using conditional_edges.
Nodes focus on business logic and return updated state (dict).
Routing functions check current_state and return next node name (string) or END.
This maintains the non-negotiable constraint: _DISCOVERY_TABLE remains the single source of truth.
"""

import logging
from typing import Optional, TypedDict
from datetime import datetime, timezone

from langgraph.graph import StateGraph, START, END

from aios_orchestration_core.events.discovery import DiscoveryEvent
from aios_orchestration_core.github.discovery_gateway import DiscoveryGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.states.discovery import DiscoveryState, TERMINAL_DISCOVERY_STATES
from aios_orchestration_core.transitions.discovery import get_next_discovery_state
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.runlog.models import TransitionLogEntry
from discovery_orchestrator.nodes.idea_scout import IdeaScoutNode


class DiscoveryRunState(TypedDict, total=False):
    """State dictionary passed through LangGraph nodes.

    total=False means all fields are optional.
    Nodes update only the fields they affect.
    """

    run_id: str
    current_state: DiscoveryState
    created_pm_idea_numbers: list
    deferred_count: int
    dropped_count: int
    halted_reason: Optional[str]


class DiscoveryGraphOrchestrator:
    """Manages Discovery loop orchestration via LangGraph StateGraph with conditional_edges routing."""

    def __init__(
        self,
        gateway: DiscoveryGateway,
        llm_adapter: JudgmentLLMAdapter,
        log_store: Optional[TransitionLogStore] = None,
        creation_cap: int = 3,
        batch_cap: int = 5,
    ):
        """Initialize orchestrator with dependencies."""
        self.gateway = gateway
        self.llm_adapter = llm_adapter
        self.log_store = log_store
        self.creation_cap = creation_cap
        self.batch_cap = batch_cap
        self._logger = logging.getLogger(__name__)

        # Initialize node instances
        self.idea_scout_node = IdeaScoutNode(llm_adapter, gateway)

        # Build the graph
        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build and compile the Discovery StateGraph with conditional_edges routing.

        Nodes:
        - check_preconditions: Verify foundation gate and focus file (G1 source-state + precondition check)
        - idea_scout: Wrapper around IdeaScoutNode (LLM invocation + issue creation)
        """
        builder = StateGraph(DiscoveryRunState)

        builder.add_node("check_preconditions", self._node_check_preconditions)
        builder.add_node("idea_scout", self._node_idea_scout_wrapper)

        builder.add_edge(START, "check_preconditions")

        builder.add_conditional_edges(
            "check_preconditions",
            self._route_check_preconditions,
        )

        builder.add_edge("idea_scout", END)

        return builder.compile()

    def _node_check_preconditions(self, state: DiscoveryRunState) -> DiscoveryRunState:
        """Check foundation gate and focus file preconditions. Apply G1 source-state gate."""
        # Transition to RUNNING
        current_state = DiscoveryState.DISCOVERY_IDLE
        next_state = get_next_discovery_state(current_state, DiscoveryEvent.RUN_TRIGGERED)

        # Load context fresh from gateway (not cached) for each run
        context = self.gateway.get_context()

        # G4 preconditions: foundation gate must be passed
        if not context.foundation_gate_passed:
            terminal_state = get_next_discovery_state(next_state, DiscoveryEvent.GATE_MISSING)
            self._logger.warning("check_preconditions: foundation gate not passed — halting")
            self._log_transition(
                state, next_state, terminal_state,
                DiscoveryEvent.GATE_MISSING, "GATE_MISSING", "Foundation gate not passed",
            )
            return {
                **state,
                "current_state": terminal_state,
                "halted_reason": "Foundation gate not passed",
            }

        # G4 preconditions: focus file must exist and be populated
        if not context.focus_file_exists or not context.focus_file_populated:
            terminal_state = get_next_discovery_state(next_state, DiscoveryEvent.FOCUS_MISSING)
            self._logger.warning("check_preconditions: DISCOVERY-FOCUS.md missing or empty — halting")
            self._log_transition(
                state, next_state, terminal_state,
                DiscoveryEvent.FOCUS_MISSING, "FOCUS_MISSING", "DISCOVERY-FOCUS.md missing or empty",
            )
            return {
                **state,
                "current_state": terminal_state,
                "halted_reason": "DISCOVERY-FOCUS.md missing or empty",
            }

        # G4 preconditions: discovery-focus:approved label must exist
        if not context.discovery_focus_approved:
            terminal_state = get_next_discovery_state(next_state, DiscoveryEvent.FOCUS_MISSING)
            self._logger.warning(
                "check_preconditions: DISCOVERY-FOCUS.md not yet approved — halting. "
                "Review DISCOVERY-FOCUS.md and apply discovery-focus:approved label."
            )
            self._log_transition(
                state, next_state, terminal_state,
                DiscoveryEvent.FOCUS_MISSING, "FOCUS_NOT_APPROVED",
                "DISCOVERY-FOCUS.md exists but discovery-focus:approved label not found",
            )
            return {
                **state,
                "current_state": terminal_state,
                "halted_reason": (
                    "DISCOVERY-FOCUS.md has not been approved. "
                    "Review DISCOVERY-FOCUS.md, complete any placeholder sections, "
                    "then apply the discovery-focus:approved label to the tracking issue."
                ),
            }

        self._logger.info("check_preconditions: preconditions passed — routing to idea_scout")
        return {**state, "current_state": next_state}

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
        """Wrapper around IdeaScoutNode. Updates state with run results."""
        self._logger.info("idea_scout: invoking LLM for discovery candidates")
        final_state, created, deferred, dropped = self.idea_scout_node.run(
            run_id=state.get("run_id", ""),
            creation_cap=self.creation_cap,
            batch_cap=self.batch_cap,
        )

        self._log_transition(
            state,
            DiscoveryState.DISCOVERY_RUNNING,
            final_state,
            DiscoveryEvent.IDEA_SCOUT_COMPLETED,
            "IDEA_SCOUT_COMPLETED",
            f"Created {len(created)} pm-ideas, deferred {deferred}, dropped {dropped}",
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
        """Log a transition to the log store if available."""
        if not self.log_store:
            return
        entry = TransitionLogEntry(
            loop_id="discovery",
            run_id=state.get("run_id", ""),
            issue_number=0,
            from_state=from_state.value,
            to_state=to_state.value,
            trigger_event=event.value,
            reason_code=reason_code,
            reason_detail=reason_detail,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            adapter_source=self.llm_adapter.adapter_source,
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
