# AIOS Workshop V2

This is the new workshop track built from the approved ground-up outline.

## Repo Topology

This workshop uses a two-repo default model, with an optional third repo.

1. Repo 1: Workshop Instructions Repo
- Purpose: workshop modules and templates.
- In this workspace: this repository and this docs folder.

2. Repo 2: Learner Delivery Repo
- Purpose: where learners create issues, implement code, run checks, and merge PRs.
- This is the primary execution surface during the workshop.

3. Repo 3: Framework Repo (optional)
- Purpose: package a reusable Agentic OS framework separate from project code.
- Not required for the workshop modules in this track.

Design intent:
- one fixed starter app baseline for all learners
- shared app context is set in Module 0
- build starts in Module 1
- every module has a concrete exercise
- every module creates a visible artifact
- every module has pass/fail checkpoint and recovery path

## How to run this track

1. Start at Module 00.
2. Complete modules in order.
3. Do not skip checkpoints.
4. Capture scorecard metrics at end of each module.

## Module index

1. [00-module-0-shared-app-foundation.md](00-module-0-shared-app-foundation.md)
2. [01-module-1-tiny-end-to-end-run.md](01-module-1-tiny-end-to-end-run.md)
3. [02-module-2-intake-quality-template.md](02-module-2-intake-quality-template.md)
4. [03-module-3-first-ess.md](03-module-3-first-ess.md)
5. [04-module-4-objective-gates.md](04-module-4-objective-gates.md)
6. [05-module-5-loop-safety-and-escalation.md](05-module-5-loop-safety-and-escalation.md)
7. [06-module-6-first-intake-skill-contract.md](06-module-6-first-intake-skill-contract.md)
8. [07-module-7-design-build-skill-contracts.md](07-module-7-design-build-skill-contracts.md)
9. [08-module-8-first-agentic-os-run.md](08-module-8-first-agentic-os-run.md)

## Modules 9-13 (being rebuilt)

The following modules are being rebuilt based on the new agentic OS architecture. Legacy versions are in `docs/legacy/` for reference.

- 09. Module 09 - GitHub State as Source of Truth (coming soon)
- 10. Module 10 - Add Verification to the Agentic OS (coming soon)
- 11. Module 11 - Add QA to the Agentic OS (coming soon)
- 12. Module 12 - Policy, Boundaries, and Approvals (coming soon)
- 13. Module 13 - Capstone: Full System Run with 2–3 Issues (coming soon)

## Scorecard template (copy into each issue comment)

```markdown
## Module Scorecard
- Module:
- Completion time (minutes):
- Retry count by gate:
- Primary blocker cause:
- Evidence completeness (0-100%):
- Outcome: PASS | FAIL
```
