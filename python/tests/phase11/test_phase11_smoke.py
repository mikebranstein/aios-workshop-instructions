import unittest

from pm_orchestrator.smoke import run_pm_phase_smoke


class Phase11SmokeTests(unittest.TestCase):
    def test_smoke_path(self) -> None:
        self.assertTrue(run_pm_phase_smoke())


if __name__ == "__main__":
    unittest.main()
