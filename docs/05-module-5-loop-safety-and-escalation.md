# Module 05 - Loop Safety and Escalation

## Goal

Prevent infinite retries and define clear blocked-state recovery.

## Time Box

- Target: 65 minutes

## Why this matters

Bounded retries protect time, quality, and team focus.

## Required tasks

1. Add loop safety rules.
2. Define escalation owners and SLA.
3. Simulate one failed gate and escalation.

## Stretch tasks

- Add escalation notification template with deadline tracking.

## Build exercise

Update `docs/state-machine.md` and `docs/escalation-runbook.md` with:
- max retries per gate = 3
- blocked state transition on third fail
- escalation owner map
- SLA and follow-up procedure

Simulate a failed verification gate and perform escalation steps.

## Micro checks

- Minute 20: retry rules are written.
- Minute 40: escalation simulation complete.

## You should see

- one documented blocked-state path that can be executed without ambiguity.

## If this fails, do this

- run a second simulation with a different gate and refine ownership.

## Definition of done

- retry and escalation policy is validated on at least one sample case.

## Next module

Continue to [06-module-6-first-intake-skill-contract.md](06-module-6-first-intake-skill-contract.md).