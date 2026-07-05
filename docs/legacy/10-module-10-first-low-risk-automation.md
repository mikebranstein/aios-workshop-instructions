# Module 10 - First Low-Risk Automation

## Goal

Automate one repetitive action without bypassing policy controls.

## Time Box

- Target: 80 minutes

## Why this matters

Safe automation improves speed only when behavior is predictable.

## Required tasks

1. Create one workflow for state update or check summary.
2. Test one successful path.
3. Test one blocked/no-op path.

## Stretch tasks

- add idempotency guard to prevent duplicate updates.

## Build exercise

Create `.github/workflows/state-transition.yml` that triggers on a PR event.

Behavior options:
- post verification summary comment
- update state when required checks succeed

Must include:
- explicit no-op behavior for insufficient context
- explicit blocked behavior for policy violations

## Micro checks

- Minute 30: workflow committed.
- Minute 55: first event execution observed.

## You should see

- one successful automation and one safe blocked/no-op outcome.

## If this fails, do this

- disable auto-transition and keep summary-only mode until fixed.

## Definition of done

- workflow behaves predictably on at least two event paths.

## Next module

Continue to [11-module-11-policy-boundaries-and-approvals.md](11-module-11-policy-boundaries-and-approvals.md).