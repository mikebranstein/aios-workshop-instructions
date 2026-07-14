"""Discovery run_once orchestrator using LangGraph.

Uses DiscoveryGraphOrchestrator (LangGraph implementation) for bounded discovery
semantics. Circuit breaker handles exception escalation to DISCOVERY_HALTED_NEEDS_HUMAN.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from aios_orchestration_core.core.circuit_breaker import BlockContext
from aios_orchestration_core.events.discovery import DiscoveryEvent
from aios_orchestration_core.github.discovery_gateway import DiscoveryGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.states.discovery import DiscoveryState
from aios_orchestration_core.policies.retry import RetryPolicy, RetryState
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from discovery_orchestrator.circuit_breaker import DiscoveryCircuitBreaker
from discovery_orchestrator.context import DiscoveryContext, DiscoveryRunResult
from discovery_orchestrator.langgraph_discovery_graph import (
    DiscoveryGraphOrchestrator,
    DiscoveryRunState,
)


@dataclass
class DiscoveryRunRecord:
    """Record of one bounded discovery run."""

    run_id: str
    started_at_utc: str
    ended_at_utc: Optional[str] = None
    created_pm_idea_numbers: List[int] = field(default_factory=list)
    deferred_count: int = 0
    dropped_count: int = 0
    halted_reason: Optional[str] = None


@dataclass
class DiscoveryRunRegistry:
    """Registry of discovery runs by run_id."""

    by_run_id: Dict[str, DiscoveryRunRecord] = field(default_factory=dict)
    retry_state_by_run: Dict[str, RetryState] = field(default_factory=dict)

    def start_new_run(self) -> DiscoveryRunRecord:
        """Create and register a new discovery run."""
        record = DiscoveryRunRecord(
            run_id=str(uuid4()),
            started_at_utc=datetime.now(timezone.utc).isoformat(),
        )
        self.by_run_id[record.run_id] = record
        return record


class DiscoveryRunOnceOrchestrator:
    """Bounded discovery orchestrator using LangGraph.

    Checks preconditions (foundation gate, focus file), invokes idea-scout LLM,
    and creates pm-idea issues up to creation_cap. Orchestration is managed by
    LangGraph StateGraph via DiscoveryGraphOrchestrator.

    Mirrors the structure of FoundationRunOnceOrchestrator.
    """

    def __init__(
        self,
        gateway: DiscoveryGateway,
        llm_adapter: JudgmentLLMAdapter,
        run_registry: Optional[DiscoveryRunRegistry] = None,
        log_store: Optional[TransitionLogStore] = None,
        retry_policy: Optional[RetryPolicy] = None,
        creation_cap: int = 3,
        batch_cap: int = 5,
    ) -> None:
        self.gateway = gateway
        self.llm_adapter = llm_adapter
        self.run_registry = run_registry or DiscoveryRunRegistry()
        self.log_store = log_store or TransitionLogStore()

        self.graph_orchestrator = DiscoveryGraphOrchestrator(
            gateway=gateway,
            llm_adapter=llm_adapter,
            log_store=self.log_store,
            creation_cap=creation_cap,
            batch_cap=batch_cap,
        )
        self.circuit_breaker = DiscoveryCircuitBreaker(
            retry_policy or RetryPolicy(max_attempts=3),
            self.log_store,
        )

    def run(self) -> DiscoveryRunResult:
        """Execute one bounded discovery run via LangGraph.

        Returns:
            DiscoveryRunResult with final state and outcome metrics.
        """
        run_record = self.run_registry.start_new_run()
        retry_state = self.run_registry.retry_state_by_run.setdefault(
            run_record.run_id, RetryState()
        )

        initial_state: DiscoveryRunState = {
            "run_id": run_record.run_id,
            "current_state": None,
            "created_pm_idea_numbers": [],
            "deferred_count": 0,
            "dropped_count": 0,
            "halted_reason": None,
        }

        try:
            final_state = self.graph_orchestrator.invoke(initial_state)
            retry_state.attempts = 0

            run_record.ended_at_utc = datetime.now(timezone.utc).isoformat()
            run_record.created_pm_idea_numbers = final_state.get("created_pm_idea_numbers", [])
            run_record.deferred_count = final_state.get("deferred_count", 0)
            run_record.dropped_count = final_state.get("dropped_count", 0)
            run_record.halted_reason = final_state.get("halted_reason")

            return DiscoveryRunResult(
                state=final_state["current_state"].value,
                created_pm_idea_numbers=run_record.created_pm_idea_numbers,
                deferred_count=run_record.deferred_count,
                dropped_count=run_record.dropped_count,
                halted_reason=run_record.halted_reason,
            )

        except Exception as ex:
            run_record.ended_at_utc = datetime.now(timezone.utc).isoformat()

            resulting = self.circuit_breaker.handle_failure(
                run_id=run_record.run_id,
                issue_number=0,
                from_state=DiscoveryState.DISCOVERY_RUNNING,
                retry_state=retry_state,
                context=BlockContext(
                    blocked_stage=DiscoveryState.DISCOVERY_RUNNING.value,
                    reason_code="RUN_ONCE_NODE_FAILURE",
                    reason_detail=str(ex),
                    last_error_class=type(ex).__name__,
                ),
            )

            halted_state = (
                DiscoveryState.DISCOVERY_HALTED_NEEDS_HUMAN
                if resulting == DiscoveryState.DISCOVERY_HALTED_NEEDS_HUMAN
                else DiscoveryState.DISCOVERY_HALTED_NO_GATE
            )

            return DiscoveryRunResult(
                state=halted_state.value,
                halted_reason=f"Discovery run failed: {ex}",
            )
