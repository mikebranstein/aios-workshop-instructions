# Regression Analysis — Actual Test Failure Comparison

## Raw pytest Output: Prior State vs Current State

### Prior State (b844338 — before adapter_source changes)
```
170 passed, 3 skipped in 5.82s
```
**Status:** ✅ All tests passing

### Current State (4ec0ed7 — after adapter_source enforcement)
```
13 failed, 161 passed, 3 skipped in 5.85s
```
**Status:** ❌ 13 new test failures (regression)

---

## Regression Finding

**The 13 failures are NOT pre-existing.** They were introduced by this session's adapter_source changes.

**Failing tests (by loop):**
- **ArchReview (2):** test_no_action_path, test_warn_creates_refactor_requests
- **Dev (5):** test_design_revise_feedback_loop_completes, test_full_pipeline_happy_path, test_resumes_from_mid_pipeline_state, test_happy_path_to_released, test_terminal_design_blocked
- **Foundation (4):** test_full_happy_path_approved, test_revise_then_approve, test_gate_blocked_terminal, test_happy_path_approved
- **PO (2):** test_full_path_queued_to_feature_requests_created, test_happy_path_to_feature_requests_created

---

## Root Cause: Unknown — Requires Investigation

The failures are consistent across all loops:
1. First auto-transition (PENDING→IN_PROGRESS, QUEUED→PRIORITIZING) completes
2. Next state advancement does not occur
3. Tests fail expecting terminal state or further progression

**Example failure log:**
```
[2026-07-12T20:49:48.398527+00:00] [arch_review] issue=1 ARCH_REVIEW_PENDING -> ARCH_REVIEW_IN_PROGRESS (EVALUATION_STARTED, EVALUATION_STARTED)
AssertionError: Expected 'arch:no-action' but got 'arch:review-in-progress'
```

**Changes made to this session that could cause regression:**
1. Added `adapter_source` parameter to 11 TransitionLogEntry creations
2. Moved `adapter_source` field in dataclass (moved from after optional fields to mixed position, then moved back)
3. Changed default from `adapter_source: str = "copilot"` to `adapter_source: str = ""` (current)
4. Added `adapter_source` property to JudgmentLLMAdapter base class

---

## Reclassification — Escalating to MUST FIX

The 13 failures indicate **broken state advancement in 4 of 6 orchestrator loops**. This is not "CAN DEFER (low priority)". This must be resolved before any production claims.

---

## Status

❌ **This session's adapter_source enforcement work has introduced a regression that breaks core orchestrator state advancement.**

**No production readiness claims can be made until this regression is resolved.**

Pending:
1. **Identify and fix regression source** (causes orchestrator routing to stop after first auto-transition)
2. **Restore 170 passed, 0 failed baseline**
3. Re-verify registry alignment and circuit breaker behavior
4. Test adapter_source enforcement without breaking state advancement
