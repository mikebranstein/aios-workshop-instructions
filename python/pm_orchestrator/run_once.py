from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

from aios_orchestration_core.github.pm_gateway import PMGateway
from aios_orchestration_core.labels.pm_labels import PM_CANONICAL_LABEL_BY_STATE, PM_CANONICAL_STATE_LABELS, normalize_pm_state_from_labels
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.policies.retry import RetryPolicy, RetryState
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.pm import PMState
from pm_orchestrator.circuit_breaker import PMBlockContext, PMCircuitBreaker
from pm_orchestrator.migration.bridge import BridgeModeController, CleanRunCounter
from pm_orchestrator.langgraph_pm_graph import PMGraphOrchestrator, PMRunState


@dataclass
class PMRunRecord:
    run_id: str
    source_issue_number: int
    linked_prior_run_id: Optional[str]
    started_at_utc: str
    ended_at_utc: Optional[str] = None
    current_state: Optional[str] = None


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
    """PM run_once flow using LangGraph StateGraph orchestration.

    Wraps PMGraphOrchestrator (LangGraph implementation) with circuit breaker,
    bridge mode controller, and run registry for resilience and migration support.
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
        self.circuit_breaker = PMCircuitBreaker(retry_policy or RetryPolicy(max_attempts=3), log_store)
        self.handoff_contract_version = handoff_contract_version
        self.prompt_version = prompt_version
        self._bridge_exit_notified = False
        
        # Create LangGraph orchestrator
        self.graph_orchestrator = PMGraphOrchestrator(
            gateway=gateway,
            log_store=log_store,
            phase1_adapter=phase1_adapter,
            research_planning_adapter=research_planning_adapter,
            synthesis_adapter=synthesis_adapter,
            phase2_adapter=phase2_adapter,
            min_research_count=min_research_count,
            min_synthesis_confidence=min_synthesis_confidence,
        )
        
        # Keep node references for backward compatibility / debugging
        self.phase1_node = self.graph_orchestrator.phase1_node
        self.research_planning_node = self.graph_orchestrator.research_planning_node
        self.synthesis_node = self.graph_orchestrator.synthesis_node
        self.phase2_node = self.graph_orchestrator.phase2_node
        self.min_research_count = min_research_count

    def run_once(self, source_issue_number: int, external_resume_link_run_id: Optional[str] = None) -> PMRunRecord:
        """Execute PM orchestration loop once using LangGraph graph.invoke().
        
        Wraps graph execution with circuit breaker, bridge mode, and run tracking.
        """
        run = self.run_registry.start_new_run(source_issue_number, linked_prior_run_id=external_resume_link_run_id)

        issue = self.gateway.get_issue(source_issue_number)
        normalized = normalize_pm_state_from_labels(issue.labels)
        had_conflict = bool(normalized.conflict_labels)
        current_state = normalized.state or PMState.PM_QUEUED
        retry_state = self.run_registry.retry_state_by_issue.setdefault(source_issue_number, RetryState())

        # Update phase1 node dual-write config based on bridge controller
        self.phase1_node.config.dual_write_legacy_labels = self.bridge_controller.dual_write_legacy_labels

        try:
            # Prepare initial state for graph
            initial_state: PMRunState = {
                "source_issue_number": source_issue_number,
                "run_id": run.run_id,
                "current_state": current_state,
                "handoff_contract_version": self.handoff_contract_version,
                "prompt_version": self.prompt_version,
            }
            
            # Invoke graph and get final state
            final_state = self.graph_orchestrator.invoke(initial_state)
            final_current_state = final_state.get("current_state", current_state)
            
            retry_state.attempts = 0
            
        except Exception as ex:
            # Handle failure via circuit breaker (outside graph)
            resulting_state = self.circuit_breaker.handle_failure(
                run_id=run.run_id,
                issue_number=source_issue_number,
                from_state=current_state,
                retry_state=retry_state,
                context=PMBlockContext(
                    blocked_stage=current_state.value,
                    reason_code="RUN_ONCE_GRAPH_FAILURE",
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
            final_current_state = resulting_state

        self.bridge_controller.record_run(had_conflict=had_conflict)
        if not self.bridge_controller.dual_write_legacy_labels and not self._bridge_exit_notified:
            self.gateway.post_comment(source_issue_number, "PM migration bridge exited: legacy dual-write disabled after clean-run threshold")
            self._bridge_exit_notified = True

        run.ended_at_utc = datetime.now(timezone.utc).isoformat()
        run.current_state = final_current_state.value if hasattr(final_current_state, "value") else str(final_current_state)
        return run
