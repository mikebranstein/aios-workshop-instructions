import tempfile

from aios_orchestration_core.github.pm_gateway import PMGitHubGateway, PMIssue
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from pm_orchestrator.run_once import PMRunOnceOrchestrator, PMRunRegistry


class _StaticPhase1Adapter:
    def __init__(self, payload):
        self.payload = payload

    @property
    def adapter_source(self):
        return "stub"

    def invoke_json(self, task_type, prompt_vars, model_hint=""):
        return type("Result", (), {"payload": self.payload, "model": "smoke-model"})()


def run_pm_full_lifecycle_smoke() -> bool:
    gateway = PMGitHubGateway({1: PMIssue(1, "Smoke idea", "body", labels={"pm:queued", "foundation-approved"})})
    with tempfile.TemporaryDirectory() as tmp:
        orchestrator = PMRunOnceOrchestrator(
            gateway=gateway,
            log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
            run_registry=PMRunRegistry(),
            phase1_adapter=_StaticPhase1Adapter({"decision": "PROVISIONAL_CHAMPION", "reason": "smoke"}),
            research_planning_adapter=_StaticPhase1Adapter({"tasks": []}),
            synthesis_adapter=_StaticPhase1Adapter({"summary": "validated", "confidence_score": 0.91, "closed_linked_research_count": 0}),
            phase2_adapter=_StaticPhase1Adapter({"decision": "CHAMPION", "reason": "ship", "confidence_score": 0.91}),
            min_research_count=0,
        )
        orchestrator.run_once(1)
    return "pm:output-published" in gateway.get_issue(1).labels


def run_pm_terminal_smoke(phase1_decision: str | None = None, phase2_decision: str | None = None) -> str:
    gateway = PMGitHubGateway({1: PMIssue(1, "Smoke idea", "body", labels={"pm:queued", "foundation-approved"})})
    with tempfile.TemporaryDirectory() as tmp:
        orchestrator = PMRunOnceOrchestrator(
            gateway=gateway,
            log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
            run_registry=PMRunRegistry(),
            phase1_adapter=_StaticPhase1Adapter({"decision": phase1_decision or "PROVISIONAL_CHAMPION", "reason": "smoke"}),
            research_planning_adapter=_StaticPhase1Adapter({"tasks": []}),
            synthesis_adapter=_StaticPhase1Adapter({"summary": "validated", "confidence_score": 0.91, "closed_linked_research_count": 0}),
            phase2_adapter=_StaticPhase1Adapter({"decision": phase2_decision or "CHAMPION", "reason": "smoke", "confidence_score": 0.91}),
            min_research_count=0,
        )
        orchestrator.run_once(1)

    labels = gateway.get_issue(1).labels
    for label in ["pm:output-published", "pm:deferred", "pm:blocked", "pm:escalated", "pm:needs-human"]:
        if label in labels:
            return label
    return "unknown"


def run_pm_needs_human_smoke() -> str:
    class _FailingAdapter:
        def invoke_json(self, task_type, prompt_vars, model_hint=""):
            raise RuntimeError("simulated failure")

    gateway = PMGitHubGateway({1: PMIssue(1, "Smoke idea", "body", labels={"pm:queued", "foundation-approved"})})
    with tempfile.TemporaryDirectory() as tmp:
        orchestrator = PMRunOnceOrchestrator(
            gateway=gateway,
            log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
            run_registry=PMRunRegistry(),
            phase1_adapter=_FailingAdapter(),
            research_planning_adapter=_StaticPhase1Adapter({"tasks": []}),
            synthesis_adapter=_StaticPhase1Adapter({"summary": "validated", "confidence_score": 0.91, "closed_linked_research_count": 0}),
            phase2_adapter=_StaticPhase1Adapter({"decision": "CHAMPION", "reason": "smoke", "confidence_score": 0.91}),
            min_research_count=0,
            retry_policy=RetryPolicy(max_attempts=1),
        )
        orchestrator.run_once(1)
    return "pm:needs-human" if "pm:needs-human" in gateway.get_issue(1).labels else "unknown"


def run_pm_phase_smoke() -> bool:
    return run_pm_full_lifecycle_smoke()
