# ADR 0001: Generalize PM Orchestrator Pattern to All Six Loops

**Status:** ACCEPTED  
**Date:** 2026-07-13  
**Author:** AIOS Development Team  
**Affected Components:** PM, PO, Dev, Foundation, Discovery, ArchReview orchestrators  

---

## Context

The PM orchestrator was initially designed as a prototype to validate the LangGraph StateGraph pattern for orchestrating deterministic, multi-stage agentic workflows. It successfully demonstrated:

- Typed, immutable state machines (StateGraph + TransitionTable)
- Label-based state persistence (GitHub issue labels)
- Circuit breaker escalation on retry exhaustion
- Audit trail via TransitionLogEntry
- Gateway abstraction for issue operations

After validation, the question arose: **should this pattern be generalized to all 6 loops (PO, Dev, Foundation, Discovery, ArchReview), or should they use different approaches?**

---

## Decision

**Generalize the PM orchestrator pattern to all six loops uniformly.**

All 6 loops (PM, PO, Dev, Foundation, Discovery, ArchReview) now use:
1. **LangGraph StateGraph** with identical architecture (conditional_edges, routers delegating to get_next_*_state functions)
2. **TransitionTable[S, E]** as the single source of truth for state transitions
3. **Label-based state persistence** (GitHub issue labels)
4. **Circuit breaker** wrapping the entire compiled graph
5. **TransitionLogEntry** audit trail with explicit adapter_source field

---

## Rationale

### 1. Consistency Across Loops

- **Single pattern, six implementations** reduces cognitive load for maintainers
- Debugging and reasoning about state transitions is uniform across all loops
- Training and onboarding is simpler: one architecture to understand, not six variants

### 2. Proven Pattern

- PM orchestrator already validated this design in production scenarios
- No need to experiment with alternative patterns that haven't been tested
- Risk of divergent patterns: each would need separate testing, debugging, and maintenance

### 3. Correctness by Construction

- StateGraph + TransitionTable enforces correctness at initialization time
- No implicit state changes; all transitions are explicit in the transition table
- Type safety at both Python type-check time and runtime validation

### 4. Auditability

- Every state transition logged with explicit adapter_source (copilot vs stub)
- Label-based state is human-readable in GitHub UI
- Complete audit trail enables post-hoc reasoning about decision sequences

### 5. Extensibility

- New loops (if added) can follow the same pattern without redesign
- New gateway types (if needed) are isolated behind the Gateway protocol

---

## Implications

### Validation Scope

- All 6 orchestrators were validated with the same pattern once (after PM prototype)
- Each loop was NOT re-validated separately after generalization
- Rationale: The pattern itself is invariant across loops; what differs is the state/event enums and transition tables (loop-specific, data-driven)

### State Persistence

- All 6 loops persist state via GitHub issue labels (single source of truth)
- LangGraph compile() is called without an explicit checkpointer argument
- Consequence: Between runs, orchestrators recover state by reading issue labels
- This is by design (deliberate, not undecided)

### GitHub Integration

- Only the PM loop currently has a real GitHub API gateway (GitHubApiPMGateway)
- Other 5 loops use in-memory gateways (suitable for simulation/testing)
- If other loops need real GitHub integration, they can follow the PM pattern (GitHub CLI-based, subprocess calls)

### Adapter Strategy

- All runners support `--stub` flag to force StubLLMAdapter (test mode)
- Without `--stub`, Copilot SDK is required and failure is loud (no silent fallback)
- adapter_source field in TransitionLogEntry tracks which adapter was used (auditable)

---

## Alternatives Considered

### Alt 1: Loop-Specific Implementations

- **Pro:** Each loop could be optimized for its specific domain needs
- **Con:** Massive maintenance burden; 6 different patterns to debug and evolve
- **Decision:** Rejected — consistency and maintainability outweigh domain optimization

### Alt 2: Hybrid Approach (PM Real, Others Stub-Only)

- **Pro:** Only PM would require Copilot SDK; others would use in-memory logic
- **Con:** Defeats purpose of having 6 loops; only 1 would do real work
- **Decision:** Rejected — all 6 loops should be equally capable

---

## Consequences

### Positive

- ✅ Uniform, testable architecture across all 6 loops
- ✅ Easy to add new loops following the same pattern
- ✅ Auditability of decisions (adapter_source field)
- ✅ Simple recovery semantics (read issue labels between runs)

### Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Pattern may not fit all 6 loop semantics | Comprehensive test coverage (170 tests passing) validates pattern for all loops |
| State persistence via labels may be limiting for future requirements | Label registry is extensible; new label types can be added as needed |
| Copilot SDK dependency for production runs | Explicit SDK requirement fails closed; no silent fallbacks. Stubs only available with --stub flag |
| Silent fallback to stub could hide real SDK issues | Fixed: adapter_factory now fails closed; errors are logged loudly. adapter_source field tracks adapter type in audit trail |

---

## Acceptance Criteria

- ✅ All 6 orchestrators implement LangGraph StateGraph pattern
- ✅ All 6 have TransitionTable as single source of truth for routing
- ✅ All 6 use label-based state persistence
- ✅ All 6 have circuit breaker wrapping compiled graph
- ✅ Audit trail (TransitionLogEntry) includes explicit adapter_source field
- ✅ Test suite passes (170 tests, 3 skipped) validating all 6 loops
- ✅ Alignment test validates routing-registry.md against all 6 Python transition tables

---

## References

- `aios_orchestration_core/core/transition_table.py` — TransitionTable[S, E] pattern
- `aios_orchestration_core/llm/adapter_factory.py` — Adapter initialization (fail-closed)
- `aios_orchestration_core/runlog/models.py` — TransitionLogEntry with adapter_source field
- `templates-old-v2/orchestration/routing-registry.md` — Declarative routing rules (all 6 loops)
- `tests/registry/test_routing_registry_alignment.py` — Registry alignment validation

---

## Follow-Up ADRs

Future decisions may include:
- ADR 0002: Real GitHub integration for PO, Dev, Foundation, Discovery, ArchReview loops
- ADR 0003: Live Copilot SDK integration testing in CI/CD
- ADR 0004: Performance optimization strategies for high-volume runs
