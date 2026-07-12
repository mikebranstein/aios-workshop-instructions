import tempfile
import unittest

from aios_orchestration_core.github.pm_gateway import PMGitHubGateway, PMIssue
from aios_orchestration_core.runlog.sqlite_store import TransitionLogStore
from pm_orchestrator.run_once import PMRunOnceOrchestrator, PMRunRegistry


class _StaticAdapter:
    def __init__(self, payload):
        self.payload = payload

    def invoke_json(self, task_type, prompt_vars, model_hint=""):
        return type("Result", (), {"payload": self.payload, "model": "test-model"})()


class Phase4RunOnceTests(unittest.TestCase):
    def test_run_once_links_external_resume_and_logs(self) -> None:
        gateway = PMGitHubGateway(
            {
                101: PMIssue(
                    number=101,
                    title="Idea",
                    body="Body",
                    labels={"pm-idea", "foundation-approved"},
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmp:
            orchestrator = PMRunOnceOrchestrator(
                gateway,
                TransitionLogStore(f"{tmp}/runlog.sqlite"),
                PMRunRegistry(),
                phase1_adapter=_StaticAdapter({"decision": "DEFER", "reason": "not now"}),
                research_planning_adapter=_StaticAdapter({"tasks": []}),
                synthesis_adapter=_StaticAdapter({"summary": "ok", "confidence_score": 0.9, "closed_linked_research_count": 0}),
                phase2_adapter=_StaticAdapter({"decision": "CHAMPION", "reason": "ok", "confidence_score": 0.9}),
                min_research_count=0,
            )
            run = orchestrator.run_once(101, external_resume_link_run_id="run-prev")
            self.assertEqual(run.linked_prior_run_id, "run-prev")
            self.assertIsNotNone(run.ended_at_utc)
            self.assertGreater(len(gateway.get_issue(101).comments), 0)

    def test_run_once_idempotent_on_research_planning(self) -> None:
        gateway = PMGitHubGateway(
            {
                201: PMIssue(
                    number=201,
                    title="Idea",
                    body="Body",
                    labels={"pm:research-planning"},
                )
            }
        )

        with tempfile.TemporaryDirectory() as tmp:
            orchestrator = PMRunOnceOrchestrator(
                gateway,
                TransitionLogStore(f"{tmp}/runlog.sqlite"),
                PMRunRegistry(),
                phase1_adapter=_StaticAdapter({"decision": "PROVISIONAL_CHAMPION", "reason": "ok"}),
                research_planning_adapter=_StaticAdapter({"tasks": [{"topic": "pricing", "persona": "Admin"}]}),
                synthesis_adapter=_StaticAdapter({"summary": "ok", "confidence_score": 0.9, "closed_linked_research_count": 0}),
                phase2_adapter=_StaticAdapter({"decision": "CHAMPION", "reason": "ok", "confidence_score": 0.9}),
                min_research_count=1,
            )
            orchestrator.run_once(201)
            first_count = len(gateway.get_issue(201).linked_research_issue_numbers)
            orchestrator.run_once(201)
            second_count = len(gateway.get_issue(201).linked_research_issue_numbers)
            self.assertEqual(first_count, 1)
            self.assertEqual(second_count, 1)


if __name__ == "__main__":
    unittest.main()
