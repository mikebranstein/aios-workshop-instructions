# Module 01 - Tiny End-to-End Run (Manual)

## Goal

Complete one tiny issue from creation to closure so you experience the full lifecycle immediately.

## Prerequisite handoff from Module 0

Before starting this module, confirm you already have:
- scaffolded starter app (Team Equipment Checkout Tracker)
- baseline restore/build/test passing from Module 0
- In Scope Now and Not In Scope Now boundaries defined
- .NET 10 MVC app running locally

If you do not have these, complete [00-module-0-shared-app-foundation.md](00-module-0-shared-app-foundation.md) first.

## Time Box

Target: 75 minutes

This module is intentionally longer than the number of visible commands because you are not only running commands. You are practicing decision points, evidence capture, and state transitions in a controlled way.

## Why this matters

You learn the full flow first, then improve quality and automation in later modules.

Most workshop failures happen when learners understand isolated steps but have never run the full lifecycle once. This module fixes that first.

## Module flow

You will complete this module in five phases:

Step 1: preflight check and workspace readiness.
Step 2: create one tiny issue and set initial board state.
Step 3: run intake review and move the issue from To Do to In Progress.
Step 4: implement a minimal code change and run verification.
Step 5: close the issue with complete evidence.

## What to build in this module

You will build one small but complete delivery record. That means the issue is not only closed, but also traceable from request to implementation to proof.

## Preflight environment gate (10 minutes)

Start here and do not skip it. Run the commands below to confirm your toolchain is available:

```powershell
git --version
dotnet --info
code --version
```

Now verify you can actually work in the repository by running `git fetch origin`, creating or editing one issue, and updating one project item.

If one of these checks fails, pause and fix it before moving on. The purpose is to prevent a 40-minute derailment later in the module.

## Safety rules for this exercise

Before you continue, use these as ground rules for this module.

Rule 1: Keep this exercise low risk.
Choose a tiny, safe change and avoid work that could impact production behavior broadly.

Rule 2: Do not merge anything high risk on your own.
If your change turns out to be medium or high risk, pause and get human review before merge.

Rule 3: Do not loop forever on failures.
If the same gate fails three times, stop retrying, mark the work as Blocked, and escalate.

What this means in practice:
If you are unsure, choose the safer path, reduce scope, and ask for review.

## Build exercise (50 minutes)

### Step 1 (10 minutes): create one fixed tiny issue and put it in To Do

Use this exact tiny issue for Module 1:

Title:
`[Feature] Show available equipment count on the list page`

Paste this markdown as the issue body:

```markdown
## Problem Statement
The equipment list page does not show a quick summary of how many items are currently available, which slows down inventory checks.

## Scope
Display an "Available items" count at the top of the equipment list page.

## Non-Goals
- No authentication or user accounts
- No database changes
- No redesign of page layout

## Acceptance Criteria
- [ ] AC1: Equipment list page shows a numeric "Available items" count.
- [ ] AC2: The count matches the number of items where `IsAvailable = true`.
- [ ] AC3: Existing equipment list behavior remains unchanged.

## Test Scenarios
- Scenario 1 (happy path): Seeded items include available entries -> count displays correctly.
- Scenario 2 (edge case): No items are available -> count displays 0.
- Scenario 3 (regression): Item list still renders with existing columns and availability values.

## Risk Level
Low

## Dependencies
None

## Notes
Keep this change to equipment list flow and one small test update.
```

Then add this issue to your project delivery board and set status to To Do.

### Step 2 (10 minutes): intake decision and start approval

Review the issue body and confirm it is complete enough to start build.

Use this intake checklist:
- scope is one change in one flow (equipment list summary count)
- acceptance criteria are binary pass/fail
- one happy path and one edge case are present
- risk level is Low
- non-goals are explicit and prevent scope creep

If all checks pass, post this comment in the issue:

```markdown
## Intake Decision
Decision: Approved for In Progress

Why:
- Scope is narrow and fits one pull request.
- Acceptance criteria are testable and binary.
- Failure path and happy path are both defined.
- Risk is low and non-goals are explicit.

Next:
- Implement available-equipment count on the list page.
- Run restore/build/test and attach evidence.
```

If any checklist item fails, do not start implementation yet. Fix the issue body first.

If intake passes, move status on the delivery board from To Do to In Progress.

### Step 3 (15 minutes): implement one minimal change

Create a branch and implement the smallest change that satisfies the issue intent. Do not broaden scope. Keep this focused on one outcome.

Use this prompt in Copilot Chat to implement the minimal change:

```text
Implement a minimal .NET 10 ASP.NET Core MVC change for this issue:
"Show available equipment count on the list page".

Context:
- App: Team Equipment Checkout Tracker
- Flow: Equipment list page
- Stack: classic MVC with Controllers, ViewModels, Views, Services

Requirements:
1. Compute available item count where IsAvailable is true.
2. Expose the count to the equipment list MVC view (via ViewModel or view data).
3. Render a clear "Available items: <count>" summary on the list page.
4. Keep existing list rendering behavior unchanged.
5. Add or update one focused test for count calculation or list view model data.
6. Keep changes small and localized to list flow only.

Output format:
- Return markdown only so the output is copy/paste ready.
- List files to edit.
- Show minimal code edits per file in fenced code blocks.
- End with a short "Apply order" checklist.
- Do not refactor unrelated code.
```

After coding, commit with a message that clearly references the issue.

### Step 4 (10 minutes): verification evidence

Run the verification commands and capture results in the issue:

```powershell
dotnet restore
dotnet build --configuration Release
dotnet test --configuration Release
```

If a command fails, fix only the first failure, rerun, and update your issue note.

### Step 5 (5 minutes): closure evidence

When verification is complete, add this exact closure comment in the issue:

```markdown
## Closure Summary

### Outcome
PASS | FAIL

### What changed
- Added available equipment count to the list page.
- Kept existing list behavior intact.

### Evidence
- Issue: <issue-link>
- Branch: <branch-link>
- Commit: <commit-link>
- PR (if opened): <pr-link-or-N/A>

### Verification
- dotnet restore: PASS | FAIL
- dotnet build --configuration Release: PASS | FAIL
- dotnet test --configuration Release: PASS | FAIL

### Acceptance Criteria Check
- AC1 (count shown): PASS | FAIL
- AC2 (count matches IsAvailable=true): PASS | FAIL
- AC3 (existing list behavior unchanged): PASS | FAIL

### Notes
- Any follow-up work or known limitations:
```

After posting the comment:
1. Confirm all required evidence links are filled in.
2. Confirm all three verification commands are marked PASS.
3. Move status to Done on the delivery board.

## Micro checks

By minute 15 you should see the issue created and attached to the project.
By minute 30 you should see status moved to In Progress with a decision note.
By minute 50 you should see verification results posted.

## Stretch task (optional)

If time remains, repeat the same pattern with a second tiny issue to confirm the flow is repeatable.

## You should see

One closed issue with a clear trail from request to implementation to verification proof.

## If this fails, do this

If you run out of time, reduce scope instead of skipping evidence.
If verification fails repeatedly, isolate one root cause and fix only that first.
If issue quality is weak, rewrite the issue before coding.

## Definition of done

The module is done when all are true:

- issue state is Done
- implementation exists and is linked
- verification evidence is posted
- decision notes are visible in issue history
- module scorecard is posted

## Module scorecard template

```markdown
## Module Scorecard
- Module: 01
- Completion time (minutes):
- Retry count by gate:
- Primary blocker cause:
- Evidence completeness (0-100%):
- Outcome: PASS | FAIL
```

## Next module

Continue to [02-module-2-intake-quality-template.md](02-module-2-intake-quality-template.md).