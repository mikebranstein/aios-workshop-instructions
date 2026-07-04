# 05 - Step-by-Step Training Regimen (Hands-On Bootcamp)

This is the exact follow-along version. Open this file during each session and execute line by line.

This file is your execution calendar, not your concept glossary.

Use it together with:

- docs/02-foundations.md for concept explanations
- docs/16-zero-to-hero-live-workshop.md for scripted live runs

If you only use this file, you will execute correctly but may miss architecture reasoning.
If you only use concept files, you will understand but not operationalize.
Use both.

## Before You Start

00 through 03 explain why the system works.

This file schedules when to apply each concept so you do not overload yourself or skip quality controls.

## Apply this schedule directly

Pick the current day, execute only that day, and log one evidence artifact before ending the session.

## Checkpoint for this regimen

At the end of each day, you should have one visible artifact change:

- a file created or updated
- a command output captured
- a project state transition logged

If none happened, that day was not complete.

## Next step

Continue to docs/06-build-first-vertical-slice.md.

## Operating Assumptions

- You are on Windows.
- You use VS Code + GitHub Copilot.
- Your repo root is this folder.
- You can create GitHub issues and PRs in your target repo.
- Your primary implementation stack is .NET/C#.

## How To Run Each Session

Every session follows this script:

1. Read the "Objective" for the day.
2. Execute each task exactly in order.
3. Do the validation check at the bottom.
4. Commit your progress.

If validation fails, do not continue to the next day.

Why this rule exists:

Agentic systems amplify process drift. Advancing with unresolved drift creates compounded failures later.

Treat each day as a gate.

## Week 1 - Build The Foundation

Why Week 1 matters:

- This week creates your control plane.
- If this week is weak, all later automation will be brittle.

### Day 1 - Set up core folders and docs

Objective: create the base structure for your Agentic OS artifacts.

Do this:

1. Create folders in repo root:
	 - docs
	 - templates
	 - templates/skills
	 - .github/ISSUE_TEMPLATE
	 - .github/workflows
2. Ensure these files exist:
	 - docs/glossary.md
	 - docs/state-machine.md
	 - docs/gates.md
3. If docs/gates.md does not exist, create it with:

```markdown
# Quality Gates

## Design Gate
- Required inputs:
- Pass criteria:
- Evidence:
- Owner:

## Verification Gate
- Required inputs:
- Pass criteria:
- Evidence:
- Owner:

## QA Gate
- Required inputs:
- Pass criteria:
- Evidence:
- Owner:

## Merge Gate
- Required inputs:
- Pass criteria:
- Evidence:
- Owner:
```

Validation:

- You can explain each gate in one sentence.

### Day 2 - Create your first issue template

Objective: standardize intake quality.

Create .github/ISSUE_TEMPLATE/feature.yml with this content:

```yaml
name: Feature Request
description: Structured feature work item for Agentic OS
title: "[Feature]: "
labels: ["type:feature", "state:backlog"]
body:
	- type: textarea
		id: problem
		attributes:
			label: Problem Statement
			description: What problem are we solving?
		validations:
			required: true

	- type: textarea
		id: scope
		attributes:
			label: Scope
			description: What is in scope?
		validations:
			required: true

	- type: textarea
		id: non_goals
		attributes:
			label: Non-Goals
			description: What are we explicitly not doing?
		validations:
			required: true

	- type: textarea
		id: acceptance
		attributes:
			label: Acceptance Criteria
			description: Use clear pass/fail criteria.
		validations:
			required: true

	- type: textarea
		id: test_scenarios
		attributes:
			label: Test Scenarios
			description: Include happy path and failure path.
		validations:
			required: true

	- type: dropdown
		id: risk
		attributes:
			label: Risk Level
			options:
				- Low
				- Medium
				- High
		validations:
			required: true
```

Validation:

- Open GitHub new issue page and confirm the template renders.

### Day 3 - Define agent contracts

Objective: create deterministic behavior for each agent.

Create these files:

- templates/skills/intake-agent.md
- templates/skills/design-agent.md
- templates/skills/build-agent.md
- templates/skills/verification-agent.md

For each file, use this structure:

```markdown
# <Agent Name>

## Mission

## Inputs
- Required:
- Optional:

## Output Schema
- decision:
- summary:
- artifacts:
- risks:
- next_state:

## Guardrails
- Must not:
- Must always:

## Escalation
- Trigger:
- Action:
```

Validation:

- For each agent, you can answer: what exact output keys should I get?

### Day 4 - Create a real ESS for one practice feature

Objective: produce one executable system spec.

Do this:

1. Pick one small feature.
2. Create docs/ess-practice-001.md.
3. Copy templates/ess-feature.md content into it.
4. Fill sections 1 through 7 completely.

Validation:

- Every acceptance criterion is binary pass/fail.

### Day 5 - Run manual simulation of your pipeline

Objective: do a dry run without coding.

Do this:

1. Create one issue with the Day 2 template.
2. Use Intake prompt from templates/prompts-pack.md.
3. Move issue to Ready or Blocked.
4. Use Design prompt and create ESS draft.
5. Fill a Decision Log comment in the issue.

Validation:

- You generated at least one state transition and one decision log entry.

Before Week 2, read docs/12-dotnet-command-pack.md and set your exact build/test command set.

## Week 2 - First Real Build Through Verification

Why Week 2 matters:

- This week converts templates into real delivery behavior.
- You are proving that agents can operate against objective gates, not just produce text.

### Day 1 - Branch and implementation setup

Objective: run your first real coding flow.

Do this in PowerShell from repo root:

```powershell
git checkout -b feature/issue-001-first-agentic-flow
```

Run Build Agent prompt for your issue.

Validation:

- Code changes are linked to explicit acceptance criteria.

### Day 2 - Add/adjust tests

Objective: enforce test-backed delivery.

Do this:

1. Add or update tests for each acceptance criterion.
2. Note missing testability in issue comments if any.

Validation:

- At least one test maps to each criterion.

### Day 3 - Verification pass

Objective: collect machine evidence.

Do this:

1. Run local verification commands (default .NET):

```powershell
dotnet restore
dotnet build --configuration Release
dotnet test --configuration Release --logger "trx;LogFileName=test-results.trx"
```

2. Save output snippets in issue comment.
3. If fail, loop Build -> Verify.

Validation:

- You can prove pass/fail with logs.

### Day 4 - QA pass

Objective: collect scenario evidence.

Do this:

1. Create docs/qa-report-issue-001.md.
2. Copy templates/qa-checklist.md and fill it.
3. Attach defects or PASS decision.

Validation:

- QA decision is explicit and evidence-backed.

### Day 5 - PR and closure workflow

Objective: complete the lifecycle.

Do this:

1. Open PR and reference issue number.
2. Paste release summary from Release Agent prompt.
3. Merge after approvals.
4. Post closure comment with links to ESS, PR, checks, QA.

Validation:

- Issue is closed with full evidence links.

## Weeks 3-6 (Scale Up)

Use same rhythm, but increase complexity:

- Week 3: medium feature + one integration touchpoint
- Week 4: add CI and enforce required checks
- Week 5: automate state transitions via workflow
- Week 6: run 2 back-to-back issues without process drift

Why scaling is staged:

- Reliability precedes speed.
- You scale only after stable behavior appears on real issues.

## Challenge Blocks (Try Solo First)

### Challenge A

Implement automation that sets label state:in-verification when PR is opened.

Hint:

- Use .github/workflows/state-transition.yml
- Trigger on pull_request opened

### Challenge B

Automatically comment gate summary when checks complete.

Hint:

- Trigger on check_suite completed

### Challenge C

Reduce QA defect rate by tightening Design Gate criteria.

Hint:

- Add explicit non-goals and edge cases in ESS

## Graduation Standard

You are done with training when all are true:

1. Three issues completed end-to-end.
2. Every issue has ESS + QA report + closure evidence.
3. No gate was skipped.
4. Retry loops did not exceed your max retry policy.
