"""Shared helper for dev stage nodes.

Each dev stage node follows the same pattern:
  1. Fetch issue
  2. invoke_json(tool_type, {issue fields})
  3. Map decision string → DevEvent
  4. Compute next_state
  5. Atomically update labels
  6. Close if terminal
  7. Write TransitionLogEntry + comment
  8. Return next_state
"""
from datetime import datetime, timezone
from typing import Dict

from aios_orchestration_core.events.dev import DevEvent
from aios_orchestration_core.github.dev_gateway import DevGateway
from aios_orchestration_core.labels.dev_labels import DEV_CANONICAL_LABEL_BY_STATE, DEV_CANONICAL_STATE_LABELS
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.dev import DevState, TERMINAL_DEV_STATES
from aios_orchestration_core.transitions.dev import get_next_dev_state


def run_dev_stage_node(
    *,
    adapter: JudgmentLLMAdapter,
    gateway: DevGateway,
    log_store: TransitionLogStore,
    run_id: str,
    issue_number: int,
    tool_type: str,
    from_state: DevState,
    decision_to_event: Dict[str, DevEvent],
    reason_prefix: str,
) -> DevState:
    """Drive one dev stage: invoke LLM, transition state, log, comment, return next state."""
    issue = gateway.get_issue(issue_number)
    result = adapter.invoke_json(
        tool_type,
        {"issue_number": issue.number, "title": issue.title, "body": issue.body},
    )

    decision = result.payload["decision"]
    event = decision_to_event[decision]
    next_state = get_next_dev_state(from_state, event)

    gateway.set_state_labels(
        issue_number,
        list(DEV_CANONICAL_STATE_LABELS),
        [DEV_CANONICAL_LABEL_BY_STATE[next_state]],
    )

    if next_state in TERMINAL_DEV_STATES:
        reason = "completed" if next_state == DevState.DEV_RELEASED else "not planned"
        gateway.close_issue(issue_number, reason)

    entry = TransitionLogEntry(
        loop_id="dev",
        run_id=run_id,
        issue_number=issue_number,
        from_state=from_state.value,
        to_state=next_state.value,
        trigger_event=event.value,
        reason_code=f"{reason_prefix}_{decision}",
        reason_detail=result.payload.get("reason", f"{reason_prefix} decision"),
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )
    log_store.append(entry)
    gateway.post_comment(issue_number, entry.to_comment())
    return next_state
