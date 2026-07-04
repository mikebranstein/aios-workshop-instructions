# 18 - Live Lab Answer Keys and Failure Recovery

Use this file while running labs.

## Before You Start

This file is your validation companion for 14 and 16.

You use it to confirm output shape and recover quickly when results drift from expected contracts.

## How to apply this file

After each lab step, compare your output to the matching answer key before proceeding.

If shape does not match, run the listed recovery prompt and retry once.

## Lab 0 answer key

Expected state after Lab 0:

- State: Backlog
- Risk: Medium
- Next Gate: Design Gate
- Owner Agent: Intake

If your board shows any empty value, fix before Lab 1.

## Lab 1 answer key

Correct pattern:

- Deterministic steps are gate-controlled stage transitions.
- Agentic decisions are inside-stage dynamic choices.

If your Deterministic section contains words like maybe, should, likely, rewrite with hard conditions.

## Lab 2 answer key

Valid JSON schema:

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

Common failures:

1. Model returns markdown.
- Recovery prompt: Return raw JSON only. No markdown.

2. Missing confidence field.
- Recovery prompt: Include confidence as decimal from 0.0 to 1.0.

3. READY despite missing fields.
- Recovery prompt: If required input missing, decision must be BLOCKED.

## ESS quality answer key

A good ESS has:

- 3 to 7 binary acceptance criteria
- executable verification commands
- rollback trigger and actions
- explicit risk mitigation

If acceptance criteria include vague words like improve, optimize, enhance without metric, rewrite.

## Verification gate answer key

PASS means all true:

- restore/build/test/format commands succeeded
- no unresolved blocking test failure
- evidence comment posted on issue

If one is false, gate is FAIL.

## QA gate answer key

PASS means all true:

- acceptance scenarios passed
- regressions checked
- no blocking defects open

If a blocking defect exists, return to Build state.

## Closure gate answer key

Issue cannot be Done unless closure comment has links to:

- ESS
- PR
- verification evidence
- QA report

Missing any link means closure is invalid.

## Emergency fallback script

If the workshop gets stuck, run this reset sequence:

1. Set State = Blocked.
2. Add issue comment with root cause and missing artifact.
3. Create postmortem using docs/postmortem-template.md.
4. Define next minimal action.
5. Resume from previous gate only.

## Next step

Continue to docs/19-capstone-evaluator-rubric.md.
