# 02 - Foundations Workshop (From Zero to Operational)

This is the foundation module rewritten as a real workshop.

## Before You Start

In 00 you learned the operating model and success criteria.

In this file you turn those ideas into concrete habits through short labs.

## While You Read

Complete each lab before reading the next part so learning stays tied to real repo changes.

Read this file top-to-bottom once, then run the labs exactly in order.

For fully scripted live execution with copy-paste text and answer keys, immediately continue with:

- docs/16-zero-to-hero-live-workshop.md
- docs/17-copy-paste-exercise-pack.md
- docs/18-live-lab-answer-keys.md

If a step says create a file, create it.
If a step says run a command, run it.
If a step has an output check, do not continue until it passes.

## Checkpoint before you leave this file

You should have:

- one issue with state fields set
- one workflow-vs-agent note in your repo
- one tested intake skill contract with confidence rule

If any item is missing, complete labs before moving on.

## Next step

Continue to docs/03-reference-architecture.md.

---

## Part 1 - What Agentic OS Actually Means

### Plain-English definition

An Agentic OS is an operating model for AI-assisted work.

It is not a single model prompt.
It is a repeatable system with:

- specialized roles (agents)
- a workflow (orchestration)
- a shared state/memory model
- quality gates
- retry loops
- human approvals at risk boundaries

For your goal, your Agentic OS is the delivery engine that takes a GitHub work item and runs it through:

Intake -> Design -> Build -> Verify -> QA -> PR -> Close.

### Why this matters

Without an OS model, you get one-off outputs.
With an OS model, you get repeatable outcomes.

Repeatability is the whole point.

---

## Part 2 - Industry Baseline (What Frontier Teams Converge On)

This section ties together what major sources are saying.

### 1) Start simple, add complexity only when needed

Common message across Anthropic and Microsoft guidance:

- Do not jump to multi-agent first.
- Start with single agent + tools.
- Add multi-agent only when specialization is clearly useful.

Practical implication for you:

- Week 1-2: single flow with strict gates
- Week 3+: add specialists where quality or speed improves measurably

### 2) Workflow vs Agent (critical distinction)

Anthropic-style distinction:

- Workflow: predefined code path (predictable)
- Agent: model decides steps/tools dynamically (flexible)

Practical implication:

- Use workflows for deterministic delivery stages.
- Use agent autonomy inside stages where exploration is needed.

Example:

- Deterministic: do not skip Design Gate.
- Agentic: Build Agent chooses exact files to edit.

### 3) Orchestration patterns are not interchangeable

Microsoft architecture guidance describes major patterns:

- Sequential: fixed pipeline
- Concurrent: parallel specialists
- Handoff: dynamic transfer between specialists
- Group chat: collaborative debate / maker-checker
- Magentic: manager builds and adapts a task ledger dynamically

Practical implication:

- For coding delivery, your default should be Sequential + maker-checker loops.
- Add Concurrent only for independent tasks (for example, security review and docs review in parallel).
- Use Magentic pattern only when task path is unknown upfront.

### 4) Loops need caps, or they become chaos

Across sources, loop guidance is consistent:

- loops improve quality
- uncapped loops waste time and money

Your rule (adopt now):

- max retries per gate = 3
- after 3 failures -> Blocked + escalate to human

Retry definition:

- one retry = one full gate attempt
- verification gate attempt means run full restore/build/test/format sequence once
- retry count resets only when root cause class changes

Detailed policy lives in docs/state-machine.md.

### 5) State must be external and durable

Industry guidance emphasizes durable state for long-running workflows.

Your implementation:

- GitHub Project fields = state
- issue comments = decision log
- PR checks = verification truth
- ESS + QA report = execution evidence

If state only exists in chat, it is not operational state.

### 6) Skills and tools must be explicit

Modern agent stacks separate:

- Skills: reusable behavior modules (instructions/contracts)
- Tools: external actions (filesystem, APIs, shells)

Practical implication:

- skills define how an agent thinks and reports
- tools define what an agent can do

Your AIOS needs both, with least privilege.

---

## Part 3 - Your Target Architecture (for this training)

You are building a coding Agentic OS with this control model:

1. GitHub Issue starts work
2. Intake skill validates completeness
3. ESS is created and approved
4. Build runs in feature branch
5. Verification gate enforces build/test/lint
6. QA gate validates scenarios
7. PR merges with required approvals
8. Closure posts evidence and marks Done

This is a controlled, auditable pipeline.

Not "vibe coding."

---

## Part 4 - Foundation Labs (Do These Now)

Each lab takes 15-30 minutes.

## Lab 0 - Confirm the operating surface

Goal: verify your system of record.

Do this:

1. Open docs/13-github-projects-click-by-click.md and complete Part A through Part D.
2. Ensure one issue exists in your project board.
3. Set fields on that item:
   - State = Backlog
   - Risk = Medium
   - Next Gate = Design Gate
   - Owner Agent = Intake

Output check:

- You can point to one issue card with all four fields set.

## Lab 1 - Understand workflow vs agent in your own repo

Goal: make the distinction concrete.

Create file docs/workflow-vs-agent.md with this exact template:

```markdown
# Workflow vs Agent (My Repo)

## Deterministic Workflow Steps
- Step 1:
- Step 2:
- Step 3:

## Agentic Decision Points
- Decision 1:
- Decision 2:
- Decision 3:

## Guardrails
- Never skip:
- Always require human approval when:
```

Fill it using your current AIOS process.

Output check:

- At least 3 deterministic steps and 3 agentic decisions listed.

## Lab 2 - Build your first real skill contract

Goal: create one reusable skill with strict output.

1. Open templates/skills/intake-agent.md.
2. Confirm output schema is JSON-only.
3. Add one field to output schema: confidence (0.0 to 1.0).
4. Add guardrail: confidence < 0.7 cannot return READY.

Now test in Copilot chat with one real issue.

Prompt:

```text
Act as templates/skills/intake-agent.md exactly.
Input:
<PASTE ISSUE BODY>
Return JSON only.
```

Output check:

- You get valid JSON with decision, missing_fields, questions, next_state, summary, confidence.

## Lab 3 - Install loop safety

Goal: prevent infinite refinement loops.

1. Open docs/state-machine.md.
2. Add a section named Loop Safety Policy.
3. Add these rules:
   - Max retries per gate = 3
   - On third fail: move State to Blocked
   - Set Owner Agent = Human Review
   - Require postmortem document before retry

Output check:

- The policy is written and referenced in your process docs.

## Lab 4 - Add objective gate criteria

Goal: remove ambiguity from pass/fail.

1. Open docs/gates.md.
2. For each gate, add at least 3 pass criteria that are objective.
3. For Verification Gate, include .NET command set from docs/12-dotnet-command-pack.md.

Output check:

- A reviewer can determine pass/fail without asking follow-up questions.

## Lab 5 - Create your first ESS from scratch

Goal: produce executable planning artifact.

1. Copy templates/ess-feature.md to docs/ess-foundations-lab.md.
2. Fill sections 1-7 completely.
3. Ensure every acceptance criterion is binary.
4. Ensure rollback section is realistic.

Output check:

- Another engineer could implement from ESS without a live meeting.

---

## Part 5 - What "Magentic" Means and Where It Fits

You mentioned "magenta OS." In current architecture language, you likely mean Magentic orchestration.

Magentic pattern (per Microsoft architecture language):

- a manager agent dynamically builds and updates a task ledger
- delegates to specialists
- checks progress in loops
- adapts plan as new evidence appears

When to use:

- open-ended tasks where step order is unknown

When not to use:

- deterministic delivery flows like normal feature implementation

For your AIOS now:

- Do not start with full Magentic.
- Start with deterministic delivery pipeline + evaluator loops.
- Introduce Magentic manager later for large refactors or incident-like tasks.

---

## Part 6 - Common Beginner Mistakes (and exact fixes)

Mistake: adding too many agents too soon.
Fix: begin with Intake, Design, Build, Verification.

Mistake: prose outputs with no schema.
Fix: force JSON outputs for gate decisions.

Mistake: no durable state.
Fix: GitHub Project fields are mandatory state.

Mistake: no stop conditions.
Fix: retry caps + escalation.

Mistake: closing issues without evidence.
Fix: closure template with ESS/PR/Verification/QA links.

---

## Part 7 - Definition of Foundation Complete

You are done with Foundations only when all are true:

1. You can explain workflow vs agent in your own words.
2. You can explain why your default pattern is sequential with loops.
3. You have one active issue with project state fields populated.
4. You have one tested Intake skill returning strict JSON.
5. You have loop safety and objective gates documented.
6. You created one full ESS draft.

If any item is false, Foundations is not complete.

---

## Sources Used For This Foundations Rewrite

- Anthropic Engineering: Building effective agents
  - https://www.anthropic.com/engineering/building-effective-agents
- Microsoft Azure Architecture Center: AI Agent Orchestration Patterns
  - https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns
- GitHub Copilot docs (agents, skills, automations, memory, hooks)
  - https://docs.github.com/en/copilot
- OpenAI: New tools for building agents + Agents SDK docs
  - https://openai.com/index/new-tools-for-building-agents/
  - https://developers.openai.com/api/docs/guides/agents

Use these as concept references. Your implementation remains Copilot-first in this repo.
