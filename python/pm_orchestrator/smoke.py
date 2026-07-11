import tempfile

from aios_orchestration_core.github.pm_gateway import PMGitHubGateway, PMIssue
from aios_orchestration_core.runlog.sqlite_store import TransitionLogStore
from pm_orchestrator.nodes.phase1 import PMPhase1Node, Phase1Config


class _StaticPhase1Adapter:
    def invoke_json(self, task_type, prompt_vars, model_hint=""):
        return type("Result", (), {"payload": {"decision": "PROVISIONAL_CHAMPION", "reason": "smoke"}})()


def run_pm_phase_smoke() -> bool:
    gateway = PMGitHubGateway({1: PMIssue(1, "Smoke idea", "body", labels={"pm:phase1-validating"})})
    with tempfile.TemporaryDirectory() as tmp:
        node = PMPhase1Node(
            adapter=_StaticPhase1Adapter(),
            gateway=gateway,
            log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
            config=Phase1Config(),
        )
        node.run("smoke-run", 1)
    return "pm:research-planning" in gateway.get_issue(1).labels
