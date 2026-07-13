import json
import subprocess
import unittest
from unittest.mock import patch

from aios_orchestration_core.github.dev_gateway_api import GitHubApiDevGateway
from aios_orchestration_core.github.pm_gateway_api import GitHubApiConfig
from aios_orchestration_core.github.po_gateway_api import GitHubApiPOGateway


def _cp(stdout: str) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")


class GitHubApiPOGatewayTests(unittest.TestCase):
    def test_create_feature_request_and_list_linked_numbers(self) -> None:
        cfg = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiPOGateway(cfg)

        def fake_run(cmd, check, capture_output, text, **kwargs):
            gh_args = cmd[3:]
            if gh_args[:2] == ["issue", "create"]:
                return _cp("https://github.com/owner/repo/issues/321")
            if gh_args[:2] == ["issue", "list"] and "--label" in gh_args:
                return _cp(json.dumps([{"number": 321}, {"number": 322}]))
            return _cp("")

        with patch("aios_orchestration_core.github.po_gateway_api.subprocess.run", side_effect=fake_run):
            created = gateway.create_feature_request(
                source_opportunity_number=12,
                title="Feature request",
                body="Build this",
                priority_score=88,
            )
            linked = gateway.list_created_feature_request_numbers(12)

        self.assertEqual(created, 321)
        self.assertEqual(linked, [321, 322])

    def test_list_open_issues_with_any_label_filters_results(self) -> None:
        cfg = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiPOGateway(cfg)

        issues = [
            {
                "number": 1,
                "title": "One",
                "body": "A",
                "state": "OPEN",
                "labels": [{"name": "po:queued"}],
            },
            {
                "number": 2,
                "title": "Two",
                "body": "B",
                "state": "OPEN",
                "labels": [{"name": "other"}],
            },
        ]

        def fake_run(cmd, check, capture_output, text, **kwargs):
            gh_args = cmd[3:]
            if gh_args[:2] == ["issue", "list"]:
                return _cp(json.dumps(issues))
            return _cp("")

        with patch("aios_orchestration_core.github.po_gateway_api.subprocess.run", side_effect=fake_run):
            result = gateway.list_open_issues_with_any_label(["po:queued"])

        self.assertEqual([i.number for i in result], [1])


class GitHubApiDevGatewayTests(unittest.TestCase):
    def test_list_open_issues_with_any_label_filters_results(self) -> None:
        cfg = GitHubApiConfig(repo="owner/repo")
        gateway = GitHubApiDevGateway(cfg)

        issues = [
            {
                "number": 10,
                "title": "Dev One",
                "body": "A",
                "state": "OPEN",
                "labels": [{"name": "dev:intake"}],
            },
            {
                "number": 11,
                "title": "Dev Two",
                "body": "B",
                "state": "OPEN",
                "labels": [{"name": "dev:qa"}],
            },
        ]

        def fake_run(cmd, check, capture_output, text, **kwargs):
            gh_args = cmd[3:]
            if gh_args[:2] == ["issue", "list"]:
                return _cp(json.dumps(issues))
            return _cp("")

        with patch("aios_orchestration_core.github.dev_gateway_api.subprocess.run", side_effect=fake_run):
            result = gateway.list_open_issues_with_any_label(["dev:intake"])

        self.assertEqual([i.number for i in result], [10])


if __name__ == "__main__":
    unittest.main()
