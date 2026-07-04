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
- build starts in Module 1
- every module has a concrete exercise
- every module creates a visible artifact
- every module has pass/fail checkpoint and recovery path

## How to run this track

1. Start at Module 01.
2. Complete modules in order.
3. Do not skip checkpoints.
4. Capture scorecard metrics at end of each module.

## Module index

1. [01-module-1-tiny-end-to-end-run.md](01-module-1-tiny-end-to-end-run.md)
2. [02-module-2-intake-quality-template.md](02-module-2-intake-quality-template.md)
3. [03-module-3-first-ess.md](03-module-3-first-ess.md)
4. [04-module-4-objective-gates.md](04-module-4-objective-gates.md)
5. [05-module-5-loop-safety-and-escalation.md](05-module-5-loop-safety-and-escalation.md)
6. [06-module-6-first-intake-skill-contract.md](06-module-6-first-intake-skill-contract.md)
7. [07-module-7-design-build-skill-contracts.md](07-module-7-design-build-skill-contracts.md)
8. [08-module-8-verification-qa-evidence-loop.md](08-module-8-verification-qa-evidence-loop.md)
9. [09-module-9-github-state-source-of-truth.md](09-module-9-github-state-source-of-truth.md)
10. [10-module-10-first-low-risk-automation.md](10-module-10-first-low-risk-automation.md)
11. [11-module-11-policy-boundaries-and-approvals.md](11-module-11-policy-boundaries-and-approvals.md)
12. [12-module-12-capstone-two-issue-run.md](12-module-12-capstone-two-issue-run.md)

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
