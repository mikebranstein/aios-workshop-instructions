import tempfile
import unittest

from aios_orchestration_core.github.pm_gateway import PMGitHubGateway, PMIssue
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from pm_orchestrator.run_once import PMRunOnceOrchestrator, PMRunRegistry


class _StaticAdapter:
    def __init__(self, payload):
        self.payload = payload

    @property
    def adapter_source(self):
        return "stub"

    def invoke_json(self, task_type, prompt_vars, model_hint=""):
        return type("Result", (), {"payload": self.payload, "model": "test-model"})()


class _CountingPMGateway(PMGitHubGateway):
    def __init__(self, issues):
        super().__init__(issues)
        self.set_state_labels_calls = 0
        self.post_comment_calls = 0
        self.ensure_research_issue_calls = 0

    def set_state_labels(self, issue_number, labels_to_remove, labels_to_add):
        self.set_state_labels_calls += 1
        return super().set_state_labels(issue_number, labels_to_remove, labels_to_add)

    def post_comment(self, issue_number, body):
        self.post_comment_calls += 1
        return super().post_comment(issue_number, body)

    def ensure_research_issue(self, pm_issue_number, title, body, labels):
        self.ensure_research_issue_calls += 1
        return super().ensure_research_issue(pm_issue_number, title, body, labels)


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
        gateway = _CountingPMGateway(
            {
                201: PMIssue(
                    number=201,
                    title="Idea",
                    body="Body",
                    labels={"pm:research-planning"},
                    linked_research_issue_numbers=[202],
                ),
                202: PMIssue(
                    number=202,
                    title="[research]: Admin - pricing",
                    body="Research topic: pricing",
                    labels={"research", "pm-idea-201"},
                    open=False,
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
                synthesis_adapter=_StaticAdapter({"summary": "ok", "confidence_score": 0.9, "closed_linked_research_count": 1}),
                phase2_adapter=_StaticAdapter({"decision": "CHAMPION", "reason": "ok", "confidence_score": 0.9}),
                min_research_count=1,
            )
            orchestrator.run_once(201)
            first_count = len(gateway.get_issue(201).linked_research_issue_numbers)
            first_comment_calls = gateway.post_comment_calls
            first_label_calls = gateway.set_state_labels_calls
            first_ensure_calls = gateway.ensure_research_issue_calls

            orchestrator.run_once(201)

            second_count = len(gateway.get_issue(201).linked_research_issue_numbers)
            self.assertEqual(first_count, 1)
            self.assertEqual(second_count, 1)
            self.assertEqual(first_ensure_calls, 1)
            self.assertEqual(gateway.ensure_research_issue_calls, first_ensure_calls)
            self.assertEqual(gateway.post_comment_calls, first_comment_calls)
            self.assertEqual(gateway.set_state_labels_calls, first_label_calls)


if __name__ == "__main__":
    unittest.main()
