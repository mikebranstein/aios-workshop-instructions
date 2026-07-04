# 17 - Capstone Evaluator Rubric

Use this rubric to score yourself objectively.

Scoring: 0 to 5 per category.

## Before You Start

This rubric is not standalone.

It measures whether you can execute the full path from 14 workshop using controls defined in 02, 03, 10, and 12.

## How to apply this correctly

Score yourself after one full issue run, not during individual steps.

Use evidence links while scoring:

- issue timeline
- ESS
- PR checks
- QA report

## Checkpoint before graduation

You only pass when:

- total score is at least 28/35
- Category 2 is at least 4
- Category 6 is at least 4

If any hard condition fails, return to the matching module and run one more controlled issue.

## Next step

After passing, move to 07 implementation blueprint and promote your process from workshop mode to operational mode.

## Category 1 - State discipline

5:
- Every transition reflected in project State field.
- Owner Agent and Next Gate always updated.

3:
- Minor delays in updates.

1:
- Frequent mismatch between real progress and board state.

## Category 2 - Gate integrity

5:
- No gate skipped.
- PASS/FAIL criteria applied exactly.

3:
- One soft bypass with documentation.

1:
- Gate bypass without evidence.

## Category 3 - Skill contract quality

5:
- JSON outputs consistently valid.
- Decisions and next_state always present.

3:
- Occasional schema drift fixed quickly.

1:
- Frequent prose outputs and inconsistent contracts.

## Category 4 - Verification quality

5:
- .NET command set executes reliably.
- Failures triaged by root cause.

3:
- Commands run but weak triage quality.

1:
- Verification evidence incomplete or missing.

## Category 5 - QA quality

5:
- Scenarios complete and regression considered.
- Defects tracked and looped correctly.

3:
- Scenario coverage partial.

1:
- QA treated as informal check.

## Category 6 - Closure quality

5:
- Closure comment includes all required links and final decision.

3:
- Missing one artifact link.

1:
- Issue closed without audit trail.

## Category 7 - Recovery behavior

5:
- Retry cap honored, blocked escalation handled cleanly.

3:
- Escalation delayed but completed.

1:
- Infinite loops or hidden failures.

## Graduation score

- Minimum total for zero-to-hero graduation: 28/35
- Hard condition: Category 2 and 6 must be at least 4
