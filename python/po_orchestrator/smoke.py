import tempfile

from aios_orchestration_core.github.po_gateway import POGitHubGateway, POIssue
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from po_orchestrator.run_once import PORunOnceOrchestrator, PORunRegistry


class _StaticAdapter:
    def __init__(self, payload):
        self.payload = payload

    def invoke_json(self, task_type, prompt_vars, model_hint=""):
        return type("Result", (), {"payload": self.payload, "model": "smoke-model"})()


def run_po_full_lifecycle_smoke() -> bool:
    """Happy-path: strategic-opportunity → feature-requests-created."""
    gateway = POGitHubGateway(
        {1: POIssue(1, "Opportunity A", "body", labels={"po:queued"})}
    )
    with tempfile.TemporaryDirectory() as tmp:
        orchestrator = PORunOnceOrchestrator(
            gateway=gateway,
            log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
            run_registry=PORunRegistry(),
            prioritize_adapter=_StaticAdapter({"decision": "CREATE_FEATURE_REQUESTS", "reason": "high value"}),
            create_features_adapter=_StaticAdapter({
                "feature_requests": [
                    {"title": "Feature X", "body": "Do X", "priority_score": 80},
                ]
            }),
        )
        orchestrator.run_once(1)
    return "po:feature-requests-created" in gateway.get_issue(1).labels


def run_po_terminal_smoke(decision: str) -> str:
    """Smoke test for DEFER and REJECT terminal paths."""
    gateway = POGitHubGateway(
        {1: POIssue(1, "Opportunity B", "body", labels={"po:queued"})}
    )
    with tempfile.TemporaryDirectory() as tmp:
        orchestrator = PORunOnceOrchestrator(
            gateway=gateway,
            log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
            run_registry=PORunRegistry(),
            prioritize_adapter=_StaticAdapter({"decision": decision, "reason": "not now"}),
            create_features_adapter=_StaticAdapter({"feature_requests": []}),
        )
        orchestrator.run_once(1)
    labels = gateway.get_issue(1).labels
    for label in ["po:feature-requests-created", "po:deferred", "po:rejected", "po:needs-human"]:
        if label in labels:
            return label
    return "unknown"


def run_po_needs_human_smoke() -> str:
    """Smoke test for circuit-breaker escalation to needs-human."""
    class _FailingAdapter:
        def invoke_json(self, task_type, prompt_vars, model_hint=""):
            raise RuntimeError("simulated failure")

    gateway = POGitHubGateway(
        {1: POIssue(1, "Opportunity C", "body", labels={"po:queued"})}
    )
    with tempfile.TemporaryDirectory() as tmp:
        orchestrator = PORunOnceOrchestrator(
            gateway=gateway,
            log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
            run_registry=PORunRegistry(),
            prioritize_adapter=_FailingAdapter(),
            create_features_adapter=_FailingAdapter(),
            retry_policy=RetryPolicy(max_attempts=1),
        )
        orchestrator.run_once(1)
    return "po:needs-human" if "po:needs-human" in gateway.get_issue(1).labels else "unknown"
