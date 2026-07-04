# 03 - Reference Architecture (Hands-On Mapping)

This module turns architecture into practical, visible controls.

## Before You Start

Complete docs/02-foundations.md first.

## How to run this module

Use one real issue while you read.

For each section:

1. Read context.
2. Perform the build task.
3. Pass checkpoint.

## Module 1 - Draw your delivery path

Context:
Your architecture must be visible to your team.

Build task:

1. Create docs/architecture-map.md.
2. Add the workflow line:

Backlog -> Ready -> In Design -> In Build -> In Verification -> In QA -> Ready to Merge -> Done

3. Add exception paths:
	- Any active state -> Blocked
	- In Verification -> In Build on failed checks
	- In QA -> In Build on failed scenarios

Checkpoint:

- One person can read the file and explain normal flow and fallback flow.

## Module 2 - Define artifact requirements per state

Context:
State transitions are only trustworthy with required evidence.

Build task:

1. In docs/architecture-map.md, add an artifact table for each active state.
2. Minimum required artifacts:
	- In Design: ESS or design note
	- In Build: scoped commits and tests
	- In Verification: build and test evidence
	- In QA: QA report
	- Ready to Merge: PR summary and approvals
	- Done: closure summary with links

Checkpoint:

- Every active state has explicit exit evidence.

## Module 3 - Assign ownership

Context:
Unowned transitions create stalled work.

Build task:

1. In docs/architecture-map.md, add transition ownership lines.
2. Use a single owner per transition.
3. Add one escalation owner for Blocked.

Checkpoint:

- You can answer who moves each transition without ambiguity.

## Module 4 - Add human approval boundaries

Context:
Some transitions require human sign-off.

Build task:

1. Add a section named Approval Boundaries.
2. Define required human review for:
	- medium and high risk design approval
	- risk exception approval before merge
	- high risk closure approval

Checkpoint:

- Risk-sensitive transitions have explicit human review points.

## Module 5 - Run a quick architecture audit

Context:
Architecture is only useful if it works on real work.

Build task:

1. Take one active issue.
2. Record in issue comments:
	- current state
	- owner
	- next gate
	- missing artifact
	- approval needed now or not

Checkpoint:

- Issue comment proves architecture can be applied in under five minutes.

## Next step

Continue to docs/04-github-as-state.md.
