from aios_orchestration_core.events.dev import DevEvent
from aios_orchestration_core.github.dev_gateway import DevGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.dev import DevState
from dev_orchestrator.nodes._stage_helper import run_dev_stage_node

_DECISION_MAP = {
    "APPROVED": DevEvent.INTAKE_APPROVED,
    "BLOCKED": DevEvent.INTAKE_BLOCKED,
}


class DevIntakeNode:
    def __init__(self, adapter: JudgmentLLMAdapter, gateway: DevGateway, log_store: TransitionLogStore) -> None:
        self.adapter, self.gateway, self.log_store = adapter, gateway, log_store

    def run(self, run_id: str, issue_number: int) -> DevState:
        return run_dev_stage_node(
            adapter=self.adapter, gateway=self.gateway, log_store=self.log_store,
            run_id=run_id, issue_number=issue_number,
            tool_type="dev_intake", from_state=DevState.DEV_INTAKE,
            decision_to_event=_DECISION_MAP, reason_prefix="DEV_INTAKE",
        )
