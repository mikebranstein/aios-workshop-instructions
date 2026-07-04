# Module 02 - Intake Quality Template

## Goal

Prevent incomplete work items from entering build flow.

## Time Box

- Target: 70 minutes

## Why this matters

High-quality intake reduces rework in every downstream step.

## Required tasks

1. Create or refine feature issue template.
2. Enforce required fields.
3. Create one valid issue with testable acceptance criteria.

## Stretch tasks

- Create one intentionally weak issue and mark it BLOCKED.

## Build exercise

Create or update `.github/ISSUE_TEMPLATE/feature.yml` with required fields:
- problem statement
- scope
- non-goals
- acceptance criteria
- test scenarios
- risk level

Then create one issue using the template and validate all required fields are present.

## Micro checks

- Minute 20: template renders.
- Minute 40: issue includes binary acceptance criteria.

## You should see

- one issue that passes intake quality review without clarifications.

## If this fails, do this

- rewrite acceptance criteria to explicit pass/fail statements.
- split broad requirements into smaller criteria.

## Definition of done

- template enforces required fields.
- one valid issue is ready for ESS authoring.

## Next module

Continue to [03-module-3-first-ess.md](03-module-3-first-ess.md).