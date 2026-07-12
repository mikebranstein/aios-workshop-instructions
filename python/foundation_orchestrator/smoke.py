import tempfile

from aios_orchestration_core.github.foundation_gateway import (
    FoundationArtifactState,
    FoundationGitHubGateway,
    FoundationIssue,
)
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from foundation_orchestrator.run_once import FoundationRunOnceOrchestrator, FoundationRunRegistry


class _S:
    def __init__(self, payload):
        self.payload = payload

    def invoke_json(self, *a, **kw):
        return type("R", (), {"payload": self.payload, "model": "smoke"})()


def _full_artifact_state() -> FoundationArtifactState:
    return FoundationArtifactState(
        decision_pack_exists=True,
        adr_template_exists=True,
        discovery_focus_exists=True,
        discovery_focus_populated=True,
    )


def run_foundation_full_lifecycle_smoke() -> bool:
    gateway = FoundationGitHubGateway(
        {1: FoundationIssue(1, "Foundation", "body", labels={"foundation:needed"})},
        artifact_state=_full_artifact_state(),
    )
    with tempfile.TemporaryDirectory() as tmp:
        FoundationRunOnceOrchestrator(
            gateway=gateway,
            log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
            run_registry=FoundationRunRegistry(),
            research_adapter=_S({"decision": "RECOMMEND", "reason": "all good"}),
            gate_adapter=_S({"decision": "APPROVE_FOUNDATION", "reason": "approved"}),
        ).run_once(1)
    return "foundation:approved" in gateway.get_issue(1).labels


def run_foundation_terminal_smoke(research_decision: str = "RECOMMEND", gate_decision: str = "APPROVE_FOUNDATION") -> str:
    gateway = FoundationGitHubGateway(
        {1: FoundationIssue(1, "Foundation", "body", labels={"foundation:needed"})},
        artifact_state=_full_artifact_state(),
    )
    with tempfile.TemporaryDirectory() as tmp:
        FoundationRunOnceOrchestrator(
            gateway=gateway,
            log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
            run_registry=FoundationRunRegistry(),
            research_adapter=_S({"decision": research_decision, "reason": "test"}),
            gate_adapter=_S({"decision": gate_decision, "reason": "test"}),
        ).run_once(1)
    labels = gateway.get_issue(1).labels
    for label in ["foundation:approved", "foundation:blocked", "foundation:needs-human"]:
        if label in labels:
            return label
    return "unknown"


def run_foundation_needs_human_smoke() -> str:
    class _Fail:
        def invoke_json(self, *a, **kw):
            raise RuntimeError("fail")

    gateway = FoundationGitHubGateway(
        {1: FoundationIssue(1, "Foundation", "body", labels={"foundation:needed"})},
        artifact_state=_full_artifact_state(),
    )
    with tempfile.TemporaryDirectory() as tmp:
        FoundationRunOnceOrchestrator(
            gateway=gateway,
            log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
            run_registry=FoundationRunRegistry(),
            research_adapter=_Fail(),
            gate_adapter=_Fail(),
            retry_policy=RetryPolicy(max_attempts=1),
        ).run_once(1)
    return "foundation:needs-human" if "foundation:needs-human" in gateway.get_issue(1).labels else "unknown"
