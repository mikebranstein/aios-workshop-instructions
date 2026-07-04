# Module 03 - First Executable System Spec (ESS)

## Goal

Convert one valid issue into an implementation-ready execution spec.

## Time Box

Target: 75 minutes

Suggested pacing:
- 10 min: understand what makes an ESS usable
- 20 min: create ESS file and fill metadata/scope
- 20 min: write binary acceptance criteria and verification plan
- 15 min: write rollback and risk handling
- 10 min: peer review, revisions, and scorecard

## Why this matters

A strong ESS aligns design, build, verification, and QA with less ambiguity.

If this document is weak, build work drifts and QA becomes guesswork. If it is clear, every later module runs faster.

This module teaches you to write an ESS that another engineer can execute without a clarification call.

## What you will build

- one ESS file for the issue created in Module 2
- one short peer-review note with changes applied
- one clear implementation handoff note for the delivery board workflow

## Required tasks

1. Create one ESS from template.
2. Define scope, non-goals, ACs, verification commands, rollback.
3. Run a 10-minute peer review and finalize the ESS for implementation.

## Stretch tasks

- Add a risk matrix with mitigation mapping.

## Build exercise (step-by-step)

### Step 1 (10 minutes): choose the issue and set ESS objective

Use the issue you created in Module 2.

Before continuing, confirm the issue has the Module 2 `Intake Quality Check` comment and that `ready for ESS` is marked `yes`.

Before writing anything, state the ESS objective in one sentence:
what change will be delivered, for whom, and what success looks like.

If you cannot express this in one sentence, your issue is still too broad and should be split.

### Step 2 (20 minutes): create the ESS file and fill structure

Create the ESS file:

1. Copy `templates/ess-feature.md` to `docs/ess-issue-001.md`.
2. Fill metadata, problem statement, scope, and non-goals.
3. Keep non-goals explicit. This is what prevents scope creep later.

If you want Copilot to generate a first ESS draft, use this prompt:

```text
Generate a first draft of an ESS in markdown for this feature issue.

Context:
- App: Team Equipment Checkout Tracker
- Stack: .NET 10 classic ASP.NET Core MVC + xUnit
- Workflow states: To Do, In Progress, Done

Requirements:
- Keep scope small and implementation-ready.
- Keep non-goals explicit.
- Keep language concrete and testable.

Output format:
- Return markdown only (copy/paste ready).
- Follow the structure of templates/ess-feature.md.
- Do not include explanation outside the ESS content.

Feature issue markdown:
<paste finalized Module 2 issue markdown here>
```

By the end of this step, a reviewer should understand exactly what is included and what is not.

### Step 3 (20 minutes): write binary acceptance criteria and verification

Now fill acceptance criteria and verification plan.

Use binary statements. Avoid vague phrases like "improves", "better", or "handles appropriately".

Better examples:
- PASS: empty email shows validation message and blocks submit
- PASS: valid email allows submit
- FAIL: submit succeeds with empty email

Then add verification commands that can be run exactly as written.

If you want Copilot to tighten AC and verification quality, use this prompt:

```text
Rewrite the Acceptance Criteria and Verification sections of this ESS.

Requirements:
- Acceptance criteria must be explicit PASS/FAIL and observable.
- Include at least one failure-path criterion.
- Verification commands must be copy/paste-ready for this stack:
	- dotnet restore
	- dotnet build --configuration Release
	- dotnet test --configuration Release
- Keep scope unchanged.

Output format:
- Return markdown only (copy/paste ready).
- Return only these two sections:
	- Acceptance Criteria
	- Verification

ESS draft content:
<paste current ESS draft here>
```

### Step 4 (15 minutes): write risk and rollback sections

Add likely risks and one mitigation for each.

Then write rollback in concrete terms:
- what change is reverted
- how to verify rollback worked
- where rollback evidence is logged

If rollback says only "revert commit", it is incomplete. Include how to confirm system behavior after rollback.

### Step 5 (10 minutes): peer review and revision pass

Run a short peer review with this checklist:
- Is scope clear?
- Are non-goals explicit?
- Are ACs binary and testable?
- Can verification be run without interpretation?
- Is rollback actionable?

Capture comments and revise the ESS before marking the ESS complete for this module.

Add this short comment to the issue when ESS revision is complete:

```markdown
## ESS Handoff Note
- ESS file: docs/ess-issue-001.md
- Scope and non-goals verified: Yes | No
- ACs binary and testable: Yes | No
- Verification commands copy/paste-ready: Yes | No
- Rollback concrete and verifiable: Yes | No
- Ready to move issue to In Progress: Yes | No
```

If all checks are `Yes`, move the issue status on the delivery board from `To Do` to `In Progress`.

## Micro checks

By minute 25 you should see scope and non-goals complete.
By minute 45 you should see binary acceptance criteria drafted.
By minute 65 you should see peer review comments applied.

## You should see

An ESS that another engineer can implement without a live clarification call.

## If this fails, do this

If the ESS feels vague, cut scope and rewrite ACs as pass/fail behaviors.
If reviewer asks many clarifying questions, add those clarifications directly into ESS sections.
If verification commands are unclear, rewrite them so a teammate can copy/paste without guessing.

## Definition of done

Module 3 is complete when all are true:

- ESS file exists at `docs/ess-issue-001.md`
- acceptance criteria are binary and testable
- verification commands are explicit
- rollback steps are concrete and verifiable
- peer review comments are resolved
- ESS handoff note is posted in the issue
- module scorecard is posted

## Module scorecard template

```markdown
## Module Scorecard
- Module: 03
- Completion time (minutes):
- Retry count by gate:
- Primary blocker cause:
- Evidence completeness (0-100%):
- Outcome: PASS | FAIL
```

## Next module

Continue to [04-module-4-objective-gates.md](04-module-4-objective-gates.md).