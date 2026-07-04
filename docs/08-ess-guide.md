# 06 - ESS Guide (Executable System Spec, Full Walkthrough)

You asked for detailed guidance, so this module is intentionally literal.

If you complete this file step-by-step, you will produce one real ESS artifact you can execute with your agents.

## How this builds on earlier modules

This is where design discipline becomes concrete.

You move from idea quality rules in 01 and gate logic in 02 into one executable specification file agents can follow without guessing.

## Apply this immediately

Do not read this passively.

Create the ESS file while you read, fill each section in order, and keep criteria binary.

## First, what you meant by "essays"

I am treating "essays" as ESS, which stands for Executable System Spec.

If you meant something different, tell me and I will swap this module.

## Why ESS exists

The ESS is the contract between idea and delivery.

Without ESS:

- Build agent guesses scope.
- QA agent invents test scenarios.
- Closure happens without objective proof.

With ESS:

- Every agent works from the same source.
- Gates can be evaluated objectively.
- Rework drops because ambiguity drops.

## Create your first ESS now

### Step 1 - Create the file

Create this file:

- docs/ess-issue-001.md

Copy all content from templates/ess-feature.md into that file.

### Step 2 - Fill Metadata section

Use this example style:

```markdown
## 1) Metadata
- Work item ID: #123
- Title: Add retry-safe order submit endpoint
- Repo: my-org/my-repo
- Owner: Mike
- Risk level: Medium
- Target milestone: Sprint 14
```

Rule:

- If you do not know the risk level yet, set Medium and revisit after design.

### Step 3 - Fill Objective section

Use one sentence in this format:

"When complete, <user/persona> can <action> with <expected result> under <constraints>."

Example:

"When complete, checkout clients can submit orders idempotently and receive consistent order IDs under retry conditions."

### Step 4 - Fill Constraints section

List real constraints only. No fluff.

Example:

```markdown
## 3) Constraints
- Technical constraints: Must use existing OrdersService API; no database schema changes.
- Policy/security constraints: No PII in logs.
- Performance constraints: p95 endpoint latency must remain under 300ms.
```

### Step 5 - Write Acceptance Criteria correctly

Each criterion must be binary and testable.

Bad:

- "System should be robust."

Good:

- "Given duplicate request with same idempotency key within 10 minutes, API returns 200 and same order ID without creating a second row."

Target: 3-7 criteria.

### Step 6 - Write Implementation Plan

Break tasks so a Build Agent can execute without guessing.

Template:

```markdown
## 5) Implementation Plan
- Task 1: Add idempotency-key validation middleware in api/orders route.
- Task 2: Add service-level lookup for existing in-flight request key.
- Task 3: Add integration tests for duplicate submit behavior.
```

### Step 7 - Fill Verification Plan with real commands

This section must contain executable commands, not ideas.

Example:

```markdown
## 6) Verification Plan
- Build command: npm run build
- Test command: npm test -- orders
- Static checks: npm run lint
- Expected results: exit code 0, all tests pass, no lint errors.
```

### Step 8 - Fill QA Plan

Define at least:

- 1 happy path scenario
- 2 edge/failure scenarios
- regression scope list

### Step 9 - Fill Rollback Plan

You must be able to undo safely.

Example:

```markdown
## 8) Rollback Plan
- Trigger condition: Increased duplicate order failures or latency spike >20%.
- Rollback actions:
	1. Revert PR commit.
	2. Disable endpoint flag RETRY_SAFE_ORDER_SUBMIT.
	3. Re-run smoke tests.
```

### Step 10 - Add Closure Evidence after merge

This is the last thing you fill, not the first.

Add:

- PR URL
- CI/check URL
- QA report URL
- issue closure comment URL

## How agents consume ESS

Intake agent:

- validates required fields are present

Design agent:

- tightens constraints and risk analysis

Build agent:

- implements only in ESS scope

Verification agent:

- executes commands in ESS section 6

QA agent:

- runs ESS section 7 scenarios

Closure agent:

- checks section 9 links before marking done

## ESS review checklist before build starts

Do not begin coding until all are true:

1. Objective is one sentence and unambiguous.
2. Acceptance criteria are binary.
3. Verification commands are executable.
4. Rollback is realistic.
5. Risk level has at least one mitigation.

## Challenge: Try solo first

Challenge prompt:

Create an ESS for a feature in your current codebase that touches at least two modules and has one external dependency.

Expected difficulty: medium.

When done, self-check using this scoring:

- Clarity (0-5)
- Testability (0-5)
- Risk coverage (0-5)
- Rollback quality (0-5)

If total < 15, revise ESS before coding.

## Checkpoint and next step

You are done with this module when your ESS can pass Design Gate without manual reinterpretation.

Then continue with 05 step 4 or 14 live workshop design phase.
