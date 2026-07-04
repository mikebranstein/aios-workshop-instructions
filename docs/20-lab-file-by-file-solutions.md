# 20 - Lab File-by-File Solutions (Exact Text)

This file gives exact solution content for the first foundation labs.

Use this only after attempting the labs once.

## Before You Start

You first attempt in 01 and 14.

Then you use this file to compare output shape, correct mistakes, and internalize what good artifacts look like.

## How to apply this file

Compare your file to one solution section at a time.

Do not replace everything blindly. Keep your context, but align structure and gate evidence expectations.

## Checkpoint

After using this file, your artifacts should match required schema and gate evidence shape without removing your real issue context.

## Solution: docs/lab0-operating-surface-check.md

```markdown
# Lab 0 Operating Surface Check

## Source of truth
- Project fields are state source of truth.
- Issue comments are decision source of truth.
- PR checks are verification source of truth.

## Current issue
- Issue ID: #001
- State: Backlog
- Risk: Medium
- Next Gate: Design Gate
- Owner Agent: Intake
```

## Solution: docs/workflow-vs-agent.md

```markdown
# Workflow vs Agent (My Repo)

## Deterministic Workflow Steps
- Intake must pass before Design starts.
- Design gate PASS + human approval before Build starts.
- Verification gate PASS before QA starts.

## Agentic Decision Points
- Build Agent chooses exact files to edit based on ESS.
- Verification Agent groups failures by root cause.
- QA Agent decides severity and recommends release readiness.

## Guardrails
- Never skip Design, Verification, QA, or Merge gate.
- Always require human approval for Medium and High risk merges.
```

## Solution: templates/skills/intake-agent.md output schema section

Use this exact JSON schema block:

```json
{
  "decision": "READY|BLOCKED",
  "missing_fields": ["string"],
  "questions": ["string"],
  "next_state": "Ready|Blocked",
  "summary": "string",
  "confidence": 0.0
}
```

## Solution: docs/gates.md objective criteria examples

Design Gate objective criteria:

- ESS sections 1-8 completed.
- Acceptance criteria are binary and testable.
- At least one mitigation listed per identified risk.

Verification Gate objective criteria:

- dotnet build --configuration Release exits 0.
- dotnet test --configuration Release exits 0.
- dotnet format --verify-no-changes exits 0.

QA Gate objective criteria:

- All acceptance scenarios executed.
- Blocking defects count equals 0.
- QA report file exists and linked in issue.

Merge Gate objective criteria:

- Required reviewers approved.
- Required checks are green.
- Closure evidence template prepared.

## Solution: docs/state-machine.md loop safety section

```markdown
## Loop Safety Policy

- Max retries per gate = 3.
- On third fail, set State = Blocked.
- Set Owner Agent = Human Review.
- Require postmortem document before retry.
```

## Next step

Continue to docs/21-escalation-runbook.md.
