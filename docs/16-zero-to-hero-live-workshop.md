# 16 - Zero-to-Hero Live Workshop (Fully Scripted)

This is your end-to-end live workshop.

Use this exactly as written.
Do not skip steps.
Do not continue when a gate says stop.

If you complete this workshop, you will have a working AIOS for coding delivery using GitHub + Copilot with deterministic controls.

## Before You Start

This workshop applies the concepts and control rules from 00 through 15 in one continuous execution path.

## How to apply this file

Run one step at a time, record evidence at each gate, and use 17 for exact prompt text and 18 for output recovery.

## Copilot Chat quickstart (required before Day 1)

1. Open Copilot Chat in VS Code.
2. Confirm you are signed in and can send prompts.
3. Run this test prompt:

```text
Return raw JSON only with key status and value ready.
```

Expected output:

```json
{
  "status": "ready"
}
```

If output is markdown or prose, retry with:

```text
Return raw JSON only. No markdown fence. No explanation.
```

If prompts become too large, split input into parts and label each part clearly.

## Workshop contract

- You execute steps in order.
- Each step has:
  - Action
  - Copy-paste text
  - Expected output
  - Failure handling
  - Pass gate
- If a pass gate fails, you must repair before continuing.

## Time model

- Foundation Sprint: 2 days
- Core Build Sprint: 3 days
- Automation Sprint: 3 days
- Capstone Sprint: 2 days

Total: 10 working sessions.

## Outcome definition

At the end, you can create a work item and your AIOS can reliably progress it through:

Backlog -> Ready -> In Design -> In Build -> In Verification -> In QA -> Ready to Merge -> Done

with evidence and approvals.

---

## Day 1 - System setup and state control

### Step 1.1 - Create project state system

Action:

1. Follow docs/13-github-projects-click-by-click.md Part A through Part E.
2. Create one issue using .github/ISSUE_TEMPLATE/feature.yml.
3. Add issue to project board.

Expected output:

- Project item exists with fields:
  - State = Backlog
  - Risk = Medium
  - Next Gate = Design Gate
  - Owner Agent = Intake

Failure handling:

- If item does not show on board, reconnect repo in project settings and re-add issue.

Pass gate:

- You can open the card and see all four fields populated.

### Step 1.2 - Create Decision Log baseline

Action:

Add this exact comment to the issue:

```text
Decision Log
- 2026-07-04: Issue created and added to AIOS board. Initial state Backlog.
- Skill versions: intake-agent 1.0, design-agent 1.0, verification-agent 1.0
```

Expected output:

- Decision Log comment appears on issue timeline.

Pass gate:

- Timeline includes at least one operational decision entry.

### Step 1.3 - Lock governance

Action:

In repository settings, add branch rule for main:

1. Require pull request before merging.
2. Require status checks to pass.
3. Require conversation resolution.

Expected output:

- Protected branch rule is active.

Failure handling:

- If check names unavailable, continue and return after Step 6.1 activates CI.
- If you do not have admin permissions, tag a repository admin and record that dependency in issue comment.

Pass gate:

- Direct pushes to main are blocked.

---

## Day 2 - Labs 0 to 2 (deep scripted)

### Lab 0 - Operating surface validation

Action:

Create file docs/lab0-operating-surface-check.md with this exact content:

```markdown
# Lab 0 Operating Surface Check

## Source of truth
- Project fields are state source of truth.
- Issue comments are decision source of truth.
- PR checks are verification source of truth.

## Current issue
- Issue ID:
- State:
- Risk:
- Next Gate:
- Owner Agent:
```

Fill values from your real issue card.

Expected output:

- File exists and is fully filled.

Pass gate:

- No empty field remains in Current issue section.

### Lab 1 - Workflow versus Agent exercise

Action:

Create docs/workflow-vs-agent.md using the template in docs/02-foundations.md Lab 1.

Use this exact minimum content:

```markdown
## Deterministic Workflow Steps
- Intake must pass before Design starts.
- Design approval is required before Build starts.
- Verification pass is required before QA starts.

## Agentic Decision Points
- Build Agent selects exact files to modify.
- Verification Agent groups failures by root cause.
- QA Agent classifies defects by severity.

## Guardrails
- Never skip Design, Verification, or QA gate.
- Always require human approval when risk is Medium or High.
```

Expected output:

- The distinction between fixed control and dynamic decision is clear.

Pass gate:

- A teammate could route work using this file without asking follow-up questions.

### Lab 2 - Intake skill live test

Action:

1. Open templates/skills/intake-agent.md.
2. Ensure schema contains these keys:
   - decision
   - missing_fields
   - questions
   - next_state
   - summary
   - confidence
3. Run this prompt in Copilot Chat:

```text
Act exactly as templates/skills/intake-agent.md.
Use this issue content:

Problem Statement:
Users cannot quickly find failed orders in the admin portal.

Scope:
Add a filter in the orders page for status=Failed and date range.

Non-Goals:
No schema changes. No export features.

Acceptance Criteria:
1) Admin can filter by Failed status.
2) Admin can filter by date range.
3) Empty result shows clear message.

Test Scenarios:
- Filter by Failed only
- Filter by Failed + date range
- No results path

Risk Level:
Medium

Return JSON only.
```

Expected output sample:

```json
{
  "decision": "READY",
  "missing_fields": [],
  "questions": [],
  "next_state": "Ready",
  "summary": "Work item has required fields and can proceed to design.",
  "confidence": 0.86
}
```

Failure handling:

- If output is not JSON-only, retry with: Do not include markdown.
- If confidence < 0.7, keep state Backlog and clarify issue text.

Pass gate:

- Valid JSON output with all keys and confidence >= 0.7.

---

## Day 3 - Design and ESS execution

### Step 3.1 - Create real ESS

Action:

1. Create docs/ess-issue-001.md.
2. Copy templates/ess-feature.md.
3. Fill sections 1-8 now.

Use these verification defaults for .NET:

- Build: dotnet build --configuration Release
- Test: dotnet test --configuration Release --logger "trx;LogFileName=test-results.trx"
- Lint/format: dotnet format --verify-no-changes

Expected output:

- ESS has binary criteria and executable verification commands.

Pass gate:

- Another engineer can execute section 6 without interpretation.

### Step 3.2 - Design gate pass/fail

Action:

Run this prompt:

```text
Act as templates/skills/design-agent.md.
Evaluate this ESS for scope clarity, risk handling, and readiness for build.
Return JSON only with decision PASS|REVISE|BLOCKED.
```

Expected output:

- JSON decision with risks and mitigations.

Failure handling:

- If REVISE, update ESS and re-run once.
- If still REVISE, escalate with a human design decision.

Pass gate:

- Design decision is PASS and logged in issue comment.

---

## Day 4 - Build and verification loops

### Step 4.1 - Branch and implement

Action:

Run:

```powershell
git checkout -b feature/issue-001-orders-failed-filter
```

Implement only ESS scope.

Commit format:

```powershell
git add .
git commit -m "feat(issue-001): implement AC1 failed status filter"
```

Expected output:

- One scoped commit tied to AC1 (repeat for AC2, AC3).

Pass gate:

- Every acceptance criterion maps to code/test changes.

### Step 4.2 - Verification loop

Action:

Run commands from docs/12-dotnet-command-pack.md baseline.

Post this exact issue comment template:

```markdown
## Verification Summary
- Restore: PASS/FAIL
- Build: PASS/FAIL
- Test: PASS/FAIL
- Format/Lint: PASS/FAIL
- Root cause (if fail):
- Next action:
```

Loop policy:

- Up to 3 retries.
- On third fail: State = Blocked, Owner Agent = Human Review.

Pass gate:

- Verification gate is PASS with evidence comment.

---

## Day 5 - QA and PR lifecycle

### Step 5.1 - QA report

Action:

1. Create docs/qa-report-issue-001.md.
2. Copy templates/qa-checklist.md.
3. Fill all checklist items.

Expected output:

- QA decision marked PASS or FAIL with evidence.

Pass gate:

- QA PASS or defect list created with return-to-build decision.

### Step 5.2 - PR and closure

Action:

1. Push branch.
2. Open PR with issue reference.
3. Include links to ESS + verification + QA report.
4. Merge after checks and approvals.

Post closure comment:

```markdown
## Closure Summary
- ESS: <link>
- PR: <link>
- Verification evidence: <link>
- QA report: <link>
- Final decision: DONE
```

Pass gate:

- Issue moved to Done with all links present.

---

## Days 6-8 - Automation sprint

Goal: remove manual state updates and summary posting.

### Step 6.1 - Activate CI workflow

Action:

1. Copy templates/workflows/ci-example.yml to .github/workflows/ci.yml.
2. Commit and push the workflow file.
3. Open or update a PR and confirm status check appears.
4. In branch protection rule, set this CI check as required.

Expected output:

- CI workflow runs restore, build, test, and format check on PRs.

Pass gate:

- CI runs on pull requests.

### Step 7.1 - State transition automation

Action:

1. Create .github/workflows/state-transition.yml based on templates/workflows/state-transition-example.yml.
2. Implement PR opened, checks completed, and PR merged comment transitions.

Pass gate:

- Workflow posts issue comment on each lifecycle event.

### Step 8.1 - Enforce merge gate by policy

Action:

1. Use docs/policy-risk-and-approvals.md.
2. Ensure medium risk requires design approval + PR reviewer.

Pass gate:

- Medium-risk PR cannot merge without required reviewers.

---

## Days 9-10 - Capstone sprint

Run two real issues end-to-end.

Rules:

- No skipped gates.
- Full evidence links at closure.
- Retry caps enforced.

Metrics to record in docs/capstone-results.md:

- Cycle time per issue
- Verification retries
- QA defects count
- Manual interventions count

Graduation gate:

- Two consecutive issues completed with full evidence and no skipped gate.

---

## Zero-to-Hero final checklist

You are hero-ready when all are true:

1. You can explain all five orchestration patterns and when not to use them.
2. You can execute Labs 0-5 from memory.
3. Your project board fields are always current.
4. Your AIOS enforces gate policy through workflow + branch rules.
5. You can run a feature from issue to Done in one controlled pass.

If one is false, repeat the relevant day until true.


## Next step

Continue to docs/17-copy-paste-exercise-pack.md.

