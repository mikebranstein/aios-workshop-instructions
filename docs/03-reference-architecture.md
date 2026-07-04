# 02 - Reference Architecture (Copilot-First, Explained)

This file explains the architecture decisions behind your workshop system.

It is not just a list of agents. It is the operating blueprint for a controllable, auditable coding pipeline.

## Before You Start

You have already established the big picture in 00 overview and core principles in 01 foundations.

Now you are turning those ideas into an explicit architecture you can run and audit.

## What to do while you read

Apply this while you read by mapping each architecture section to one concrete gate or artifact in your current issue.

As you read each section, write one short note in your issue or notebook:

- control this section adds
- failure this control prevents

Keep those notes. You will use them in 05 vertical slice and 14 live workshop.

## Checkpoint before continuing

Before moving on, you should be able to explain:

- why each agent exists
- why gates cannot be skipped
- what artifact is required at each state exit

## Next step

Continue to 03 github-as-state and map this architecture to concrete GitHub fields and artifacts.

## 1) System boundary

Your architecture intentionally uses tools you already have:

- VS Code and GitHub Copilot for agentic assistance
- GitHub Issues and Projects for work tracking and state
- GitHub Pull Requests for review and merge control
- GitHub Actions for repeatable machine checks and transitions

This boundary matters because it keeps complexity low and adoption high.

If a feature requires infrastructure outside this boundary, defer it unless it solves a clear bottleneck.

## 2) Architectural principle: small specialists, strong contracts

Each agent should do one main job well and hand off cleanly.

Do not create agents based on vague roles like "smart engineer".

Create agents based on transition responsibilities.

That is why this architecture uses role-specialized agents linked to state edges.

## 3) Recommended agent set and why each exists

1. Intake Agent

- Purpose: prevent garbage-in at the top of the pipeline
- Decision: READY or BLOCKED
- Failure mode prevented: starting work on incomplete requirements

2. Planning Agent

- Purpose: convert request into executable task structure
- Decision: plan completeness and dependency ordering
- Failure mode prevented: chaotic build sequence

3. Design Agent

- Purpose: produce solution strategy and risk treatment
- Decision: PASS, REVISE, or BLOCKED
- Failure mode prevented: coding before constraints are understood

4. Build Agent

- Purpose: implement approved scope and tests
- Decision: implementation complete or partial
- Failure mode prevented: uncontrolled code changes outside scope

5. Verification Agent

- Purpose: execute objective machine checks
- Decision: PASS or FAIL
- Failure mode prevented: subjective "looks good" quality checks

6. QA Agent

- Purpose: validate acceptance scenarios and regression impact
- Decision: PASS or FAIL with defects
- Failure mode prevented: shipping behavior regressions

7. Release Agent

- Purpose: compose risk-aware PR and merge readiness package
- Decision: merge readiness recommendation
- Failure mode prevented: low-context pull requests

8. Closure Agent

- Purpose: close work item only when evidence is complete
- Decision: DONE readiness
- Failure mode prevented: un-auditable issue closure

## 4) State machine and transition logic

Primary workflow:

Backlog -> Ready -> In Design -> In Build -> In Verification -> In QA -> Ready to Merge -> Done

Exception workflow:

- Any active state -> Blocked
- In Verification -> In Build on check failure
- In QA -> In Build on defect failure

Why this shape works:

- It enforces a predictable quality path.
- It allows controlled backtracking when quality fails.
- It makes progress measurable in GitHub Project fields.

## 5) Artifact contract per state

Each state requires a minimum artifact set before exit.

Ready

- complete issue statement
- explicit acceptance criteria

In Design

- ESS or design note
- risk and mitigation list

In Build

- scoped commits linked to issue
- tests added or updated for changed behavior

In Verification

- build, test, lint or format evidence
- failure triage summary when failing

In QA

- QA report and scenario outcomes
- defect list and severity if failing

Ready to Merge

- PR summary with rationale and rollback notes
- required approvals and checks satisfied

Done

- closure summary with links to ESS, PR, verification, QA

## 6) Control architecture: human at policy boundaries

The system is agent-assisted, not blindly autonomous.

Mandatory human gates:

- design approval for medium and high risk
- risk exception approvals before merge
- final closure review for high-risk work

This pattern keeps speed in low-risk flows while preserving safety in sensitive changes.

## 7) Deterministic flow plus adaptive internals

This architecture combines two modes:

- deterministic stage progression
- adaptive decision-making inside stages

Example:

- deterministic: cannot skip Verification before QA
- adaptive: Build Agent decides exact file-level changes needed to satisfy AC2

This is the practical middle ground between rigid pipelines and unconstrained autonomy.

## 8) Observability requirements

A production-worthy AIOS must be debuggable.

Minimum telemetry in this architecture:

- state transitions over time
- gate pass and fail counts
- retry counts per gate
- cycle time from Ready to Done
- manual intervention count

If these are not visible, optimization becomes guesswork.

## 9) What to automate first

Priority order for automation:

1. CI verification checks
2. state updates on PR lifecycle events
3. gate summary comments
4. policy checks for merge readiness

Automate in this order to maximize reliability gain with low implementation complexity.

## 10) Architecture quality checklist

Use this checklist before scaling to more agents.

- every agent has strict input and output contracts
- every state has explicit exit criteria
- every gate has objective pass and fail conditions
- every loop has retry cap and escalation behavior
- every closure has complete evidence links

If any item is false, do not add more autonomy yet.

## Practical exercise

Take one active issue and map it to this architecture explicitly:

1. current state
2. current owner agent
3. next gate
4. missing artifact before transition
5. required human approval, if any

When you can do this quickly, you are using the architecture correctly rather than only reading about it.
