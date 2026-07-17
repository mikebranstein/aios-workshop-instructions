"""LangGraph StateGraph for Foundation orchestration loop.

Every create phase transitions to a separate LLM-driven verify phase before promotion.
_FOUNDATION_TABLE remains the single source of truth for all transitions.
"""

import logging
from datetime import datetime, timezone
from typing import TypedDict

MAX_FOUNDATION_RESEARCH_AREAS = 25

from langgraph.graph import END, START, StateGraph

from aios_orchestration_core.events.foundation import FoundationEvent
from aios_orchestration_core.github.foundation_gateway import FoundationGateway
from aios_orchestration_core.labels.foundation_labels import (
    FOUNDATION_CANONICAL_LABEL_BY_STATE,
    FOUNDATION_CANONICAL_STATE_LABELS,
    normalize_foundation_state_from_labels,
)
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.states.foundation import FoundationState, TERMINAL_FOUNDATION_STATES
from aios_orchestration_core.transitions.foundation import get_next_foundation_state
from foundation_orchestrator.nodes.gate import FoundationGateNode
from foundation_orchestrator.nodes.research import FoundationResearchNode


class FoundationRunState(TypedDict, total=False):
    source_issue_number: int
    run_id: str
    current_state: FoundationState


class FoundationGraphOrchestrator:
    def __init__(
        self,
        gateway: FoundationGateway,
        log_store: TransitionLogStore,
        research_adapter: JudgmentLLMAdapter,
        gate_adapter: JudgmentLLMAdapter,
    ):
        self.gateway = gateway
        self.log_store = log_store
        self.research_node = FoundationResearchNode(research_adapter, gateway, log_store)
        self.gate_node = FoundationGateNode(gate_adapter, gateway, log_store)
        self._logger = logging.getLogger(__name__)
        self._graph = self._build_graph()

    # ------------------------------------------------------------------ graph

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(FoundationRunState)

        for name, fn in [
            ("normalize_and_route",               self._node_normalize_and_route),
            ("needed_to_intent_capture_create",    self._node_needed_to_intent_capture_create),
            ("intent_capture_create",              self._node_intent_capture_create),
            ("intent_capture_verify",              self._node_intent_capture_verify),
            ("shell_design_create",                self._node_shell_design_create),
            ("shell_design_verify",                self._node_shell_design_verify),
            ("backlog_build_create",               self._node_backlog_build_create),
            ("backlog_build_verify",               self._node_backlog_build_verify),
            ("readiness_assess_create",            self._node_readiness_assess_create),
            ("readiness_assess_verify",            self._node_readiness_assess_verify),
            ("handoff_pack_create",                self._node_handoff_pack_create),
            ("handoff_pack_verify",                self._node_handoff_pack_verify),
        ]:
            builder.add_node(name, fn)

        builder.add_edge(START, "normalize_and_route")

        for name, fn in [
            ("normalize_and_route",               self._route_normalize_and_route),
            ("needed_to_intent_capture_create",    self._route_needed_to_intent_capture_create),
            ("intent_capture_create",              self._route_intent_capture_create),
            ("intent_capture_verify",              self._route_intent_capture_verify),
            ("shell_design_create",                self._route_shell_design_create),
            ("shell_design_verify",                self._route_shell_design_verify),
            ("backlog_build_create",               self._route_backlog_build_create),
            ("backlog_build_verify",               self._route_backlog_build_verify),
            ("readiness_assess_create",            self._route_readiness_assess_create),
            ("readiness_assess_verify",            self._route_readiness_assess_verify),
            ("handoff_pack_create",                self._route_handoff_pack_create),
            ("handoff_pack_verify",                self._route_handoff_pack_verify),
        ]:
            builder.add_conditional_edges(name, fn)

        return builder.compile()

    # -------------------------------------------------------- shared helpers

    def _apply_event(
        self,
        state: FoundationRunState,
        from_state: FoundationState,
        event: FoundationEvent,
        reason_code: str,
        reason_detail: str,
        adapter_source: str,
    ) -> FoundationState:
        next_state = get_next_foundation_state(from_state, event)
        issue_number = state["source_issue_number"]
        self.gateway.set_state_labels(
            issue_number,
            list(FOUNDATION_CANONICAL_STATE_LABELS),
            [FOUNDATION_CANONICAL_LABEL_BY_STATE[next_state]],
        )
        entry = TransitionLogEntry(
            loop_id="foundation",
            run_id=state["run_id"],
            issue_number=issue_number,
            from_state=from_state.value,
            to_state=next_state.value,
            trigger_event=event.value,
            reason_code=reason_code,
            reason_detail=reason_detail,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            adapter_source=adapter_source,
        )
        self.log_store.append(entry)
        self.gateway.post_comment(issue_number, entry.to_comment())
        return next_state

    def _llm_verify_phase(self, state: FoundationRunState, phase: str) -> str:
        """Invoke the gate LLM for a phase-specific verification. Returns APPROVE/REVISE/BLOCK."""
        issue_number = state["source_issue_number"]
        issue = self.gateway.get_issue(issue_number)
        payload = self.gate_node.adapter.invoke_json(
            "foundation_gate",
            {
                "phase": phase,
                "issue_number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "comments": self.gateway.get_issue_comments(issue_number),
                "foundation_markdown": self.gateway.read_foundation_markdown(),
                "linked_research": [
                    {"number": r.number, "title": r.title, "body": r.body, "open": r.open}
                    for r in self.gateway.list_linked_research_issues(issue_number)
                ],
            },
        ).payload or {}
        return payload.get("decision", "REVISE_FOUNDATION")

    def _plan_and_sync_research_areas(self, issue_number: int, issue, foundation_markdown: str) -> None:
        """Plan research areas via LLM and create missing sub-issues. Idempotent."""
        existing = self.gateway.list_linked_research_issues(issue_number)
        if existing:
            return  # backlog already initialised — don't re-plan
        result = self.research_node.adapter.invoke_json(
            "foundation_research_plan",
            {
                "issue_number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "foundation_markdown": foundation_markdown,
            },
        )
        raw = result.payload.get("research_areas")
        if not isinstance(raw, list):
            raise ValueError("foundation_research_plan must return research_areas as an array")
        areas = [a.strip() for a in raw if isinstance(a, str) and a.strip()]
        areas = list(dict.fromkeys(areas))[:MAX_FOUNDATION_RESEARCH_AREAS]
        if not areas:
            raise ValueError("foundation_research_plan returned no valid research areas")
        self._logger.info(f"  Issue #{issue_number}: backlog_build_create — planned {len(areas)} research area(s)")
        for area in areas:
            title = f"[foundation-research] {area} for #{issue_number}"
            body = (
                f"## Research Area\n{area}\n\n"
                f"## Decision Area\n<!-- enter the architectural decision domain -->\n\n"
                f"## Scope\nDocument findings and recommendation for the foundational question above.\n"
            )
            self.gateway.ensure_research_issue(
                foundation_issue_number=issue_number,
                title=title,
                body=body,
                labels=[],
            )

    # -------------------------------------------------------- normalize entry

    def _node_normalize_and_route(self, state: FoundationRunState) -> FoundationRunState:
        issue = self.gateway.get_issue(state["source_issue_number"])
        normalized = normalize_foundation_state_from_labels(issue.labels)
        return {**state, "current_state": normalized.state or FoundationState.FOUNDATION_NEEDED}

    def _route_normalize_and_route(self, state: FoundationRunState) -> str:
        s = state.get("current_state")
        if s in TERMINAL_FOUNDATION_STATES:
            return END
        return {
            FoundationState.FOUNDATION_NEEDED:                    "needed_to_intent_capture_create",
            FoundationState.FOUNDATION_INTENT_CAPTURE_CREATE:     "intent_capture_create",
            FoundationState.FOUNDATION_INTENT_CAPTURE_VERIFY:     "intent_capture_verify",
            FoundationState.FOUNDATION_SHELL_DESIGN_CREATE:       "shell_design_create",
            FoundationState.FOUNDATION_SHELL_DESIGN_VERIFY:       "shell_design_verify",
            FoundationState.FOUNDATION_BACKLOG_BUILD_CREATE:      "backlog_build_create",
            FoundationState.FOUNDATION_BACKLOG_BUILD_VERIFY:      "backlog_build_verify",
            FoundationState.FOUNDATION_READINESS_ASSESS_CREATE:   "readiness_assess_create",
            FoundationState.FOUNDATION_READINESS_ASSESS_VERIFY:   "readiness_assess_verify",
            FoundationState.FOUNDATION_HANDOFF_PACK_CREATE:       "handoff_pack_create",
            FoundationState.FOUNDATION_HANDOFF_PACK_VERIFY:       "handoff_pack_verify",
        }.get(s, END)

    # ------------------------------------------------- NEEDED → INTENT CREATE

    def _node_needed_to_intent_capture_create(self, state: FoundationRunState) -> FoundationRunState:
        next_state = self._apply_event(
            state, FoundationState.FOUNDATION_NEEDED, FoundationEvent.FOUNDATION_STARTED,
            "FOUNDATION_STARTED", "Starting foundation workflow", "system",
        )
        return {**state, "current_state": next_state}

    def _route_needed_to_intent_capture_create(self, state: FoundationRunState) -> str:
        return "intent_capture_create" if state.get("current_state") == FoundationState.FOUNDATION_INTENT_CAPTURE_CREATE else END

    # -------------------------------------------- INTENT CAPTURE CREATE/VERIFY

    def _node_intent_capture_create(self, state: FoundationRunState) -> FoundationRunState:
        self.gateway.post_comment(state["source_issue_number"], "Intent capture create: drafting context and constraints.")
        next_state = self._apply_event(
            state, FoundationState.FOUNDATION_INTENT_CAPTURE_CREATE, FoundationEvent.INTENT_CAPTURE_CREATED,
            "INTENT_CAPTURE_CREATED", "Intent artifacts created", "system",
        )
        return {**state, "current_state": next_state}

    def _route_intent_capture_create(self, state: FoundationRunState) -> str:
        return "intent_capture_verify" if state.get("current_state") == FoundationState.FOUNDATION_INTENT_CAPTURE_VERIFY else END

    def _node_intent_capture_verify(self, state: FoundationRunState) -> FoundationRunState:
        decision = self._llm_verify_phase(state, "intent_capture_verify")
        event = (
            FoundationEvent.INTENT_CAPTURE_VERIFIED if decision == "APPROVE_FOUNDATION"
            else FoundationEvent.INTENT_CAPTURE_BLOCK if decision == "BLOCK_FOUNDATION"
            else FoundationEvent.INTENT_CAPTURE_REVISE
        )
        next_state = self._apply_event(
            state, FoundationState.FOUNDATION_INTENT_CAPTURE_VERIFY, event,
            f"INTENT_CAPTURE_VERIFY_{decision}", "Intent capture verification",
            self.gate_node.adapter.adapter_source,
        )
        return {**state, "current_state": next_state}

    def _route_intent_capture_verify(self, state: FoundationRunState) -> str:
        s = state.get("current_state")
        if s == FoundationState.FOUNDATION_SHELL_DESIGN_CREATE:
            return "shell_design_create"
        if s == FoundationState.FOUNDATION_INTENT_CAPTURE_CREATE:
            return "intent_capture_create"
        return END

    # ------------------------------------------------ SHELL DESIGN CREATE/VERIFY

    def _node_shell_design_create(self, state: FoundationRunState) -> FoundationRunState:
        self.gateway.post_comment(state["source_issue_number"], "Shell design create: drafting architecture baseline.")
        next_state = self._apply_event(
            state, FoundationState.FOUNDATION_SHELL_DESIGN_CREATE, FoundationEvent.SHELL_DESIGN_CREATED,
            "SHELL_DESIGN_CREATED", "Shell design artifacts created", "system",
        )
        return {**state, "current_state": next_state}

    def _route_shell_design_create(self, state: FoundationRunState) -> str:
        return "shell_design_verify" if state.get("current_state") == FoundationState.FOUNDATION_SHELL_DESIGN_VERIFY else END

    def _node_shell_design_verify(self, state: FoundationRunState) -> FoundationRunState:
        decision = self._llm_verify_phase(state, "shell_design_verify")
        event = (
            FoundationEvent.SHELL_DESIGN_VERIFIED if decision == "APPROVE_FOUNDATION"
            else FoundationEvent.SHELL_DESIGN_BLOCK if decision == "BLOCK_FOUNDATION"
            else FoundationEvent.SHELL_DESIGN_REVISE
        )
        next_state = self._apply_event(
            state, FoundationState.FOUNDATION_SHELL_DESIGN_VERIFY, event,
            f"SHELL_DESIGN_VERIFY_{decision}", "Shell design verification",
            self.gate_node.adapter.adapter_source,
        )
        return {**state, "current_state": next_state}

    def _route_shell_design_verify(self, state: FoundationRunState) -> str:
        s = state.get("current_state")
        if s == FoundationState.FOUNDATION_BACKLOG_BUILD_CREATE:
            return "backlog_build_create"
        if s == FoundationState.FOUNDATION_SHELL_DESIGN_CREATE:
            return "shell_design_create"
        return END

    # ----------------------------------------------- BACKLOG BUILD CREATE/VERIFY

    def _node_backlog_build_create(self, state: FoundationRunState) -> FoundationRunState:
        issue_number = state["source_issue_number"]
        issue = self.gateway.get_issue(issue_number)
        foundation_markdown = self.gateway.read_foundation_markdown()
        self._plan_and_sync_research_areas(issue_number, issue, foundation_markdown)
        self.gateway.post_comment(issue_number, "Backlog build create: research areas planned and sub-issues synced.")
        next_state = self._apply_event(
            state, FoundationState.FOUNDATION_BACKLOG_BUILD_CREATE, FoundationEvent.BACKLOG_BUILD_CREATED,
            "BACKLOG_BUILD_CREATED", "Backlog build artifacts created", "system",
        )
        return {**state, "current_state": next_state}

    def _route_backlog_build_create(self, state: FoundationRunState) -> str:
        return "backlog_build_verify" if state.get("current_state") == FoundationState.FOUNDATION_BACKLOG_BUILD_VERIFY else END

    def _node_backlog_build_verify(self, state: FoundationRunState) -> FoundationRunState:
        # Delegates to the FoundationResearchNode LLM judgment (separate verify adapter).
        next_state = self.research_node.run(state["run_id"], state["source_issue_number"])
        return {**state, "current_state": next_state}

    def _route_backlog_build_verify(self, state: FoundationRunState) -> str:
        s = state.get("current_state")
        if s == FoundationState.FOUNDATION_READINESS_ASSESS_CREATE:
            return "readiness_assess_create"
        if s == FoundationState.FOUNDATION_BACKLOG_BUILD_CREATE:
            return "backlog_build_create"
        return END

    # ------------------------------------------ READINESS ASSESS CREATE/VERIFY

    def _node_readiness_assess_create(self, state: FoundationRunState) -> FoundationRunState:
        issue_number = state["source_issue_number"]
        self.gateway.post_comment(
            issue_number,
            f"Readiness assess create: open_research={self.gateway.count_open_linked_research_issues(issue_number)}, "
            f"closed_research={self.gateway.count_closed_linked_research_issues(issue_number)}.",
        )
        next_state = self._apply_event(
            state, FoundationState.FOUNDATION_READINESS_ASSESS_CREATE, FoundationEvent.READINESS_ASSESS_CREATED,
            "READINESS_ASSESS_CREATED", "Readiness artifacts created", "system",
        )
        return {**state, "current_state": next_state}

    def _route_readiness_assess_create(self, state: FoundationRunState) -> str:
        return "readiness_assess_verify" if state.get("current_state") == FoundationState.FOUNDATION_READINESS_ASSESS_VERIFY else END

    def _node_readiness_assess_verify(self, state: FoundationRunState) -> FoundationRunState:
        # Delegates to FoundationGateNode LLM judgment.
        next_state = self.gate_node.run(state["run_id"], state["source_issue_number"])
        return {**state, "current_state": next_state}

    def _route_readiness_assess_verify(self, state: FoundationRunState) -> str:
        s = state.get("current_state")
        if s == FoundationState.FOUNDATION_HANDOFF_PACK_CREATE:
            return "handoff_pack_create"
        if s == FoundationState.FOUNDATION_READINESS_ASSESS_CREATE:
            return "readiness_assess_create"
        return END

    # ---------------------------------------------- HANDOFF PACK CREATE/VERIFY

    def _node_handoff_pack_create(self, state: FoundationRunState) -> FoundationRunState:
        self.gateway.post_comment(state["source_issue_number"], "Handoff pack create: synthesising DISCOVERY-FOCUS.md.")
        next_state = self._apply_event(
            state, FoundationState.FOUNDATION_HANDOFF_PACK_CREATE, FoundationEvent.HANDOFF_PACK_CREATED,
            "HANDOFF_PACK_CREATED", "Handoff artifacts created", "system",
        )
        return {**state, "current_state": next_state}

    def _route_handoff_pack_create(self, state: FoundationRunState) -> str:
        return "handoff_pack_verify" if state.get("current_state") == FoundationState.FOUNDATION_HANDOFF_PACK_VERIFY else END

    def _node_handoff_pack_verify(self, state: FoundationRunState) -> FoundationRunState:
        focus_content = self.gateway.read_discovery_focus() if self.gateway.discovery_focus_exists() else ""
        payload = self.research_node.adapter.invoke_json(
            "foundation_discovery_focus_verify",
            {"focus_content": focus_content},
        ).payload or {}
        passed = bool(payload.get("passed", False))
        event = FoundationEvent.HANDOFF_PACK_VERIFIED if passed else FoundationEvent.HANDOFF_PACK_REVISE
        next_state = self._apply_event(
            state, FoundationState.FOUNDATION_HANDOFF_PACK_VERIFY, event,
            f"HANDOFF_PACK_VERIFY_{'PASS' if passed else 'REVISE'}",
            payload.get("verdict", "Handoff pack verification"),
            self.research_node.adapter.adapter_source,
        )
        if next_state == FoundationState.FOUNDATION_APPROVED:
            self.gateway.close_issue(state["source_issue_number"], "completed")
        return {**state, "current_state": next_state}

    def _route_handoff_pack_verify(self, state: FoundationRunState) -> str:
        s = state.get("current_state")
        if s == FoundationState.FOUNDATION_HANDOFF_PACK_CREATE:
            return "handoff_pack_create"
        return END

    # ------------------------------------------------------------------- invoke

    def invoke(self, initial_state: FoundationRunState, recursion_limit: int | None = None) -> FoundationRunState:
        if recursion_limit is None:
            return self._graph.invoke(initial_state)
        return self._graph.invoke(initial_state, config={"recursion_limit": recursion_limit})