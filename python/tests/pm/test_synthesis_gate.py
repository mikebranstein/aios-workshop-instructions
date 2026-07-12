import unittest

from pm_orchestrator.nodes.synthesis import PMResearchSynthesisNode, SynthesisGateConfig


class StubSynthesisAdapter:
    def invoke_json(self, task_type, prompt_vars, model_hint=""):
        return type(
            "Result",
            (),
            {
                "payload": {
                    "summary": "Market signal supported",
                    "confidence_score": 0.81,
                    "closed_linked_research_count": prompt_vars["closed_linked_research_count"],
                }
            },
        )()


class Phase7SynthesisTests(unittest.TestCase):
    def test_hybrid_gate_passes_with_floor_and_confidence(self) -> None:
        node = PMResearchSynthesisNode(
            StubSynthesisAdapter(),
            SynthesisGateConfig(min_confidence_score=0.75, min_closed_linked_research_count=2),
        )
        synthesis = node.run(issue_number=1, closed_linked_research_count=2)
        self.assertEqual(synthesis.closed_linked_research_count, 2)

    def test_hybrid_gate_fails_when_floor_not_met(self) -> None:
        node = PMResearchSynthesisNode(
            StubSynthesisAdapter(),
            SynthesisGateConfig(min_confidence_score=0.75, min_closed_linked_research_count=3),
        )
        with self.assertRaises(ValueError):
            node.run(issue_number=1, closed_linked_research_count=2)


if __name__ == "__main__":
    unittest.main()
