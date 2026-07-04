# 00d - ESS Example Gallery (Good vs Weak)

Use this file when writing ESS in 07-ess-guide and 06-build-first-vertical-slice.

## How this builds on previous docs

06 teaches ESS rules. This file gives concrete examples so you can apply those rules in different feature types.

## ESS quality rubric (quick)

A strong acceptance criterion is:

- binary pass/fail
- testable with an explicit scenario
- tied to measurable behavior
- scoped to stated constraints

A weak acceptance criterion uses words like improve, optimize, better, intuitive, or robust without measurable checks.

## Example A - UI filter feature

Objective:

- When complete, support users can filter failed orders by status and date range within admin UI.

Good acceptance criteria:

- AC1: Given an admin user on Orders page, when status filter is set to Failed, only orders with status Failed are displayed.
- AC2: Given Failed status and date range 2026-07-01 to 2026-07-03, results include only Failed orders within that range.
- AC3: Given no matching records, UI shows No results found and no client-side error is thrown.

Weak acceptance criteria:

- Admin can filter failed orders quickly.
- Date range works better.

Why weak:

- no explicit expected output
- no bounded scenario
- no measurable pass/fail

## Example B - API idempotency feature

Objective:

- When complete, repeated submit requests with same idempotency key return same order id and do not create duplicates.

Good acceptance criteria:

- AC1: Given POST /orders with idempotency key K and valid payload P, first request returns 200 with order id O.
- AC2: Given second POST with same key K and payload P within 10 minutes, response returns 200 with same order id O and no new row is created.
- AC3: Given payload mismatch for same key K, API returns 409 with conflict message.

Weak acceptance criteria:

- Endpoint is retry safe.
- Duplicate submits should not happen.

## Example C - CI reliability fix

Objective:

- When complete, pull requests run deterministic verification workflow and block merge on failure.

Good acceptance criteria:

- AC1: On pull_request to main, workflow executes restore, build, test, format steps.
- AC2: If any step fails, workflow conclusion is failure and merge is blocked by required check.
- AC3: Test results artifact is uploaded for each run.

Weak acceptance criteria:

- CI should be more reliable.
- Checks are stricter.

## ESS authoring checklist

Before design gate PASS, confirm:

- [ ] objective states actor, action, expected result, constraints
- [ ] each AC has clear precondition and expected output
- [ ] verification commands are executable
- [ ] at least one failure path is covered
- [ ] rollback trigger and rollback steps are explicit

## Next step

Return to 07-ess-guide and write your ESS. Then validate with 18-live-lab-answer-keys.