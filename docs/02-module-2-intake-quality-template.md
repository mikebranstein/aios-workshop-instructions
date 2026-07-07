# Module 02 - Intake Quality Template

## Goal

Prevent incomplete work items from entering build flow.

## Time Box

Target: 70 minutes

Suggested pacing:
- 10 min: understand what a good issue template does
- 20 min: create or refine the template in GitHub
- 15 min: use Copilot to draft a feature request body
- 15 min: create and test one real issue from the template
- 5 min: quality-check acceptance criteria
- 5 min: capture scorecard and handoff

## Why this matters

High-quality intake reduces rework in every downstream step.

If issue input quality is weak, every later module becomes harder: design is unclear, build scope drifts, and QA cannot verify outcomes objectively.

This module makes that problem visible and fixable.

## What you will build

- one structured feature issue template in `.github/ISSUE_TEMPLATE/feature_request.md`
- one Copilot-generated feature request body based on your template fields
- one real issue created from the template
- one intake-quality check note proving the issue is ready for ESS

## Required tasks

1. Create or refine a feature issue template.
2. Use GitHub Copilot to draft a complete feature request body.
3. Make key fields required.
4. Create one issue from the template.
5. Validate that acceptance criteria are binary and testable.

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

### Step 2 (20 minutes): create or refine the template

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
title: "[feature-request]: "
labels: ''
assignees: ''

---

## Problem Statement
What problem are we solving?

## Scope
What is included in this change?

## Non-Goals
What is explicitly out of scope?

## Acceptance Criteria (Draft - for discussion framing)
Include 3-5 initial acceptance criteria as discussion starters. 
These will be refined by BA during Intake to "Confirmation" state (Given/When/Then format).
Focus on outcomes, not implementation details.

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

### Step 3 (15 minutes): use Copilot to draft the feature request body

Before opening your issue, use Copilot Chat to generate the body text so you start from a complete draft instead of a blank form.

Use a tiny, concrete feature so you can carry it into Module 3.

Example prompt you can paste into Copilot Chat:

```text
Create a complete GitHub feature request draft using this structure:
- Problem Statement
- Scope
- Non-Goals
- Acceptance Criteria (draft, 3-5 criteria for BA to refine)
- Test Scenarios (happy path + failure path)
- Risk Level (Low/Medium/High with one-line reason)
- Dependencies
- Notes

Feature idea: Add input validation for empty customer email in checkout form.
Context: Web checkout form currently allows blank email submission in some flows.
Constraints:
- Keep scope small enough for one pull request.
- Keep the feature tiny and concrete so it can be implemented in Module 3.
- Acceptance criteria are DRAFT (BA will refine to testable Given/When/Then format during Intake).
- Write draft criteria focused on outcomes, not implementation.
- Include both happy path (valid email) and failure path (empty email error).

Draft acceptance criteria style example:
- User can submit checkout with valid email
- User sees validation error when email is empty
- System prevents checkout with blank email field

Return only markdown content for the issue body.
Do not include commentary before or after the markdown.
```

After Copilot generates the draft, refine it using one of these options:

Option A (manual):
- remove vague words like "improve," "better," or "as needed"
- make every acceptance criterion focused on outcomes (what user can do), not implementation (how system works)
- keep non-goals explicit so scope does not drift
- remember: BA will refine these to Given/When/Then format during Intake

Option B (Copilot-assisted):
Paste your draft into Copilot Chat with this prompt:

```text
Rewrite this feature request draft to make it intake-ready.

Requirements:
- Keep the same feature intent and scope.
- Remove vague wording (avoid "improve," "better," "as needed").
- Make all acceptance criteria focused on outcomes (what users can do), not implementation details.
- Keep acceptance criteria as DRAFT (BA will refine to Given/When/Then during Intake).
- Keep non-goals explicit and specific.
- Keep risk level and dependencies concise.

Output format:
- Return markdown only (copy/paste ready).
- Return clean markdown using these sections only:
	- Problem Statement
	- Scope
	- Non-Goals
	- Acceptance Criteria (keep as draft, outcome-focused)
	- Test Scenarios
	- Risk Level
	- Dependencies
	- Notes
- Do not include any extra explanation outside those sections.

Here is the draft to improve:
<paste draft here>
```

### Step 4 (15 minutes): create one real issue from template

Create a new issue using the feature template.

Paste the finalized feature text you generated in Step 3 into the template sections.

Do a quick final pass only if needed to fix weak or ambiguous lines.

### Step 5 (5 minutes): run intake quality check

Before you leave this module, verify your issue has all required fields completed and no ambiguous acceptance criteria.

Add one comment in the issue titled `Intake Quality Check` summarizing:
- missing fields: none or list
- acceptance criteria testable: yes or no
- ready for ESS: yes or no

If you want Copilot to generate the comment draft, use this prompt:

```text
Generate a markdown issue comment titled "Intake Quality Check" for this feature request.

Requirements:
- Use exactly these fields:
	- missing fields: none or list
	- acceptance criteria testable: yes or no
	- ready for ESS: yes or no
- Be strict and concise.
- If any section is weak or ambiguous, mark ready for ESS as "no".

Output format:
- Return markdown only (copy/paste ready).
- Do not include explanation outside the comment.

Feature request content:
<paste finalized feature request markdown here>
```

### Step 6 (5 minutes): capture module scorecard

Post your module scorecard and prepare to continue to ESS creation.

## Micro checks

By minute 20 you should see template structure drafted.
By minute 35 you should see a Copilot-generated draft ready for review.
By minute 50 you should see one issue created from template.
By minute 60 you should see intake-quality check comment posted.

## You should see

One issue that can move to design without clarification churn.

## If this fails, do this

If template does not render in GitHub, confirm file path and frontmatter format.
If criteria are vague, rewrite each criterion focused on outcomes (what users can do), not implementation.
If issue scope is too broad, split into a smaller first issue and move the rest to backlog.

## Definition of done

Module 2 is complete when all are true:

- template enforces required intake fields
- one Copilot-generated draft was reviewed and used to create a real issue
- one real issue is created from that template
- acceptance criteria are outcome-focused and clear (draft for BA to refine)
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