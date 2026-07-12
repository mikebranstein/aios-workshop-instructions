import unittest

from pm_orchestrator.smoke import (
    run_pm_full_lifecycle_smoke,
    run_pm_needs_human_smoke,
    run_pm_terminal_smoke,
)


class Phase11SmokeTests(unittest.TestCase):
    def test_happy_path_to_output_published(self) -> None:
        self.assertTrue(run_pm_full_lifecycle_smoke())

    def test_terminal_deferred(self) -> None:
        self.assertEqual(run_pm_terminal_smoke(phase1_decision="DEFER"), "pm:deferred")

    def test_terminal_blocked(self) -> None:
        self.assertEqual(run_pm_terminal_smoke(phase1_decision="BLOCK"), "pm:blocked")

    def test_terminal_escalated(self) -> None:
        self.assertEqual(run_pm_terminal_smoke(phase2_decision="ESCALATE"), "pm:escalated")

    def test_terminal_needs_human(self) -> None:
        self.assertEqual(run_pm_needs_human_smoke(), "pm:needs-human")


if __name__ == "__main__":
    unittest.main()
