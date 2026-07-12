import unittest

from aios_orchestration_core.github.dev_gateway_api import GitHubApiDevGateway
from aios_orchestration_core.github.pm_gateway_api import GitHubApiPMGateway
from aios_orchestration_core.github.po_gateway_api import GitHubApiPOGateway
from aios_orchestration_core.repo_context import RepoContext


class RepoContextGatewayTests(unittest.TestCase):
    def test_github_context_creates_pm_po_dev_gateways(self) -> None:
        context = RepoContext.from_string("owner/repo")
        self.assertTrue(context.is_github)

        self.assertIsInstance(context.create_pm_gateway(), GitHubApiPMGateway)
        self.assertIsInstance(context.create_po_gateway(), GitHubApiPOGateway)
        self.assertIsInstance(context.create_dev_gateway(), GitHubApiDevGateway)

    def test_local_context_raises_for_unimplemented_gateways(self) -> None:
        context = RepoContext.from_string("./local/repo")
        self.assertFalse(context.is_github)

        with self.assertRaises(NotImplementedError):
            context.create_pm_gateway()
        with self.assertRaises(NotImplementedError):
            context.create_po_gateway()
        with self.assertRaises(NotImplementedError):
            context.create_dev_gateway()


if __name__ == "__main__":
    unittest.main()
