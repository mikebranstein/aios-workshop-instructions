import tempfile
import unittest

from aios_orchestration_core.policies.retry import RetryPolicy, RetryState
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.pm import PMState
from pm_orchestrator.circuit_breaker import PMBlockContext, PMCircuitBreaker


class Phase10CircuitBreakerTests(unittest.TestCase):
    def test_reaches_pm_needs_human_with_block_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            breaker = PMCircuitBreaker(
                retry_policy=RetryPolicy(max_attempts=2),
                log_store=TransitionLogStore(f"{tmp}/runlog.sqlite"),
            )
            retry_state = RetryState()
            context = PMBlockContext(
                blocked_stage="PHASE2_VALIDATING",
                reason_code="SCHEMA_VALIDATION_FAILED",
                reason_detail="artifact schema mismatch",
                last_error_class="ToolSchemaValidationError",
            )

            state = breaker.handle_failure("run-1", 101, PMState.PM_PHASE2_VALIDATING, retry_state, context)
            self.assertEqual(state, PMState.PM_PHASE2_VALIDATING)
            state = breaker.handle_failure("run-1", 101, PMState.PM_PHASE2_VALIDATING, retry_state, context)
            self.assertEqual(state, PMState.PM_NEEDS_HUMAN)


if __name__ == "__main__":
    unittest.main()
