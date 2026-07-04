# Module 01 - Tiny End-to-End Run (Manual)

## Goal

Complete one tiny issue from creation to closure so you experience the full lifecycle immediately.

## Time Box

Target: 75 minutes

This module is intentionally longer than the number of visible commands because you are not only running commands. You are practicing decision points, evidence capture, and state transitions in a controlled way.

## Why this matters

You learn the full flow first, then improve quality and automation in later modules.

Most workshop failures happen when learners understand isolated steps but have never run the full lifecycle once. This module fixes that first.

## Module flow

You will complete this module in five phases:

Step 1: preflight check and workspace readiness.
Step 2: create one tiny issue and set initial state.
Step 3: move the issue from Backlog to Ready with a clear decision.
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

### Step 1 (10 minutes): create a tiny issue

Create one tiny feature issue, such as adding one validation guard or one small error message improvement. Keep scope intentionally narrow so the full lifecycle fits in a single session.

Add the issue to your project board and set state to Backlog.

### Step 2 (10 minutes): intake and Ready decision

Review the issue body and confirm it is complete enough to start build. Record a short decision note in the issue comment history explaining why it is ready.

Move state from Backlog to Ready.

### Step 3 (15 minutes): implement one minimal change

Create a branch and implement the smallest change that satisfies the issue intent. Do not broaden scope. Keep this focused on one outcome.

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

When verification is complete, post a closure summary with links to:

- issue
- branch or commit
- verification output

Move state to Done.

## Micro checks

By minute 15 you should see the issue created and attached to the project.
By minute 30 you should see state moved to Ready with a decision note.
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