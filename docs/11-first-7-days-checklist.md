# 09 - First 7 Days Plan (Guided)

This file is your short operational launch plan.

Use it when you want momentum without reading the full workshop first.

Each day includes:

- purpose
- required actions
- pass condition
- common mistake to avoid

## Before You Start

Each day depends on the previous day.

Do not jump ahead. You are stacking controls in order so the system is stable before automation pressure increases.

## Daily checkpoint rule

Do not mark a day complete until pass condition is true and visible in repo artifacts or issue history.

Apply this rule every day, even when work feels simple.

## Day 1 - Build control points

Purpose:

- define what counts as quality before any code is generated

Required actions:

- [ ] Create docs/gates.md
- [ ] Confirm docs/state-machine.md transitions
- [ ] Add retry policy to state machine

Pass condition:

- You can explain exactly why an item can and cannot move between each state.

Common mistake:

- jumping into implementation before writing gate pass criteria

## Day 2 - Standardize intake

Purpose:

- prevent incomplete work items from entering your pipeline

Required actions:

- [ ] Create .github/ISSUE_TEMPLATE/feature.yml
- [ ] Create one real issue with template
- [ ] Run Intake skill once

Pass condition:

- Intake returns READY or BLOCKED using schema, not prose.

Common mistake:

- treating issue template fields as optional

## Day 3 - Lock design intent

Purpose:

- convert idea into executable spec with bounded scope

Required actions:

- [ ] Create docs/ess-issue-001.md
- [ ] Fill ESS sections 1-7
- [ ] Get human design approval

Pass condition:

- ESS acceptance criteria are binary and verification commands are executable.

Common mistake:

- writing vague criteria like improve, optimize, or better UX without measurements

## Day 4 - Build with traceability

Purpose:

- implement approved scope while preserving auditability

Required actions:

- [ ] Create feature branch
- [ ] Run Build Agent prompt
- [ ] Add tests for each acceptance criterion

Pass condition:

- Every criterion maps to a code or test change.

Common mistake:

- bundling unrelated changes in the same branch

## Day 5 - Prove correctness objectively

Purpose:

- replace subjective quality claims with machine evidence

Required actions:

- [ ] Run verification commands
- [ ] Capture outputs in issue comment
- [ ] Loop fixes until verification PASS

Pass condition:

- build, test, and lint or format checks pass with evidence logged.

Common mistake:

- retrying without documenting root cause and next action

## Day 6 - Validate real behavior

Purpose:

- verify user-facing outcomes and regression safety

Required actions:

- [ ] Complete QA checklist report
- [ ] Attach defects or PASS statement
- [ ] Prepare PR summary

Pass condition:

- QA decision is explicit and linked to scenarios.

Common mistake:

- using QA as a formality after tests already passed

## Day 7 - Close with evidence

Purpose:

- complete lifecycle with full traceability for future audits and learning

Required actions:

- [ ] Merge PR after approvals
- [ ] Post closure summary with evidence links
- [ ] Mark issue Done

Pass condition:

- closure comment links ESS, PR, verification evidence, and QA report.

Common mistake:

- closing issue immediately after merge without closure evidence

## Seven-day success definition

This launch is successful only if all are true:

1. no skipped gate
2. no missing closure evidence
3. no unresolved blocking defect at closure

If any item fails, rerun the failed day before moving forward.

## Next step

After day 7 succeeds, run 17 capstone rubric and identify the lowest-scoring category to improve next.
