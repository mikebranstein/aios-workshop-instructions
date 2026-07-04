# Module 11 - Policy Boundaries and Approvals

## Goal

Enforce risk-based human approvals while preserving delivery flow.

## Time Box

- Target: 75 minutes

## Why this matters

Policy boundaries prevent unsafe merges and preserve trust in automation.

## Note

Policy boundaries were introduced in Module 01 and are fully enforced here.

## Required tasks

1. Configure branch protections.
2. Define approval requirements by risk.
3. Test medium/high-risk merge path.

## Stretch tasks

- add emergency hotfix exception template with approval logging.

## Build exercise

In repository settings:
- require PR before merge
- require status checks
- require review approvals
- require conversation resolution

In `docs/policy-risk-and-approvals.md`:
- map risk level to required approvers
- document exception process

Run one simulated medium/high-risk path and verify merge is blocked without required approvals.

## Micro checks

- Minute 25: branch protections verified.
- Minute 50: approval path tested.

## You should see

- risky changes cannot merge without required human approval.

## If this fails, do this

- tighten branch rules and rerun merge simulation.

## Definition of done

- unauthorized merge attempts are blocked and auditable.

## Next module

Continue to [12-module-12-capstone-two-issue-run.md](12-module-12-capstone-two-issue-run.md).