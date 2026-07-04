# 12 - .NET Command Pack (Operational Edition)

This file is your single source for .NET verification commands in local runs, gate checks, and CI workflows.

Use these commands consistently so your gate decisions are reproducible.

## Before You Start

You already defined gates in 02 and state transitions in 03.

This file gives the exact machine checks that make Verification Gate objective instead of opinion-based.

## Apply this now

Create scripts/verify.ps1 from section 6 and run it once on your current branch before you continue.

If it fails, stop and fix root causes before proceeding.

## Checkpoint before Verification Gate

Your verification run is ready only when restore, build, test, and format checks all pass and evidence is posted.

## 1) Command strategy

Your verification sequence should answer three questions in order:

1. Can dependencies resolve
2. Can the code compile
3. Does behavior pass tests and style checks

That is why the default order is restore -> build -> test -> format or lint.

## 2) Environment preflight

Run from repository root:

```powershell
dotnet --info
```

Expected result:

- SDK information is printed
- target runtime line is visible

If this fails, stop and install the SDK before continuing.

Optional preflight for multi-solution repositories:

```powershell
dotnet sln list
```

Use this to confirm the solution includes expected projects.

## 3) Baseline verification command set

Run in this exact order:

```powershell
dotnet restore
dotnet build --configuration Release
dotnet test --configuration Release --logger "trx;LogFileName=test-results.trx"
dotnet format --verify-no-changes
```

Why this order:

- restore failure means no point building
- build failure means tests are not trustworthy yet
- test failure means behavior is incorrect
- format failure means quality bar is unmet

## 4) Fallback command set when formatting is not yet configured

Use this temporary substitute:

```powershell
dotnet build --configuration Release /warnaserror
```

This is not equivalent to formatting, but it enforces stricter compile hygiene while you bootstrap.

## 5) Coverage command option

If your test setup supports coverage collection:

```powershell
dotnet test --configuration Release --collect:"XPlat Code Coverage"
```

Use coverage for trend monitoring, not as the only quality metric.

## 6) Repeatable local verify script

Create scripts/verify.ps1:

```powershell
$ErrorActionPreference = "Stop"

Write-Host "[1/4] Restore"
dotnet restore

Write-Host "[2/4] Build"
dotnet build --configuration Release

Write-Host "[3/4] Test"
dotnet test --configuration Release --logger "trx;LogFileName=test-results.trx"

Write-Host "[4/4] Format Check"
dotnet format --verify-no-changes

Write-Host "Verification PASS"
```

Run script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

## 7) Verification evidence standard

Post this exact template in issue comments after each verification run:

```markdown
## Verification Summary
- Restore: PASS/FAIL
- Build: PASS/FAIL
- Test: PASS/FAIL
- Format/Lint: PASS/FAIL
- Command set used:
	dotnet restore
	dotnet build --configuration Release
	dotnet test --configuration Release --logger "trx;LogFileName=test-results.trx"
	dotnet format --verify-no-changes
- Root cause (if fail):
- Next action:
```

Do not mark Verification Gate as PASS without this evidence block.

## 8) Failure triage playbook

Restore failure:

- run dotnet nuget list source
- verify private feed credentials and network access

Build failure:

- fix compile errors first
- do not run repeated test loops until build is green

Test failure:

- classify failure by category:
	- deterministic functional
	- flaky timing or environment
	- wrong test expectation

Format failure:

- run dotnet format once
- commit formatting separately if large
- rerun full verification

## 9) CI command baseline

Minimum CI steps:

1. dotnet restore
2. dotnet build --configuration Release
3. dotnet test --configuration Release --logger "trx;LogFileName=test-results.trx"
4. dotnet format --verify-no-changes

If step 4 is too noisy initially, use temporary warn-as-error fallback and schedule format adoption.

## 10) Gate decision rule

Verification Gate is PASS only when all required commands pass and evidence is posted.

If one command fails, the gate is FAIL and state must return to In Build.

Explicit pass criteria:

- PASS = restore/build/test/format all exit code 0 AND evidence block is posted.

Explicit fail criteria:

- FAIL = any required command exits non-zero.
- FAIL = flaky test reproduced in 2 or more runs during same gate attempt.

When flaky behavior is detected:

1. mark Test as FAIL
2. add root cause hypothesis in issue
3. return to In Build and fix determinism before reattempt

## Next step

Continue to docs/13-github-projects-click-by-click.md.
