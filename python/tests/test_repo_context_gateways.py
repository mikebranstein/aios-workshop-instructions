import unittest

from aios_orchestration_core.github.arch_review_gateway_api import GitHubApiArchReviewGateway
from aios_orchestration_core.github.dev_gateway_api import GitHubApiDevGateway
from aios_orchestration_core.github.discovery_gateway_api import GitHubApiDiscoveryGateway
from aios_orchestration_core.github.foundation_gateway_api import GitHubApiFoundationGateway
from aios_orchestration_core.github.pm_gateway_api import GitHubApiPMGateway
from aios_orchestration_core.github.po_gateway_api import GitHubApiPOGateway
from aios_orchestration_core.repo_context import RepoContext


class RepoContextGatewayTests(unittest.TestCase):
    def test_github_context_creates_all_gateways(self) -> None:
        context = RepoContext.from_string("owner/repo")
        self.assertTrue(context.is_github)

        self.assertIsInstance(context.create_pm_gateway(), GitHubApiPMGateway)
        self.assertIsInstance(context.create_po_gateway(), GitHubApiPOGateway)
        self.assertIsInstance(context.create_dev_gateway(), GitHubApiDevGateway)
        self.assertIsInstance(context.create_foundation_gateway(), GitHubApiFoundationGateway)
        self.assertIsInstance(context.create_arch_review_gateway(), GitHubApiArchReviewGateway)
        self.assertIsInstance(context.create_discovery_gateway(), GitHubApiDiscoveryGateway)

    def test_local_context_raises_for_unimplemented_gateways(self) -> None:
        context = RepoContext.from_string("./local/repo")
        self.assertFalse(context.is_github)

        with self.assertRaises(NotImplementedError):
            context.create_pm_gateway()
        with self.assertRaises(NotImplementedError):
            context.create_po_gateway()
        with self.assertRaises(NotImplementedError):
            context.create_dev_gateway()
        with self.assertRaises(NotImplementedError):
            context.create_foundation_gateway()
        with self.assertRaises(NotImplementedError):
            context.create_arch_review_gateway()
        with self.assertRaises(NotImplementedError):
            context.create_discovery_gateway()


if __name__ == "__main__":
    unittest.main()
