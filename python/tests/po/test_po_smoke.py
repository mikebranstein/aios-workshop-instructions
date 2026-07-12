import unittest

from po_orchestrator.smoke import (
    run_po_full_lifecycle_smoke,
    run_po_needs_human_smoke,
    run_po_terminal_smoke,
)


class POSmokeTests(unittest.TestCase):
    def test_happy_path_to_feature_requests_created(self) -> None:
        self.assertTrue(run_po_full_lifecycle_smoke())

    def test_terminal_deferred(self) -> None:
        self.assertEqual(run_po_terminal_smoke("DEFER"), "po:deferred")

    def test_terminal_rejected(self) -> None:
        self.assertEqual(run_po_terminal_smoke("REJECT"), "po:rejected")

    def test_terminal_needs_human(self) -> None:
        self.assertEqual(run_po_needs_human_smoke(), "po:needs-human")


if __name__ == "__main__":
    unittest.main()
