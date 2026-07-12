from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

from aios_orchestration_core.events.pm import PMEvent
from aios_orchestration_core.github.pm_gateway import PMGateway
from aios_orchestration_core.labels.pm_labels import PM_CANONICAL_LABEL_BY_STATE, PM_CANONICAL_STATE_LABELS, normalize_pm_state_from_labels
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.policies.retry import RetryPolicy, RetryState
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.pm import PMState
from aios_orchestration_core.transitions.pm import get_next_pm_state
from pm_orchestrator.circuit_breaker import PMBlockContext, PMCircuitBreaker
from pm_orchestrator.migration.bridge import BridgeModeController, CleanRunCounter
from pm_orchestrator.nodes.phase1 import PMPhase1Node, Phase1Config
from pm_orchestrator.nodes.phase2_decision import PMPhase2DecisionNode
from pm_orchestrator.nodes.research_closure_gate import evaluate_research_closure_gate
from pm_orchestrator.nodes.research_planning import PMResearchPlanningNode
from pm_orchestrator.nodes.synthesis import PMResearchSynthesisNode, SynthesisGateConfig


@dataclass
class PMRunRecord:
    run_id: str
    source_issue_number: int
    linked_prior_run_id: Optional[str]
    started_at_utc: str
    ended_at_utc: Optional[str] = None


@dataclass
class PMRunRegistry:
    by_source_issue: Dict[int, PMRunRecord] = field(default_factory=dict)
    retry_state_by_issue: Dict[int, RetryState] = field(default_factory=dict)

    def start_new_run(self, source_issue_number: int, linked_prior_run_id: Optional[str]) -> PMRunRecord:
        record = PMRunRecord(
            run_id=str(uuid4()),
            source_issue_number=source_issue_number,
            linked_prior_run_id=linked_prior_run_id,
            started_at_utc=datetime.now(timezone.utc).isoformat(),
        )
        self.by_source_issue[source_issue_number] = record
        return record


class PMRunOnceOrchestrator:
    """PM run_once flow.

    LangGraph remains the target runtime architecture; this run_once is a
    deterministic orchestration shell used pending graph assembly.
    """

    def __init__(
        self,
        gateway: PMGateway,
        log_store: TransitionLogStore,
        run_registry: PMRunRegistry,
        phase1_adapter: JudgmentLLMAdapter,
        research_planning_adapter: JudgmentLLMAdapter,
        synthesis_adapter: JudgmentLLMAdapter,
        phase2_adapter: JudgmentLLMAdapter,
        retry_policy: Optional[RetryPolicy] = None,
        min_research_count: int = 1,
        min_synthesis_confidence: float = 0.75,
        handoff_contract_version: str = "1.0.0",
        prompt_version: str = "pm-pilot-v1",
    ):
        self.gateway = gateway
        self.log_store = log_store
        self.run_registry = run_registry
        self.bridge_controller = BridgeModeController(counter=CleanRunCounter(required_consecutive_clean_runs=10))
        self.phase1_node = PMPhase1Node(
            phase1_adapter,
            gateway,
            log_store,
            config=Phase1Config(dual_write_legacy_labels=True),
        )
        self.research_planning_node = PMResearchPlanningNode(research_planning_adapter, gateway)
        self.synthesis_node = PMResearchSynthesisNode(
            synthesis_adapter,
            SynthesisGateConfig(
                min_confidence_score=min_synthesis_confidence,
                min_closed_linked_research_count=min_research_count,
            ),
        )
        self.phase2_node = PMPhase2DecisionNode(phase2_adapter, gateway)
        self.circuit_breaker = PMCircuitBreaker(retry_policy or RetryPolicy(max_attempts=3), log_store)
        self.min_research_count = min_research_count
        self.handoff_contract_version = handoff_contract_version
        self.prompt_version = prompt_version
        self._bridge_exit_notified = False

    def run_once(self, source_issue_number: int, external_resume_link_run_id: Optional[str] = None) -> PMRunRecord:
        run = self.run_registry.start_new_run(source_issue_number, linked_prior_run_id=external_resume_link_run_id)

        issue = self.gateway.get_issue(source_issue_number)
        normalized = normalize_pm_state_from_labels(issue.labels)
        had_conflict = bool(normalized.conflict_labels)
        current_state = normalized.state or PMState.PM_QUEUED
        retry_state = self.run_registry.retry_state_by_issue.setdefault(source_issue_number, RetryState())

        self.phase1_node.config.dual_write_legacy_labels = self.bridge_controller.dual_write_legacy_labels

        try:
            if current_state == PMState.PM_QUEUED:
                if "foundation-approved" not in issue.labels:
                    self.bridge_controller.record_run(had_conflict=had_conflict)
                    run.ended_at_utc = datetime.now(timezone.utc).isoformat()
                    return run
                next_state = get_next_pm_state(PMState.PM_QUEUED, PMEvent.FOUNDATION_GATE_PASSED)
                self._apply_transition(run.run_id, issue.number, current_state, next_state, PMEvent.FOUNDATION_GATE_PASSED, "FOUNDATION_GATE", "Foundation gate present on source issue")
                current_state = next_state

            if current_state == PMState.PM_PHASE1_VALIDATING:
                current_state = self.phase1_node.run(run.run_id, issue.number)

            if current_state in {PMState.PM_DEFERRED, PMState.PM_BLOCKED, PMState.PM_ESCALATED, PMState.PM_OUTPUT_PUBLISHED, PMState.PM_NEEDS_HUMAN}:
                self.bridge_controller.record_run(had_conflict=had_conflict)
                run.ended_at_utc = datetime.now(timezone.utc).isoformat()
                return run

            if current_state == PMState.PM_RESEARCH_PLANNING:
                self.research_planning_node.run(issue.number)
                next_state = get_next_pm_state(PMState.PM_RESEARCH_PLANNING, PMEvent.RESEARCH_TASKS_CREATED)
                self._apply_transition(run.run_id, issue.number, current_state, next_state, PMEvent.RESEARCH_TASKS_CREATED, "RESEARCH_TASKS_CREATED", "Research tasks planned")
                current_state = next_state

            if current_state == PMState.PM_RESEARCH_WAITING:
                closure = evaluate_research_closure_gate(self.gateway, issue.number, self.min_research_count)
                if not closure.passed:
                    self.gateway.post_comment(issue.number, f"PM run_once: research waiting remains active. reason={closure.reason}")
                    self.bridge_controller.record_run(had_conflict=had_conflict)
                    run.ended_at_utc = datetime.now(timezone.utc).isoformat()
                    return run
                next_state = get_next_pm_state(PMState.PM_RESEARCH_WAITING, PMEvent.LINKED_RESEARCH_ALL_CLOSED)
                self._apply_transition(run.run_id, issue.number, current_state, next_state, PMEvent.LINKED_RESEARCH_ALL_CLOSED, "RESEARCH_CLOSED", "All linked research issues are closed")
                current_state = next_state

            if current_state == PMState.PM_RESEARCH_SYNTHESIZING:
                synthesis = self.synthesis_node.run(issue.number, self.gateway.count_closed_linked_research_issues(issue.number))
                next_state = get_next_pm_state(PMState.PM_RESEARCH_SYNTHESIZING, PMEvent.SYNTHESIS_READY)
                self._apply_transition(run.run_id, issue.number, current_state, next_state, PMEvent.SYNTHESIS_READY, "SYNTHESIS_READY", "Synthesis passed hybrid gate")
                current_state = next_state

                final_state = self.phase2_node.run(
                    run_id=run.run_id,
                    issue_number=issue.number,
                    synthesis_summary=synthesis.summary,
                    synthesis_confidence=synthesis.confidence_score,
                    prompt_version=self.prompt_version,
                    handoff_contract_version=self.handoff_contract_version,
                )
                current_state = final_state

            retry_state.attempts = 0
        except Exception as ex:
            resulting_state = self.circuit_breaker.handle_failure(
                run_id=run.run_id,
                issue_number=source_issue_number,
                from_state=current_state,
                retry_state=retry_state,
                context=PMBlockContext(
                    blocked_stage=current_state.value,
                    reason_code="RUN_ONCE_NODE_FAILURE",
                    reason_detail=str(ex),
                    last_error_class=type(ex).__name__,
                ),
            )
            if resulting_state == PMState.PM_NEEDS_HUMAN:
                self.gateway.set_state_labels(
                    source_issue_number,
                    list(PM_CANONICAL_STATE_LABELS),
                    [PM_CANONICAL_LABEL_BY_STATE[PMState.PM_NEEDS_HUMAN]],
                )
                self.gateway.post_comment(source_issue_number, "PM run_once: transitioned to needs-human after retry threshold")

        self.bridge_controller.record_run(had_conflict=had_conflict)
        if not self.bridge_controller.dual_write_legacy_labels and not self._bridge_exit_notified:
            self.gateway.post_comment(source_issue_number, "PM migration bridge exited: legacy dual-write disabled after clean-run threshold")
            self._bridge_exit_notified = True

        run.ended_at_utc = datetime.now(timezone.utc).isoformat()
        return run

    def _apply_transition(
        self,
        run_id: str,
        issue_number: int,
        from_state: PMState,
        to_state: PMState,
        event: PMEvent,
        reason_code: str,
        reason_detail: str,
    ) -> None:
        self.gateway.set_state_labels(
            issue_number,
            list(PM_CANONICAL_STATE_LABELS),
            [PM_CANONICAL_LABEL_BY_STATE[to_state]],
        )
        entry = TransitionLogEntry(
            run_id=run_id,
            issue_number=issue_number,
            from_state=from_state.value,
            to_state=to_state.value,
            trigger_event=event.value,
            reason_code=reason_code,
            reason_detail=reason_detail,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )
        self.log_store.append(entry)
        self.gateway.post_comment(issue_number, entry.to_comment())
