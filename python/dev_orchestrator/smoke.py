import tempfile

from aios_orchestration_core.github.dev_gateway import DevGitHubGateway, DevIssue
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from dev_orchestrator.run_once import DevRunOnceOrchestrator, DevRunRegistry


class _S:
    def __init__(self, payload):
        self.payload = payload

    def invoke_json(self, task_type, prompt_vars, model_hint=""):
        return type("R", (), {"payload": self.payload, "model": "smoke"})()


def _orch(gateway, tmp, intake, design, build, qa, policy, **kw):
    return DevRunOnceOrchestrator(
        gateway=gateway,
        log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
        run_registry=DevRunRegistry(),
        intake_adapter=_S(intake),
        design_adapter=_S(design),
        build_adapter=_S(build),
        qa_adapter=_S(qa),
        policy_adapter=_S(policy),
        **kw,
    )


def run_dev_full_lifecycle_smoke() -> bool:
    gateway = DevGitHubGateway({1: DevIssue(1, "Feature", "body", labels={"dev:intake"})})
    with tempfile.TemporaryDirectory() as tmp:
        _orch(
            gateway, tmp,
            intake={"decision": "APPROVED", "reason": "clear"},
            design={"decision": "APPROVED", "reason": "good"},
            build={"decision": "COMPLETE", "reason": "done"},
            qa={"decision": "PASSED", "reason": "all green"},
            policy={"decision": "APPROVED", "reason": "ok"},
        ).run_once(1)
    return "dev:released" in gateway.get_issue(1).labels


def run_dev_terminal_smoke(*, intake=None, design=None, build=None, qa=None, policy=None) -> str:
    gateway = DevGitHubGateway({1: DevIssue(1, "Feature", "body", labels={"dev:intake"})})
    with tempfile.TemporaryDirectory() as tmp:
        _orch(
            gateway, tmp,
            intake=intake or {"decision": "APPROVED", "reason": "ok"},
            design=design or {"decision": "APPROVED", "reason": "ok"},
            build=build or {"decision": "COMPLETE", "reason": "ok"},
            qa=qa or {"decision": "PASSED", "reason": "ok"},
            policy=policy or {"decision": "APPROVED", "reason": "ok"},
        ).run_once(1)
    labels = gateway.get_issue(1).labels
    for label in ["dev:released", "dev:blocked", "dev:needs-human"]:
        if label in labels:
            return label
    return "unknown"


def run_dev_needs_human_smoke() -> str:
    class _Fail:
        def invoke_json(self, *a, **kw):
            raise RuntimeError("fail")

    gateway = DevGitHubGateway({1: DevIssue(1, "Feature", "body", labels={"dev:intake"})})
    with tempfile.TemporaryDirectory() as tmp:
        DevRunOnceOrchestrator(
            gateway=gateway,
            log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
            run_registry=DevRunRegistry(),
            intake_adapter=_Fail(),
            design_adapter=_Fail(),
            build_adapter=_Fail(),
            qa_adapter=_Fail(),
            policy_adapter=_Fail(),
            retry_policy=RetryPolicy(max_attempts=1),
        ).run_once(1)
    return "dev:needs-human" if "dev:needs-human" in gateway.get_issue(1).labels else "unknown"
