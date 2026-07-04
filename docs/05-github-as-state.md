# 03 - Using GitHub as State and Memory (Operational Model)

This file explains how GitHub becomes your AIOS control plane, not just your code host.

If you apply this model correctly, your AIOS can be inspected, audited, and resumed by anyone on the team.

## How this builds on previous modules

In 02 you defined architecture roles and transitions.

In this file you bind that architecture to durable state in GitHub so it can run repeatedly without relying on chat memory.

## Apply this immediately

While reading, keep one real issue open and map these fields on it:

- State
- Risk
- Owner Agent
- Next Gate

After each section, confirm your issue still reflects the canonical state rule.

## Checkpoint before continuing

You should be able to answer, without guessing:

- what is canonical state
- where each decision is logged
- what evidence is required before Done

## Customization starts here

This is the first step where project custom fields become required.

If your board does not yet have operational fields, configure them now.
Reuse equivalent existing fields when possible and create only missing ones.

Required operational fields:

- State (single select)
- Risk (single select)
- Next Gate (single select)
- Owner Agent (text)

For a click-by-click setup walkthrough, run docs/14-github-projects-click-by-click.md.

## Next step

Run 11 github-projects-click-by-click to implement this model in your board, then return to 04 and 14 for execution.

## 1) Why GitHub is a strong first state layer

An Agentic OS needs durable state, event history, approvals, and artifacts.

GitHub already has these primitives:

- durable entities: issues, projects, pull requests
- timeline events: comments, review actions, merges
- verification outputs: check runs and workflow logs
- governance points: approvals and branch protection

Because this infrastructure already exists, you can start with process quality instead of infrastructure engineering.

## 2) Canonical state rule

Your system needs exactly one source of truth for delivery state.

For this workshop:

- GitHub Project field State is canonical.

Labels and comments are useful, but not canonical.

If project state and labels disagree, project state wins and labels must be reconciled.

## 3) Required state schema

Minimum fields to operate reliably:

- State: Backlog, Ready, In Design, In Build, In Verification, In QA, Ready to Merge, Done, Blocked
- Priority: P0 to P3
- Risk: Low, Medium, High
- Owner Agent: current role responsible for progress
- Next Gate: immediate gate that must pass next

Why these five:

- State tells where work is
- Priority and Risk tell how to treat work
- Owner Agent tells who acts next
- Next Gate tells what must be proven before moving

## 4) Memory model mapping

Your AIOS memory is distributed across GitHub artifacts.

Requirement memory:

- issue body and linked requirements

Decision memory:

- issue Decision Log comments

Design memory:

- ESS and design documents

Implementation memory:

- commits and pull request conversation

Verification memory:

- CI logs and verification summaries

QA memory:

- QA report files and defect comments

Closure memory:

- final closure comment with evidence links

This memory model is practical because it is reviewable by humans and machines.

## 5) Event-driven state transitions

Once your manual process is stable, transitions should be triggered by events.

High-value events:

- issue marked ready
- pull request opened and linked to issue
- checks completed
- review approved
- pull request merged

Each event should produce one of three outcomes:

- transition applied
- transition blocked with reason
- no-op with explanation

Avoid silent behavior.

## 6) Transition ownership

Every transition must have a responsible owner.

Example ownership map:

- Backlog -> Ready: Intake Agent
- Ready -> In Design: Planning or Design Agent
- In Build -> In Verification: Build Agent
- In Verification -> In QA: Verification Agent
- In QA -> Ready to Merge: QA Agent
- Ready to Merge -> Done: Release and Closure with human approval

When ownership is unclear, items stall.

## 7) What to automate and what not to automate

Automate first:

- field and label transitions from deterministic events
- check result summaries
- evidence reminders

Keep human-required:

- medium and high risk design approvals
- policy exceptions
- high-risk merge and closure decisions

This split preserves velocity while protecting safety.

## 8) Data quality rules

If your state data quality drops, your AIOS becomes unreliable.

Enforce these rules:

1. State field always populated.
2. Owner Agent always populated for active states.
3. Next Gate always populated outside Done.
4. Decision Log updated on every gate decision.
5. Closure requires links to ESS, PR, verification, and QA evidence.

## 9) Common anti-patterns and fixes

Anti-pattern: state only in chat context.
Fix: persist state transitions in project fields and comments.

Anti-pattern: issue closed after merge without QA evidence.
Fix: closure check rejects missing QA link.

Anti-pattern: too many labels with no operational meaning.
Fix: keep labels lightweight and rely on state fields.

Anti-pattern: no blocker semantics.
Fix: use Blocked state with explicit reason and owner.

## 10) Practical implementation walkthrough

Run this sequence on one issue:

1. create issue from template
2. add to project with initial fields
3. run Intake skill and log decision
4. set State to Ready or Blocked based on output
5. create ESS and set Next Gate to Design Gate
6. continue through Build, Verification, QA, and closure with evidence links

If you can perform this sequence with complete artifact traceability, your GitHub state model is functioning.

## Exercise

Pick one real issue and complete this short audit:

1. What is current State
2. Who is current Owner Agent
3. What is Next Gate
4. What evidence is missing for next transition
5. Is a human approval required now

If you cannot answer all five from GitHub alone, your state model is incomplete.
