# Module 11 - Adding QA: Intake → Design → Build → Verify → QA

## Concept: The difference between automated checks and real-world testing

In Module 10, you added verification—an automated gate that runs tests, lint checks, and builds. Verification proves the code compiles and passes unit tests. But does it work in realistic user scenarios? Does it handle edge cases? Does it fail gracefully when things go wrong?

**Module 11 introduces QA as the final gate before release.** QA is manual, scenario-based testing. A person (or QA team) executes real-world workflows, documents results, and decides: "Is this ready for production?"

The key distinction:
- **Verification:** Automated. Deterministic. "Does it build and test?" Runs without human judgment.
- **QA:** Manual. Scenario-based. "Does it work in real workflows?" Includes human observation and edge case discovery.

Both are required. Verification catches regressions fast. QA catches what automation misses: usability issues, edge cases, real-world data patterns, integrations with other systems.

When a feature passes verification but fails QA, it routes back to build with specific failure scenarios—not for code quality, but for behavior rework. This creates a complete quality funnel.

## How this extends the pipeline

```
Issue Created
     ↓
[Intake Contract] → APPROVED
     ↓
[Design Contract] → PASS
     ↓
[Business Analyst] → CLARIFIED (if needed)
     ↓
[Build Contract] → COMPLETE (PR created)
     ↓
[Verification Contract] → PASS (tests pass, lint clean, build successful)
     ↓
[QA Contract] → PASS (scenarios pass, edge cases handled, real workflow tested)
     ↓
PR Approved & Merged to Main
```

When QA passes, the PR is ready for release. When it fails, the issue returns to build with specific scenario failure details so the developer can fix behavior, not just code structure.

## Time Box

- Target: 90 minutes

## Required tasks

1. Create the QA skill contract and agent.
2. Add two new labels for the QA stage.
3. Extend the orchestrator to include QA routing (creating v5.1).
4. Define QA scenarios for Feature 1 (from Module 10).
5. Manually execute QA scenarios and record results.
6. Route Feature 1 through the complete 5-stage pipeline: Intake → Design → Build → Verify → QA.
7. Observe QA pass and feature flow to release-ready state.

---

## Step 1 (5 minutes): Set up QA labels in GitHub

Add two new labels for the QA stage:

```bash
gh label create "qa-passed"  --color "0e8a16" --description "QA contract passed"
gh label create "qa-failed"  --color "e4e669" --description "QA contract failed"
```

Or in GitHub UI:
1. Go to **Issues** → **Labels**
2. Create `qa-passed` (green `#0e8a16`)
3. Create `qa-failed` (yellow `#e4e669`)

These labels mark the QA stage completion. When an issue reaches `qa-passed`, it is ready for release.

---

## Step 2 (10 minutes): Review the pre-built QA skill contract

The QA skill contract is already prepared for you in `templates/skills/qa-agent.md`. This contract defines what QA must verify before approving a feature. Unlike the automated verification agent, QA is manual—but the decision criteria are clear and consistent.

**What's included in the contract:**
- **Decision Framework:** Clear criteria for PASS (all scenarios pass, no regressions, error handling works) and BLOCK (any scenario fails, regressions detected, crashes or unclear errors)
- **Process:** How to read issues, extract scenarios, execute them, and record results
- **Scenarios to Always Verify:** Functional (happy path, failure path, edge cases), Regression checks, Non-functional (error handling, logging, performance)
- **Decision Output:** Both JSON-structured and human-readable formats

**To review the contract:**

```bash
cat templates/skills/qa-agent.md
```

Read through it and familiarize yourself with:
1. What scenarios you need to verify (happy path, failure path, edge case, integration)
2. What regression checks you must run
3. What the PASS/FAIL criteria are
4. What format your decision should be posted in

**Option A - Use the pre-built contract as-is**

Use it immediately in Step 3.

**Option B - Customize the contract with Copilot**

If you want to refine or customize the QA contract for your specific project needs, use this prompt:

```
You are helping me define a QA contract for a GitHub-native agentic workflow.

Context:
- My project is: [your project name]
- My app's critical flows are: [describe key user workflows]
- Common failure modes I want to catch: [e.g., data validation, race conditions, error messaging]
- My team's QA focus areas: [e.g., usability, performance, accessibility, reliability]

I have a base QA contract in templates/skills/qa-agent.md that I'd like to customize.

Please help me:
1. Identify the top 3 functional scenarios I should ALWAYS verify for any feature
2. Define what "regression checks" means for my specific project (what existing flows are critical?)
3. Suggest 2-3 non-functional checks beyond error handling (performance, logging, etc.)
4. Refine the PASS/FAIL criteria to match my project's quality bar

Then provide an updated contract that I can save back to templates/skills/qa-agent.md.
```

Fill in the bracketed sections with details about your project, then let Copilot help you customize the contract.

---

## Step 3 (5 minutes): Copy the pre-built QA agent

The QA agent is already prepared for you in `templates/agents/qa.agent.md`. Simply copy it to your repository:

```bash
cp templates/agents/qa.agent.md .github/agents/qa.agent.md
```

This agent will execute the QA skill contract you reviewed in Step 2. The agent is ready to use—no customization needed.

**What the agent does:**
- Reads issues that have passed verification
- Extracts QA scenarios and acceptance criteria
- **Checks out the PR branch** to work in the context of the built feature
- Executes scenarios manually or via automation
- Documents results (pass/fail, regressions, edge cases)
- Posts QA decision with JSON and human-readable summary
- Applies `qa-passed` or `qa-failed` labels

**Important:** The QA agent checks out and works in the feature branch context (the actual code being tested). This is the same branch used by the verification agent. QA ensures all scenario tests run against the built feature, not the main branch.

---

## Step 4 (20 minutes): Extend the orchestrator to include QA routing and auto-merge

Update your orchestrator agent file to include QA routing and final merge authorization.

Copy the orchestrator v6 file:

```bash
cp templates/agents/orchestrator.v6.agent.md .github/agents/orchestrator.agent.md
```

This extends the pipeline from v5 (intake → BA → design → build → verification) to v6 (intake → BA → design → build → verification → QA).

**What v6 adds:**

- After `verification-passed` label is applied, the next cycle routes the issue to QA for manual scenario testing
- QA executes scenarios and posts a PASS/FAIL decision
- If `qa-passed`: the QA agent **automatically merges the PR to main** and deletes the feature branch (final gate before merge)
- If `qa-failed`: issue returns to build stage for behavior rework based on specific scenario failures

**Routing table update:**
- New routing: `verification-passed` (no qa label) → Spawn QA
- New routing: `qa-failed` → Remove build-complete, keep design-approved, route back to build
- New terminal state: `qa-passed` → Done (PR auto-merged by QA)

**Key distinction from v5:**
- **v5 (Module 10):** Verification checks code quality, does NOT merge. Routes to QA.
- **v6 (Module 11):** QA checks scenarios, and DOES merge on PASS. This is the final release gate.

The orchestrator now enforces the complete quality funnel: automated checks (verification) → manual testing (QA) → merge to production (main branch).

**If qa-failed label is present:**
a) Read the QA decision comment to understand which scenarios failed
b) Keep verification-passed and design-approved labels
c) Remove build-complete label (revert to build stage for behavior rework)
d) Post comment: "QA found scenario failures. Re-routing to build for behavior rework."
e) Spawn build: `task(description="Fix QA failures on issue #N", agent_id="build")`

**If qa-passed label is present:**
a) Skip to next issue (done and approved for release)
```

---

## Step 5 (10 minutes): Define QA scenarios for your feature

Take the feature you're testing (Feature 1 from Module 10, or any feature that passed verification). Define QA scenarios for it.

In the issue, create a new comment with QA scenarios. Use this template structure (customize with your actual feature details):

```markdown
## QA Scenarios for #N: [Feature Title]

### Scenario 1: Happy Path - [Core Success Workflow]
- **Precondition:** [Initial state before executing the feature]
- **Steps:**
  1. [Action 1]
  2. [Action 2]
  3. [Action 3]
- **Expected Result:** [Feature works as specified]
- **Actual Result:** [Record after testing]

### Scenario 2: Failure Path - [Constraint Violation]
- **Precondition:** [Initial state with constraint that would be violated]
- **Steps:**
  1. [Attempt action that violates constraint]
  2. [Observe system response]
- **Expected Result:** [System shows clear error and recovers gracefully]
- **Actual Result:** [Record after testing]

### Scenario 3: Edge Case - [Boundary or Race Condition]
- **Precondition:** [Edge case state]
- **Steps:**
  1. [Execute edge case scenario]
  2. [Observe behavior]
- **Expected Result:** [Feature handles edge case gracefully]
- **Actual Result:** [Record after testing]

### Scenario 4: Regression Check - [Critical Existing Workflow A]
- **Precondition:** [Setup for workflow A]
- **Steps:**
  1. [Execute workflow A]
- **Expected Result:** [Workflow A still works as before]
- **Actual Result:** [Record after testing]

### Scenario 5: Regression Check - [Critical Existing Workflow B]
- **Precondition:** [Setup for workflow B]
- **Steps:**
  1. [Execute workflow B]
- **Expected Result:** [Workflow B still works as before]
- **Actual Result:** [Record after testing]

## Execution Environment
- Test environment: [localhost, staging, etc.]
- Build version: Commit [hash from verification result]
- Tested by: [Your name]
- Date: [Today]
```

---

## Step 6 (20 minutes): Run QA and record results

### Option A: Automated QA (Playwright or similar)

If you have automated UI tests, run them against the built feature:

```bash
npm test -- --testNamePattern="QA.*Scenario"
```

Capture output and post as evidence.

### Option B: Manual QA

Deploy the built feature to a test environment and manually execute each scenario:

1. Check out the PR branch from Module 10
2. Start the app locally (or deploy to test environment)
3. Walk through each scenario you defined (happy path, failure path, edge cases, regressions)
4. For each scenario, document:
   - What you did
   - What you expected
   - What actually happened
   - Pass/Fail
   - Any observations or defects

---

## Step 7 (10 minutes): Post QA decision

Once you've executed all scenarios, post a QA decision comment on the issue. Use this template structure:

```markdown
## QA Decision

**Status:** PASS or FAIL

**Summary:** [One sentence: all scenarios passed and ready for release, or specific failures blocking release]

**Scenarios Tested:** [Number of scenarios]
- [Scenario 1 name]: ✅ PASS or ❌ FAIL [brief result]
- [Scenario 2 name]: ✅ PASS or ❌ FAIL [brief result]
- [Scenario 3 name]: ✅ PASS or ❌ FAIL [brief result]
- [Regression 1 name]: ✅ PASS or ❌ FAIL [brief result]
- [Regression 2 name]: ✅ PASS or ❌ FAIL [brief result]

**Regressions:** None detected, or [list of impacted workflows]

**Recommendation:** Feature is ready for release, or [list of issues blocking release]

**JSON Decision:**
```json
{
  "contract": "QA",
  "decision": "PASS or FAIL",
  "qa_date": "[today's date]",
  "tester": "[Your Name]",
  "environment": "[test environment]",
  "scenarios_passed": [count],
  "scenarios_failed": [count],
  "regressions_found": "none | [list]",
  "blockers": "none | [specific blockers]",
  "recommendations": "[any notes for next steps]"
}
```
```

---

## Step 8 (10 minutes): Watch the orchestrator advance Feature 1 to release-ready

Once you've posted the QA decision with `qa-passed` label, the orchestrator will:
1. Detect `qa-passed` label on the next cycle
2. Skip the issue (it's done and approved for release)
3. Move on to the next issue

### Watch the orchestrator output:

```
--- Orchestrator Cycle Summary (Cycle N) ---
Model: [your active model]
Issue focused on: #1 [Feature Title] -> QA PASSED
Issues ready for release: 1
Issues in pipeline: 0

--- Next Cycle ---
Checking issue #1: [Feature Title]
  Labels: intake-approved, design-approved, build-complete, verification-passed, qa-passed
  -> Action: COMPLETE. Ready for release.

Checking issue #2: [Next Feature]
  Labels: [no pipeline labels]
  -> Action: Route to intake.
```

---

## Step 9 (10 minutes): Verify the full 5-stage pipeline

Create or find a second feature (Feature 2 or Feature 3 from Module 10). Let it flow through the complete pipeline:

1. **Intake** validates requirements ✓
2. **Design** approves architecture ✓
3. **Build** creates PR ✓
4. **Verification** tests code ✓
5. **QA** validates scenarios ✓

Watch the issue labels advance: intake-approved → design-approved → build-complete → verification-passed → qa-passed.

### Micro-check: Run through at least two features (Feature 1 and Feature 2)

- Feature 1 should reach `qa-passed` and show clear QA decision comments
- Feature 2 should follow the same pattern and reach `qa-passed` (or `qa-failed` if you want to test the failure path)

---

## Step 10 (Optional - 15 minutes): Test a QA failure and recovery

To see the rework flow, deliberately create a feature or scenario that will fail QA:

1. Run a feature through intake → design → build → verification
2. When running QA, introduce a failure: mark one scenario as failing (e.g., "User workflow did not complete as expected" or "Error message was unclear")
3. Post a `qa-failed` comment with specific failure details
4. Apply `qa-failed` label
5. The orchestrator will:
   - Detect `qa-failed` on the next cycle
   - Remove `build-complete` label (route back to build stage)
   - Route back to build for behavior rework
   - Build will fix the issue and create a new PR
   - On the next cycle, verification will run again
   - On the next cycle after that, QA will run again
   - If it passes, feature advances to release-ready

This demonstrates the full loop: QA finds an issue → developer fixes → verification re-validates → QA re-validates → release.

---

## Definition of Done

✅ You have successfully completed Module 11 when:

1. **QA skill contract created** (`templates/skills/qa-agent.md`)
   - Contract clearly defines decision criteria (PASS/FAIL)
   - Includes scenario execution process
   - Decision output structure defined

2. **QA agent created** (`.github/agents/qa.agent.md`)
   - Agent can read issues and scenario definitions
   - Agent executes scenarios (manual or automated)
   - Agent posts structured decision comments

3. **Orchestrator extended to include QA** (`.github/agents/orchestrator.agent.md`)
   - Routing table includes QA stage
   - Orchestrator routes verification-passed to QA
   - Orchestrator handles qa-passed (done) and qa-failed (back to build)

4. **QA labels created and applied** in GitHub
   - `qa-passed` and `qa-failed` labels exist
   - At least one feature has `qa-passed` label
   - QA decision comments are visible on issues

5. **Full 5-stage pipeline validated** by running at least 2 features through:
   - Intake → Design → Build → Verification → QA
   - Each stage shows clear decision comments
   - Labels advance correctly
   - Orchestrator maintains steady rhythm

6. **QA scenarios documented and tested** for at least one feature:
   - Scenarios cover happy path, failure path, and edge cases
   - Regression checks included
   - Results documented (pass/fail, observations)
   - Decision is traceable in issue comments

7. **Optional: QA failure and recovery tested**
   - At least one feature marked `qa-failed`
   - Orchestrator routes back to build
   - Build creates new PR
   - QA re-validates on next cycle

## Stretch Goals

- Automate QA scenarios using Playwright or similar UI automation tool
- Create a QA dashboard showing pass/fail rates by feature
- Add performance benchmarking to QA (compare build time, response time to baseline)
- Run 3 features through the full 5-stage pipeline
- Test both success and failure paths for QA gate

---

## Key Takeaways

- **Verification is automated; QA is manual.** Verification catches code quality issues. QA catches behavior issues and edge cases.
- **QA is a decision gate.** Issues don't merge until QA approves. Failures route back to build with specific scenario details.
- **The full pipeline is now: Intake → Design → Build → Verification → QA.** Each stage adds a layer of quality confidence.
- **Main branch is authoritative.** Every PR rebases onto current main before verification and QA. Features integrate safely because they test against the latest code.
- **State is traceable.** All decisions (intake, design, build, verification, QA) are posted as comments. Anyone can read the full history and understand why a feature was approved or rejected.

