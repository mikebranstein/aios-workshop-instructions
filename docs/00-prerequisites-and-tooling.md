# 00 - Prerequisites and Tooling (Beginner Gate)

Use this file before you start 02-overview or 17-zero-to-hero-live-workshop.

If one required prerequisite fails, stop and fix it now.

Yes, your assumption is correct: this workshop requires both of these:

- one GitHub repository (where code and docs artifacts live)
- one GitHub Project (where workflow state is tracked)

## What this builds on

This file is your zero step. It prevents early failures caused by missing tools, permissions, or environment setup.

## Environment prerequisites

You need all of these:

- Windows 10 or 11
- VS Code installed
- Git installed
- GitHub account with access to your target repository
- GitHub Copilot entitlement enabled for your account
- .NET SDK installed (8.x preferred unless your repo requires another version)

## Step 1 - Verify local tools

Run these commands in PowerShell:

```powershell
git --version
code --version
dotnet --info
```

Pass condition:

- all three commands return version output without errors

If one fails:

- install or repair that tool before continuing

## Step 2 - Create or select workshop repository

If you already have a repository for this workshop, use it and continue.

If you do not have one yet:

1. In GitHub, click New repository.
2. Name it something like aios-workshop.
3. Keep it private or public based on your team policy.
4. Create repository.
5. Clone locally and open in VS Code.

```powershell
git clone <your-repo-url>
cd <your-repo-folder>
code .
```

Pass condition:

- you can open the repository locally in VS Code
- you can see this workshop docs structure in that repository

## Step 3 - Verify repository access

From repository root:

```powershell
git remote -v
git fetch origin
```

Pass condition:

- fetch succeeds with no authentication error

If it fails:

- re-authenticate with GitHub in VS Code or Git Credential Manager

## Step 4 - Verify Copilot in VS Code

1. Open VS Code Extensions view.
2. Confirm these are installed and enabled:
   - GitHub Copilot
   - GitHub Copilot Chat
3. Sign in when prompted.

Pass condition:

- Copilot Chat panel opens and accepts input

## Step 5 - Copilot chat quick test

Open Copilot Chat and send this prompt:

```text
Return valid JSON only with one key named status and value ready.
```

Expected output:

```json
{
  "status": "ready"
}
```

If output is markdown or prose:

Use retry prompt:

```text
Return raw JSON only. No markdown fence. No explanation.
```

## Step 6 - Create or verify GitHub Project shell

If your team already has a project board for this workshop, verify it and continue.

If not, create one now:

1. Open GitHub and go to your account or organization page.
2. Open Projects.
3. Click New project.
4. Choose Board layout.
5. Name it AIOS Delivery Board.
6. Create the project.

Now connect your repository for workshop tracking:

1. Open project settings.
2. Connect your workshop repository.
3. Enable auto-add workflow from connected repository issues.

Validation test:

1. Create one issue in your repository.
2. Add issue to project.
3. Confirm issue appears as a card on the project board.

Pass condition:

- you can create/edit project and see one real issue card on it

If permission denied:

- request project admin access before continuing

Custom field configuration is intentionally deferred to docs/05-github-as-state.md.
For click-by-click setup of those fields, run docs/14-github-projects-click-by-click.md after docs/05.

## Step 7 - Branch protection readiness

Apply or verify branch protection for main:

1. Open repository Settings.
2. Open Branches.
3. Add rule for main.
4. Enable:
  - Require a pull request before merging
  - Require status checks to pass before merging
  - Require conversation resolution before merging

If checks are not available yet, configure the rule now and return after CI is activated in workshop day 6.

Pass condition:

- branch rule exists for main and blocks direct push, or you have named admin owner who will apply it

If you cannot edit:

- identify approver/admin who will apply required rules in 17 step 1.3

## Step 8 - Run baseline verify script

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-windows.ps1
```

Pass condition:

- restore/build/test/format checks complete or fail with clear actionable output

If script file is missing:

- create it from scripts/verify-windows.ps1 template in this workshop

## Beginner gate checklist

You are ready only when all are true:

- [ ] git works
- [ ] dotnet works
- [ ] Copilot Chat works
- [ ] workshop repository exists and is accessible
- [ ] GitHub repo access works
- [ ] GitHub Project board exists and is connected to repository
- [ ] branch protection owner identified
- [ ] verify script runs

## Next step

Continue to 02-overview, then 03-foundations, then 17-zero-to-hero-live-workshop.