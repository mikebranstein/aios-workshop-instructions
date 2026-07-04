# 04 - Using GitHub as State and Memory (Hands-On)

This module makes GitHub your visible system of record.

## Before You Start

Complete docs/03-reference-architecture.md first.

## How to run this module

Keep one real issue open while you work.

For each section:

1. Read context.
2. Perform the build task.
3. Pass checkpoint.

## Module 1 - Set canonical state fields

Context:
One source of truth is required for predictable delivery.

Build task:

1. In your project board, verify or create these fields:
	- State
	- Risk
	- Next Gate
	- Owner Agent
2. Reuse equivalent existing fields before creating new ones.
3. Mark State as the canonical state field for workflow tracking.

Checkpoint:

- One issue shows all four fields populated.

## Module 2 - Add state value definitions

Context:
State names are useful only when team meaning is consistent.

Build task:

1. In docs/state-machine.md, confirm state list:
	- Backlog, Ready, In Design, In Build, In Verification, In QA, Ready to Merge, Done, Blocked
2. Add one-line definition for each state.

Checkpoint:

- Team members can read definitions and classify one issue the same way.

## Module 3 - Define decision log location

Context:
Decisions must be findable after the work is done.

Build task:

1. Decide one standard location for gate decisions.
2. Add the rule to docs/evidence-convention.md.
3. Add one decision comment to your active issue.

Checkpoint:

- You can find the latest decision in under 30 seconds.

## Module 4 - Run one event-to-state update

Context:
State should update from real delivery events.

Build task:

1. Open or update a pull request linked to your issue.
2. Update project State and Next Gate based on that event.
3. Add a short comment explaining why the transition was valid.

Checkpoint:

- Issue timeline and project fields tell the same story.

## Module 5 - Perform a data quality audit

Context:
Bad state data breaks reporting and automation.

Build task:

For one active issue, verify all are true:

1. State is populated.
2. Owner Agent is populated for active state.
3. Next Gate is populated unless State is Done.
4. At least one gate decision comment exists.
5. Evidence links are present before closure.

Checkpoint:

- All five checks pass.

## Common anti-patterns and fixes

Anti-pattern: state only in chat.
Fix: use project fields and issue timeline.

Anti-pattern: issue closed without evidence links.
Fix: require ESS, PR, verification, and QA links before Done.

Anti-pattern: too many labels used as state.
Fix: keep labels lightweight and use canonical project fields.

## Next step

Continue to docs/05-training-regimen.md.
