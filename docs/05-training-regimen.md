# 05 - Step-by-Step Training Regimen (Hands-On Bootcamp)

Use this file as your weekly execution calendar.

## Before You Start

Complete docs/00-prerequisites-and-tooling.md through docs/04-github-as-state.md first.

## Session rhythm (repeat every day)

1. Read the daily objective.
2. Complete tasks in order.
3. Pass the daily checkpoint.
4. Log one evidence artifact before ending.

If checkpoint fails, do not advance to next day.

## Week 1 - Build core workflow habits

### Day 1 - Set up core files

Objective:
Ensure baseline docs and folders exist.

Tasks:

1. Verify folders: docs, templates, templates/skills, .github/ISSUE_TEMPLATE, .github/workflows.
2. Verify files: docs/gates.md, docs/state-machine.md, docs/evidence-convention.md.
3. If missing, create placeholders and fill required sections.

Checkpoint:

- All core files exist and are readable.

### Day 2 - Standardize issue intake

Objective:
Create or verify one structured feature issue template.

Tasks:

1. Open .github/ISSUE_TEMPLATE/feature.yml.
2. Ensure required fields include problem, scope, non-goals, acceptance criteria, test scenarios, and risk.
3. Create one test issue with the template.

Checkpoint:

- Template renders and required fields are enforced.

### Day 3 - Define role contracts

Objective:
Make role outputs consistent and reviewable.

Tasks:

1. Review templates/skills/intake-agent.md, design-agent.md, build-agent.md, verification-agent.md.
2. Ensure each has mission, inputs, output schema, guardrails, and escalation.
3. Ensure output schema uses consistent keys.

Checkpoint:

- You can list expected output keys for each role.

### Day 4 - Produce one execution spec

Objective:
Create one complete ESS for a small feature.

Tasks:

1. Copy templates/ess-feature.md to docs/ess-practice-001.md.
2. Fill all required sections.
3. Keep acceptance criteria binary.

Checkpoint:

- ESS is complete and implementation-ready.

### Day 5 - Run a no-code rehearsal

Objective:
Practice workflow transitions without coding.

Tasks:

1. Take one issue from Backlog to Ready or Blocked.
2. Log intake and design decisions.
3. Set Next Gate correctly.

Checkpoint:

- Issue history shows clear transitions and reasons.

## Week 2 - Run first real build to QA

### Day 1 - Start implementation branch

Objective:
Begin one real feature flow.

Tasks:

1. Create feature branch for selected issue.
2. Implement smallest acceptance criterion first.
3. Link commit to issue.

Checkpoint:

- At least one criterion has a matching code change.

### Day 2 - Add or update tests

Objective:
Tie criteria to tests.

Tasks:

1. Add or update tests for changed behavior.
2. Document any non-testable criterion and reason.

Checkpoint:

- Each implemented criterion has test evidence or explicit rationale.

### Day 3 - Run verification commands

Objective:
Collect machine evidence.

Tasks:

1. Run restore, build, and test commands.
2. Save result summary in issue or PR.
3. If failing, return to build and retry within policy.

Checkpoint:

- Verification status and logs are visible in project history.

### Day 4 - Complete QA report

Objective:
Capture scenario evidence.

Tasks:

1. Create or update a QA report file.
2. Record scenario outcomes and defects.
3. Set QA decision.

Checkpoint:

- QA decision is explicit and evidence-backed.

### Day 5 - Merge and close with evidence

Objective:
Finish lifecycle with complete traceability.

Tasks:

1. Open PR linked to issue.
2. Confirm required approvals and checks.
3. Merge and post closure summary with links to ESS, PR, verification, and QA.

Checkpoint:

- Issue closes with complete evidence links.

## Weeks 3-6 - Scale carefully

Use same session rhythm while increasing complexity:

- Week 3: medium-size feature with one integration dependency
- Week 4: enforce required CI checks
- Week 5: automate deterministic state updates
- Week 6: complete two consecutive issues without gate drift

## Graduation standard

You are done when all are true:

1. Three issues completed end-to-end.
2. Every issue has ESS, QA, and closure evidence links.
3. No quality gate was skipped.
4. Retry policy was respected.

## Next step

Continue to docs/06-build-first-vertical-slice.md.
