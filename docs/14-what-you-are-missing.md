# 12 - What You Are Missing (Diagnostic + Recovery Guide)

This file is the answer to the question most builders ask after first success:

Why does my AIOS work once, then degrade on real workloads

Short answer:

You are usually missing operating controls, not model intelligence.

This guide explains each missing control, why it matters, and exactly how to implement it.

## Before You Start

Use this file after you complete at least one issue run.

It turns "it worked once" into a repeatable system by revealing missing controls that only show up under repetition.

## Apply this now

Mark each control Present or Missing in your repo today, then fix the top missing item before adding any new automation.

## How to use this file

Run a quick self-audit:

1. read each control item
2. mark it Present or Missing in your current repo
3. implement missing items in priority order

If three or more core controls are missing, do not increase automation yet.

## Control 1 - Risk and approvals policy

What is missing:

- explicit mapping from risk level to required approvals

Why it matters:

- without this, teams either over-block low-risk work or under-review high-risk changes

How to add:

- maintain docs/policy-risk-and-approvals.md
- define gates and approvers for Low, Medium, High

Operational test:

- two reviewers can independently reach same approval requirement for a given issue

## Control 2 - Branch protection enforcement

What is missing:

- technical enforcement of merge requirements

Why it matters:

- process docs are advisory unless protected by repository rules

How to add:

1. Settings -> Branches -> Add rule for main
2. require PR before merge
3. require status checks
4. require conversation resolution

Operational test:

- direct push to main is blocked

## Control 3 - Machine-readable agent outputs

What is missing:

- decisions appear as narrative text instead of parseable data

Why it matters:

- automation and reliable handoffs require structured outputs

How to add:

- enforce JSON-only output schemas in skill files

Operational test:

- Intake, Design, and Verification outputs parse consistently

## Control 4 - Retry and escalation rules

What is missing:

- undefined behavior for repeated failures

Why it matters:

- uncapped loops consume time and hide unresolved blockers

How to add:

- in state machine, set max retries per gate to 3
- on third failure set State to Blocked and Owner Agent to Human Review

Operational test:

- no issue remains in repeating fail loops without escalation

## Control 5 - Evidence convention

What is missing:

- evidence scattered across comments and hard to audit

Why it matters:

- closure quality depends on traceable proof

How to add:

- enforce docs/evidence-convention.md
- require closure links to ESS, PR, verification, QA

Operational test:

- auditor can validate a closure in under two minutes

## Control 6 - Active CI enforcement

What is missing:

- CI template exists but not wired as required check

Why it matters:

- verification gate is weak without machine-enforced checks

How to add:

1. copy templates/workflows/ci-example.yml to .github/workflows/ci.yml
2. push workflow and confirm it runs on pull_request to main
3. mark CI check as required for merge

Operational test:

- PR cannot merge when CI fails

## Control 7 - Prompt and skill versioning

What is missing:

- behavior changes without traceability

Why it matters:

- output quality drifts and regressions become hard to diagnose

How to add:

- add a Version section to each skill file (example: 1.0 with date)
- include skill version in gate decision comments when behavior changes
- use explicit commit messages for behavior changes

Operational test:

- you can identify which skill change caused behavior change

## Control 8 - Postmortem loop

What is missing:

- failures are fixed but lessons are not institutionalized

Why it matters:

- same class of failure repeats across issues

How to add:

- run docs/postmortem-template.md for every blocked issue
- include preventive action that changes process, skills, or tests

Operational test:

- repeated blocker types trend downward over time

## Control 9 - AIOS definition of done

What is missing:

- no measurable standard for AIOS maturity

Why it matters:

- teams celebrate activity, not reliability

How to add:

- enforce docs/aios-definition-of-done.md with measurable criteria

Operational test:

- three consecutive issues meet full completion criteria

## Control 10 - Autonomy boundaries

What is missing:

- unclear division between auto-allowed and human-required actions

Why it matters:

- unsafe autonomy or unnecessary human bottlenecks

How to add:

- maintain docs/autonomy-boundaries.md with explicit allowed and restricted actions

Operational test:

- any team member can tell if an action requires approval without debate

## Implementation priority order

If time is limited, implement controls in this order:

1. branch protection enforcement
2. risk and approvals policy
3. active CI required checks
4. retry and escalation rules
5. evidence convention

## Checkpoint and next step

You are ready for broader automation only when critical controls are present and operational tests pass.

Then continue with 07 implementation blueprint Phase B.

These five controls create the minimum reliable operating core.

## 30-minute high-impact plan

If you only have half an hour today:

1. enable branch protection on main
2. verify CI check is required
3. ensure retry cap exists in state machine
4. confirm closure template requires all evidence links
5. run one issue through Intake and log Decision entry

Completing these gives immediate reliability gains even before full automation.
