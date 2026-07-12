from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional
from uuid import uuid4

from aios_orchestration_core.core.circuit_breaker import BlockContext
from aios_orchestration_core.github.po_gateway import POGateway
from aios_orchestration_core.labels.po_labels import (
    PO_CANONICAL_LABEL_BY_STATE,
    PO_CANONICAL_STATE_LABELS,
)
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.policies.retry import RetryPolicy, RetryState
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.po import POState, TERMINAL_PO_STATES
from po_orchestrator.circuit_breaker import POCircuitBreaker
from po_orchestrator.langgraph_po_graph import POGraphOrchestrator, PORunState


@dataclass
class PORunRecord:
    run_id: str
    source_issue_number: int
    started_at_utc: str
    ended_at_utc: Optional[str] = None


@dataclass
class PORunRegistry:
    by_source_issue: Dict[int, PORunRecord] = field(default_factory=dict)
    retry_state_by_issue: Dict[int, RetryState] = field(default_factory=dict)

    def start_new_run(self, source_issue_number: int) -> PORunRecord:
        record = PORunRecord(
            run_id=str(uuid4()),
            source_issue_number=source_issue_number,
            started_at_utc=datetime.now(timezone.utc).isoformat(),
        )
        self.by_source_issue[source_issue_number] = record
        return record


def _normalize_po_state(labels: Iterable[str]) -> Optional[POState]:
    """Derive PO state from an issue's label set.

    Canonical labels take precedence.  Returns None if the state is
    ambiguous or unknown (caller defaults to PO_QUEUED).
    """
    from aios_orchestration_core.labels.po_labels import normalize_po_state_from_labels
    
    normalized = normalize_po_state_from_labels(labels)
    return normalized.state



class PORunOnceOrchestrator:
    """Single-issue PO run_once flow.

    Picks up a strategic-opportunity issue at any point in the PO pipeline
    and advances it as far as possible in one invocation.
    Uses LangGraph-backed orchestration internally.
    """

    def __init__(
        self,
        gateway: POGateway,
        log_store: TransitionLogStore,
        run_registry: PORunRegistry,
        prioritize_adapter: JudgmentLLMAdapter,
        create_features_adapter: JudgmentLLMAdapter,
        retry_policy: Optional[RetryPolicy] = None,
    ) -> None:
        self.gateway = gateway
        self.log_store = log_store
        self.run_registry = run_registry
        self.circuit_breaker = POCircuitBreaker(retry_policy or RetryPolicy(max_attempts=3), log_store)
        self.graph_orchestrator = POGraphOrchestrator(
            gateway, log_store, prioritize_adapter, create_features_adapter
        )

    def run_once(self, source_issue_number: int) -> PORunRecord:
        run = self.run_registry.start_new_run(source_issue_number)
        issue = self.gateway.get_issue(source_issue_number)
        current_state = _normalize_po_state(issue.labels) or POState.PO_QUEUED
        retry_state = self.run_registry.retry_state_by_issue.setdefault(
            source_issue_number, RetryState()
        )

        try:
            if current_state in TERMINAL_PO_STATES:
                run.ended_at_utc = datetime.now(timezone.utc).isoformat()
                return run

            # Prepare initial state for graph
            initial_state: PORunState = {
                "source_issue_number": source_issue_number,
                "run_id": run.run_id,
                "current_state": current_state,
            }

            # Invoke graph
            final_state = self.graph_orchestrator.invoke(initial_state)
            
            # Update run record with final state
            run.ended_at_utc = datetime.now(timezone.utc).isoformat()
            retry_state.attempts = 0

        except Exception as ex:
            resulting_state = self.circuit_breaker.handle_failure(
                run_id=run.run_id,
                issue_number=source_issue_number,
                from_state=current_state,
                retry_state=retry_state,
                context=BlockContext(
                    blocked_stage=current_state.value,
                    reason_code="RUN_ONCE_NODE_FAILURE",
                    reason_detail=str(ex),
                    last_error_class=type(ex).__name__,
                ),
            )
            if resulting_state == POState.PO_NEEDS_HUMAN:
                self.gateway.set_state_labels(
                    source_issue_number,
                    list(PO_CANONICAL_STATE_LABELS),
                    [PO_CANONICAL_LABEL_BY_STATE[POState.PO_NEEDS_HUMAN]],
                )
                self.gateway.post_comment(
                    source_issue_number,
                    "PO run_once: transitioned to needs-human after retry threshold",
                )

        run.ended_at_utc = datetime.now(timezone.utc).isoformat()
        return run

