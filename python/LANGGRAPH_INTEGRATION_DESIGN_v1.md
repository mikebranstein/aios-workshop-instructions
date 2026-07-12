# LangGraph Integration for PM Loop — Design Document v1

**Status**: Design Proposal (awaiting review before implementation)  
**Scope**: PM loop only (PO, Dev, Foundation, Discovery, ArchReview, Debt unchanged)  
**Non-Negotiable Constraints**:
- `aios_orchestration_core/transitions/pm.py` (_PM_TABLE) remains the single source of truth
- LangGraph edges delegate to `get_next_pm_state()` / `allowed_events_for_pm_state()` — no duplication
- Existing node classes' `.run()` methods are wrapped, not reimplemented inline
- All existing PM tests must still pass (or explicit justification if deprecated)

---

## 1. Concept Mapping: PM → LangGraph

### 1.1 States and Events

| Concept | Current | LangGraph Equivalent | Details |
|---------|---------|---------------------|---------|
| **State representation** | `PMState` enum in memory + GitHub labels as durable pointer | `LangGraph StateSchema` | Durable state remains on GitHub labels; LangGraph's state dict holds transient runtime context (issue number, run_id, current_state, synthesis summary, etc.) |
| **Event** | `PMEvent` enum (semantic trigger for transition) | Input `HumanMessage` or `ToolResult` carrying decision payload | Not a direct 1:1; events are derived from LLM tool outputs (e.g., Phase1 decision → PHASE1_PROVISIONAL_CHAMPION event) |
| **Terminal states** | `TERMINAL_PM_STATES` set in `states/pm.py` | Graph node that checks membership in `TERMINAL_PM_STATES`; graph halts | LangGraph's END node reached when current_state ∈ TERMINAL_PM_STATES |

### 1.2 Transition Table → LangGraph Conditional Edges

| Current | LangGraph |
|---------|-----------|
| `_PM_TABLE: TransitionTable[PMState, PMEvent]` — immutable dict of (state, event) → next_state | `@graph.add_conditional_edges()` router functions that delegate to `_PM_TABLE.allowed_events(state)` and `get_next_pm_state(state, event)` |
| `get_next_pm_state(state: PMState, event: PMEvent) -> PMState` | Not reimplemented; called directly by LangGraph conditional edge handlers |
| Manual orchestration loops checking state, branching, calling nodes | LangGraph state machine: edges route automatically; graph.invoke() replaces `run_once()` iteration |

**Critical Assertion**: LangGraph's add_conditional_edges() is a **wrapper**, not a restatement. It reads from _PM_TABLE, never declares transitions independently.

### 1.3 Node Classes → LangGraph Node Functions

| Current | LangGraph | Relationship |
|---------|-----------|--------------|
| `PMPhase1Node.run(run_id, issue_number) -> PMState` | `async def phase1_node_runner(state: PMRunState) -> dict` | LangGraph node wraps Phase1Node; calls `.run()`, updates state dict |
| `PMResearchPlanningNode.run(issue_number)` | `async def research_planning_node_runner(state: PMRunState) -> dict` | Wraps; calls `.run()` |
| `PMResearchSynthesisNode.run(...)` | `async def synthesis_node_runner(state: PMRunState) -> dict` | Wraps; calls `.run()` |
| `PMPhase2DecisionNode.run(...)` | `async def phase2_node_runner(state: PMRunState) -> dict` | Wraps; calls `.run()` |

**Key Principle**: Each LangGraph node function is a thin adapter that:
1. Extracts relevant fields from the state dict
2. Calls the existing node class's `.run()` method  
3. Updates the state dict with the returned next_state
4. Logs the transition to runlog
5. Returns the updated state dict

No logic is duplicated or reimplemented inside LangGraph node functions.

---

## 2. Orchestrator Architecture: What Changes?

### 2.1 PMRunOnceOrchestrator — Replaced vs. Wrapped

**Current design** (`run_once.py`):
- Manual loop: check state, if X then run X-node, check next state, loop
- Calls each node sequentially via `if` statements
- Catches exceptions, routes to circuit breaker
- Returns `PMRunRecord` when done

**Post-LangGraph design** (two options):

#### Option A: graph.invoke() Replaces run_once()
```python
class PMRunOnceOrchestrator:
    def __init__(self, ...):
        self.graph = build_pm_graph(...)  # LangGraph StateGraph
    
    def run_once(self, source_issue_number: int, ...) -> PMRunRecord:
        initial_state = {
            "source_issue_number": source_issue_number,
            "run_id": str(uuid4()),
            "current_state": fetch_normalized_state_from_labels(...),
            ...
        }
        final_state = self.graph.invoke(initial_state, config={"configurable": {...}})
        return PMRunRecord(..., ended_at_utc=datetime.now(...))
```

**Pros**: Clean separation of concerns; graph is the engine; orchestrator is a thin wrapper  
**Cons**: `run_once()` semantics change slightly (caller doesn't see intermediate states)

#### Option B: run_once() Wraps graph.invoke()
```python
class PMRunOnceOrchestrator:
    def __init__(self, ...):
        self.graph = build_pm_graph(...)
    
    def run_once(self, source_issue_number: int, ...) -> PMRunRecord:
        # Current exception handling + bridge controller logic wraps graph.invoke()
        try:
            final_state = self.graph.invoke(...)
        except Exception as ex:
            # Handle via circuit breaker (unchanged)
            ...
        return PMRunRecord(...)
```

**Pros**: Exception handling stays familiar; existing test stubs work  
**Cons**: run_once() becomes thinner but still exists; slight redundancy

**Recommendation**: **Option A** — let LangGraph be the orchestration engine. If exception handling is needed, implement it as a LangGraph error handler node or via a dedicated exception handler at the top level.

### 2.2 PMCircuitBreaker — Wrapped or Unchanged?

**Current design**:
- `handle_failure(from_state, retry_state, context)` is called when a node throws
- Updates runlog, escalates to PM_NEEDS_HUMAN if retries exhausted

**Post-LangGraph**:

Option 1: **Circuit breaker as a LangGraph node**
- A dedicated node checks if an exception occurred in the previous step
- If yes, delegates to `PMCircuitBreaker.handle_failure()`
- Updates state with escalation or retry

Option 2: **Circuit breaker as a top-level exception handler**
- Wrap `graph.invoke()` in try-except
- On exception, call `circuit_breaker.handle_failure()` as today
- Transition to PM_NEEDS_HUMAN, update labels

**Recommendation**: **Option 2** — Keep circuit breaker logic outside the graph. It's a fault-tolerance wrapper, not part of the core state machine. This is cleaner and lets the graph model the happy path without exception plumbing.

---

## 3. State Schema for LangGraph

```python
from typing import Optional
from langchain_core.pydantic_v1 import BaseModel

class PMRunState(BaseModel):
    # Persistent identifiers
    source_issue_number: int
    run_id: str
    
    # State tracking
    current_state: PMState
    
    # Node outputs (materialized between steps)
    phase1_decision: Optional[str] = None  # e.g., "PROVISIONAL_CHAMPION"
    research_count: Optional[int] = None
    synthesis_summary: Optional[str] = None
    synthesis_confidence: Optional[float] = None
    phase2_final_state: Optional[PMState] = None
    
    # Metadata
    issue: Optional[PMIssue] = None  # Cached from gateway
    started_at_utc: str
    current_cycle: int = 0
```

**Rationale**:
- Minimal state dict; don't duplicate all gateway data
- Node functions extract issue details on demand via gateway
- Each node updates only its own output fields + current_state

---

## 4. Conditional Edges: Delegating to _PM_TABLE

### Example: Phase1 Decision Router

**Current `run_once()` pattern**:
```python
if current_state == PMState.PM_PHASE1_VALIDATING:
    current_state = self.phase1_node.run(run.run_id, issue.number)
    # phase1_node.run() returns PMState (e.g., PM_RESEARCH_PLANNING)
    # Implicit: run_once loop continues to next step
```

**LangGraph pattern (non-negotiable constraint: use _PM_TABLE)**:
```python
def phase1_router(state: PMRunState) -> str:
    """Route after phase1 completes."""
    if state.current_state not in _PM_TABLE.allowed_events(state.current_state):
        # Should never happen if state machine is correct
        return "end"
    
    # Phase1 node has already updated state.current_state to next state
    # (e.g., PM_RESEARCH_PLANNING or PM_DEFERRED)
    next_state = state.current_state
    
    # Check if terminal
    if next_state in TERMINAL_PM_STATES:
        return "end"
    
    # Route to appropriate node based on current_state
    if next_state == PMState.PM_RESEARCH_PLANNING:
        return "research_planning"
    elif next_state == PMState.PM_DEFERRED:
        return "end"
    elif next_state == PMState.PM_BLOCKED:
        return "end"
    # ... etc
```

**Key**: The router does NOT re-declare the transition table. It reads `current_state` after the node updates it, then routes based on that. The transition validity is already verified by `get_next_pm_state()` inside the node.

### More Elegant Alternative: Generic Router

```python
def generic_pm_router(state: PMRunState) -> str:
    """Route based on current_state, delegating to _PM_TABLE for validation."""
    current = state.current_state
    
    if current in TERMINAL_PM_STATES:
        return "end"
    
    # Map state to node name
    state_to_node = {
        PMState.PM_QUEUED: "check_foundation_gate",
        PMState.PM_PHASE1_VALIDATING: "phase1",
        PMState.PM_RESEARCH_PLANNING: "research_planning",
        PMState.PM_RESEARCH_WAITING: "research_gate",
        PMState.PM_RESEARCH_SYNTHESIZING: "synthesis",
        PMState.PM_PHASE2_VALIDATING: "phase2",
    }
    
    return state_to_node.get(current, "end")
```

**Advantage**: Clearer intent; router maps states to nodes, doesn't duplicate transitions.

---

## 5. LangGraph Graph Structure (Pseudo-Code)

```python
from langgraph.graph import StateGraph, END

def build_pm_graph(
    phase1_node: PMPhase1Node,
    research_planning_node: PMResearchPlanningNode,
    synthesis_node: PMResearchSynthesisNode,
    phase2_node: PMPhase2DecisionNode,
    gateway: PMGateway,
    log_store: TransitionLogStore,
) -> StateGraph:
    
    graph = StateGraph(PMRunState)
    
    # Add nodes (thin adapters wrapping existing node classes)
    graph.add_node("check_foundation_gate", 
                   lambda state: foundation_gate_node(state, gateway, log_store))
    graph.add_node("phase1", 
                   lambda state: phase1_node_runner(state, phase1_node, log_store))
    graph.add_node("research_planning", 
                   lambda state: research_planning_node_runner(state, research_planning_node))
    graph.add_node("research_gate", 
                   lambda state: research_gate_node(state, gateway, min_research_count=1))
    graph.add_node("synthesis", 
                   lambda state: synthesis_node_runner(state, synthesis_node))
    graph.add_node("phase2", 
                   lambda state: phase2_node_runner(state, phase2_node))
    
    # Add edges using generic router (delegates to _PM_TABLE)
    graph.add_edge("check_foundation_gate", "phase1")  # Deterministic; always phase1 after gate
    graph.add_conditional_edges("phase1", generic_pm_router)
    graph.add_conditional_edges("research_planning", generic_pm_router)
    graph.add_conditional_edges("research_gate", generic_pm_router)
    graph.add_conditional_edges("synthesis", generic_pm_router)
    graph.add_conditional_edges("phase2", generic_pm_router)
    
    graph.set_entry_point("check_foundation_gate")
    
    return graph.compile()
```

**Key Points**:
- Entry point is "check_foundation_gate" (replaces the `if current_state == PM_QUEUED` logic in run_once)
- All decision edges use `generic_pm_router`, which reads current_state after node execution
- Nodes are thin adapters wrapping existing PM node classes
- No transitions are re-declared

---

## 6. Test Compatibility Matrix

| Test File | Current Purpose | Post-LangGraph Status | Notes |
|-----------|-----------------|----------------------|-------|
| `test_pm_contracts.py` | Validate transition table | **Still passes** | Transitions are unchanged; only router mechanism changes |
| `test_phase1_node.py` | Unit test PMPhase1Node | **Still passes** | Node class unchanged; LangGraph just wraps it |
| `test_phase2_publish.py` | Unit test phase2 node | **Still passes** | Same as above |
| `test_synthesis_gate.py` | Unit test synthesis | **Still passes** | Same as above |
| `test_research_floor_gate.py` | Unit test research gate | **Still passes** | Same as above |
| `test_circuit_breaker.py` | Unit test circuit breaker | **Still passes** | Circuit breaker logic unchanged |
| `test_run_once_shell.py` | Integration: full orchestration flow | **Needs adaptation** | Must call LangGraph graph.invoke() instead of orchestrator.run_once() directly, OR run_once() becomes a thin wrapper |
| `test_gateway_and_runlog.py` | Verify runlog entries | **Still passes** | Runlog is still called by each node wrapper |
| `test_migration_bridge.py` | Legacy label bridge | **Still passes** | Bridge logic is orthogonal |
| `test_smoke.py` | Happy-path integration | **Needs adaptation** | Same as test_run_once_shell |
| `test_forced_tool_adapter.py` | LLM tool forcing | **Still passes** | Unaffected by graph composition |
| `test_github_api_gateway_disposable.py` | Real GitHub integration (optional) | **Unchanged** | Gate doesn't affect this |

**Summary**: 
- ~70% of PM tests remain **unchanged** (unit tests of nodes, contracts, tools)
- ~30% need **adaptation** (integration tests that directly call run_once → need to invoke graph)
- **NO tests become obsolete** unless their purpose is specifically "test old run_once orchestration," which isn't the case

---

## 7. Deployment Path

### Phase 1: Build & Test (this design review)
- [ ] Design approved
- [ ] Implement LangGraph graph builder
- [ ] Implement thin node wrappers
- [ ] Run full PM test suite; adapt integration tests as needed

### Phase 2: Shadow Mode (optional)
- Build a `@router` that allows switching between current run_once and LangGraph via config
- Run both in parallel on a set of issues; compare outputs

### Phase 3: Cutover
- Replace run_once's orchestration loop with graph.invoke()
- Keep PMRunOnceOrchestrator as public API; have it use graph internally

### Phase 4: Cleanup
- Remove old orchestration loop code from run_once.py
- Update PM documentation

---

## 8. Open Questions for Review

1. **Checkpointer value**: Does LangGraph's checkpointer add sufficient benefit given that GitHub labels are the persistent state? See separate Checkpointer Evaluation document.

2. **Error handling placement**: Should circuit breaker logic be:
   - A dedicated LangGraph error node? 
   - Kept outside the graph as a wrapper around graph.invoke()?  
   - Mixed (both)?

3. **Async/Sync**: Should LangGraph nodes be `async def` or sync? Impacts integration with blocking I/O (gateway, LLM adapter).

4. **Migration bridge**: Does BridgeModeController need to be graph-aware, or does it continue as a side-effect in run_once wrapper?

5. **Future loops**: Once PM is stable on LangGraph, apply same pattern to PO? Or wait for broader framework decisions?

---

## 9. Success Criteria

- [ ] Graph structure compiles without errors
- [ ] All existing PM tests pass (or justified why not)
- [ ] graph.invoke(initial_state) returns correct final_state
- [ ] Transitions always come from _PM_TABLE; no duplication
- [ ] Node wrappers call existing .run() methods unchanged
- [ ] Runlog entries are identical to pre-LangGraph run_once
- [ ] PM loop behavior is indistinguishable from production perspective

---

**Document Version**: 1.0  
**Date**: 2026-07-12  
**Ready for Review**: YES (awaiting feedback before implementation begins)
