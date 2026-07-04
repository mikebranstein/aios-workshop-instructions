# Module 01 - Tiny End-to-End Run (Manual)

## Goal

Complete one tiny issue from creation to closure so you experience the full lifecycle immediately.

## Time Box

- Target: 75 minutes

## Why this matters

You learn the full flow first, then improve quality and automation in later modules.

## Required tasks

1. Run preflight checks.
2. Create one tiny feature issue.
3. Move it through Backlog -> Ready -> In Build -> In Verification -> Done.
4. Run build and test once.
5. Post closure comment with evidence links.

## Stretch tasks

- Run the same flow on a second tiny issue.

## Preflight environment gate (10 minutes)

Run:

```powershell
git --version
dotnet --info
code --version
```

Verify:
- repository access works (`git fetch origin`)
- one issue can be created and edited
- one project item can be updated

If one check fails, stop and fix before continuing.

## Policy preview (for awareness now)

- Low risk: standard checks and evidence required.
- Medium/High risk: human approval required before merge.
- Retry cap: 3 attempts per gate before escalation.

## Build exercise

1. Create a tiny issue (example: add one validation guard).
2. Add issue to project and set `State=Backlog`.
3. Run intake decision manually and move to `Ready`.
4. Implement smallest change in branch.
5. Run verification commands:

```powershell
dotnet restore
dotnet build --configuration Release
dotnet test --configuration Release
```

6. Post verification summary in issue.
7. Move to `Done` with closure summary.

## Micro checks

- Minute 15: issue exists and is in project.
- Minute 30: issue moved to Ready with decision note.
- Minute 50: build/test evidence posted.

## You should see

- one closed issue with links to code change and verification evidence.

## If this fails, do this

- reduce scope and retry with a smaller issue.
- fix only first failing gate before rerunning.

## Definition of done

- issue is closed with complete evidence links.
- module scorecard is posted.

## Next module

Continue to [02-module-2-intake-quality-template.md](02-module-2-intake-quality-template.md).