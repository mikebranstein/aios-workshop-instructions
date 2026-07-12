from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional
from uuid import uuid4

from aios_orchestration_core.core.circuit_breaker import BlockContext
from aios_orchestration_core.events.po import POEvent
from aios_orchestration_core.github.po_gateway import POGateway
from aios_orchestration_core.labels.po_labels import (
    PO_CANONICAL_LABEL_BY_STATE,
    PO_CANONICAL_STATE_LABELS,
    PO_LABEL_REGISTRY,
)
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.policies.retry import RetryPolicy, RetryState
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.runlog.sqlite_store import TransitionLogStore
from aios_orchestration_core.states.po import POState, TERMINAL_PO_STATES
from aios_orchestration_core.transitions.po import get_next_po_state
from po_orchestrator.circuit_breaker import POCircuitBreaker
from po_orchestrator.nodes.create_features import POCreateFeaturesNode
from po_orchestrator.nodes.prioritize import POPrioritizeNode


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
    canonical_hits = set()
    all_hits = set()
    for label in labels:
        state = PO_LABEL_REGISTRY.state_for_label(label)
        if state is not None:
            all_hits.add(state)
            if label in PO_LABEL_REGISTRY.all_canonical_labels:
                canonical_hits.add(state)
    if len(canonical_hits) == 1:
        return next(iter(canonical_hits))
    if len(all_hits) == 1:
        return next(iter(all_hits))
    return None


class PORunOnceOrchestrator:
    """Single-issue PO run_once flow.

    Picks up a strategic-opportunity issue at any point in the PO pipeline
    and advances it as far as possible in one invocation.
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
        self.prioritize_node = POPrioritizeNode(prioritize_adapter, gateway, log_store)
        self.create_features_node = POCreateFeaturesNode(create_features_adapter, gateway, log_store)
        self.circuit_breaker = POCircuitBreaker(retry_policy or RetryPolicy(max_attempts=3), log_store)

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

            if current_state == POState.PO_QUEUED:
                next_state = get_next_po_state(POState.PO_QUEUED, POEvent.ENTERED_PRIORITIZATION)
                self._apply_transition(
                    run.run_id, source_issue_number,
                    POState.PO_QUEUED, next_state, POEvent.ENTERED_PRIORITIZATION,
                    "ENTERED_PRIORITIZATION", "Strategic opportunity entered PO prioritization",
                )
                current_state = next_state

            if current_state == POState.PO_PRIORITIZING:
                current_state = self.prioritize_node.run(run.run_id, source_issue_number)

            if current_state in TERMINAL_PO_STATES:
                run.ended_at_utc = datetime.now(timezone.utc).isoformat()
                return run

            if current_state == POState.PO_CREATING_FEATURES:
                current_state = self.create_features_node.run(run.run_id, source_issue_number)

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

    def _apply_transition(
        self,
        run_id: str,
        issue_number: int,
        from_state: POState,
        to_state: POState,
        event: POEvent,
        reason_code: str,
        reason_detail: str,
    ) -> None:
        self.gateway.set_state_labels(
            issue_number,
            list(PO_CANONICAL_STATE_LABELS),
            [PO_CANONICAL_LABEL_BY_STATE[to_state]],
        )
        entry = TransitionLogEntry(
            loop_id="po",
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
