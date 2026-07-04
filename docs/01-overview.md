# 01 - Program Overview (How To Use This Workshop)

This file answers five questions before you begin:

1. What this program teaches
2. What an Agentic OS means in practice
3. Why this is different from prompt engineering alone
4. How to move through the training without getting lost
5. What "done" looks like at the end

If you read only one orientation file, read this one.

## How to use this file right now

Read this once, then move into execution.

If you have not completed setup yet, run docs/00-prerequisites-and-tooling.md first.

Choose one learner path:

- Understand first: go to 02-foundations.
- Build first: go to 16-zero-to-hero-live-workshop.
- Control model first: go to 03-reference-architecture, then 04-github-as-state.

## Quick checkpoint before moving on

You should be able to say, in one sentence each:

- what Agentic OS means in this workshop
- what your target state flow is
- what proof is required before closure

## What you are building

You are building an Agentic OS for software delivery.

In plain language, this means a repeatable system that can take a work item from idea to closure with controls and evidence.

Your target run looks like this:

Backlog -> Ready -> In Design -> In Build -> In Verification -> In QA -> Ready to Merge -> Done

Each state transition requires an owner, a gate decision, and evidence.

## What Agentic OS means here

An Agentic OS is not a model. It is an operating model.

It combines:

- role-specialized agents
- explicit workflow control
- shared state and memory
- quality gates
- retry and escalation loops
- human approvals at policy boundaries

You can think of it like DevOps for AI-assisted delivery.

Without this operating model, AI helps you produce output.
With this operating model, AI helps you produce reliable outcomes.

## Why this is not just "one great prompt"

One excellent prompt can produce surprisingly good code.

The problem is reliability under repetition.

When you run 20 work items, prompt-only systems drift:

- scope drift
- skipped checks
- inconsistent documentation
- weak rollback planning
- hard-to-audit decisions

This workshop solves that by making process explicit and testable.

## What your final system will do

By completion, your AIOS will support this flow:

1. Intake: validates issue completeness
2. Design: produces ESS and risk-aware approach
3. Build: implements within approved scope
4. Verification: runs .NET build/test/lint checks
5. QA: validates acceptance and regression scenarios
6. Release: prepares PR with evidence and rollback notes
7. Closure: closes issue with complete audit links

## How the curriculum is structured

The material is intentionally split into three layers so you can learn and execute in parallel.

Layer A: Concepts and architecture

- 02 foundations
- 15 industry synthesis
- 03 reference architecture

Layer B: Operational setup

- 13 GitHub Projects setup
- 12 .NET command pack
- 04 GitHub as state and memory

Layer C: Live execution

- 16 zero-to-hero workshop
- 17 copy-paste exercise pack
- 18 answer keys
- 19 capstone rubric

Use Layer C while you are doing real work. Use Layers A and B to understand why each step exists.

## Program principles

These principles are non-negotiable in this workshop:

- Reliability over novelty
- Evidence over opinion
- Deterministic workflow where possible
- Explicit escalation when uncertain
- Human approvals at risk boundaries

If you are unsure what to do, return to these five principles.

## Maturity model you will pass through

Stage 1: Manual orchestrator

- You run the flow with checklists and skills.
- Goal is process correctness.

Stage 2: Assisted orchestration

- GitHub Actions automate transitions and summaries.
- Goal is consistency and reduced manual overhead.

Stage 3: Selective autonomy

- Agent behaviors are automated under policy.
- Goal is speed without losing control.

Important: You are not trying to skip to Stage 3 quickly. You are trying to reach Stage 3 safely.

## What you will produce

By design, this workshop leaves artifacts, not just understanding.

You will produce:

- skills and agent contracts
- ESS and QA artifacts
- gate and policy documents
- GitHub workflow automation
- closure evidence for real issues
- capstone run metrics

These artifacts are your operational knowledge base.

## Completion criteria

You complete this program when all are true:

1. You can run two consecutive real issues end-to-end.
2. No gate is skipped in either run.
3. Every closure includes ESS, PR, verification, and QA links.
4. Retry and escalation policy is honored.
5. Your capstone score meets the rubric threshold.

## How to start right now

1. Read 02 foundations carefully once.
2. Run Day 1 and Day 2 in 16 zero-to-hero workshop.
3. Use 17 copy-paste pack during execution.
4. Validate with 18 answer keys.
5. Score with 19 rubric after your first full issue.

If you do this sequence exactly, you will have real traction within your first two sessions.

## Next step

Open 02 foundations and complete the first two labs before attempting full live execution.
