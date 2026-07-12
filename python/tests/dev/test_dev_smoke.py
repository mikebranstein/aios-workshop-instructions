import unittest

from dev_orchestrator.smoke import (
    run_dev_full_lifecycle_smoke,
    run_dev_needs_human_smoke,
    run_dev_terminal_smoke,
)


class DevSmokeTests(unittest.TestCase):
    def test_happy_path_to_released(self) -> None:
        self.assertTrue(run_dev_full_lifecycle_smoke())

    def test_terminal_intake_blocked(self) -> None:
        self.assertEqual(
            run_dev_terminal_smoke(intake={"decision": "BLOCKED", "reason": "dep"}),
            "dev:blocked",
        )

    def test_terminal_design_blocked(self) -> None:
        self.assertEqual(
            run_dev_terminal_smoke(design={"decision": "BLOCKED", "reason": "dep"}),
            "dev:blocked",
        )

    def test_terminal_needs_human(self) -> None:
        self.assertEqual(run_dev_needs_human_smoke(), "dev:needs-human")


if __name__ == "__main__":
    unittest.main()
