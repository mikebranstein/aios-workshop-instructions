# Orchestrator Consistency Checklist

## Purpose
Ensure all 6 LangGraph orchestrators (PM, PO, Foundation, Dev, Discovery, ArchReview) maintain identical architectural patterns and code structure.

---

## File Structure & Naming

- [ ] File named: `langgraph_[loop]_graph.py` (e.g., `langgraph_pm_graph.py`)
- [ ] Located in: `[loop]_orchestrator/` directory
- [ ] Module docstring documents: Entry point, nodes, and routing model
- [ ] All imports are necessary (unused imports removed)

---

## Class Structure

### RunState TypedDict
- [ ] Named `[Loop]RunState` (e.g., `PMRunState`, `PORunState`)
- [ ] Inherits from `TypedDict` with `total=False`
- [ ] Docstring explains `total=False` semantics
- [ ] Contains: `source_issue_number`, `run_id`, `current_state`
- [ ] Additional fields marked as `Optional`

### Main Orchestrator Class
- [ ] Named `[Loop]GraphOrchestrator` (e.g., `PMGraphOrchestrator`)
- [ ] Docstring: "Manages [Loop] loop orchestration via LangGraph StateGraph with conditional_edges routing"
- [ ] `__init__` signature:
  - Takes gateway, log_store, adapter(s) as parameters
  - Initializes node instances (if applicable)
  - Calls `self._graph = self._build_graph()`
- [ ] `_build_graph()` method returns compiled StateGraph
- [ ] `invoke()` method: Takes `initial_state: [RunState]`, returns `[RunState]`

---

## Routing Implementation (Conditional_Edges Pattern)

### Node Methods
- [ ] Method name: `_node_[node_name]`
- [ ] Parameter: `state: [RunState]`
- [ ] Returns: `[RunState]` (always returns dict with `current_state`)
- [ ] Pattern: `return {**state, "current_state": next_state}`
- [ ] Docstring: Describes what node does

### Routing Methods
- [ ] Method name: `_route_[node_name]`
- [ ] Parameter: `state: [RunState]`
- [ ] Returns: `str` (node name) or `END`
- [ ] Pattern:
  ```python
  def _route_[node_name](self, state: [RunState]) -> str:
      current_state = state.get("current_state")
      if current_state in TERMINAL_[LOOP]_STATES:
          return END
      elif current_state == [State].STATE_A:
          return "next_node"
      else:
          return END
  ```
- [ ] **One routing function per node** (not reused across multiple nodes)

### Graph Building
- [ ] `builder = StateGraph([RunState])`
- [ ] Add all nodes: `builder.add_node("name", self._node_name)`
- [ ] Add entry: `builder.add_edge(START, "normalize_and_route")`
- [ ] Conditional edges: `builder.add_conditional_edges("node", self._route_node)`
- [ ] Terminal edges: `builder.add_edge("final_node", END)`
- [ ] Return: `builder.compile()`

---

## Import Consistency

### Required Imports
- [ ] `from typing import Optional, TypedDict`
- [ ] `from datetime import datetime, timezone` (if logging transitions)
- [ ] `from langgraph.graph import StateGraph, START, END`
- [ ] Domain-specific imports from `aios_orchestration_core`
- [ ] Loop-specific event, state, transition imports

### Removed Imports
- [ ] ❌ `from typing_extensions import Literal` (not needed with conditional_edges)
- [ ] ❌ `from langgraph.types import Command` (old pattern, removed)

---

## Imports Order
1. Standard library (`typing`, `datetime`)
2. Third-party (`langgraph`)
3. Domain core (`aios_orchestration_core`)
4. Loop-specific nodes

---

## Docstring Standards

### Module Docstring
```python
"""LangGraph StateGraph for [Loop] orchestration loop.

This module wraps the [Loop] orchestration logic in a LangGraph StateGraph using conditional_edges.
Nodes focus on business logic and return updated state (dict).
Routing functions check current_state and return next node name (string) or END.
This maintains the non-negotiable constraint: _[LOOP]_TABLE remains the single source of truth.
"""
```

### Method Docstrings
- [ ] Node methods: "Wrapper around [NodeClass]. Update state with result."
- [ ] Routing methods: "Route from [node_name] using TransitionTable."
- [ ] Special nodes: Describe conditional logic (e.g., "Auto-transition from X to Y")

---

## TransitionTable Usage

- [ ] Imported: `from aios_orchestration_core.transitions.[loop] import get_next_[loop]_state`
- [ ] Used in nodes to compute state transitions
- [ ] Routing functions call nodes, not TransitionTable directly
- [ ] Routes based on state values, not events

---

## Testing

### Routing Tests (`test_langgraph_conditional_edges.py`)
- [ ] One test per routing function
- [ ] Tests terminal state handling (returns `END`)
- [ ] Tests active state transitions (returns correct next node)
- [ ] Test method naming: `test_route_[node_name]_*`

### State Schema Tests (`test_langgraph_state_schema.py`)
- [ ] Verify `[RunState]` has required fields
- [ ] Test `invoke()` returns valid state dict
- [ ] Test node methods return valid state updates

### Full Graph Tests (`test_langgraph_full_graph_invoke.py`)
- [ ] Test terminal state behavior
- [ ] Test state transitions with real node behavior
- [ ] Use meaningful test data (not mocks with zero counts)

---

## Feedback Loops (if applicable)

If the loop supports cycling:
- [ ] Identify cycle nodes (e.g., design→intake, research→research)
- [ ] Routing function checks for loop-back conditions
- [ ] Comment explains: `# REASON loops back` or `# REASON advances`

Example:
```python
elif current_state == FoundationState.FOUNDATION_IN_PROGRESS:
    return "research"  # NEEDS_MORE loops back
elif current_state == FoundationState.FOUNDATION_REVIEW:
    return "gate"  # RECOMMEND advances
```

---

## Method Ordering (Recommended)

1. `__init__`
2. `_build_graph()`
3. `_node_normalize_and_route` (entry node)
4. `_route_normalize_and_route` (entry router)
5. Remaining `_node_*` methods (main flow)
6. Corresponding `_route_*` methods
7. `invoke()` (public interface)
8. Optional: Helper methods (logging, validation)

---

## Quick Audit Script

```bash
# Check all files have correct pattern
grep -r "_route_" python/*/langgraph_*.py | grep "def _router"  # Should be empty
grep -r "from typing_extensions import Literal" python/*/langgraph_*.py  # Should be empty
grep -r "from langgraph.types import Command" python/*/langgraph_*.py  # Should be empty

# Check all have invoke method
grep -c "def invoke" python/*/langgraph_*.py | grep ":1$"  # All should have 1

# Count routing functions (should roughly match nodes)
for f in python/*/langgraph_*.py; do echo "$f:"; grep -c "def _route_" "$f"; done
```

---

## Common Pitfalls

| Pitfall | ✅ Correct | ❌ Wrong |
|---------|----------|---------|
| Routing reuse | One function per node | One function for all nodes |
| Return types | Node returns `dict`, router returns `str` | Mixed return types |
| State updates | `{**state, "current_state": ...}` | Direct state mutation |
| Imports | Organize by category | Random order |
| Terminal check | Check first in router | Check last or missing |
| Naming | `_route_node_name` | `_router_node_name` or `route_node` |

---

## When Adding a New Orchestrator

1. Copy structure from an existing orchestrator (reference: PO)
2. Rename all `[LOOP]` placeholders
3. Update imports for domain-specific events/states/transitions
4. Update `_build_graph()` with correct nodes and edges
5. Implement routing functions for each node
6. Add tests following existing patterns
7. Run full test suite: `pytest tests/ -q`
8. Update this checklist with any new patterns discovered

---

## Reference Implementation

Use **PO Orchestrator** as reference for all new changes:
- `python/po_orchestrator/langgraph_po_graph.py` (4 nodes, simple flow)
- `tests/po/` (example test patterns)
