# Module 00 - Shared App Foundation

## Goal

Set one fixed starter app for the full workshop and scaffold it in your repo with GitHub Copilot.

## Fixed starter app for everyone

Use this app for all modules in this workshop.

- App name: Team Equipment Checkout Tracker
- Problem: teams share a small set of devices (laptops, test phones, tablets) and need a simple way to check items out and return them
- Primary user: operations coordinator
- Core workflow: add item -> check out item -> return item -> view available items

This is intentionally not an AI app. It is a small, realistic operations tool with clear, testable behavior.

## Time Box

Target: 60 minutes

Suggested pacing:
- 10 min: align on starter app context
- 25 min: use Copilot to scaffold the project
- 10 min: run baseline verify commands
- 15 min: define scope boundaries and non-goals

## Why this matters

Without a shared app and code baseline, workshop work becomes abstract and inconsistent.

With one fixed app, everyone uses the same domain, same starting structure, and same backlog style. That makes Module 1 and Module 2 much easier to run and evaluate.

## What you will build

- one scaffolded starter project in your learner delivery repo
- one reusable Copilot context preface for this app
- one list of explicit non-goals and scope boundaries

## Required tasks

1. Use the fixed starter app context (do not choose a different app).
2. Use GitHub Copilot to scaffold the starter project in your repo.
3. Verify the baseline project builds and tests successfully.
4. Keep a short In Scope Now and Not In Scope Now boundary block for prompts.

## Stretch tasks

- Add two deferred feature candidates under `Not In Scope Now` so future modules can pick them up intentionally.

## Build exercise (step-by-step)

### Step 1 (10 minutes): set your reusable Copilot context preface

No new file is required.

Copy this text and keep it in a scratch note so you can paste it into Copilot before feature prompts:

```text
Project context for this workshop run:
- App: Team Equipment Checkout Tracker
- Primary user: operations coordinator
- Core workflow: add item -> check out item -> return item -> view available items
- Keep changes small and beginner-friendly
- Use .NET 10 classic MVC + xUnit tests
```

### Step 2 (25 minutes): use Copilot to scaffold the starter project

Open Copilot Chat in your learner delivery repo and paste this prompt:

```text
Scaffold a complete .NET 10 starter project for a "Team Equipment Checkout Tracker".

Requirements:
- Use a solution with two projects:
	- src/EquipmentTracker.Web (ASP.NET Core MVC)
	- tests/EquipmentTracker.Web.Tests (xUnit)
- Include a simple in-memory data store (no database).
- Use a classic MVC folder structure with separate files for:
	- Controllers
	- Models
	- ViewModels
	- Views
	- Services
- Add domain models:
	- EquipmentItem (Id, Name, Category, IsAvailable)
	- CheckoutRecord (Id, EquipmentItemId, BorrowerName, CheckedOutAtUtc, ReturnedAtUtc)
- Add MVC controllers and actions:
	- HomeController: Index
	- EquipmentController: Index (list), Create (GET/POST), Checkout (GET/POST), Return (POST)
- Add Razor views for:
	- equipment list with availability
	- create equipment form
	- checkout form
	- success and validation message display
- Enforce basic validation:
	- item name required
	- borrower name required for checkout
	- cannot checkout unavailable item
	- cannot return an item that is already available
- Seed 3 sample equipment items at startup.
- Add tests for:
	- creating an item through service logic
	- checkout success
	- checkout failure when unavailable
	- return success
	- return failure when already available
- Add a .gitignore for .NET/C#/ASP.NET Core MVC projects (bin/, obj/, .vs/, TestResults/, user-specific files).
- Add a README.md with exact commands to run restore, build, test, and run.

Constraints:
- Keep code simple and beginner-friendly.
- Keep everything in one repository.
- Do not add authentication, authorization, or database migration.
- Do not use minimal API style.
- Do not place application logic in Program.cs.

Output format:
- Return markdown only.
- Include a "File Tree" section with a fenced code block.
- Include a "Run Commands" section with a fenced `powershell` code block.
- Include a "Files Created" checklist.

When done, show a file tree and list the exact terminal commands I should run next.
```

Then apply the generated files, review them, and commit.

### Step 3 (10 minutes): run baseline verification

Run:

```powershell
dotnet restore
dotnet build --configuration Release
dotnet test --configuration Release
```

If any command fails, fix one root cause at a time, then rerun all three commands.

### Step 4 (15 minutes): lock scope boundaries

Copy this exact markdown and keep it with your prompt preface (scratch note is fine):

```markdown
## In Scope Now

These are allowed in this workshop run:

- MVC pages for equipment list, create, checkout, and return
- Controller actions for create, checkout, and return flows
- In-memory service logic with checkout and return rules
- Validation messages in forms (empty item name, empty borrower name)
- Basic tests for checkout and return rules

## Not In Scope Now

These are blocked for this workshop run:

- User login, auth, roles, or permissions
- Email, Slack, or push notifications
- Reporting dashboards or analytics views
- Database persistence, migrations, or cloud hosting
- SPA frameworks or mobile clients

## Scope Guardrails

Use these rules before you start any new issue:

1. A feature must fit in one pull request.
2. A feature must have testable pass/fail acceptance criteria.
3. If a feature touches auth, notifications, analytics, or persistence, move it to backlog as out-of-scope.
```

Use this block as your guardrail when writing issues and prompts. Keep boundaries unchanged for now.

## Micro checks

By minute 20 you should see your reusable prompt preface ready.
By minute 40 you should see scaffolded project files in place.
By minute 50 you should see restore/build/test passing.
By minute 60 you should see scope boundaries locked for prompts.

## You should see

One working starter app baseline plus a clear shared app context that carries into Module 1 and Module 2.

## If this fails, do this

If Copilot generates too much complexity, ask it to simplify and remove advanced patterns.
If tests fail, keep only one failing path in focus and fix that first.
If scope boundaries are unclear, tighten In Scope Now to only what you can verify in one small controller/view change.

## Definition of done

Module 0 is complete when all are true:

- starter app is scaffolded in the learner repo
- baseline restore/build/test commands pass
- in-scope and non-goal boundaries are explicit
- reusable prompt preface exists for Copilot prompts
- module scorecard is posted

## Module scorecard template

```markdown
## Module Scorecard
- Module: 00
- Completion time (minutes):
- Retry count by gate:
- Primary blocker cause:
- Evidence completeness (0-100%):
- Outcome: PASS | FAIL
```

## Next module

Continue to [01-module-1-tiny-end-to-end-run.md](01-module-1-tiny-end-to-end-run.md).