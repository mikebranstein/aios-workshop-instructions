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

Follow the workshop in strict order from docs/02-foundations.md through docs/24-style-audit-and-migration.md.

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

This curriculum is designed as one continuous sequence from docs/00-prerequisites-and-tooling.md to docs/24-style-audit-and-migration.md.

Read and execute in numeric order.

Earlier files establish foundations and controls.
Middle files turn those controls into repeatable operating behavior.
Later files run full execution, recovery, and evaluation loops.

## Program principles

These principles are non-negotiable in this workshop:

- Reliability over novelty
- Evidence over opinion
- Deterministic workflow where possible
- Explicit escalation when uncertain
- Human approvals at risk boundaries

If you are unsure what to do, return to these five principles.

## Progression model you will pass through

Step 1: Manual orchestration

- You run the flow with checklists and skills.
- Goal is process correctness.

Step 2: Assisted orchestration

- GitHub Actions automate transitions and summaries.
- Goal is consistency and reduced manual overhead.

Step 3: Selective autonomy

- Agent behaviors are automated under policy.
- Goal is speed without losing control.

Important: Do not skip ahead. Move to the next step only when current controls are stable.

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

1. Complete docs/02-foundations.md.
2. Continue sequentially through each numbered file in order.
3. Do not skip ahead. Finish each checkpoint before moving on.

## Next step

Continue to docs/02-foundations.md.

