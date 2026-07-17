---
description: LangGraph multi-agent pipeline guidelines — enforces explicit state-transition contracts, discrete input/output schemas for every LLM prompt, and loop-termination guarantees between create/verify state pairs.
applyTo: '**/*.py,**/*.md,**/agents/**,**/graph/**,**/prompts/**'
---

<!-- Tip: Use /create-instructions in chat to generate content with agent assistance -->

# Project Context

This repo implements a multi-agent product development pipeline built on LangGraph, using GitHub Issues as the persistent state store and GitHub Copilot as the coding agent. Orchestration loops include: Foundation, Discovery, PM, PO, Development, and Architecture Review. AI-generated or AI-reviewed code in this repo must follow the rules below.

# 1. State Transitions (LangGraph)

- Every node in the graph must have an explicit, named state it reads from and an explicit, named state it writes to. No node may mutate state fields it doesn't declare ownership of.
- Every edge (conditional or fixed) must be traceable to a specific field or predicate on the state object — never to implicit side effects, free-text parsing of prior LLM output, or "vibes" from message history.
- When adding or modifying a node, update the state schema (TypedDict/Pydantic model) in the same change. Do not let the schema and the graph drift apart.
- Every conditional edge function must have unit test coverage for each branch it can take, including the "stuck" branch (see §3).
- Document each node's entry/exit state in a docstring: `Reads: {...}`, `Writes: {...}`, `Transitions to: {...} when {...}`.

# 2. Discrete Input/Output Contracts for LLM Prompts

- Every prompt used in the pipeline must have a formal input schema and output schema (Pydantic model or JSON Schema), not a free-text blob in, free-text blob out.
- Prefer structured output (tool calling / forced JSON) over prompting the model to "return JSON" in prose. If the model provider doesn't support structured output for a given call, validate and parse defensively and fail closed (raise, don't guess) on schema mismatch.
- Input to a prompt must only include the fields declared in its input schema — no ad hoc dumping of the entire state object into context. This keeps prompts testable and keeps the graph's data flow auditable.
- Output from a prompt must be validated against its schema immediately after the LLM call, before it's written back to state. Invalid output routes to an explicit error/retry state — it must never silently pass through as if valid.
- Version prompts alongside their schemas (e.g. `prompts/pm_review_v2.py` + `schemas/pm_review_v2.py`). Changing a schema without bumping the prompt version (or vice versa) should be flagged in review.

# 3. Loop Prevention Between Create/Verify State Pairs

Any pair of states where one produces an artifact (create) and another judges it (verify — e.g. PM↔PO, Development↔Architecture Review) must satisfy all of the following:

- **Bounded retries**: a hard `max_iterations` counter (stored in state, not in a closure) that increments on every create→verify→create cycle. On exceeding the limit, the graph must transition to an explicit `escalation` or `human_review` state — never silently exit or silently keep looping.
- **Convergence signal**: the verify state must emit a structured pass/fail/needs-revision verdict (part of its output schema per §2), plus a diff or delta of what changed since the last iteration. If two consecutive iterations produce no meaningful delta, that's an automatic escalation, since the loop isn't converging.
- **No mutual recursion without a monotonic counter in state.** If create and verify are separate nodes with a conditional edge between them, that edge's predicate function must read the iteration counter from state and enforce the bound — don't rely on the LLM "deciding" when to stop.
- **Idempotent verify**: verify should not have side effects on retries other than updating the state/GitHub Issue with its verdict and iteration count, so re-running it after a timeout or crash doesn't corrupt state.
- **Every create/verify pair must be listed in a central registry** (e.g. `graph/loop_registry.py`) noting: node names, max_iterations, escalation target. New create/verify pairs must be added here before merge — grep for this file when reviewing any new loop.

# 4. Review Checklist for AI-Assisted Changes

Before approving AI-generated changes to the graph or prompts, confirm:

- [ ] State schema updated to match new/changed node behavior
- [ ] New/changed prompts have explicit input and output schemas
- [ ] Output validation happens before state write, with an explicit failure path
- [ ] Any new create/verify pair has a bounded `max_iterations` and an escalation state
- [ ] Convergence/delta check exists for the verify state, not just a pass/fail flag
- [ ] Node docstrings document reads/writes/transitions
- [ ] GitHub Issue (state store) updates are idempotent and safe to replay