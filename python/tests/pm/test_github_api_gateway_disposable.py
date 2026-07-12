import json
import os
import subprocess
import time
import unittest

from aios_orchestration_core.github.pm_gateway_api import GitHubApiConfig, GitHubApiPMGateway


class Phase6GitHubApiGatewayDisposableTests(unittest.TestCase):
    repo = None

    @classmethod
    def setUpClass(cls):
        if os.environ.get("RUN_GITHUB_DISPOSABLE_TESTS") != "1":
            raise unittest.SkipTest("Set RUN_GITHUB_DISPOSABLE_TESTS=1 to run disposable GitHub integration test")

        auth_raw = subprocess.run(["gh", "api", "user"], check=True, capture_output=True, text=True).stdout
        login = json.loads(auth_raw)["login"]
        ts = int(time.time())
        cls.repo = f"{login}/aios-pm-gateway-disposable-{ts}"

        subprocess.run(
            ["gh", "repo", "create", cls.repo, "--private"],
            check=True,
            capture_output=True,
            text=True,
        )

        subprocess.run(
            [
                "gh",
                "-R",
                cls.repo,
                "label",
                "create",
                "pm-idea",
                "--color",
                "1D76DB",
                "--description",
                "test",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [
                "gh",
                "-R",
                cls.repo,
                "label",
                "create",
                "foundation-approved",
                "--color",
                "1D76DB",
                "--description",
                "test",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    @classmethod
    def tearDownClass(cls):
        if cls.repo:
            subprocess.run(["gh", "repo", "delete", cls.repo, "--yes"], check=False, capture_output=True, text=True)

    def test_gateway_round_trip(self):
        gateway = GitHubApiPMGateway(GitHubApiConfig(repo=self.repo))

        create_out = subprocess.run(
            [
                "gh",
                "-R",
                self.repo,
                "issue",
                "create",
                "--title",
                "Disposable PM Idea",
                "--body",
                "Body",
                "--label",
                "pm-idea",
                "--label",
                "foundation-approved",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        issue_number = int(create_out.strip().split("/")[-1])

        issue = gateway.get_issue(issue_number)
        self.assertEqual(issue.number, issue_number)
        self.assertIn("pm-idea", issue.labels)

        first_research = gateway.ensure_research_issue(
            pm_issue_number=issue_number,
            title="[research]: Admin - Pricing",
            body="Research topic: pricing",
            labels=["research", f"pm-idea-{issue_number}"],
        )
        second_research = gateway.ensure_research_issue(
            pm_issue_number=issue_number,
            title="[research]: Admin - Pricing",
            body="Research topic: pricing",
            labels=["research", f"pm-idea-{issue_number}"],
        )
        self.assertEqual(first_research, second_research)

        gateway.post_comment(issue_number, "Disposable gateway test comment")
        gateway.add_labels(issue_number, ["pm:queued"])
        gateway.close_issue(issue_number, "not planned")

        closed_issue = gateway.get_issue(issue_number)
        self.assertFalse(closed_issue.open)


if __name__ == "__main__":
    unittest.main()
