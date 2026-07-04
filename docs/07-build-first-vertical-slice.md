# 05 - Build Your First Vertical Slice (Exact Runbook)

Use this file as your live checklist while executing a real feature from issue to close.

## How this builds on previous modules

You already defined concepts in 01, architecture in 02, and state rules in 03.

Now you execute one full issue using those rules exactly as written.

## How to run this file

Keep this file open while you work.

Apply this as a strict gate checklist, not as a loose reference.

Do one step at a time, post evidence before advancing, and treat each exit criteria line as a hard gate.

## Before You Start

Confirm these files exist:

- .github/ISSUE_TEMPLATE/feature.yml
- docs/gates.md
- templates/skills/intake-agent.md
- templates/skills/design-agent.md
- templates/skills/verification-agent.md
- templates/ess-feature.md
- templates/qa-checklist.md

If any are missing, create them first.

If this is a .NET repository, also confirm:

- A solution file exists (*.sln)
- Test project exists with naming like *.Tests

## Step 1 - Create a real issue

1. In GitHub, create a new issue using Feature Request template.
2. Fill every field.
3. Set State to Backlog.
4. Add label state:backlog.

Exit criteria:

- Issue has problem, scope, non-goals, acceptance criteria, test scenarios, risk.

## Step 2 - Intake gate

Run this prompt in Copilot Chat:

```text
Act as the Intake Agent Skill defined in templates/skills/intake-agent.md.
Use this issue content:

<PASTE ISSUE BODY>

Return JSON only.
```

If decision is BLOCKED:

1. Post missing fields in issue comment.
2. Keep state as Backlog.
3. Stop and fix issue body.

If decision is READY:

1. Move state to Ready.
2. Add Decision Log comment.

Decision Log template:

```text
Decision Log
- YYYY-MM-DD: Intake gate READY by @<name>. Next state Ready.
- Skill version: intake-agent 1.0
```

## Step 3 - Create ESS

1. Create file docs/ess-issue-<id>.md.
2. Copy templates/ess-feature.md into it.
3. Fill sections 1 through 7 completely.

Do not start coding yet.

Exit criteria:

- Acceptance criteria are binary.
- Verification commands are real commands.

## Step 4 - Design gate

Run this prompt:

```text
Act as the Design Agent Skill in templates/skills/design-agent.md.
Input:
- Work item content
- ESS draft

Return JSON only.
```

If decision is REVISE or BLOCKED:

1. Update ESS.
2. Re-run Design prompt.

If decision is PASS:

1. Get human approval in issue comment.
2. Move state to In Build.

## Step 5 - Build execution

From repo root PowerShell:

Branch naming rule:

- feature/issue-<id>-<kebab-case-description>

Example:

- feature/issue-123-admin-failed-filter

```powershell
git checkout -b feature/issue-<id>-<short-slug>
```

After your first commit, push branch:

```powershell
git push -u origin feature/issue-<id>-<short-slug>
```

If you accidentally committed on the wrong branch:

```powershell
git checkout -b feature/issue-<id>-<short-slug>
git push -u origin feature/issue-<id>-<short-slug>
```

Then open PR from the correct branch.

Implementation rules:

1. One commit per meaningful task.
2. Keep each commit message tied to acceptance criteria.
3. Update tests with code changes.

Example commit pattern:

```powershell
git add .
git commit -m "feat(issue-<id>): implement AC1 request validation"
```

## Step 6 - Verification gate

Run this prompt:

```text
Act as the Verification Agent Skill in templates/skills/verification-agent.md.
Use these commands:
- Build: dotnet build --configuration Release
- Test: dotnet test --configuration Release --logger "trx;LogFileName=test-results.trx"
- Lint: dotnet format --verify-no-changes

Return JSON only.
```

If FAIL:

1. Copy failing_checks and root_causes into issue comment.
2. Move state back to In Build.
3. Fix and rerun verification.

If PASS:

1. Move state to In QA.
2. Post verification summary in issue.

If dotnet format is not configured yet, use this temporary lint substitute:

- dotnet build --configuration Release /warnaserror

## Step 7 - QA gate

1. Create docs/qa-report-issue-<id>.md.
2. Copy templates/qa-checklist.md and fill it.
3. Execute each acceptance scenario manually or automated.

If QA FAIL:

1. Log defects.
2. Move state to In Build.
3. Repeat Build -> Verification -> QA.

If QA PASS:

1. Move state to Ready to Merge.

## Step 8 - PR and merge

Push branch and open PR linked to issue.

PR must include:

1. What changed
2. Why it changed
3. Risks and rollback
4. Links to ESS, verification, QA report

After approvals and passing checks, merge PR.

## Step 9 - Closure gate

Post final issue comment with this exact structure:

```markdown
## Closure Summary
- ESS: <link>
- PR: <link>
- Verification evidence: <link>
- QA report: <link>
- Final decision: DONE
```

Set state to Done and close issue.

## Definition of Success

Your vertical slice is successful when:

1. No gate skipped.
2. Every gate has evidence.
3. Issue is closed with an audit trail.

## Final checkpoint and next step

If this vertical slice passes, run a second issue with the same discipline and then score yourself using 17 capstone evaluator rubric.

## Troubleshooting

Problem: verification repeatedly fails.
Action: isolate first failing root cause and fix only that.

Problem: scope keeps expanding.
Action: enforce non-goals in ESS before new code.

Problem: closure feels subjective.
Action: require all four links in closure template.
