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

---

## Modules 1-7: Foundation (not shown; pre-module content)

Modules 1-7 build the foundational agents (Intake, BA, Design, Build) and establish the basic Agentic OS structure: orchestration, GitHub state management, and depth-first workflow routing.

**Previous modules covered:**
- Module 0: Shared app foundation (starter project template)
- Modules 1-7: Individual agents (Intake, BA, Design, Build, with state tracking and basic orchestration)

## Modules 8-12: Quality Gates and Governance (core workshop focus)

Modules 8-12 add quality gates (Verification, QA) and policy governance, transforming the system from basic agent routing into a mature, controlled release pipeline.

**New modules (8-12) covered above:**
- Module 8: Orchestrator & end-to-end workflow
- Module 9: GitHub state tracking as source of truth
- Module 10: Verification gate (automated code quality)
- Module 11: QA gate (automated test validation)
- Module 12: Policy gate (selective human approval)

## Modules 13-14: Strategic Leadership and Capstone (new)

Modules 13-14 add product leadership (PM + PO strategy) and integrate the full end-to-end system.

## Module 13: Product Leadership — Strategic Direction and Tactical Execution

**Goal:** Learn the complete product leadership layer: Product Manager (strategic) and Product Owner (tactical). Understand how strategy flows into execution and practice the two-tier leadership model.

**Why this module matters:** Every feature needs a "why." Product leaders ensure the development pipeline works on strategically important, market-validated features. This module teaches you to think like a Product Manager (discover market opportunities, validate with customers, set strategic direction) and like a Product Owner (prioritize the backlog, execute strategy tactically, collaborate with development).

**Learning outcome:**
- Learners understand the PM role: strategic discovery, market research, opportunity validation
- Learners understand the PO role: backlog prioritization, tactical execution, team collaboration
- Learners see how strategy flows into execution (PM sets direction → PO executes → pipeline delivers)
- Learners practice both roles and understand when each should make decisions
- Learners grasp the PM ↔ PO collaboration pattern

**What you do:**
1. Define product vision (market, problem, advantage, goals, priorities, roadmap)
2. Conduct market research and discover 2-3 feature opportunities
3. Validate opportunities with customers/stakeholders
4. Evaluate against strategy (CHAMPION / DEFER / BLOCK)
5. Assume PO role: Prioritize using formula (User Value + Business Value) / (Complexity × 1.5)
6. Create GitHub issues for prioritized features
7. Practice PM ↔ PO collaboration
8. Verify backlog is ordered and ready

**Artifacts:**
- Product vision document
- 2-3 market opportunities with validation evidence
- PM decision comments with rationale
- GitHub backlog with prioritized issues
- Evidence of PM ↔ PO collaboration

**Time box:** 90 minutes

**Stretch:**
- Conduct customer interviews
- Create competitive analysis
- Build 12-month product roadmap
- Document strategic trade-offs

**Definition of done:**
- Product vision documented
- 2-3 market opportunities researched and evaluated
- Backlog created with 2-3 GitHub issues ordered by priority
- PM and PO agents reviewed
- PM ↔ PO collaboration demonstrated
- Both roles understood
- PM-PO orchestrator reviewed (orchestrator.pm-po.agent.md)

---

## Module 14: Capstone — Full System End-to-End Run

**Goal:** Run 2–3 complete issues through both independent orchestrator loops end-to-end: 
1. **PM-PO Orchestrator**: Product Manager discovery/validation → Product Owner prioritization → "Ready for Development"
2. **Development Orchestrator**: Intake → BA → Design → Build → Verification → QA → Policy → Release

Prove mastery of the complete strategic product organization running concurrently.

**Why this module matters:** Learners prove they understand the entire system by running it successfully multiple times with real strategic context. This is the capstone: they built it, understand it, and can teach someone else. Key insight: PM-PO and Development run **independently and concurrently**—neither blocks the other.

**Learning outcome:**
- Learners can run both orchestrators concurrently without guidance
- Learners see how product strategy flows into execution without blocking
- Learners understand the backlog as the contract between PM-PO and Development
- Learners observe patterns, efficiency, and opportunities for improvement
- Learners have a working, production-ready strategic product organization

**What you do:**
1. **PM-PO Orchestrator**: Use Module 13 backlog; discover and validate 1-2 new opportunities
   - Submit as `pm-idea` issues
   - Let PM agent autonomously research/validate
   - Let PO agent prioritize and move to "Ready for Development"
2. **Development Orchestrator**: Run 2-3 issues from "Ready for Development" through the 8-stage pipeline
   - Pull one issue at a time
   - Execute Intake → BA → Design → Build → Verification → QA → Policy → Release
   - Never wait for PM-PO; PM-PO continues independently
3. For each feature, observe and document:
   - Flow time through pipeline
   - Which gates add the most value
   - How risk level affected policy routing
   - How feedback loops worked
4. Compare the runs: What patterns emerge? How efficient is the system?
5. Document the overall system
6. Reflect: What worked? What would you change?

**Artifacts:**
- 2-3 issues with complete decision trails for all 8 development stages
- 1-2 PM-PO discovery/validation issues showing autonomous workflow
- Summary report: timing, patterns, outcomes
- System documentation: two-loop workflow, routing, frameworks
- Reflection: lessons learned and evolution paths

**Time box:** 120 minutes

**Stretch:**
- Run 4-5 features to show full throughput
- Intentionally trigger high-risk escalation scenarios
- Add metrics: decisions per stage, flow time, bottlenecks
- Demonstrate PM-PO re-prioritization while development is in progress
- Create onboarding/handoff documentation
- Propose system improvements

**Definition of done:**
- 2-3 issues traversed the full 8-stage development pipeline end-to-end
- 1-2 PM-PO discoveries showing autonomous research + validation + prioritization
- Complete decision trails with evidence at every gate
- Low-risk and high-risk feature paths both demonstrated
- Both orchestrators (PM-PO and Development) worked concurrently without blocking
- All 10 agents (PM, PO, Intake, BA, Design, Build, Verification, QA, Policy, Release) worked together seamlessly
- Strategic context clear: why was this feature built? How did it align with vision?
- System demonstrated as production-ready and repeatable
- System is teachable to someone else

---

## Summary: What Learners Build (With Continuous Validation)

| Module | What You Add | What You See | Issues Run |
|--------|-------------|--------------|-----------|
| 8 | Intake → Design → Build workflow | End-to-end automation working | 1–2 |
| 9 | GitHub project state tracking | State is auditable and queryable | 1–2 (new) |
| 10 | Verification gate | Code quality gated automatically | 1–2 (new) |
| 11 | QA gate | Automated test execution | 1–2 (new) |
| 12 | Policy & selective approvals | High-risk features reviewed; low-risk auto-merged | 1–2 (new) |
| 13 | Product leadership (PM + PO) | Strategic vision flowing into execution | (backlog prep) |
| 14 | Full system capstone | Complete 10-stage pipeline with strategy | 2–3 (new) |

By the end of Module 14, learners will have run **12–14 issues through the system**, managed a strategically-validated backlog, and built a working, production-ready strategic product organization they can teach and evolve.

---

## What to Save from Current Module 8

- Verification agent contract outline (reuse in Module 10)
- QA checklist template and structure (reuse in Module 11)
- Concept explanations on verification vs. QA (integrate into Module 11 narrative)

These become module content and templates, not workshop deliverables.
