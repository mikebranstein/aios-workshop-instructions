# Module 09 - Adding Verification: Intake → Design → Build → Verify

## Concept: Quality gates in the agentic OS

In Module 8, you built an orchestrator that routes work through intake, design, and build. Each stage made a decision and posted it to GitHub. But what happens after code is built? Who verifies that the implementation actually works?

Module 9 adds the next stage: **Verification**. This is where objective quality checks run automatically. Tests execute. Lint checks pass. The build passes. If all checks pass, the PR is approved. If any check fails, the issue returns to build for rework.

**What makes this different from design/build:** Verification is not a judgment call. It is automated, repeatable, objective. Either tests pass or they don't. Either lint is clean or it has errors. The verification agent's job is to run these checks and report the facts—not to interpret or negotiate.

## How this extends the pipeline

```
Issue Created
     ↓
[Intake Contract] → APPROVED
     ↓
[Design Contract] → PASS
     ↓
[Build Contract] → COMPLETE (PR created)
     ↓
[Verification Contract] → PASS (tests pass, lint clean, build successful)
     ↓
Ready for Merge
```

When verification passes, the PR is ready to be merged. When it fails, the failure report goes back to build with clear guidance on what went wrong.

## Time Box

- Target: 90 minutes

## Required tasks

1. Create the verification agent file in `.github/agents/`.
2. Extend the orchestrator to include verification routing and conflict handling.
3. Watch Features 1, 2, 3 flow from build → verification (already built from Module 8).
4. Create Feature 4 and watch it flow through the complete intake → design → build → verify pipeline.
5. Merge Feature 1's PR and observe Feature 2's verification detect integration conflicts.
6. Watch Feature 2 automatically re-route to design for re-evaluation with the new codebase changes.

---

## Step 1 (10 minutes): Set up verification labels in GitHub

Add two new labels for the verification stage:

```bash
gh label create "verification-passed"  --color "0e8a16" --description "Verification checks passed"
gh label create "verification-failed"  --color "e4e669" --description "Verification checks failed"
```

Or in GitHub UI:
1. Go to **Issues** → **Labels**
2. Create `verification-passed` (green `#0e8a16`)
3. Create `verification-failed` (yellow `#e4e669`)

These labels tell the orchestrator that a feature has passed (or failed) quality checks.

---

## Step 2 (15 minutes): Create the verification agent file

The verification agent is like the other specialists—it reads the PR, runs objective checks (tests, lint, build), and posts a decision.

Create the file `.github/agents/verification.agent.md`:

```bash
cp templates/agents/verification.agent.md .github/agents/verification.agent.md
```

**Or** if it doesn't exist yet, create it manually in VS Code. The agent will:
1. Read the PR created by build
2. Run test commands, lint checks, build validation
3. Post a decision: PASS or FAIL
4. Apply the appropriate label

---

## Step 3 (15 minutes): Extend the orchestrator to include verification and conflict handling

Update the orchestrator to route completed builds to verification, and to handle integration conflicts by re-routing to design:

```bash
cp templates/agents/orchestrator.v4.agent.md .github/agents/orchestrator.agent.md
```

**What v4 adds:**
- After `build-complete` label is applied, the next cycle routes the issue to verification
- Verification runs the checks on the PR
- If `verification-passed`: issue is done and ready for manual merge
- **If `verification-failed` with integration conflict:** issue returns to `design-approved` (keeps design label, removes build/verification labels) so design can be re-evaluated with the new codebase state
- **If `verification-failed` with test/lint failure:** issue returns to build for rework

**Depth-first routing remains:** The orchestrator still processes one issue at a time through all available stages before moving to the next.

---

## Step 4 (20 minutes): Phase 1 — Watch Features 1, 2, 3 verify

At the end of Module 8, Features 1, 2, and 3 are sitting in `build-complete` state with open PRs. They've been designed and built, but not yet verified.

Keep the orchestrator running (or restart it):

```bash
copilot --autopilot --allow-all-tools --enable-all-github-mcp-tools \
  -p "Start the agentic OS orchestrator. Run continuously."
```

**Watch the three features flow through verification in order:**
- Cycle N: Feature 1 routes to verification → runs checks
- Cycle N+1: Feature 1 verification decision posted (PASS or FAIL), Feature 2 routes to verification
- Cycle N+2: Feature 2 verification decision posted, Feature 3 routes to verification
- Cycle N+3: Feature 3 verification decision posted; all three features now have `verification-passed` or `verification-failed` labels

**On each issue, you should see:**
- Four decision comments: Intake, Design, Build, Verification
- Verification comment includes test/lint results in JSON details
- Labels: `intake-approved`, `design-approved`, `build-complete`, `verification-passed` (or failed)

---

## Step 5 (20 minutes): Phase 2 — Run Feature 4 through the complete pipeline

Once Features 1, 2, 3 are done verifying, create a 4th feature to see the complete pipeline from start to finish:

```bash
gh issue create --title "Feature 4: Add pagination to checkout history" \
  --body "Show checkout history for each item in a paginated list with 10 items per page."
```

**Watch Feature 4 flow through all four stages depth-first:**
- Cycle N: Feature 4 created, routes to intake
- Cycle N+1: intake decision posted, routes to design
- Cycle N+2: design decision posted, routes to build (creates PR)
- Cycle N+3: build decision posted, routes to verification
- Cycle N+4: verification decision posted, complete

Each stage decision will include the full JSON trail, so you can see how each agent inherited and responded to the previous stage's decision.

---

## Step 6 (15 minutes): Phase 3 — Merge Feature 1, trigger Feature 2 re-design on conflict

This step shows how the orchestrator handles integration conflicts.

**Manually merge Feature 1's PR:**

Go to GitHub UI or use:
```bash
gh pr merge PR_NUMBER --squash --delete-branch
```

When Feature 1 is merged, its code changes are now in `main`. This may conflict with Feature 2's open PR if both changed overlapping code.

**On the next orchestrator cycle:**
- Orchestrator re-checks Feature 2's open PR against the now-updated main branch
- Verification agent detects a merge conflict or integration failure
- Verification posts FAIL with root cause: `integration_conflict` or `merge_conflict`
- **Orchestrator routes Feature 2 back to design** (keeps `design-approved` label, removes `build-complete` and `verification-failed` labels)
- On the next cycle, design re-evaluates Feature 2 against the new codebase state and suggests adjustments
- Design posts updated decision, build executes new implementation, verification checks again

**You should see:**
- Feature 1: merged, complete
- Feature 2: re-enters design pipeline with a comment like "Re-designing due to integration conflict with Feature 1"
- Feature 2's labels: `intake-approved` → `design-approved` (returns from verification)
- Feature 2 will flow through design → build → verify again with the updated codebase

This is the key resilience pattern: **conflicts are not blockers, they're re-design opportunities.**

---

---

## Micro checks

- Minute 10: Two verification labels created (`verification-passed`, `verification-failed`).
- Minute 25: Verification agent file in `.github/agents/`.
- Minute 40: Orchestrator v4 deployed with conflict handling; Features 1, 2, 3 route to verification on next cycles.
- Minute 50: Feature 1 verification decision posted (PASS or FAIL).
- Minute 60: Feature 2 verification decision posted; Feature 3 routing to verification.
- Minute 70: Feature 3 verification decision posted; all three features checked.
- Minute 75: Feature 4 created; enters intake stage.
- Minute 90: Feature 4 complete through all stages (intake → design → build → verify).
- Minute 100: Feature 1 PR merged; Feature 2 detects integration conflict, re-routes to design.

## You should see

- `.github/agents/` now has five files (intake, design, build, verification, orchestrator)
- **Features 1, 2, 3:** All have `verification-passed` or `verification-failed` labels and four decision comments
- **Feature 4:** Complete pipeline with four decision comments and all labels (intake-approved → design-approved → build-complete → verification-passed)
- **Feature 2 (after Feature 1 merge):** Re-routed to design with label sequence: `intake-approved` → `design-approved` → (returns from verification) → design re-evaluates
- Verification decisions include test/lint results, or integration conflict details
- Orchestrator running continuously, advancing one issue one stage per 10-second cycle

## What you learned

- **Quality gates are objective, not judgment calls.** Verification runs automated checks (tests, lint, build). Pass or fail is binary.
- **Depth-first orchestration scales across stages.** The orchestrator queues features and advances them one stage per cycle through intake → design → build → verify.
- **Integration conflicts trigger re-design, not just rebuilds.** When Feature 2's PR conflicts with Feature 1's merged code, the orchestrator routes Feature 2 back to design so the design is re-evaluated against the new codebase state.
- **Failures are actionable and recoverable.** When verification detects a merge conflict, the decision includes the root cause, triggering the re-design flow automatically.
- **Contracts form a pipeline.** Each contract inherits the decisions of the previous stage and makes its own decision. Together, they form a complete workflow that handles both happy-path and conflict scenarios.
- **GitHub is the state store.** Labels, comments, and PR links tell the complete story. The orchestrator reads fresh state every cycle and routes accordingly. No separate database needed.
