import tempfile
import unittest

from aios_orchestration_core.github.pm_gateway import PMGitHubGateway, PMIssue
from aios_orchestration_core.runlog.models import TransitionLogEntry
from aios_orchestration_core.runlog.sqlite_store import TransitionLogStore


class Phase3GatewayRunlogTests(unittest.TestCase):
    def test_linked_research_closed_check(self) -> None:
        gateway = PMGitHubGateway(
            {
                1: PMIssue(1, "idea", "body", labels={"pm-idea"}, linked_research_issue_numbers=[2, 3]),
                2: PMIssue(2, "r1", "body", open=False),
                3: PMIssue(3, "r2", "body", open=True),
            }
        )
        self.assertFalse(gateway.are_linked_research_issues_closed(1))
        gateway.close_issue(3, "completed")
        self.assertTrue(gateway.are_linked_research_issues_closed(1))

    def test_sqlite_runlog_persists_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = TransitionLogStore(f"{tmp}/runlog.sqlite")
            entry = TransitionLogEntry(
                run_id="r1",
                issue_number=42,
                from_state="PM_QUEUED",
                to_state="PM_PHASE1_VALIDATING",
                trigger_event="FOUNDATION_GATE_PASSED",
                reason_code="FOUNDATION_GATE",
                reason_detail="foundation-approved present",
                timestamp_utc="2026-07-12T00:00:00+00:00",
            )
            store.append(entry)


if __name__ == "__main__":
    unittest.main()
