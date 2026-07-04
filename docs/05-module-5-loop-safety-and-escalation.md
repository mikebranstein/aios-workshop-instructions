# Module 05 - Loop Safety and Escalation

## Concept: what a loop is

In this workshop, a loop is a repeated decision cycle around the same work item.

Simple example:
1. Run a gate check.
2. If it fails, apply a fix.
3. Run the same gate check again.

That retry pattern is a loop.

Loops are normal in delivery work. They become risky only when they are unbounded, unclear, or ownerless.

In frontier agentic systems, loops are not accidental. They are the core control pattern.

Common pattern:
1. Plan: propose next action.
2. Act: execute tool calls or code changes.
3. Verify: run checks and compare results against objective criteria.
4. Decide: continue, retry, escalate, or stop.

This plan-act-verify-decide cycle is how advanced agents stay productive under uncertainty without drifting.

## How this applies to GitHub Copilot workflows

When working manually with prompt-by-prompt control, people often do this:
- ask Copilot for a change
- run one command
- hit a failure
- ask a new prompt with partial context
- repeat without a clear retry boundary

That style is flexible, but inefficient at scale. It creates context loss, duplicated retries, and inconsistent decisions about when to stop.

Loop-based workflow is different:
- same issue, same objective, same evidence contract
- explicit retry count
- explicit blocked transition
- explicit escalation owner and SLA

This transforms Copilot from "helpful autocomplete plus ad hoc prompts" into a controlled delivery engine where failures are expected and managed.

## Concept: what loop safety is

Loop safety means retry behavior is bounded, observable, and recoverable.

In an agentic workflow, failures happen. The risk is not one failure. The risk is repeating the same failed step without a stop rule.

A safe loop has three parts:
- retry limit (how many attempts are allowed)
- blocked transition rule (when work must stop)
- escalation path (who is notified, by when, and what evidence is required)

Weak rule (subjective):
"Retry until it works."

Strong rule (objective):
"If the same gate fails 3 times, move to Blocked and post escalation comment with owner, SLA, and failure evidence."

## Why this matters

Bounded retries protect delivery time, quality, and team focus.

Without loop safety, teams lose time on repeated retries and unclear ownership. With loop safety, recovery is predictable and auditable.

In practical terms:
- manual prompting optimizes for local progress per prompt
- loop safety optimizes for end-to-end throughput and reliability

## What you should learn in this module

By the end of this module, you should be able to:
- define retry and blocked rules that are objective
- define escalation ownership and SLA without ambiguity
- run one failed-gate simulation and produce a complete escalation trail

## How this applies to prior modules

Module 4 gave you objective gate contracts.

This module adds failure handling for those same gates on the same issue. You are not creating new work items. You are defining what happens when gate checks fail repeatedly.

The practical sequence is:
- Module 2: define feature intent
- Module 3: define implementation spec (ESS)
- Module 4: define gate pass/fail rules
- Module 5: define what to do when a gate keeps failing

## Goal

Define loop safety and escalation rules for your current issue so repeated gate failures move to a clear, evidence-backed recovery path.

## Module rules for this exercise

- Do not create a new feature issue in this module.
- Continue using the same issue from Modules 2, 3, and 4.
- Do not create or update files in this module.
- Track all state in comments on the same GitHub issue.
- In writing steps, define the structure manually first; use Copilot prompts as fallback.
- Steps 3 and 4 are verification-only (no refinement prompts).

## Time Box

Target: 65 minutes

Suggested pacing:
- 10 min: confirm issue context and set safety objective
- 20 min: draft full loop safety policy comment
- 10 min: validate retry and blocked rules
- 15 min: validate escalation owner/SLA/evidence rules
- 10 min: run one failed-gate simulation and post escalation decision note

## What you will build

- one `Loop Safety Policy` comment on the existing feature issue
- one `Escalation Decision Note` comment from a failed-gate simulation
- one clear blocked-to-recovery decision trail on the same issue

## Required tasks

1. Define retry limits and blocked transition rules.
2. Define escalation owner, backup owner, and SLA.
3. Simulate one failed gate path and apply the escalation rules.
4. Post escalation decision evidence in the issue.

## Stretch tasks

- Add one alternate escalation path when primary owner is unavailable.

## Build exercise (step-by-step)

### Step 1 (10 minutes): confirm context and set safety objective

Use the same feature issue from Modules 2 through 4.

Before continuing, confirm:
- `Gate Contracts` comment exists
- `Gate Handoff Note` comment exists
- issue status on the delivery board is `In Progress`

Write one loop safety objective sentence in this format:
- "Define bounded retry and escalation rules so repeated gate failures move to Blocked with clear ownership and SLA."

Then post a comment on the same issue titled `Loop Safety Objective Check` with:
- Objective
- Decision (Go | No-Go)
- Reason (one line)

If you want Copilot to draft this objective check comment, use this prompt:

```text
Create a markdown issue comment titled "Loop Safety Objective Check".

Requirements:
- Include one objective sentence for loop safety rule creation.
- Include decision: Go | No-Go.
- Include one-line reason.

Output format:
- Return markdown only (copy/paste ready).
- Use exactly these sections:
	- Objective
	- Decision
	- Reason

Current issue context:
<paste issue title + short summary here>
```

### Step 2 (20 minutes): draft the full loop safety policy

Create one new comment on the existing issue.

Comment title:
`Loop Safety Policy`

Write the policy yourself first using this required structure:

```markdown
## Retry Limits

## Blocked Transition Rule

## Escalation Trigger

## Escalation Owner and Backup

## Escalation SLA

## Required Evidence

## Recovery Actions
```

When writing these sections, enforce these rules:
- Retry Limits: set max retries to 3 attempts per gate.
- Blocked Transition Rule: on the third failure of the same gate, transition to Blocked.
- Escalation Trigger: define exactly when escalation begins.
- Escalation Owner and Backup: include named role ownership (primary + backup).
- Escalation SLA: include a measurable response window.
- Required Evidence: list the links/proof required before escalation is considered complete.
- Recovery Actions: list concrete next actions (not vague statements).

After writing your draft, post it as a new comment on the same issue.

If you want Copilot to generate the first draft as a fallback, use this single prompt:

```text
Generate a complete markdown issue comment titled "Loop Safety Policy".

Context:
- App: Team Equipment Checkout Tracker
- Stack: .NET 10 classic ASP.NET Core MVC + xUnit
- Workflow states: To Do, In Progress, Done, Blocked
- Existing gate framework already defined in issue comments

Requirements:
- Include exactly these sections:
	- Retry Limits
	- Blocked Transition Rule
	- Escalation Trigger
	- Escalation Owner and Backup
	- Escalation SLA
	- Required Evidence
	- Recovery Actions
- Set retry limit to: 3 attempts per gate.
- Define blocked transition on third failure of the same gate.
- Define escalation trigger in explicit terms (exact condition, not vague wording).
- In Escalation Owner and Backup, include named role ownership for both primary and backup.
- In Escalation SLA, include a measurable response window (for example, within 4 business hours).
- In Required Evidence, list the specific links/proof required before escalation is complete.
- In Recovery Actions, list concrete next steps (no vague statements like "follow up as needed").
- Keep rules objective and evidence-based.
- Keep language concise and testable.
- Do not add sections beyond the required section list.

Output format:
- Return markdown only (copy/paste ready).
- Return only the final issue comment body.
- Do not include explanation outside markdown.
```

Use Copilot output as a starter, then quickly verify it matches the required structure and rules above before posting.

### Step 3 (10 minutes): validate retry and blocked rules

Verify the `Loop Safety Policy` comment for retry/blocked quality:

- retry limit is explicitly `3`
- blocked transition is explicitly triggered on third fail
- blocked condition is tied to "same gate" (not vague failures)
- rules are objective and observable

If a check fails, edit the same issue comment and fix it.

### Step 4 (15 minutes): validate escalation ownership and SLA

Verify the `Loop Safety Policy` comment for escalation quality:

- escalation owner is explicit
- backup owner is explicit
- SLA has concrete time boundary (for example, within 4 business hours)
- required evidence is listed and linkable
- recovery actions are concrete and executable

If a check fails, edit the same issue comment and fix it.

### Step 5 (10 minutes): run one failed-gate simulation and post decision note

Simulate one failed gate path on the current issue (example: Verification gate fails 3 times).

Then post this comment:

```markdown
## Escalation Decision Note
- Failed gate: Verification
- Attempt count: 3
- Transition to Blocked: Yes
- Escalation owner notified: Yes
- Backup owner notified (if needed): No
- SLA timer started: Yes
- Evidence links attached: Yes
- Recovery action selected: Assign blocker remediation to primary owner, fix root cause, and rerun Verification gate.
```

If you want Copilot to generate this comment, use this prompt:

```text
Generate a markdown issue comment titled "Escalation Decision Note".

Requirements:
- Use exactly these fields:
	- Failed gate
	- Attempt count
	- Transition to Blocked
	- Escalation owner notified
	- Backup owner notified (if needed)
	- SLA timer started
	- Evidence links attached
	- Recovery action selected
- Populate with these exact values for this failed simulation:
	- Failed gate: Verification
	- Attempt count: 3
	- Transition to Blocked: Yes
	- Escalation owner notified: Yes
	- Backup owner notified (if needed): No
	- SLA timer started: Yes
	- Evidence links attached: Yes
	- Recovery action selected: Assign blocker remediation to primary owner, fix root cause, and rerun Verification gate.
- Use these values exactly as written for this exercise.

Output format:
- Return markdown only (copy/paste ready).
- Do not include explanation outside the comment.
```

Keep issue status as `In Progress` or move to `Blocked` based on your defined policy and simulation outcome.

## Micro checks

By minute 20 you should see loop safety objective confirmed and policy structure ready.
By minute 35 you should see full `Loop Safety Policy` comment drafted.
By minute 50 you should see validation fixes applied.
By minute 65 you should see `Escalation Decision Note` posted.

## You should see

One documented blocked-state path that can be executed without ambiguity.

## If this fails, do this

If escalation ownership is unclear, assign explicit primary and backup owners.
If SLA is vague, replace it with a measurable time boundary.
If blocked transition is ambiguous, tie it directly to retry count on the same gate.

## Definition of done

Module 5 is complete when all are true:

- `Loop Safety Policy` comment exists on the existing issue
- retry limit and blocked transition rules are explicit and objective
- escalation owner, backup owner, and SLA are explicit
- failed-gate simulation is completed on one case
- `Escalation Decision Note` is posted in the issue
- module scorecard is posted

## Module scorecard template

```markdown
## Module Scorecard
- Module: 05
- Completion time (minutes):
- Retry count by gate:
- Primary blocker cause:
- Evidence completeness (0-100%):
- Outcome: PASS | FAIL
```

## Next module

Continue to [06-module-6-first-intake-skill-contract.md](06-module-6-first-intake-skill-contract.md).