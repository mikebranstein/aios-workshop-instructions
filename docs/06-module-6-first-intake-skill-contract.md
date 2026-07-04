# Module 06 - First Intake Skill Contract

## Goal

Produce deterministic machine-readable intake decisions.

## Time Box

- Target: 75 minutes

## Why this matters

Structured outputs make gate automation and auditability possible.

## Required tasks

1. Define intake skill schema.
2. Test on one READY and one BLOCKED issue.
3. Log decisions in issue history.

## Stretch tasks

- tune confidence threshold guidance.

## Build exercise

Create or update `templates/skills/intake-agent.md` with:
- mission
- required inputs
- JSON output schema
- guardrails
- escalation rule

Expected output keys:
- decision
- missing_fields
- questions
- next_state
- summary
- confidence

Run two tests and log output in issue comments.

## Micro checks

- Minute 25: contract drafted.
- Minute 50: both tests executed.

## You should see

- consistent JSON outputs and decisions aligned to issue quality.

## If this fails, do this

- validate JSON strictly and remove prose output.
- reduce optional fields until schema is stable.

## Definition of done

- two successful runs produce valid and consistent decision output.

## Next module

Continue to [07-module-7-design-build-skill-contracts.md](07-module-7-design-build-skill-contracts.md).