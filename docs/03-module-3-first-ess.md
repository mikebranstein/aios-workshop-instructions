# Module 03 - First Executable System Spec (ESS)

## Goal

Convert one valid issue into an implementation-ready execution spec.

Important:
You are not creating a new feature in Module 3. You continue using the same feature issue created in Module 2.

## What ESS means in this workshop

An ESS (Executable System Spec) is a practical build spec that makes coding easier and less ambiguous.

Use it as the "how we will implement this" document for one existing feature issue.

In this module, ESS must:
- follow the standard ESS template sections
- stay attached to the existing Module 2 feature issue for reference
- be clear enough that another engineer can implement without extra clarification

## Time Box

Target: 75 minutes

Suggested pacing:
- 10 min: understand what makes an ESS usable
- 30 min: draft full ESS comment (including AC, verification, risks, and rollback)
- 10 min: validate AC and verification quality
- 15 min: validate risk and rollback quality
- 10 min: peer review, revisions, and scorecard

## Why this matters

A strong ESS aligns design, build, verification, and QA with less ambiguity.

If this document is weak, build work drifts and QA becomes guesswork. If it is clear, every later module runs faster.

Think of ESS as the bridge from "feature request" to "code changes": the clearer the ESS, the easier implementation becomes.

This module teaches you to write an ESS that another engineer can execute without a clarification call.

## What you will build

- one ESS reference comment on that same feature issue
- one short peer-review note with changes applied
- one clear implementation handoff note for the delivery board workflow

No new feature issue is created in this module.

## Required tasks

1. Draft one ESS comment using the standard ESS template sections.
2. Define scope, non-goals, ACs, verification commands, rollback.
3. Add ESS as a reference comment on the existing feature issue.
4. Run a 10-minute peer review and finalize the ESS for implementation.

## Stretch tasks

- Add a risk matrix with mitigation mapping.

## Build exercise (step-by-step)

### Step 1 (10 minutes): choose the issue and set ESS objective

Use the issue you created in Module 2.

Do not create a new feature issue in this module.

Before continuing, confirm the issue has the Module 2 `Intake Quality Check` comment and that `ready for ESS` is marked `yes`.

Complete this step in order:

1. Open the Module 2 issue and re-read: Scope, Non-Goals, Acceptance Criteria, and Risk Level.
2. Confirm the issue is still small enough for one implementation cycle.
3. Write one ESS objective sentence in this format:
	- "Deliver <change> for <user> so that <measurable outcome>."
4. Post a short issue comment titled `ESS Objective Check` with:
	- selected issue link
	- ESS objective sentence
	- go/no-go decision for ESS drafting

If you want Copilot to generate a first draft of the objective and comment, use this prompt:

```text
Create a markdown issue comment titled "ESS Objective Check".

Context:
- App: Team Equipment Checkout Tracker
- Stack: .NET 10 classic ASP.NET Core MVC + xUnit

Requirements:
- Read the feature issue content and produce:
  1. One ESS objective sentence in this format:
	  "Deliver <change> for <user> so that <measurable outcome>."
  2. A Go/No-Go decision for starting ESS drafting.
  3. A one-line reason for that decision.
- If scope looks too broad, set decision to No-Go and state what to split.

Output format:
- Return markdown only (copy/paste ready).
- Use exactly these sections:
  - ESS Objective
  - Decision
  - Reason

Feature issue markdown:
<paste finalized Module 2 issue markdown here>
```

If you cannot express this in one sentence, your issue is still too broad and should be split.

### Step 2 (30 minutes): draft the full ESS comment in one pass

In the existing Module 2 feature issue, add one new comment for ESS draft.

1. Add one comment body structured as an ESS (no new issue, no separate ESS title needed).
2. Fill objective, problem statement, scope, and non-goals.
3. Fill Acceptance Criteria and Verification in the same draft.
4. Fill Risks and Rollback in the same draft.
5. Keep the section order as-is. Do not invent a custom ESS format.
6. Keep non-goals explicit. This is what prevents scope creep later.

For Acceptance Criteria, use explicit PASS/FAIL style and include at least one failure-path criterion.
For Risks and Rollback, be concrete and verifiable (not generic).

Use this comment format:

```markdown
### ESS Objective
<one-sentence objective>

### Problem Statement

### Scope

### Non-Goals

### Acceptance Criteria

### Verification

### ESS Snapshot
- Scope summary:
- Non-goals summary:
- Verification commands:
	- dotnet restore
	- dotnet build --configuration Release
	- dotnet test --configuration Release

### Risks

### Rollback
```

If you want Copilot to generate the full ESS issue comment in the correct format, use this single prompt:

```text
Generate a first draft of an ESS issue comment in markdown for this feature issue.

Context:
- App: Team Equipment Checkout Tracker
- Stack: .NET 10 classic ASP.NET Core MVC + xUnit
- Workflow states: To Do, In Progress, Done

Requirements:
- Keep scope small and implementation-ready.
- Keep non-goals explicit.
- Keep language concrete and testable.
- Include this exact section order and headings:
	- ### ESS Objective
	- ### Problem Statement
	- ### Scope
	- ### Non-Goals
	- ### Acceptance Criteria
	- ### Verification
	- ### ESS Snapshot
	- ### Risks
	- ### Rollback
- In ### Verification and ### ESS Snapshot, include these commands:
	- dotnet restore
	- dotnet build --configuration Release
	- dotnet test --configuration Release
- Use PASS/FAIL style for acceptance criteria and include at least one failure-path criterion.
- In ### Risks, include at least two likely risks and one mitigation for each.
- In ### Rollback, specify what is reverted, how rollback success is verified, and where evidence is logged.

Output format:
- Return markdown only (copy/paste ready).
- Return only the ESS comment body with the required headings in the exact order listed above.
- Do not include issue number, issue title, links, or any metadata outside the ESS sections.
- Do not include explanation outside the ESS content.

Feature issue markdown:
<paste finalized Module 2 issue markdown here>
```

By the end of this step, a reviewer should understand exactly what is included and what is not.

### Step 3 (10 minutes): validate AC and verification quality

Do a quick quality check of the ESS draft you generated in Step 2:

- acceptance criteria are explicit PASS/FAIL and observable
- at least one failure-path criterion exists
- verification commands are copy/paste-ready for this stack:
  - dotnet restore
  - dotnet build --configuration Release
  - dotnet test --configuration Release
- AC and verification still match scope and non-goals

If any check fails, edit the same ESS comment directly and fix it before moving to Step 4.

### Step 4 (15 minutes): validate risk and rollback quality

Do a quality check of the Risks and Rollback sections you already drafted in Step 2:

- each listed risk has one clear mitigation
- risks are specific to this feature change (not generic boilerplate)
- rollback states exactly what change is reverted
- rollback includes how to verify rollback worked
- rollback includes where rollback evidence is logged

If rollback says only "revert commit", it is incomplete. Edit the same ESS comment and add concrete verification details.

### Step 5 (10 minutes): peer review and revision pass

Run a short peer review with this checklist:
- Is scope clear?
- Are non-goals explicit?
- Are ACs binary and testable?
- Can verification be run without interpretation?
- Is rollback actionable?

Capture comments and revise the ESS before marking the ESS complete for this module.

After revision, update the same ESS issue comment so it reflects the final ESS content.

Add this short comment to the issue when ESS revision is complete:

```markdown
## ESS Handoff Note
- Scope and non-goals verified: Yes | No
- ACs binary and testable: Yes | No
- Verification commands copy/paste-ready: Yes | No
- Rollback concrete and verifiable: Yes | No
- Ready to move issue to In Progress: Yes | No
```

If you want Copilot to generate this handoff comment, use this prompt:

```text
Generate a markdown issue comment titled "ESS Handoff Note" from this ESS comment.

Requirements:
- Evaluate the ESS against these checks:
	- Scope and non-goals verified: Yes | No
	- ACs binary and testable: Yes | No
	- Verification commands copy/paste-ready: Yes | No
	- Rollback concrete and verifiable: Yes | No
	- Ready to move issue to In Progress: Yes | No
- Be strict; if a section is weak, mark it No.

Output format:
- Return markdown only (copy/paste ready).
- Do not include any explanation outside the comment.

Current ESS comment markdown:
<paste final ESS comment here>
```

If all checks are `Yes`, move the issue status on the delivery board from `To Do` to `In Progress`.

## Micro checks

By minute 25 you should see scope and non-goals complete.
By minute 45 you should see a full ESS draft comment posted.
By minute 65 you should see peer review comments applied.

## You should see

An ESS that another engineer can implement without a live clarification call.

## If this fails, do this

If the ESS feels vague, cut scope and rewrite ACs as pass/fail behaviors.
If reviewer asks many clarifying questions, add those clarifications directly into ESS sections.
If verification commands are unclear, rewrite them so a teammate can copy/paste without guessing.

## Definition of done

Module 3 is complete when all are true:

- ESS reference comment exists on the existing Module 2 feature issue
- ESS follows the standard section order used in this module
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