# 16 - Copy-Paste Exercise Pack

Use this as your exact text source during live exercises.

## Before You Start

14 tells you when to run a step.

This file gives the exact input text for that step so output quality is consistent while you learn.

## How to apply this correctly

For each live exercise:

1. read the step in 14
2. copy matching block from this file
3. run it unchanged first
4. log the output in issue timeline

## Checkpoint

You should see JSON outputs for structured prompts and complete templates for decision or closure logs.

If outputs drift to prose, use the recovery guidance in 15.

## A) Seed issue text (feature)

```text
Title: [Feature] Admin failed orders quick filter

Problem Statement:
Support engineers spend too long finding failed orders in admin.

Scope:
Add filters for order status=Failed and date range on admin orders page.

Non-Goals:
No database schema changes.
No CSV export.
No new permissions model.

Acceptance Criteria:
1) Admin can filter by Failed status only.
2) Admin can filter by Failed + date range.
3) Empty result state shows clear no-results message.
4) Existing non-failed filter behavior is unchanged.

Test Scenarios:
- Failed only returns failed orders
- Failed + date returns bounded results
- No results state displays message and no crash
- Existing status filters still work

Risk Level:
Medium
```

## B) Intake prompt

```text
Act exactly as templates/skills/intake-agent.md.
Evaluate the following work item.
Return JSON only and include confidence.

<PASTE WORK ITEM>
```

## C) Design prompt

```text
Act exactly as templates/skills/design-agent.md.
Input:
- Work item text
- ESS draft

Return JSON only with:
- decision
- design_summary
- interfaces_changed
- data_model_impact
- risks
- mitigations
- next_state
```

## D) Verification prompt

```text
Act exactly as templates/skills/verification-agent.md.
Use these commands:
- dotnet restore
- dotnet build --configuration Release
- dotnet test --configuration Release --logger "trx;LogFileName=test-results.trx"
- dotnet format --verify-no-changes

Return JSON only.
```

## E) Decision log templates

```text
Decision Log
- 2026-07-04: Intake gate READY by @<name>. Next state Ready.
- 2026-07-04: Design gate PASS by @<name>. Next state In Build.
- 2026-07-04: Verification gate PASS by @<name>. Next state In QA.
- 2026-07-04: QA gate PASS by @<name>. Next state Ready to Merge.
- Skill versions: intake-agent 1.0, design-agent 1.0, verification-agent 1.0
```

## F) Closure summary template

```markdown
## Closure Summary
- ESS: <link>
- PR: <link>
- Verification evidence: <link>
- QA report: <link>
- Final decision: DONE
```

## G) Blocked-state template

```markdown
## Blocked Notice
- Gate: <Design|Verification|QA>
- Retry count: 3
- Root cause:
- Required human decision:
- Next action owner:
```

## Next step

Return to 14 for the next execution step and validate with 15 after each gate.
