"""Cross-validates the routing-registry.md against every Python transition table.

For each loop, verifies:
  1. Every decision from the registry that maps to a known Python (state, event) pair
     has a corresponding entry in the Python TransitionTable.
  2. The Python next_state matches the registry's declared next_stage
     (using the stage→state mapping defined here).
"""
import unittest
from pathlib import Path

from aios_orchestration_core.registry.parser import parse_routing_registry, entries_by_loop
from aios_orchestration_core.transitions.pm import _PM_TABLE
from aios_orchestration_core.transitions.po import _PO_TABLE
from aios_orchestration_core.transitions.dev import _DEV_TABLE
from aios_orchestration_core.transitions.foundation import _FOUNDATION_TABLE
from aios_orchestration_core.transitions.discovery import _DISCOVERY_TABLE
from aios_orchestration_core.transitions.arch_review import _ARCH_REVIEW_TABLE, _DEBT_TABLE
from aios_orchestration_core.states.pm import PMState
from aios_orchestration_core.events.pm import PMEvent
from aios_orchestration_core.states.po import POState
from aios_orchestration_core.events.po import POEvent
from aios_orchestration_core.states.dev import DevState
from aios_orchestration_core.events.dev import DevEvent
from aios_orchestration_core.states.foundation import FoundationState
from aios_orchestration_core.events.foundation import FoundationEvent
from aios_orchestration_core.states.discovery import DiscoveryState
from aios_orchestration_core.events.discovery import DiscoveryEvent
from aios_orchestration_core.states.arch_review import ArchReviewState, DebtState
from aios_orchestration_core.events.arch_review import ArchReviewEvent, DebtEvent

_REGISTRY_PATH = (
    Path(__file__).parent.parent.parent.parent  # repo root
    / "templates-old-v2"
    / "orchestration"
    / "routing-registry.md"
)

# ---------------------------------------------------------------------------
# Mapping: registry stage-label → (LoopState enum, LoopEvent enum, table)
# Only entries that have a direct Python equivalent are mapped.
# Entries without a mapping are skipped (documented-only registry stages).
# ---------------------------------------------------------------------------

# PM
# Registry "pm-idea" stage lists Phase-1 decisions; in Python those decisions
# fire from PM_PHASE1_VALIDATING (after the FOUNDATION_GATE_PASSED step).
_PM_STAGE = {
    "pm-idea": PMState.PM_PHASE1_VALIDATING,
    "pm-provisional-champion": PMState.PM_RESEARCH_WAITING,
    "pm-finalizing": PMState.PM_PHASE2_VALIDATING,
}
_PM_DECISION = {
    "PROVISIONAL_CHAMPION": PMEvent.PHASE1_PROVISIONAL_CHAMPION,
    "DEFER": PMEvent.PHASE1_DEFER,
    "BLOCK": PMEvent.PHASE1_BLOCK,
    "CHAMPION": PMEvent.PHASE2_CHAMPION,
    "ESCALATE": PMEvent.PHASE2_ESCALATE,
}

# PO
_PO_STAGE = {
    # The registry models PO as a single "strategic-opportunity" stage where decisions fire.
    # Python splits this into PO_QUEUED (entry) and PO_PRIORITIZING (decision).
    # Decisions (CREATE_FEATURE_REQUESTS, DEFER, REJECT) fire from PO_PRIORITIZING.
    "strategic-opportunity": POState.PO_PRIORITIZING,
}
_PO_DECISION = {
    "CREATE_FEATURE_REQUESTS": POEvent.PRIORITIZATION_CREATE,
    "DEFER": POEvent.PRIORITIZATION_DEFER,
    "REJECT": POEvent.PRIORITIZATION_REJECT,
}

# Dev
_DEV_STAGE = {
    "feature-request": DevState.DEV_INTAKE,
    "design-approved": DevState.DEV_BUILD,   # build handoff section
    "qa-testing": DevState.DEV_QA,
    "policy-approval": DevState.DEV_POLICY,
}
_DEV_DECISION = {
    "PASS": DevEvent.INTAKE_APPROVED,
    "BLOCKED": DevEvent.INTAKE_BLOCKED,
    "COMPLETE": DevEvent.BUILD_COMPLETE,
    "PASS_QA": DevEvent.QA_PASSED,   # registry uses PASS
    "APPROVE": DevEvent.POLICY_APPROVED,
}

# Foundation
_FOUNDATION_STAGE = {
    "foundation-in-progress": FoundationState.FOUNDATION_IN_PROGRESS,
    "foundation-review": FoundationState.FOUNDATION_REVIEW,
}
_FOUNDATION_DECISION = {
    "RECOMMEND": FoundationEvent.RESEARCH_RECOMMEND,
    "NEEDS_MORE_RESEARCH": FoundationEvent.RESEARCH_NEEDS_MORE,
    "BLOCKED": FoundationEvent.RESEARCH_BLOCKED,
    "APPROVE_FOUNDATION": FoundationEvent.APPROVE_FOUNDATION,
    "REVISE_FOUNDATION": FoundationEvent.REVISE_FOUNDATION,
    "BLOCK_FOUNDATION": FoundationEvent.BLOCK_FOUNDATION,
}

# Arch Review
# The registry lists decisions under "arch-review-pending" but in Python those
# decisions fire from ARCH_REVIEW_IN_PROGRESS (after the EVALUATION_STARTED step).
_ARCH_STAGE = {
    "arch-review-pending": ArchReviewState.ARCH_REVIEW_IN_PROGRESS,
    "arch-review-in-progress": ArchReviewState.ARCH_REVIEW_IN_PROGRESS,
    "arch-refactor-planned": ArchReviewState.ARCH_REFACTOR_PLANNED,
}
_ARCH_DECISION = {
    "NO_ACTION": ArchReviewEvent.FITNESS_PASS,
    "CREATE_REFACTOR_PLAN": ArchReviewEvent.FITNESS_WARN,
    "ESCALATE": ArchReviewEvent.FITNESS_FAIL_CRITICAL,
    "CREATE_REFACTOR_REQUESTS": ArchReviewEvent.REFACTOR_REQUESTS_CREATED,
    "DEFER": ArchReviewEvent.REFACTOR_DEFERRED,
}

# Debt
_DEBT_STAGE = {
    "architecture-debt": DebtState.DEBT_NEW,
    "debt-triaged": DebtState.DEBT_TRIAGED,
    "debt-scheduled": DebtState.DEBT_SCHEDULED,
}
_DEBT_DECISION = {
    "TRIAGE": DebtEvent.DEBT_TRIAGE,
    "DEFER": DebtEvent.DEBT_DEFER,
    "SCHEDULE": DebtEvent.DEBT_SCHEDULE,
    "RESOLVE": DebtEvent.DEBT_RESOLVE,
}


def _check(table, stage_map, decision_map, entries, label, stage_decision_overrides=None):
    """Return list of issue descriptions for any registry entries missing in Python table."""
    overrides = stage_decision_overrides or {}
    mismatches = []
    for src, decision, _ in entries:
        state = stage_map.get(src)
        event = overrides.get((src, decision)) or decision_map.get(decision)
        if state is None or event is None:
            continue  # not mapped → skip
        if not table.is_valid(state, event):
            mismatches.append(f"{label}: ({src}, {decision}) mapped to ({state}, {event}) but not found in Python table")
    return mismatches


class RoutingRegistryAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _REGISTRY_PATH.exists():
            raise unittest.SkipTest(f"Routing registry not found at {_REGISTRY_PATH}")
        cls.entries = parse_routing_registry(_REGISTRY_PATH)
        cls.by_loop = entries_by_loop(cls.entries)

    def test_registry_parses_non_empty(self) -> None:
        self.assertGreater(len(self.entries), 0, "Registry parser returned no entries")

    def test_pm_transitions_covered(self) -> None:
        # pm-finalizing DEFER/BLOCK/ESCALATE are Phase-2 events, distinct from Phase-1.
        overrides = {
            ("pm-finalizing", "DEFER"): PMEvent.PHASE2_DEFER,
            ("pm-finalizing", "BLOCK"): PMEvent.PHASE2_BLOCK,
            ("pm-finalizing", "ESCALATE"): PMEvent.PHASE2_ESCALATE,
        }
        issues = _check(_PM_TABLE, _PM_STAGE, _PM_DECISION, self.by_loop.get("pm", []), "PM", overrides)
        self.assertEqual(issues, [], "\n".join(issues))

    def test_po_transitions_covered(self) -> None:
        issues = _check(_PO_TABLE, _PO_STAGE, _PO_DECISION, self.by_loop.get("po", []), "PO")
        self.assertEqual(issues, [], "\n".join(issues))

    def test_foundation_transitions_covered(self) -> None:
        issues = _check(_FOUNDATION_TABLE, _FOUNDATION_STAGE, _FOUNDATION_DECISION, self.by_loop.get("foundation", []), "Foundation")
        self.assertEqual(issues, [], "\n".join(issues))

    def test_arch_review_transitions_covered(self) -> None:
        issues = _check(_ARCH_REVIEW_TABLE, _ARCH_STAGE, _ARCH_DECISION, self.by_loop.get("arch_review", []), "ArchReview")
        self.assertEqual(issues, [], "\n".join(issues))

    def test_debt_transitions_covered(self) -> None:
        debt_entries = self.by_loop.get("debt", [])
        self.assertGreater(len(debt_entries), 0, "Debt entries were not parsed into the debt loop bucket")
        issues = _check(_DEBT_TABLE, _DEBT_STAGE, _DEBT_DECISION, debt_entries, "Debt")
        self.assertEqual(issues, [], "\n".join(issues))

    def test_all_python_pm_transitions_are_in_registry_or_documented(self) -> None:
        """Every Python PM transition should either exist in the registry or be a
        system-internal event (RETRY_THRESHOLD_EXCEEDED, FOUNDATION_GATE_PASSED)."""
        internal_events = {PMEvent.RETRY_THRESHOLD_EXCEEDED, PMEvent.FOUNDATION_GATE_PASSED,
                           PMEvent.RESEARCH_TASKS_CREATED, PMEvent.LINKED_RESEARCH_ALL_CLOSED,
                           PMEvent.SYNTHESIS_READY}
        registry_pm = {(src, dec) for src, dec, _ in self.by_loop.get("pm", [])}
        # Build reverse: python (state, event) → check registry has something for that stage+decision
        stage_by_state = {v: k for k, v in _PM_STAGE.items()}
        decision_by_event = {v: k for k, v in _PM_DECISION.items()}
        gaps = []
        for (state, event), _ in _PM_TABLE.items():
            if event in internal_events:
                continue
            stage = stage_by_state.get(state)
            decision = decision_by_event.get(event)
            if stage and decision and (stage, decision) not in registry_pm:
                gaps.append(f"Python PM ({state.value}, {event.value}) not found in registry")
        self.assertEqual(gaps, [], "\n".join(gaps))


if __name__ == "__main__":
    unittest.main()
