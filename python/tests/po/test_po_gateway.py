import unittest

from aios_orchestration_core.artifacts.feature_request import FeatureRequestArtifact
from aios_orchestration_core.github.po_gateway import POGitHubGateway, POIssue


class POGatewayTests(unittest.TestCase):
    def test_create_feature_request_links_to_opportunity(self) -> None:
        gateway = POGitHubGateway(
            {1: POIssue(1, "Opportunity", "body", labels={"po:prioritizing"})}
        )
        fr_number = gateway.create_feature_request(1, "Feature X", "Do X", priority_score=75)
        self.assertIn(fr_number, gateway.list_created_feature_request_numbers(1))
        fr = gateway.get_issue(fr_number)
        self.assertIn("feature-request", fr.labels)
        self.assertEqual(fr.title, "Feature X")

    def test_multiple_feature_requests_all_linked(self) -> None:
        gateway = POGitHubGateway(
            {1: POIssue(1, "Opportunity", "body", labels={"po:creating-features"})}
        )
        n1 = gateway.create_feature_request(1, "FR A", "body a", priority_score=90)
        n2 = gateway.create_feature_request(1, "FR B", "body b", priority_score=60)
        linked = gateway.list_created_feature_request_numbers(1)
        self.assertIn(n1, linked)
        self.assertIn(n2, linked)
        self.assertEqual(len(linked), 2)

    def test_set_state_labels_atomic(self) -> None:
        gateway = POGitHubGateway(
            {1: POIssue(1, "Op", "body", labels={"po:queued"})}
        )
        gateway.set_state_labels(1, ["po:queued"], ["po:prioritizing"])
        self.assertIn("po:prioritizing", gateway.get_issue(1).labels)
        self.assertNotIn("po:queued", gateway.get_issue(1).labels)

    def test_close_issue_marks_as_closed(self) -> None:
        gateway = POGitHubGateway(
            {1: POIssue(1, "Op", "body", labels={"po:creating-features"})}
        )
        gateway.close_issue(1, "completed")
        self.assertFalse(gateway.get_issue(1).open)

    def test_feature_request_artifact_validates_priority_score_bounds(self) -> None:
        artifact = FeatureRequestArtifact(
            artifact_version="1.0.0",
            artifact_id="fr-1",
            source_opportunity_number=1,
            title="Feature",
            body="body",
            priority_score=50,
            produced_at="2026-07-12T00:00:00+00:00",
        )
        artifact.validate()  # should not raise

    def test_feature_request_artifact_rejects_out_of_range_priority(self) -> None:
        artifact = FeatureRequestArtifact(
            artifact_version="1.0.0",
            artifact_id="fr-bad",
            source_opportunity_number=1,
            title="Feature",
            body="body",
            priority_score=0,  # invalid
            produced_at="2026-07-12T00:00:00+00:00",
        )
        with self.assertRaises(ValueError):
            artifact.validate()


if __name__ == "__main__":
    unittest.main()
