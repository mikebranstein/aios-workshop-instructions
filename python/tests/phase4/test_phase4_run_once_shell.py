import tempfile
import unittest

from aios_orchestration_core.github.pm_gateway import PMGitHubGateway, PMIssue
from aios_orchestration_core.runlog.sqlite_store import TransitionLogStore
from pm_orchestrator.run_once import PMRunOnceOrchestrator, PMRunRegistry


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
            )
            run = orchestrator.run_once(101, external_resume_link_run_id="run-prev")
            self.assertEqual(run.linked_prior_run_id, "run-prev")
            self.assertIsNotNone(run.ended_at_utc)
            self.assertGreater(len(gateway.get_issue(101).comments), 0)


if __name__ == "__main__":
    unittest.main()
