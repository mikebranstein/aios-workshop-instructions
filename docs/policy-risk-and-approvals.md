# Risk and Approval Policy

## Purpose

Define required gates and human approvals by risk level.

## Low Risk

- Required gates: Design, Verification
- Required human approvals: 1 PR reviewer
- QA gate: optional unless change affects shared core module

## Medium Risk

- Required gates: Design, Verification, QA
- Required human approvals: 1 design approver + 1 PR reviewer
- Merge rule: no bypass of required checks

## High Risk

- Required gates: Design, Verification, QA, Merge
- Required human approvals: 2 PR reviewers + rollback plan approval
- Additional rule: closure requires explicit sign-off comment

## Escalation

If disagreement on risk level:

1. Default to higher risk level.
2. Record decision in issue Decision Log.
3. Continue only after approver sign-off.
