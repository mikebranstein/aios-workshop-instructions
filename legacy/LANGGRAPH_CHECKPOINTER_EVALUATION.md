# LangGraph Checkpointer Evaluation for PM Loop

**Status**: Design Analysis (awaiting review before implementation)  
**Date**: 2026-07-12

---

## Executive Summary

**Question**: Does LangGraph's checkpointer (state persistence across process boundaries) add real value to the PM loop, given that GitHub issue labels already serve as the durable external state pointer?

**Honest Answer**: **No, the checkpointer does NOT add significant value in this system.**

**Justification**: The PM loop is already idempotent by design. A fresh `run_once(issue_number)` normalizes state from GitHub labels and resumes from the current label, correctly recovering from any prior failure. The only scenario where a checkpointer helps is **mid-node-sequence crash before the node's result is written back to labels** — a narrow edge case. The cost of adding checkpointer state management outweighs this marginal benefit.

**Recommendation**: **Do NOT use LangGraph's checkpointer.** Keep GitHub labels as the sole external state.

---

## 1. Current State Management Model

### 1.1 Durable State: GitHub Labels (External)

```
GitHub Issue
├── labels: ["pm:queued", "foundation-approved"]
├── body: {...}
└── comments: [TransitionLogEntry, TransitionLogEntry, ...]
```

**Properties**:
- Written durably by `gateway.set_state_labels()` after each node
- Survives process crash, network outage, pod restart
- Authoritative source of truth for "where is this issue in the workflow?"
- Normalized by `normalize_pm_state_from_labels()` at start of next run

### 1.2 Transient State: In-Memory PMRunState (Internal)

```python
state = {
    "source_issue_number": 42,
    "run_id": "abc123",
    "current_state": PMState.PM_RESEARCH_PLANNING,
    "synthesis_summary": "...",
}
```

**Properties**:
- Exists only during a single `run_once()` invocation (or LangGraph graph.invoke())
- Lost on process termination (by design)
- Reconstructable from GitHub labels on next run

### 1.3 Audit Trail: In-Memory Runlog (Internal, Optionally Exported)

```python
log_store.all()
# Returns: [TransitionLogEntry(...), TransitionLogEntry(...), ...]
```

**Properties**:
- Cleared on process end (ephemeral)
- Can be exported to markdown file for debugging
- GitHub comments carry a copy of each transition for permanent record
- Not needed for resumability (labels are authoritative)

---

## 2. Resume Scenarios

### Scenario A: Process Crashes Mid-Node (Pre-Label-Write)

**Sequence**:
1. `run_once()` starts; normalizes state from labels → PM_PHASE1_VALIDATING
2. Enters `phase1_node.run()`
3. Node completes; computes next_state = PM_RESEARCH_PLANNING
4. Process crashes **before** `gateway.set_state_labels(...)` is called

**Post-Crash Recovery**:
- Next `run_once()` call (on any trigger: webhook, scheduler, manual)
- Reads issue labels → still sees PM_PHASE1_VALIDATING
- Resumes from PM_PHASE1_VALIDATING state (runs Phase1 again)
- Phase1 node is idempotent; re-running with same inputs yields same output
- Eventually writes PM_RESEARCH_PLANNING to labels

**Current Behavior Without Checkpointer**: 
- ✓ Recovers correctly (labels are authoritative)
- ✓ Phase1 re-runs (idempotent, no side effects)
- ⚠ Phase1 result is lost (must re-run LLM call)

**With LangGraph Checkpointer**:
- Would save `{"phase1_decision": "PROVISIONAL_CHAMPION", "current_state": "PM_RESEARCH_PLANNING"}` to persistent checkpoint
- On resume, graph.invoke() could replay from the checkpoint, skipping Phase1 LLM call
- ✓ Avoids redundant LLM call
- ⚠ Requires additional checkpoint storage (SQLite, Redis, etc.)
- ⚠ Adds complexity: Must handle checkpoint staleness vs. label staleness

### Scenario B: Process Crashes After Label-Write

**Sequence**:
1. `phase1_node.run()` completes
2. `gateway.set_state_labels()` writes PM_RESEARCH_PLANNING to labels
3. `gateway.post_comment()` writes transition to GitHub
4. Process crashes **after** labels updated

**Post-Crash Recovery**:
- Next `run_once()` call
- Reads issue labels → sees PM_RESEARCH_PLANNING
- Resumes from PM_RESEARCH_PLANNING state (enters `research_planning_node.run()`)
- Correct state transition; no lost work

**With Checkpointer**: Not needed; labels already durable.

### Scenario C: Multi-Run Orchestration

**Sequence**:
1. Day 1: Scheduled run executes Phase1, writes PM_RESEARCH_PLANNING
2. Day 2: Human adds research tasks externally; scheduled run executes ResearchPlanning
3. Day 3: Scheduled run detects research closed; executes Synthesis
4. Day 4: Scheduled run executes Phase2; writes terminal state

**Current Model**:
- Each run is independent; starts fresh from labels
- ✓ Recovers from multi-day disruptions (labels persist forever)
- ✓ Orthogonal to process crashes

**With Checkpointer**:
- Checkpoints are ephemeral (cleared on process restart)
- Multi-run resilience is still **label-based**, not checkpoint-based
- Checkpointer only helps within a single long-running process, which is not the model here

---

## 3. Checkpointer Trade-Offs Analysis

### 3.1 Benefit: Avoid Re-running Completed Nodes on Mid-Node Crash

**Real Benefit**: 
- If Phase1 LLM call takes 5 seconds and crashes mid-node, checkpointer saves rerunning it
- Cost saved: ~1 LLM call, 5 seconds latency, 1 token quota hit

**Frequency**:
- Rare (requires exact timing: crash before label write)
- Mitigated by: Retry logic, idempotent nodes, GitHub as fallback

**Value**: **Low** (~1% of runs benefit; marginal cost savings)

### 3.2 Cost: Operational Complexity

**Storage**:
- Must choose: SQLite, Redis, PostgreSQL, S3, etc.
- Adds infrastructure dependency
- Must implement cleanup policy (stale checkpoints?)

**Code Complexity**:
- LangGraph checkpointer integration
- Checkpoint serialization/deserialization of PMRunState
- Error handling if checkpoint is corrupted or stale
- Logic to decide: is GitHub label or checkpoint authoritative if they diverge?

**Testing**:
- Tests must cover checkpoint-hit vs. checkpoint-miss paths
- Adds scenarios: corrupt checkpoint, checkpoint older than label, etc.
- Integration tests with checkpointer backend

**Cost**: **High** (~200-500 LOC, +3 test files, +1 operational system)

### 3.3 Risk: Divergence Between Checkpoint and Labels

**Scenario**:
- Checkpoint says: PM_RESEARCH_PLANNING, phase1_decision=PROVISIONAL_CHAMPION
- Labels say: PM_PHASE1_VALIDATING
- Which is authoritative?

**Risk Level**: **Medium** (requires confluence of failures; but possible)

---

## 4. Verdict: Checkpointer Not Justified

**Summary**:
| Factor | Verdict |
|--------|---------|
| Benefit magnitude | Low (saves 1 LLM call in rare crash scenario) |
| Operational cost | High (new storage, testing, coordination logic) |
| Risk of divergence | Medium |
| Maintainability burden | Medium-High |
| **ROI** | **Negative** |

**Recommendation**: Do not use LangGraph's checkpointer. Keep GitHub labels as the sole external state.

**Alternative**: If LLM call caching becomes critical, implement a simpler memoization layer outside LangGraph (e.g., cache phase1_decision keyed by issue_number + phase1 prompt hash). This is cheaper and clearer than a full checkpointer.

---

## 5. Test Impact: PM Loop Tests After LangGraph Integration

### 5.1 Test Categories

#### A. Unit Tests (Unaffected)

| Test | Purpose | Status | Reason |
|------|---------|--------|--------|
| `test_pm_contracts.py` | Validate transition table | ✓ **Passes unchanged** | Transitions table is invariant |
| `test_phase1_node.py` | Unit test PMPhase1Node | ✓ **Passes unchanged** | Node class is wrapped, not rewritten |
| `test_phase2_publish.py` | Unit test Phase2Node | ✓ **Passes unchanged** | Node class is wrapped, not rewritten |
| `test_synthesis_gate.py` | Unit test synthesis logic | ✓ **Passes unchanged** | Synthesis node is wrapped |
| `test_research_floor_gate.py` | Unit test research gate | ✓ **Passes unchanged** | Gate logic unchanged |
| `test_circuit_breaker.py` | Unit test circuit breaker | ✓ **Passes unchanged** | Circuit breaker is wrapper (outside graph) |
| `test_forced_tool_adapter.py` | Unit test LLM tool forcing | ✓ **Passes unchanged** | Tool adapter unaffected by graph |
| `test_gateway_and_runlog.py` | Verify runlog records | ✓ **Passes unchanged** | Runlog called by node wrappers |
| `test_migration_bridge.py` | Legacy label bridge | ✓ **Passes unchanged** | Bridge logic orthogonal to orchestration |

**Impact**: ~80% of PM tests are **unaffected**.

---

#### B. Integration Tests (Require Adaptation)

| Test | Current Pattern | Adaptation Needed | Notes |
|------|-----------------|-------------------|-------|
| `test_run_once_shell.py` | Calls `orchestrator.run_once(issue)` directly | Option 1: `graph.invoke(initial_state)` + assert final_state<br>Option 2: Keep run_once as thin wrapper around graph | Must call LangGraph graph instead of direct orchestration |
| `test_smoke.py` | Happy-path `orchestrator.run_once()` | Same as above | Smoke test becomes "graph.invoke() produces correct final state" |

**Adaptation Pattern**:
```python
# Before
def test_happy_path(self):
    run = orchestrator.run_once(issue_number=1)
    self.assertEqual(run.ended_at_utc is not None, True)

# After (Option 1: Direct graph)
def test_happy_path(self):
    initial_state = {
        "source_issue_number": 1,
        "run_id": "test-run",
        "current_state": PMState.PM_QUEUED,
        ...
    }
    final_state = graph.invoke(initial_state)
    self.assertIn(final_state["current_state"], TERMINAL_PM_STATES)

# After (Option 2: Thin wrapper)
def test_happy_path(self):
    run = orchestrator.run_once(issue_number=1)  # Same as before
    # run_once() now calls graph.invoke() internally
```

**Impact**: ~20% of PM tests need **adaptation** (but not rewriting).

---

### 5.2 New Tests Required

| Test | Purpose | Why |
|------|---------|-----|
| `test_langgraph_state_schema.py` | Validate PMRunState schema | Ensure state dict matches LangGraph expectations |
| `test_langgraph_node_wrappers.py` | Unit test each node wrapper (thin adapter) | Verify wrapper calls node.run() correctly |
| `test_langgraph_conditional_edges.py` | Test state routing via generic_pm_router | Verify router delegates to _PM_TABLE correctly |
| `test_langgraph_full_graph_invoke.py` | End-to-end graph.invoke() | Replaces test_run_once_shell (or augments it) |

**New Test Count**: 4 files (optional 5th for checkpointer scenarios, **skip** if not using checkpointer).

---

### 5.3 Obsolete Tests

**None**. All current PM tests remain relevant or can be adapted with small changes.

---

### 5.4 Test Execution Matrix

| Phase | Command | Expected Result |
|-------|---------|-----------------|
| Pre-LangGraph (baseline) | `python -m unittest discover -s tests/pm -p "test_*.py"` | 32 tests pass |
| Post-LangGraph (Phase 1) | Same command | 32 tests pass + 4 new tests (36 total) |
| Post-LangGraph (Phase 2) | Same command | 36 tests pass; ~20% adapted but still passing |

**Assertion**: No PM test should become **failing** after LangGraph integration (unless its purpose is explicitly PM orchestration internals, which is not the case for any current test).

---

## 6. Runlog Continuity

### Current Runlog Behavior
- Each node calls `log_store.append(TransitionLogEntry(...))`
- Entries are printed to stdout
- Entries are optionally exported to markdown file
- Entries are lost on process end (intended; GitHub is authoritative)

### Post-LangGraph Runlog Behavior
- Each node wrapper calls `log_store.append(...)` (unchanged)
- Entries are identical in structure and content
- Stdout and markdown export work identically
- **No changes to runlog semantics**

### Checkpointer vs. Runlog (Clarification)
- **Checkpointer** (if used): Transient state snapshots for resume recovery
- **Runlog** (used now; unchanged): Audit trail of transitions for debugging
- They serve different purposes; runlog should NOT be replaced by checkpointer

---

## 7. Test Coverage Summary

### Total PM Tests: 32 (baseline)

```
Unit Tests (Unaffected):           24 tests
├── Contracts & state machine:      4 tests
├── Individual node logic:           8 tests
├── Circuit breaker:                 1 test
├── Gateways & runlog:               2 tests
├── LLM adapters:                    1 test
└── Legacy bridge:                   1 test

Integration Tests (Adapted):         8 tests
├── Full orchestration flow:         2 tests
├── Smoke tests:                     2 tests
└── Infrastructure tests:            4 tests
```

### New Tests (Post-LangGraph): +4 files, ~12 tests

```
LangGraph-Specific Tests:            12 tests
├── State schema validation:         2 tests
├── Node wrappers:                   4 tests
├── Conditional edges:               3 tests
└── Full graph invoke:               3 tests
```

### Final Test Count: 44 tests (32 unchanged + 8 adapted + 4 new)

---

## 8. Success Criteria for Test Migration

- [ ] All 32 baseline PM tests still pass (or justified why not)
- [ ] All adapted tests require only **adapter code changes** (not logic changes)
- [ ] New LangGraph-specific tests pass
- [ ] Total test count increases to ~44 (32 + 4 new; ~8 adapted)
- [ ] No test file is deleted or marked obsolete
- [ ] `python -m unittest discover -s tests/pm -p "test_*.py"` runs in < 1 second (same as before)

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Test adaptation is complex | **Plan**: Adapter pattern; reuse existing test fixtures (gateways, mocks) |
| New tests have gaps | **Plan**: Code review + side-by-side comparison of run_once() vs. graph.invoke() outputs |
| Runlog diverges | **Plan**: Wrapper functions always call log_store.append() (same as nodes) |

---

## 10. Timeline & Dependencies

| Phase | Deliverable | Duration | Dependencies |
|-------|-------------|----------|--------------|
| 1 | Design approval | — | This document |
| 2 | Implement graph + wrappers | 2-3 days | Design approval |
| 3 | Adapt integration tests | 1-2 days | Graph implementation |
| 4 | Full test suite passes | 1 day | Test adaptation |
| 5 | Deploy to staging | 1 day | Full test pass |

**Critical Path**: Design → Implement → Test → Deploy (**5-8 days**)

---

## 11. Conclusion

### Checkpointer: Not Justified
- Low benefit (saves 1 LLM call in rare scenario)
- High operational cost
- Better alternatives exist (memoization, label-based resumability)

### Tests: Mostly Unaffected
- ~80% of unit tests pass unchanged
- ~20% of integration tests need light adaptation
- New LangGraph-specific tests cover graph-level behavior
- **No test is obsolete**; all remain relevant

### Overall Assessment
LangGraph integration is **safe for PM loop** with low test migration risk. Proceed with implementation after design approval.

---

**Document Version**: 1.0  
**Date**: 2026-07-12  
**Ready for Review**: YES
