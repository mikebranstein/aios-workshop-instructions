# Workshop Plan: Module 8 Onwards (Revised)

## Guiding Principle

Modules 0–7 built three skill contracts (intake, design, build) in isolation. Module 8 onwards shifts from "build contracts" to "build and run a working agentic OS" incrementally. Each module adds a new capability and runs it end-to-end. Learners experience real progress and a working system early.

---

## Module 8: First Agentic OS Run — Intake to Build with GitHub State

**Goal:** Run one complete issue through intake → design → build automation, with GitHub issues as the state backend.

**Why this module matters:** Contracts only matter when they are used. This is the first time learners see the intake, design, and build contracts working together as an automated pipeline. They experience the "wow, it works" moment and prove that state can be tracked and synchronized across stages.

**Learning outcome:** 
- Learners understand how contracts sequence into a workflow.
- Learners see GitHub issues as a state machine, not just a filing system.
- Learners run their first end-to-end automation and get a working artifact.

**What you do:**
1. Create a new GitHub issue (or use an existing one from Module 7).
2. Run the intake contract against the issue description → post decision comment.
3. Run the design contract against intake approval → post design summary comment.
4. Run the build contract against design approval → post build summary comment.
5. Verify the issue now has a clean decision trail and state progression.
6. **Run 1–2 additional issues through the same pipeline to prove repeatability.**

**Artifacts:**
- 1–2 GitHub issues with decision comments from all three contracts.
- A visible state progression (Intake → Approved → In Design → Design Approved → In Build → Build Complete).
- Evidence that contracts can work as agents in sequence.

**Time box:** 75 minutes

**Stretch:**
- Run three issues through the pipeline.

**Definition of done:**
- 1–2 issues have traversed intake → design → build with documented decisions at each gate.
- Comments are timestamped and traceable.
- You can compare the decision patterns across issues and see the workflow is consistent.
- Next person can read the trail and understand what was decided and why.

---

## Module 9: GitHub State as Source of Truth (Revised from Current)

**Goal:** Establish GitHub project fields and verify that automation state matches issue evidence. Show how state enriches the workflow.

**Why this module matters:** Once you have automation running, you need a way to track and query state reliably. This module teaches you to create a project view that surfaces which issues are in which stage and how to reconcile state between comments and project fields. You will see the value immediately by running issues through the updated system.

**Learning outcome:**
- Learners understand how to structure GitHub project fields for agentic workflows.
- Learners learn to reconcile state: does the project field match the decision comments?
- Learners see how state becomes auditable and queryable.
- Learners see the workflow become more visible once state is tracked.

**What you do:**
1. Create or verify GitHub project fields (State, Risk, Next Gate, Owner Agent).
2. Update the project fields for the 1–2 issues from Module 8.
3. Verify: Does the project field match the decision comments?
4. If mismatch, correct it and document why.
5. Create a project view filtered by "Next Gate" to see workflow stages at a glance.
6. **Run 1–2 new issues through the intake → design → build workflow, updating project state as they move through gates. Observe how the project board now tells the story.**

**Artifacts:**
- GitHub project with standardized fields.
- 1–2 issues from Module 8 with synchronized project state and decision comments.
- 1–2 new issues that you ran through the workflow with state tracking visible.
- A project board view that makes workflow stage visible and queryable.

**Time box:** 75 minutes

**Stretch:**
- Create a dashboard showing issues grouped by next gate and owner agent.

**Definition of done:**
- Project fields are defined and consistent.
- The issues from Module 8 are reflected accurately in project state.
- You ran 1–2 new issues through the workflow and verified state is synchronized end-to-end.
- State can be queried and is auditable.

---

## Module 10: Add Verification to the Agentic OS

**Goal:** Augment the workflow to include an automated verification gate (build, test, lint). Run issues through to see verification as a real gate.

**Why this module matters:** Now that you have intake → design → build running with state tracking, you add the first quality gate. This module shows how to add a verification contract and wire it into the sequence so learners see verification as a decision gate, not a one-off check. By running issues through immediately, the value of the gate becomes apparent.

**Learning outcome:**
- Learners understand how to add a new contract to an existing workflow without starting over.
- Learners see verification as a gate that can block progress.
- Learners experience the workflow growing and becoming more sophisticated with each stage.

**What you do:**
1. Use the verification agent contract (already exists from attempted Module 8).
2. After build completes, run verification against the built code.
3. Post verification result as a comment (PASS or FAIL).
4. If PASS, update project state to "In QA" or "Ready for QA".
5. If FAIL, revert state to "In Build" with failure notes.
6. **Run 1–2 issues through intake → design → build → verification, observing how verification gates progression. If any fail, fix the code and re-verify.**

**Artifacts:**
- The workflow now: Intake → Design → Build → Verification → GitHub state update.
- Verification results posted as evidence comments.
- 1–2 issues that show the full 4-stage pipeline working end-to-end.
- Examples of both PASS and FAIL verification outcomes (if possible).

**Time box:** 60 minutes

**Stretch:**
- Run three issues through the full pipeline and identify any bottlenecks or patterns.

**Definition of done:**
- Verification contract is integrated into the workflow sequence.
- Build/test results are posted as evidence in the issue.
- State transitions based on verification outcome.
- You ran 1–2 issues through the full pipeline and verified results are traceable.

---

## Module 11: Add QA to the Agentic OS

**Goal:** Add scenario-based QA as a final gate before release. Run issues through to see the full 5-stage workflow.

**Why this module matters:** Verification proves the code compiles and tests pass. QA proves it works in realistic scenarios. This module shows how manual QA results feed back into the workflow and inform the final gate decision. Running issues through immediately demonstrates the complete quality funnel.

**Learning outcome:**
- Learners understand the difference between automated verification and manual scenario testing.
- Learners see how to capture QA results and include them in the decision trail.
- Learners experience a multi-stage quality gate that combines automation and human judgment.

**What you do:**
1. For an issue in "Verification Passed" state, define QA scenarios (use the QA checklist template).
2. Manually execute scenarios and record outcomes.
3. Post QA results as a comment (scenarios passed/failed, evidence attached).
4. Decide: Release or back to build?
5. Update project state based on QA gate.
6. **Run 1–2 issues through the full 5-stage pipeline: Intake → Design → Build → Verification → QA. Observe how QA findings can block or approve release.**

**Artifacts:**
- QA scenario results integrated into the issue decision trail.
- Full pipeline visible: Intake → Design → Build → Verification → QA → Release Ready.
- 1–2 issues with complete evidence chains from idea to verified-and-tested.
- Evidence-backed quality gates at every stage.

**Time box:** 75 minutes

**Stretch:**
- Automate a subset of QA scenarios using a UI automation framework chosen by your tech stack (e.g., UI interaction tests) and run them as part of verification.

**Definition of done:**
- QA results are posted and visible in issue comments.
- Release decision is backed by verification + QA evidence.
- You ran 1–2 issues through the full 5-stage workflow.
- Full workflow from idea to verified-and-tested is auditable and traceable.

---

## Module 12: Policy, Boundaries, and Approvals

**Goal:** Add policy gates and human approval workflows to the agentic OS. Run issues through to see how policy shapes decisions.

**Why this module matters:** Not all decisions should be automated. This module teaches you to define which gates require human approval, which stages have risk thresholds, and how to enforce policy in the workflow. By running issues through immediately, learners see how policy gates change the workflow shape and introduce review points.

**Learning outcome:**
- Learners understand role separation: which stages can be autonomous vs. which need approval.
- Learners see how policy constraints shape the workflow and add oversight.
- Learners experience escalation, approval requests, and review patterns in action.

**What you do:**
1. Define policy rules (e.g., "Medium+ risk requires architecture review" or "High-risk changes require product approval").
2. Add approval gates to the workflow based on risk level or other criteria.
3. Run an issue that triggers a policy gate and see approvals requested.
4. Demonstrate approval and escalation decision-making.
5. Document the decision trail including approvals and reviewer rationale.
6. **Run 1–2 issues through the full 6-stage workflow (Intake → Design → Build → Verification → QA → Policy) with policy gates in effect. Show how different risk levels trigger different approval paths.**

**Artifacts:**
- Workflow with policy gates clearly defined and visible.
- Issues showing approval requests and reviewer decisions.
- Examples of issues that passed through policy gates and issues that escalated.
- Full audit trail including who approved what, when, and why.

**Time box:** 75 minutes

**Stretch:**
- Create a policy dashboard showing approval SLAs and identify any bottlenecks.

**Definition of done:**
- Policy gates are defined and enforced in the workflow.
- Approval decisions are logged and visible in issue comments.
- You ran 1–2 issues through the full 6-stage workflow including policy gates.
- Workflow includes both automation and human judgment in the right places.

---

## Module 13: Capstone — Full System Run with 2–3 Issues

**Goal:** Run 2–3 complete issues through the full 6-stage workflow end-to-end, demonstrating all gates working together and proving mastery.

**Why this module matters:** Learners prove they understand the entire system by running it successfully multiple times. This is the capstone: they built it, understand it, and can teach someone else.

**Learning outcome:**
- Learners can run the full agentic OS without guidance.
- Learners see patterns, efficiency, and can identify opportunities for improvement.
- Learners have a working system they can extend or teach to others.

**What you do:**
1. Create 2–3 new issues with realistic scope and varying risk levels.
2. Run all of them through the full workflow: Intake → Design → Build → Verification → QA → Policy → Release.
3. Compare the runs; note what was different (risk level, complexity, approval path), what was the same (core gates, state transitions).
4. Document the overall system, workflow patterns, decision distribution, and timing.
5. Reflect: What worked well? What would you improve?

**Artifacts:**
- 2–3 issues with complete decision trails and evidence for every gate.
- A summary report of the workflow including timing, decisions made, who was involved, and approval patterns.
- Documentation of the agentic OS that you built, suitable for onboarding a new user.
- Proof that the system is reproducible, teachable, and ready for evolution.

**Time box:** 120 minutes

**Stretch:**
- Add a fourth issue and automate one of the manual gates (e.g., QA scenarios → automated test suite) to show how the system can evolve.

**Definition of done:**
- 2–3 issues have traversed the full 6-stage workflow.
- Decision trails are complete and evidence is attached at every gate.
- Workflow is repeatable and auditable.
- All gates (intake, design, build, verification, QA, policy) are working together seamlessly.
- You can explain the system to someone else and they could run issues through it independently.

---

## Summary: What Learners Build (With Continuous Validation)

| Module | What You Add | What You See | Issues Run |
|--------|-------------|--------------|-----------|
| 8 | Intake → Design → Build workflow | End-to-end automation working | 1–2 |
| 9 | GitHub project state tracking | State is auditable and queryable | 1–2 (new) |
| 10 | Verification gate | Code quality gated automatically | 1–2 (new) |
| 11 | QA gate | Scenarios tested and tracked | 1–2 (new) |
| 12 | Policy & approvals | Human review where it matters | 1–2 (new) |
| 13 | Full system capstone | Working agentic OS you built | 2–3 (new) |

By the end of Module 13, learners will have run **11–13 issues through the system**, seeing each new stage add value, not just theory. They have not just contracts—they have a working platform they built incrementally and can teach.

---

## What to Save from Current Module 8

- Verification agent contract outline (reuse in Module 10)
- QA checklist template and structure (reuse in Module 11)
- Concept explanations on verification vs. QA (integrate into Module 11 narrative)

These become module content and templates, not workshop deliverables.
