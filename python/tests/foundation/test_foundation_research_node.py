"""Unit tests for FoundationResearchNode._contradiction_check and _extract_decision_area."""
import tempfile
import unittest

from aios_orchestration_core.github.foundation_gateway import (
    FoundationGitHubGateway,
    FoundationIssue,
    LinkedFoundationIssue,
)
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.foundation import FoundationState
from foundation_orchestrator.nodes.research import (
    FoundationResearchNode,
    _extract_decision_area,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_research_issue(number: int, area: str | None, open: bool = False) -> LinkedFoundationIssue:
    if area is not None:
        body = f"## Decision Area\n{area}\n\n## Research Objective\nWhat?\n"
    else:
        body = "## Research Objective\nWhat?\n"
    return LinkedFoundationIssue(number=number, title=f"Research #{number}", body=body, open=open)


class _StubAdapter:
    """Adapter that always returns the given decision."""

    def __init__(self, decision: str) -> None:
        self._decision = decision

    @property
    def adapter_source(self) -> str:
        return "stub"

    def invoke_json(self, *args, **kwargs):
        return type("R", (), {"payload": {"decision": self._decision, "reason": "test"}, "model": "stub"})()


def _make_gateway_with_issues(
    parent_body: str = "See docs/adr/0001.md and https://github.com/owner/repo/wiki/Page",
    sub_issue_bodies: list[tuple[int, str | None, bool]] | None = None,
) -> FoundationGitHubGateway:
    """Build a FoundationGitHubGateway with one parent and N research sub-issues."""
    issues: dict[int, FoundationIssue] = {
        1: FoundationIssue(
            number=1,
            title="Foundation",
            body=parent_body,
            labels={"foundation:in-progress"},
        )
    }
    sub_map: dict[int, list[int]] = {1: []}
    for number, area, open_ in (sub_issue_bodies or []):
        if area is not None:
            body = f"## Decision Area\n{area}\n\n## Research Objective\nWhat?\n"
        else:
            body = "## Research Objective\nWhat?\n"
        issues[number] = FoundationIssue(
            number=number,
            title=f"Research #{number}",
            body=body,
            labels={"foundation:research"},
            open=open_,
        )
        sub_map[1].append(number)
    return FoundationGitHubGateway(issues=issues, sub_issues=sub_map)


# ---------------------------------------------------------------------------
# _extract_decision_area
# ---------------------------------------------------------------------------

class TestExtractDecisionArea(unittest.TestCase):
    def test_returns_area_when_present(self) -> None:
        body = "## Decision Area\nruntime/language\n\n## Research Objective\nWhat?\n"
        self.assertEqual(_extract_decision_area(body), "runtime/language")

    def test_normalises_to_lowercase(self) -> None:
        body = "## Decision Area\nFramework/Engine\n"
        self.assertEqual(_extract_decision_area(body), "framework/engine")

    def test_skips_option_hint_line(self) -> None:
        body = (
            "## Decision Area\n"
            "(runtime/language | framework/engine | architecture style | data/storage | deployment | NFRs | other)\n"
            "framework/engine\n"
        )
        self.assertEqual(_extract_decision_area(body), "framework/engine")

    def test_returns_none_when_section_absent(self) -> None:
        body = "## Research Objective\nWhat question?\n"
        self.assertIsNone(_extract_decision_area(body))

    def test_returns_none_for_empty_body(self) -> None:
        self.assertIsNone(_extract_decision_area(""))

    def test_returns_none_when_section_empty(self) -> None:
        body = "## Decision Area\n\n## Research Objective\nWhat?\n"
        self.assertIsNone(_extract_decision_area(body))


# ---------------------------------------------------------------------------
# FoundationResearchNode._contradiction_check
# ---------------------------------------------------------------------------

class TestContradictionCheck(unittest.TestCase):
    def _node(self, decision: str = "RECOMMEND") -> FoundationResearchNode:
        gw = _make_gateway_with_issues()
        with tempfile.TemporaryDirectory() as tmp:
            store = TransitionLogStore(f"{tmp}/runlog.sqlite")
        return FoundationResearchNode(
            adapter=_StubAdapter(decision),
            gateway=gw,
            log_store=store,
        )

    def test_no_conflicts_when_areas_differ(self) -> None:
        node = self._node()
        issues = [
            _make_research_issue(10, "runtime/language", open=False),
            _make_research_issue(11, "framework/engine", open=False),
        ]
        self.assertEqual(node._contradiction_check(issues), [])

    def test_conflict_when_same_area_two_closed_issues(self) -> None:
        node = self._node()
        issues = [
            _make_research_issue(10, "framework/engine", open=False),
            _make_research_issue(11, "framework/engine", open=False),
        ]
        conflicts = node._contradiction_check(issues)
        self.assertEqual(len(conflicts), 1)
        self.assertIn("framework/engine", conflicts[0])
        self.assertIn("#10", conflicts[0])
        self.assertIn("#11", conflicts[0])

    def test_no_conflict_when_one_issue_is_still_open(self) -> None:
        node = self._node()
        issues = [
            _make_research_issue(10, "framework/engine", open=False),
            _make_research_issue(11, "framework/engine", open=True),  # still open → skip
        ]
        self.assertEqual(node._contradiction_check(issues), [])

    def test_graceful_degradation_without_decision_area_field(self) -> None:
        """Issues without ## Decision Area are skipped — no false positive conflicts."""
        node = self._node()
        issues = [
            _make_research_issue(10, None, open=False),
            _make_research_issue(11, None, open=False),
        ]
        self.assertEqual(node._contradiction_check(issues), [])

    def test_multiple_conflicting_areas(self) -> None:
        node = self._node()
        issues = [
            _make_research_issue(10, "runtime/language", open=False),
            _make_research_issue(11, "runtime/language", open=False),
            _make_research_issue(12, "architecture style", open=False),
            _make_research_issue(13, "architecture style", open=False),
        ]
        conflicts = node._contradiction_check(issues)
        self.assertEqual(len(conflicts), 2)
        areas_mentioned = " ".join(conflicts)
        self.assertIn("runtime/language", areas_mentioned)
        self.assertIn("architecture style", areas_mentioned)


# ---------------------------------------------------------------------------
# Integration: RECOMMEND is downgraded when contradiction check fires
# ---------------------------------------------------------------------------

class TestResearchNodeDowngradesOnConflict(unittest.TestCase):
    def test_recommend_downgraded_to_needs_more_research(self) -> None:
        """LLM says RECOMMEND but two closed issues share an area → NEEDS_MORE_RESEARCH."""
        gateway = _make_gateway_with_issues(
            sub_issue_bodies=[
                (2, "framework/engine", False),  # closed, UE5
                (3, "framework/engine", False),  # closed, Unity — same area, conflict!
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = TransitionLogStore(f"{tmp}/runlog.sqlite")
            node = FoundationResearchNode(
                adapter=_StubAdapter("RECOMMEND"),
                gateway=gateway,
                log_store=store,
            )
            result_state = node.run("test-run-id", 1)

        self.assertEqual(result_state, FoundationState.FOUNDATION_IN_PROGRESS)
        # Label should be in-progress, not review
        labels = gateway.get_issue(1).labels
        self.assertNotIn("foundation:review", labels)

    def test_recommend_passes_through_when_areas_differ(self) -> None:
        """LLM says RECOMMEND and all research issues are in different areas → promote to review."""
        gateway = _make_gateway_with_issues(
            parent_body=(
                "See docs/adr/0001.md and https://github.com/owner/repo/wiki/Foundation-Research"
            ),
            sub_issue_bodies=[
                (2, "runtime/language", False),
                (3, "framework/engine", False),
            ],
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = TransitionLogStore(f"{tmp}/runlog.sqlite")
            node = FoundationResearchNode(
                adapter=_StubAdapter("RECOMMEND"),
                gateway=gateway,
                log_store=store,
            )
            result_state = node.run("test-run-id", 1)

        self.assertEqual(result_state, FoundationState.FOUNDATION_REVIEW)

    def test_recommend_passes_through_without_decision_area_field(self) -> None:
        """Old-style issues with no Decision Area field don't block promotion."""
        gateway = _make_gateway_with_issues(
            parent_body=(
                "See docs/adr/0001.md and https://github.com/owner/repo/wiki/Foundation-Research"
            ),
            sub_issue_bodies=[
                (2, None, False),
                (3, None, False),
            ],
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = TransitionLogStore(f"{tmp}/runlog.sqlite")
            node = FoundationResearchNode(
                adapter=_StubAdapter("RECOMMEND"),
                gateway=gateway,
                log_store=store,
            )
            result_state = node.run("test-run-id", 1)

        self.assertEqual(result_state, FoundationState.FOUNDATION_REVIEW)

    def test_downgrade_reason_logged_in_comment(self) -> None:
        """When downgraded, the posted comment must mention the contradiction."""
        gateway = _make_gateway_with_issues(
            sub_issue_bodies=[
                (2, "framework/engine", False),
                (3, "framework/engine", False),
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = TransitionLogStore(f"{tmp}/runlog.sqlite")
            node = FoundationResearchNode(
                adapter=_StubAdapter("RECOMMEND"),
                gateway=gateway,
                log_store=store,
            )
            node.run("test-run-id", 1)

        comments = gateway.get_issue(1).comments
        self.assertTrue(any("Contradiction check failed" in c for c in comments))


if __name__ == "__main__":
    unittest.main()
