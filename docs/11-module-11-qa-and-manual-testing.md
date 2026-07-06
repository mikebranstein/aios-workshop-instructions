# Module 11 - Adding QA: Intake → Design → Build → Verify → QA

## Concept: Two layers of automated quality gates

In Module 10, you added verification—automated checks for build success and unit test pass. Verification proves the code compiles and unit tests pass. But does the implementation actually satisfy the acceptance criteria? Are edge cases and regressions covered by automated tests?

**Module 11 introduces QA as the comprehensive automated test layer.** QA runs the full test suite created during Build—covering acceptance criteria, edge cases, failure paths, and regressions. The orchestrator only advances a feature to release if both verification and QA test suites pass completely.

The key distinction:
- **Verification:** Runs unit tests, lint, and build checks. Confirms the code is structurally sound.
- **QA:** Runs the comprehensive UI/integration test suite. Confirms the implementation matches acceptance criteria, handles edge cases, and maintains regressions.

Both layers are automated and deterministic. Together they create a complete quality funnel: structural checks (verification) → comprehensive functional tests (QA) → release.

If QA fails, it means the test suite (created during Build) is not passing, indicating either:
- Incomplete test coverage during Build stage
- Implementation doesn't satisfy acceptance criteria

Either way, the issue routes back to Build for rework. QA's job is to execute the test suite, not to work around missing tests.

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
[Build Contract] → COMPLETE (PR created, comprehensive test suite created)
     ↓
[Verification Contract] → PASS (unit tests pass, lint clean, build successful)
     ↓
[QA Contract] → PASS (comprehensive test suite passes, acceptance criteria met)
     ↓
PR Approved & Merged to Main
```

When QA passes, the PR is ready for release. When it fails, the issue returns to build to fix either test coverage gaps or implementation gaps.

## Time Box

- Target: 75 minutes

## Required tasks

1. Create the QA skill contract and agent.
2. Add two new labels for the QA stage.
3. Extend the orchestrator to include QA routing (v6).
4. Route Feature 1 through the complete 6-stage pipeline: Intake → Design → Build → Verify → QA → Release.
5. Observe QA execute the automated test suite and advance the feature to release-ready state.
6. Verify the full pipeline with a second feature.

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

The QA skill contract is already prepared for you in `templates/skills/qa-agent.md`. This contract defines what QA must verify before approving a feature for release. Like verification, QA is fully automated—it executes the comprehensive test suite created during Build.

**What's included in the contract:**
- **Decision Framework:** Clear criteria for PASS (all tests pass, no regressions, no crashes) and FAIL (any test fails, indicating coverage gaps or implementation issues)
- **Process:** How to read issues, extract test command from build decision, execute the test suite, and record results
- **Output:** Both JSON-structured and human-readable formats showing test counts and results

**To review the contract:**

```bash
cat templates/skills/qa-agent.md
```

Read through it and familiarize yourself with:
1. What test scenarios must be automated (happy path, failure path, edge case, integration)
2. What regression checks must be automated and included in the test suite
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
- Extracts the test command from the build decision
- **Checks out the PR branch** to work in the context of the built feature
- Executes the automated test suite
- Documents test results (pass/fail, test counts)
- Posts QA decision with JSON and human-readable summary
- Applies `qa-passed` or `qa-failed` labels

**Important:** The QA agent checks out and works in the feature branch context (the actual code being tested). All tests run against the built feature, not the main branch.

---

## Step 4 (5 minutes): Extend the orchestrator to include QA routing

Update your orchestrator agent file to include QA routing and final merge authorization.

Copy the orchestrator v6 file:

```bash
cp templates/agents/orchestrator.v6.agent.md .github/agents/orchestrator.agent.md
```

**What v6 adds:**
- Routes issues from `verification-passed` to QA for test suite execution
- If QA passes: automatically merges the PR to main (final release gate)
- If QA fails: routes back to build for rework

**Key distinction from v5:**
- **v5 (Module 10):** Verification checks code quality and doesn't merge. Routes to QA.
- **v6 (Module 11):** QA runs comprehensive tests and auto-merges on PASS. This is the final release gate.

---

## Step 5 (5 minutes): Verify Feature 1 is in verification-passed state

Confirm that Feature 1 from Module 10 has passed verification (has the `verification-passed` label). If it does, it's ready for QA. If not, run verification first (see Module 10).

---

## Step 6 (5 minutes): Start the orchestrator and watch the QA agent run

With Feature 1 ready for QA (verified and passed verification), start the orchestrator:

```bash
# Start the orchestrator in a terminal
node orchestrator.js
# or your language equivalent
```

**What will happen on the next cycle:**

1. Orchestrator detects Feature 1 has `verification-passed` label
2. Orchestrator spawns the QA agent
3. QA agent:
   - Reads the issue and extracts the test command from the Build Decision
   - Checks out the PR branch
   - Executes the automated test suite
   - Posts a QA Decision comment (with test results and JSON)
   - Applies either `qa-passed` or `qa-failed` label based on test results
   - If PASS: orchestrator auto-merges the PR to main
   - If FAIL: orchestrator routes issue back to build

You do not need to manually post decisions or apply labels—the QA agent does all of this automatically.

---

## Step 7 (10 minutes): Observe the QA Decision in the issue

Once the orchestrator cycles and QA runs, check Feature 1's issue for:

**QA Decision Comment** (posted by QA agent):
```json
{
  "contract": "QA",
  "decision": "PASS or FAIL",
  "qa_date": "[today's date]",
  "automated_test_suite": "PASS or FAIL",
  "total_tests": [count],
  "tests_passed": [count],
  "tests_failed": [count],
  "test_output_summary": "[test results]",
  "blockers": "none | [failing test names]",
  "recommendations": "[if FAIL: next steps; if PASS: ready for release]"
}
```

**Labels Applied by QA Agent:**
- `qa-passed` if all tests pass → issue is complete, PR auto-merged
- `qa-failed` if any test fails → issue routes back to build

### Watch the orchestrator output:

```
--- Orchestrator Cycle Summary (Cycle N) ---
Model: [your active model]
Issue focused on: #1 [Feature Title] -> QA running
  ... [QA agent executes tests] ...
  -> QA PASSED. PR auto-merged to main.

--- Next Cycle ---
Checking issue #1: [Feature Title]
  Labels: intake-approved, design-approved, build-complete, verification-passed, qa-passed
  -> Action: COMPLETE. Ready for release.

Checking issue #2: [Next Feature]
  Labels: [no pipeline labels]
  -> Action: Route to intake.
```

---

## Step 8 (10 minutes): Verify the full 6-stage pipeline

Create or find a second feature (Feature 2 or Feature 3 from Module 10). Let it flow through the complete pipeline:

1. **Intake** validates requirements ✓
2. **Design** approves architecture ✓
3. **Build** creates PR + comprehensive test suite ✓
4. **Verification** runs unit tests, lint, build ✓
5. **QA** executes the comprehensive test suite ✓
6. **Release** PR auto-merged to main ✓

Watch the issue labels advance: intake-approved → design-approved → build-complete → verification-passed → qa-passed → (merged).

### Micro-check: Run through at least two features (Feature 1 and Feature 2)

- Feature 1 should reach `qa-passed` and show clear QA decision comments with test results
- Feature 2 should follow the same pattern and reach `qa-passed` (or `qa-failed` if you want to test the failure path)

---

## Step 9 (Optional - 10 minutes): Test a QA failure and recovery

To see the rework flow in action, run a feature through the complete pipeline and let it fail QA:

1. Run a feature through intake → design → build → verification (Feature 2 or 3)
2. When orchestrator cycles and spawns QA:
   - QA executes the test suite
   - If at least one test fails, QA posts a `qa-failed` comment with failing test names
   - QA applies the `qa-failed` label automatically
3. The orchestrator will detect `qa-failed` on the next cycle and:
   - Remove `build-complete` label
   - Route the issue back to build stage for rework
4. Build fixes the implementation or test coverage issue
5. Build creates a new PR
6. Orchestrator re-routes to verification
7. Orchestrator re-routes to QA
8. If tests now pass, QA applies `qa-passed` and feature is release-ready

This demonstrates the full loop: **test failure (detected by QA agent) → build rework → re-verification → re-test → success** — all orchestrated automatically.

---

## Definition of Done

✅ You have successfully completed Module 11 when:

1. **QA skill contract created** (`templates/skills/qa-agent.md`)
   - Contract defines decision criteria: PASS (all tests pass) / FAIL (any test fails)
   - Contract describes test execution and result reporting
   - Decision output structure includes test counts and results

2. **QA agent created** (`.github/agents/qa.agent.md`)
   - Agent can read issues and extract test command from build decision
   - Agent executes the automated test suite
   - Agent posts structured decision comments with test results
   - Agent applies appropriate labels (qa-passed / qa-failed)

3. **Orchestrator extended to include QA** (`.github/agents/orchestrator.agent.md`)
   - Routing table includes QA stage
   - Orchestrator routes verification-passed → QA
   - Orchestrator handles qa-passed (complete) and qa-failed (back to build)

4. **QA labels created and applied** in GitHub
   - `qa-passed` and `qa-failed` labels exist
   - At least one feature has `qa-passed` label
   - QA decision comments with test results visible on issues

5. **Full 6-stage pipeline validated** by running at least 2 features through:
   - Intake → Design → Build → Verification → QA → Release
   - Each stage shows clear decision comments
   - Labels advance correctly
   - Orchestrator maintains steady rhythm

6. **Automated test suite executed and reported**:
   - Build stage created comprehensive test suite
   - QA executed test suite and posted results
   - Test output captured (pass count, fail count)
   - Decision is traceable in issue comments

7. **Optional: QA failure and recovery tested**
   - At least one feature marked `qa-failed` (test failure)
   - Orchestrator routes back to build
   - Build fixes and creates new PR
   - QA re-executes tests on next cycle

## Stretch Goals

- Automate additional test coverage for edge cases not initially identified
- Create a test dashboard showing pass/fail rates by feature
- Create a QA dashboard showing pass/fail rates by feature
- Add performance benchmarking to QA (compare build time, response time to baseline)
- Run 3 features through the full 5-stage pipeline
- Test both success and failure paths for QA gate

---

## Key Takeaways

- **Both verification and QA are fully automated.** Verification catches code quality and unit test failures. QA catches acceptance criteria failures and regressions via comprehensive test suite.
- **QA is the final decision gate.** Issues don't merge until QA test suite passes completely. Failures indicate test coverage or implementation gaps, routing back to build for rework.
- **The full pipeline is now: Intake → Design → Build → Verification → QA.** Each stage adds a layer of quality confidence.
- **Main branch is authoritative.** Every PR rebases onto current main before verification and QA. Features integrate safely because they test against the latest code.
- **State is traceable.** All decisions (intake, design, build, verification, QA) are posted as comments. Anyone can read the full history and understand why a feature was approved or rejected.

