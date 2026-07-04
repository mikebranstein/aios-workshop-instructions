# Module 08 - Verification and QA Evidence Loop

## Goal

Prove quality with repeatable machine and scenario evidence.

## Time Box

- Target: 85 minutes

## Why this matters

Verification and QA together reduce regressions and subjective release calls.

## Required tasks

1. Run verification commands.
2. Create QA report from checklist.
3. Iterate once on a failing case.
4. Run peer QA review on one scenario.

## Stretch tasks

- add one regression scenario beyond core acceptance criteria.

## Build exercise

Use `templates/skills/verification-agent.md` as your verification contract.

Run:

```powershell
dotnet restore
dotnet build --configuration Release
dotnet test --configuration Release --logger "trx;LogFileName=test-results.trx"
```

Then:
- post verification summary in issue
- copy `templates/qa-checklist.md` to `docs/qa-report-issue-001.md`
- execute QA scenarios and record outcomes

## Micro checks

- Minute 25: build/test evidence captured.
- Minute 55: first QA pass completed.

## You should see

- evidence-backed gate decisions that another learner can reproduce.

## If this fails, do this

- isolate first failing scenario and rerun that branch only.

## Definition of done

- verification and QA outcomes are reproducible from documented evidence.

## Next module

Continue to [09-module-9-github-state-source-of-truth.md](09-module-9-github-state-source-of-truth.md).