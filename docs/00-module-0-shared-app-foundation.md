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

Target: 65 minutes

Suggested pacing:
- 10 min: align on starter app context
- 25 min: use Copilot to scaffold the project
- 10 min: run baseline verify commands
- 15 min: define scope boundaries and non-goals
- 5 min: run foundation quality check and capture scorecard

## Why this matters

Without a shared app and code baseline, workshop work becomes abstract and inconsistent.

With one fixed app, everyone uses the same domain, same starting structure, and same backlog style. That makes Module 1 and Module 2 much easier to run and evaluate.

## What you will build

- one scaffolded starter project in your learner delivery repo
- one app foundation note with mission, persona, and workflow
- one list of explicit non-goals and scope boundaries
- one foundation quality-check comment in your tracker

## Required tasks

1. Use the fixed starter app context (do not choose a different app).
2. Use GitHub Copilot to scaffold the starter project in your repo.
3. Verify the baseline project builds and tests successfully.
4. Document scope boundaries and non-goals.
5. Complete the Module 0 handoff gate before entering Module 1.

## Stretch tasks

- Add two deferred feature candidates under `Not In Scope Now` so future modules can pick them up intentionally.

## Build exercise (step-by-step)

### Step 1 (10 minutes): create your app foundation note

In your learner delivery repo, create `docs/app-foundation.md` with this starter content:

```markdown
# App Foundation

## App
Team Equipment Checkout Tracker

## Mission
Provide a simple way for a team to check out and return shared equipment with clear availability status.

## Primary User
Operations coordinator

## Primary Pain Point
Team members do not know what equipment is currently available or who has each item.

## North-Star Workflow
1. Coordinator adds equipment item.
2. Team member requests equipment.
3. Coordinator checks out item to team member.
4. System marks item as unavailable.
5. Team member returns item.
6. Coordinator marks return complete.
7. System marks item as available.
```

### Step 2 (25 minutes): use Copilot to scaffold the starter project

Open Copilot Chat in your learner delivery repo and paste this prompt:

```text
Scaffold a complete .NET 8 starter project for a "Team Equipment Checkout Tracker".

Requirements:
- Use a solution with two projects:
	- src/EquipmentTracker.Api (ASP.NET Core Web API)
	- tests/EquipmentTracker.Api.Tests (xUnit)
- Include a simple in-memory data store (no database).
- Add domain models:
	- EquipmentItem (Id, Name, Category, IsAvailable)
	- CheckoutRecord (Id, EquipmentItemId, BorrowerName, CheckedOutAtUtc, ReturnedAtUtc)
- Add API endpoints:
	- GET /health
	- GET /api/items
	- POST /api/items
	- POST /api/items/{id}/checkout
	- POST /api/items/{id}/return
- Enforce basic validation:
	- item name required
	- borrower name required for checkout
	- cannot checkout unavailable item
	- cannot return an item that is already available
- Seed 3 sample equipment items at startup.
- Add tests for:
	- creating an item
	- checkout success
	- checkout failure when unavailable
	- return success
	- return failure when already available
- Add a README.md with exact commands to run restore, build, test, and run.

Constraints:
- Keep code simple and beginner-friendly.
- Keep everything in one repository.
- Do not add authentication, authorization, or database migration.

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

Append this exact markdown to `docs/app-foundation.md`:

```markdown
## In Scope Now

These are allowed in this workshop run:

- CRUD-lite for equipment items (create and list only)
- Checkout flow with borrower name and timestamp
- Return flow that flips availability back to true
- Validation errors for bad requests (empty item name, empty borrower name)
- Basic API tests for checkout and return rules

## Not In Scope Now

These are blocked for this workshop run:

- User login, auth, roles, or permissions
- Email, Slack, or push notifications
- Reporting dashboards or analytics views
- Database persistence, migrations, or cloud hosting
- UI front-end (web/mobile) beyond API responses

## Scope Guardrails

Use these rules before you start any new issue:

1. A feature must fit in one pull request.
2. A feature must have testable pass/fail acceptance criteria.
3. If a feature touches auth, notifications, analytics, or persistence, move it to backlog as out-of-scope.
```

After pasting it, replace only the wording if your repo naming differs. Keep the boundaries unchanged.

### Step 5 (5 minutes): foundation handoff gate

Purpose of this step:
This is a stop/go checkpoint that proves your baseline is stable before Module 1 creates the first feature issue. It prevents Module 1 from being used to debug setup mistakes.

Post one comment titled `Module 00 Foundation Check` using this exact markdown:

```markdown
## Module 00 Foundation Check
- Starter app scaffolded: Yes | No
- Restore/build/test passing: Yes | No
- App workflow documented: Yes | No
- In Scope Now and Not In Scope Now completed: Yes | No
- Ready for Module 1: Yes | No
- Module 1 starter issue created yet: Yes | No (expected: No)

### Evidence
- Commit or branch link:
- Build/test output summary:
- Notes on any remaining gaps:
```

If any answer is no, fix that section before moving on.

## Micro checks

By minute 20 you should see `docs/app-foundation.md` created.
By minute 40 you should see scaffolded project files in place.
By minute 50 you should see restore/build/test passing.
By minute 65 you should see the foundation check posted.

## You should see

One working starter app baseline plus a clear app foundation that carries into Module 1 and Module 2.

## If this fails, do this

If Copilot generates too much complexity, ask it to simplify and remove advanced patterns.
If tests fail, keep only one failing path in focus and fix that first.
If scope boundaries are unclear, tighten In Scope Now to only what you can verify in one small API change.

## Definition of done

Module 0 is complete when all are true:

- starter app is scaffolded in the learner repo
- baseline restore/build/test commands pass
- app mission and workflow are documented
- in-scope and non-goal boundaries are explicit
- foundation check comment is posted
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