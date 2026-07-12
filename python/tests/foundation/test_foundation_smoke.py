import unittest

from foundation_orchestrator.smoke import (
    run_foundation_full_lifecycle_smoke,
    run_foundation_needs_human_smoke,
    run_foundation_terminal_smoke,
)


class FoundationSmokeTests(unittest.TestCase):
    def test_happy_path_approved(self) -> None:
        self.assertTrue(run_foundation_full_lifecycle_smoke())

    def test_research_blocked_terminal(self) -> None:
        self.assertEqual(run_foundation_terminal_smoke(research_decision="BLOCKED"), "foundation:blocked")

    def test_gate_blocked_terminal(self) -> None:
        self.assertEqual(run_foundation_terminal_smoke(gate_decision="BLOCK_FOUNDATION"), "foundation:blocked")

    def test_needs_human(self) -> None:
        self.assertEqual(run_foundation_needs_human_smoke(), "foundation:needs-human")


if __name__ == "__main__":
    unittest.main()
