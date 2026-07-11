import unittest

from aios_orchestration_core.github.pm_gateway import PMGitHubGateway, PMIssue
from pm_orchestrator.migration.bridge import (
    CleanRunCounter,
    backfill_pm_canonical_labels_for_open_issues,
    find_legacy_pm_saved_view_queries,
)


class Phase9BridgeTests(unittest.TestCase):
    def test_backfill_adds_canonical_label(self) -> None:
        gateway = PMGitHubGateway({1: PMIssue(1, "Idea", "", labels={"pm-opportunity"}, open=True)})
        updated = backfill_pm_canonical_labels_for_open_issues(gateway, [1])
        self.assertIn(1, updated)
        self.assertIn("pm:output-published", gateway.get_issue(1).labels)

    def test_clean_run_counter_uses_n_consecutive_runs(self) -> None:
        counter = CleanRunCounter(required_consecutive_clean_runs=3)
        counter.record_run(had_conflict=False)
        counter.record_run(had_conflict=False)
        self.assertFalse(counter.bridge_exit_ready)
        counter.record_run(had_conflict=False)
        self.assertTrue(counter.bridge_exit_ready)
        counter.record_run(had_conflict=True)
        self.assertFalse(counter.bridge_exit_ready)

    def test_saved_view_scanner_flags_legacy_queries(self) -> None:
        flagged = find_legacy_pm_saved_view_queries([
            "label:pm-opportunity is:open",
            "label:pm:output-published is:open",
        ])
        self.assertEqual(flagged, ["label:pm-opportunity is:open"])


if __name__ == "__main__":
    unittest.main()
