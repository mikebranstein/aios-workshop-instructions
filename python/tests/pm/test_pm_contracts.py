import unittest

from aios_orchestration_core.artifacts.pm_decisions import PMResearchSynthesis
from aios_orchestration_core.artifacts.strategic_opportunity import (
    MarketSizeEstimate,
    StrategicOpportunityArtifact,
    TraceMetadata,
)
from aios_orchestration_core.events.pm import PMEvent
from aios_orchestration_core.labels.pm_labels import normalize_pm_state_from_labels
from aios_orchestration_core.states.pm import PMState, TERMINAL_PM_STATES
from aios_orchestration_core.transitions.pm import PMTransitionError, allowed_events_for_state, get_next_pm_state


class PMContractsPhase1Tests(unittest.TestCase):
    def test_strategic_opportunity_schema_has_required_audit_and_handoff_fields(self) -> None:
        required_fields = {
            "trace",
            "handoff_contract_version",
            "decision_rationale",
            "evidence_refs",
            "research_item_ids",
        }
        self.assertTrue(required_fields.issubset(set(StrategicOpportunityArtifact.__annotations__.keys())))

        trace_required_fields = {"run_id", "model", "prompt_version"}
        self.assertTrue(trace_required_fields.issubset(set(TraceMetadata.__annotations__.keys())))

    def test_legacy_label_normalizes_to_typed_state(self) -> None:
        normalized = normalize_pm_state_from_labels(["pm-opportunity"])
        self.assertEqual(normalized.state, PMState.PM_OUTPUT_PUBLISHED)
        self.assertTrue(normalized.saw_legacy_label)

    def test_canonical_label_wins_conflict(self) -> None:
        normalized = normalize_pm_state_from_labels([
            "pm:phase1-validating",
            "pm-blocked",
        ])
        self.assertEqual(normalized.state, PMState.PM_PHASE1_VALIDATING)
        self.assertEqual(normalized.conflict_labels, frozenset())

    def test_multi_canonical_conflict_is_rejected(self) -> None:
        normalized = normalize_pm_state_from_labels([
            "pm:phase1-validating",
            "pm:blocked",
        ])
        self.assertIsNone(normalized.state)
        self.assertIn("pm:phase1-validating", normalized.conflict_labels)
        self.assertIn("pm:blocked", normalized.conflict_labels)

    def test_terminal_states_have_no_outgoing_events(self) -> None:
        for state in TERMINAL_PM_STATES:
            self.assertEqual(allowed_events_for_state(state), frozenset())

    def test_retry_from_active_state_goes_to_needs_human(self) -> None:
        next_state = get_next_pm_state(PMState.PM_PHASE1_VALIDATING, PMEvent.RETRY_THRESHOLD_EXCEEDED)
        self.assertEqual(next_state, PMState.PM_NEEDS_HUMAN)

    def test_retry_from_terminal_state_fails(self) -> None:
        with self.assertRaises(PMTransitionError):
            get_next_pm_state(PMState.PM_BLOCKED, PMEvent.RETRY_THRESHOLD_EXCEEDED)

    def test_research_synthesis_uses_hybrid_gate(self) -> None:
        synthesis = PMResearchSynthesis(
            summary="Signals are strong across three segments.",
            confidence_score=0.82,
            closed_linked_research_count=3,
        )
        synthesis.validate(min_confidence_score=0.75, min_research_count=2)

    def test_research_synthesis_rejects_overconfident_single_item(self) -> None:
        synthesis = PMResearchSynthesis(
            summary="One interview looked very positive.",
            confidence_score=0.95,
            closed_linked_research_count=1,
        )
        with self.assertRaises(ValueError):
            synthesis.validate(min_confidence_score=0.75, min_research_count=2)

    def test_market_size_estimate_allows_nullable_value(self) -> None:
        artifact = StrategicOpportunityArtifact(
            artifact_version="1.0.0",
            artifact_type="strategic_opportunity",
            artifact_id="so-001",
            source_pm_issue_number=42,
            title="Mobile workflow expansion",
            strategic_thesis="Field time savings can improve retention.",
            customer_problem="Field users cannot complete core task while mobile.",
            market_size_estimate=MarketSizeEstimate(
                method="bottom_up_interview_sampling",
                confidence=0.67,
                value=None,
                unit=None,
            ),
            decision="CHAMPION",
            decision_rationale="Strong research consensus",
            evidence_refs=["pm-idea:42", "wiki:persona/field-tech"],
            research_item_ids=[1001, 1002],
            handoff_contract_version="1.0.0",
            trace=TraceMetadata(run_id="run-1", model="claude-sonnet-4.6", prompt_version="pm-v1"),
            confidence_score=0.8,
            produced_at="2026-07-12T12:00:00",
        )
        artifact.validate()


if __name__ == "__main__":
    unittest.main()
