# Module 02 - Intake Quality Template

## Goal

Prevent incomplete work items from entering build flow.

## Time Box

Target: 70 minutes

Suggested pacing:
- 10 min: understand what a good issue template does
- 25 min: create or refine the template in GitHub
- 20 min: create and test one real issue from the template
- 10 min: quality-check acceptance criteria
- 5 min: capture scorecard and handoff

## Why this matters

High-quality intake reduces rework in every downstream step.

If issue input quality is weak, every later module becomes harder: design is unclear, build scope drifts, and QA cannot verify outcomes objectively.

This module makes that problem visible and fixable.

## What you will build

- one structured feature issue template in `.github/ISSUE_TEMPLATE/feature_request.md`
- one real issue created from the template
- one intake-quality check note proving the issue is ready for ESS

## Required tasks

1. Create or refine a feature issue template.
2. Make key fields required.
3. Create one issue from the template.
4. Validate that acceptance criteria are binary and testable.

## Stretch tasks

- Create one intentionally weak issue and document why it should be BLOCKED.

## Build exercise (step-by-step)

### Step 1 (10 minutes): inspect current intake quality

Open your repository and check whether `.github/ISSUE_TEMPLATE/feature_request.md` already exists.

If it exists, skim it and answer:
- Does it force problem statement, scope, and non-goals?
- Does it force testable acceptance criteria?
- Does it force a risk level?

If any answer is no, you will refine it in Step 2.

### Step 2 (25 minutes): create or refine the template

Use one of these two paths. Path A is the most reliable and recommended for this workshop.

Path A (recommended, always works):
1. In VS Code, create or edit `.github/ISSUE_TEMPLATE/feature_request.md`.
2. Commit and push the file.

Path B (GitHub web editor):
1. Open the repository in GitHub.
2. Press `.` to open the web editor, or browse to `.github/ISSUE_TEMPLATE/` and create `feature_request.md`.
3. Commit the file from the web editor.

Note:
GitHub's "Set up templates" button and settings navigation vary by UI version and repository state. This workshop uses the file-based method so the steps stay consistent.

Use this baseline markdown template content:

```markdown
---
name: Feature request
about: Suggest an idea for this project
title: "[Feature]: "
labels: ''
assignees: ''

---

## Problem Statement
What problem are we solving?

## Scope
What is included in this change?

## Non-Goals
What is explicitly out of scope?

## Acceptance Criteria
Write each criterion as pass/fail behavior.

- [ ] AC1:
- [ ] AC2:
- [ ] AC3:

## Test Scenarios
Include both happy path and failure path.

- Scenario 1:
- Scenario 2:
- Scenario 3:

## Risk Level
Choose one: Low / Medium / High

## Dependencies
List blockers, linked issues, or external dependencies.

## Notes
Any additional context, constraints, or references.
```

### Step 3 (20 minutes): create one real issue from template

Create a new issue using the feature template.

Use a tiny, concrete feature so you can carry it into Module 3.

Example topic:
"Add input validation for empty customer email in checkout form"

Write acceptance criteria in pass/fail style, for example:
- PASS: submitting empty email shows validation message
- PASS: valid email allows submission
- FAIL: form submits when email is empty

### Step 4 (10 minutes): run intake quality check

Before you leave this module, verify your issue has all required fields completed and no ambiguous acceptance criteria.

Add one comment in the issue titled `Intake Quality Check` summarizing:
- missing fields: none or list
- acceptance criteria testable: yes or no
- ready for ESS: yes or no

### Step 5 (5 minutes): capture module scorecard

Post your module scorecard and prepare to continue to ESS creation.

## Micro checks

By minute 20 you should see template structure drafted.
By minute 40 you should see one issue created from template.
By minute 60 you should see intake-quality check comment posted.

## You should see

One issue that can move to design without clarification churn.

## If this fails, do this

If template does not render in GitHub, confirm file path and frontmatter format.
If criteria are vague, rewrite each criterion as observable pass/fail behavior.
If issue scope is too broad, split into a smaller first issue and move the rest to backlog.

## Definition of done

Module 2 is complete when all are true:

- template enforces required intake fields
- one real issue is created from that template
- acceptance criteria are binary and testable
- intake-quality check comment is posted
- module scorecard is posted

## Module scorecard template

```markdown
## Module Scorecard
- Module: 02
- Completion time (minutes):
- Retry count by gate:
- Primary blocker cause:
- Evidence completeness (0-100%):
- Outcome: PASS | FAIL
```

## Next module

Continue to [03-module-3-first-ess.md](03-module-3-first-ess.md).