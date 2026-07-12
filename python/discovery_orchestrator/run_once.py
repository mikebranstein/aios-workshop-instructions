"""Discovery run_once orchestrator using LangGraph.

Refactored to use DiscoveryGraphOrchestrator (LangGraph implementation) instead
of inline orchestration logic. Maintains bounded discovery semantics with
circuit breaker and run registry support.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from aios_orchestration_core.events.discovery import DiscoveryEvent
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.states.discovery import DiscoveryState
from aios_orchestration_core.policies.retry import RetryPolicy, RetryState
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from discovery_orchestrator.context import DiscoveryContext, DiscoveryRunResult
from discovery_orchestrator.idea_scout_adapter import IdeaScoutAdapter
from discovery_orchestrator.langgraph_discovery_graph import (
    DiscoveryGraphOrchestrator,
    DiscoveryRunState,
)


@dataclass
class PMIdeaIssueStore:
    """Simple in-memory store for created pm-idea issues (used in tests)."""

    issues: Dict[int, Dict] = field(default_factory=dict)
    _next: int = 1000

    def create(self, title: str, body: str) -> int:
        """Create a new pm-idea issue and return its number."""
        self._next += 1
        self.issues[self._next] = {
            "title": title,
            "body": body,
            "labels": {"pm-idea", "pm-idea-auto"},
        }
        return self._next



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

    Checks preconditions (foundation gate, focus file), invokes idea-scout,
    and creates pm-idea issues up to creation_cap. Orchestration is managed
    by LangGraph StateGraph via DiscoveryGraphOrchestrator.
    """

    def __init__(
        self,
        context: DiscoveryContext,
        idea_scout: IdeaScoutAdapter,
        pm_idea_store: PMIdeaIssueStore,
        run_registry: Optional[DiscoveryRunRegistry] = None,
        log_store: Optional[TransitionLogStore] = None,
        retry_policy: Optional[RetryPolicy] = None,
    ) -> None:
        self.context = context
        self.idea_scout = idea_scout
        self.pm_idea_store = pm_idea_store
        self.run_registry = run_registry or DiscoveryRunRegistry()
        self.log_store = log_store
        self.retry_policy = retry_policy or RetryPolicy(max_attempts=3)

        # Create LangGraph orchestrator
        self.graph_orchestrator = DiscoveryGraphOrchestrator(
            context=context,
            idea_scout_adapter=idea_scout,
            pm_idea_store=pm_idea_store,
            log_store=log_store,
        )

    def run(self) -> DiscoveryRunResult:
        """Execute one bounded discovery run via LangGraph.

        Returns:
            DiscoveryRunResult with final state and outcome metrics.
        """
        # Create run record
        run_record = self.run_registry.start_new_run()

        # Prepare initial state for graph
        initial_state: DiscoveryRunState = {
            "run_id": run_record.run_id,
            "current_state": None,
            "created_pm_idea_numbers": [],
            "deferred_count": 0,
            "dropped_count": 0,
            "halted_reason": None,
        }

        try:
            # Invoke graph orchestrator
            final_state = self.graph_orchestrator.invoke(initial_state)

            # Update run record with results
            run_record.ended_at_utc = datetime.now(timezone.utc).isoformat()
            run_record.created_pm_idea_numbers = final_state.get(
                "created_pm_idea_numbers", []
            )
            run_record.deferred_count = final_state.get("deferred_count", 0)
            run_record.dropped_count = final_state.get("dropped_count", 0)
            run_record.halted_reason = final_state.get("halted_reason", None)

            # Return result
            return DiscoveryRunResult(
                state=final_state["current_state"].value,
                created_pm_idea_numbers=run_record.created_pm_idea_numbers,
                deferred_count=run_record.deferred_count,
                dropped_count=run_record.dropped_count,
                halted_reason=run_record.halted_reason,
            )

        except Exception as ex:
            # Mark run as ended with error
            run_record.ended_at_utc = datetime.now(timezone.utc).isoformat()

            if self.log_store is not None:
                self.log_store.append(
                    TransitionLogEntry(
                        loop_id="discovery",
                        run_id=run_record.run_id,
                        issue_number=0,
                        from_state=DiscoveryState.DISCOVERY_RUNNING.value,
                        to_state=DiscoveryState.DISCOVERY_HALTED_NO_GATE.value,
                        trigger_event=DiscoveryEvent.GATE_MISSING.value,
                        blocked_stage=DiscoveryState.DISCOVERY_RUNNING.value,
                        reason_code="RUN_ONCE_NODE_FAILURE",
                        reason_detail=(
                            f"{str(ex)}; "
                            f"last_error_class={type(ex).__name__}"
                        ),
                        timestamp_utc=datetime.now(timezone.utc).isoformat(),
                        adapter_source="system",
                    )
                )

            # Return halted result
            return DiscoveryRunResult(
                state="DISCOVERY_HALTED_NO_GATE",  # Safe default on error
                halted_reason=f"Discovery run failed: {str(ex)}",
            )