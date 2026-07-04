# Workshop V2 Ground-Up Outline (Build Starts in Module 1)

This redesign treats the workshop as a sequence of small build wins.

Each module has:
- one learning goal
- one concrete build exercise
- one visible artifact
- one checkpoint before moving on

Design rules used in this outline:
- Build in every module (no concept-only modules)
- Short concept brief first, then immediate action
- Progressive dependency from one module to the next
- Frequent observable checkpoints
- Reuse existing fields and artifacts where possible
- Keep learner-facing language only

## Delivery format

Recommended pacing:
- 12 core modules
- 60-90 minutes per module
- each module follows the same loop:
  1) Why this matters (5-8 min)
  2) Build task (35-55 min)
  3) Checkpoint and fix loop (10-20 min)
  4) Reflection and handoff (5-10 min)
- formative checks every 10-15 minutes during build time

## Standard module template (applies to all 12 modules)

Every module must include these fields explicitly:
- Time box (target total minutes)
- Required tasks (must complete)
- Stretch tasks (optional)
- Micro checks (10-15 minute understanding checks)
- If this fails, do this (recovery path)
- Definition of done (module exit criteria)
- Scorecard metrics (time, retries, blocker cause, evidence completeness)

Scorecard metrics captured at module end:
- completion time in minutes
- retry count by gate
- primary blocker cause (if any)
- evidence completeness (0-100%)

## Module 1 - Ship a tiny issue end-to-end (manual)

Goal:
- experience the full lifecycle once before learning detailed architecture

Time box:
- 75 minutes

Concept:
- workflow states and evidence-based completion

Required tasks:
- run preflight environment gate
- complete one tiny issue end-to-end

Stretch tasks:
- run the same flow for a second tiny issue

Micro checks:
- at minute 15: issue created and added to project
- at minute 30: state moved to Ready with decision note
- at minute 50: build and test evidence captured

Hard preflight environment gate (10 minutes):
- verify git, dotnet, and VS Code run successfully
- verify repository access and project access
- verify one issue can be created and edited
- if one check fails, fix before proceeding

Policy preview (introduced early):
- low risk can proceed with standard checks
- medium and high risk require human review before merge
- retry cap is 3 attempts before escalation

Build exercise:
- create one tiny feature issue
- move it through Backlog -> Ready -> In Build -> In Verification -> Done manually
- run local build and test once
- add closure comment with links

Artifact:
- closed issue with evidence links

Checkpoint:
- issue is closed with build/test evidence and no missing closure fields

If this fails, do this:
- reduce scope to a smaller issue and rerun
- fix first failed gate only, then re-run checkpoint

Definition of done:
- one issue completed with full closure evidence
- scorecard captured for this module

Teaches for next module:
- where workflow friction appears and why structure is needed

## Module 2 - Build quality intake (issue template)

Goal:
- prevent bad work items from entering the pipeline

Time box:
- 70 minutes

Concept:
- input quality controls and acceptance criteria

Build exercise:
- create or refine feature issue template with required fields
- create one new issue using template and validate completeness

Required tasks:
- enforce required fields in template
- create one issue that passes the intake checklist

Stretch tasks:
- add one anti-example issue showing why BLOCKED is needed

Micro checks:
- at minute 20: template renders
- at minute 40: issue has complete acceptance criteria

Artifact:
- .github/ISSUE_TEMPLATE/feature_request.md + one valid issue

Checkpoint:
- template enforces required fields and issue has testable acceptance criteria

If this fails, do this:
- simplify acceptance criteria to binary pass/fail statements

Definition of done:
- issue template enforces required inputs
- one valid issue passes intake review

Teaches for next module:
- standardized inputs for design and implementation

## Module 3 - Build your first executable spec (ESS)

Goal:
- convert a valid issue into an implementation-ready spec

Time box:
- 75 minutes

Concept:
- binary acceptance criteria and explicit rollback

Build exercise:
- create ESS for one issue from template
- define scope, non-goals, ACs, verification commands, rollback
- run a 10-minute peer review using ESS checklist

Required tasks:
- ESS sections complete
- peer review comments recorded

Stretch tasks:
- add risk matrix to ESS

Micro checks:
- at minute 25: scope and non-goals complete
- at minute 45: ACs are binary

Artifact:
- docs/ess-issue-001.md

Checkpoint:
- another engineer can implement without clarification meeting

If this fails, do this:
- remove ambiguous language and convert to measurable criteria

Definition of done:
- ESS accepted in peer review with no critical ambiguity

Teaches for next module:
- design-to-build handoff discipline

## Module 4 - Build gate definitions (objective pass/fail)

Goal:
- remove ambiguity from quality decisions

Time box:
- 70 minutes

Concept:
- design, verification, QA, merge gate contracts

Build exercise:
- define objective pass/fail criteria in gates doc
- add required evidence for each gate
- run a maker-checker review between two learners

Required tasks:
- criteria defined for Design, Verification, QA, Merge
- evidence requirements added for each gate

Stretch tasks:
- add edge-case fail signals

Micro checks:
- at minute 20: Design and Verification criteria finalized
- at minute 40: QA and Merge criteria finalized

Artifact:
- docs/gates.md with measurable criteria

Checkpoint:
- two different reviewers produce the same gate decision from evidence

If this fails, do this:
- tighten criteria wording and remove subjective terms

Definition of done:
- inter-rater agreement achieved on at least one sample issue

Teaches for next module:
- repeatable quality control and reduced subjective debates

## Module 5 - Build loop safety and escalation

Goal:
- prevent infinite retries and hidden stalls

Time box:
- 65 minutes

Concept:
- bounded retries, Blocked state, escalation ownership

Build exercise:
- add loop safety policy and escalation runbook rules
- simulate one failed gate and escalation path

Required tasks:
- retry policy documented
- escalation owner and SLA documented

Stretch tasks:
- add escalation notification template

Micro checks:
- at minute 20: retry rules written
- at minute 40: escalation simulation completed

Artifact:
- updated docs/state-machine.md + docs/escalation-runbook.md usage example

Checkpoint:
- retry cap and escalation path are clear and testable

If this fails, do this:
- run one additional failure simulation and refine owner map

Definition of done:
- blocked-state and escalation path validated on sample case

Teaches for next module:
- reliable recovery under failure

## Module 6 - Build first skill contract (intake)

Goal:
- produce deterministic machine-readable gate outputs

Time box:
- 75 minutes

Concept:
- role contract, JSON output schema, confidence threshold

Build exercise:
- create/refine intake skill contract
- test on two issues (one READY, one BLOCKED)

Required tasks:
- output schema includes required keys
- decisions logged in issue history

Stretch tasks:
- add confidence threshold tuning notes

Micro checks:
- at minute 25: contract drafted
- at minute 50: both test cases executed

Artifact:
- templates/skills/intake-agent.md + two decision logs

Checkpoint:
- outputs are valid JSON and decisions are consistent with issue quality

If this fails, do this:
- validate against schema and remove non-JSON output

Definition of done:
- two successful runs produce consistent decision output

Teaches for next module:
- contract-first behavior for additional skills

## Module 7 - Build design + build skill contracts

Goal:
- formalize design and implementation handoffs

Time box:
- 80 minutes

Concept:
- role specialization and controlled autonomy

Build exercise:
- define design and build skill contracts
- run on one issue and log decisions/artifacts

Required tasks:
- both contracts published
- one issue run through both contracts

Stretch tasks:
- add verification handoff fields

Micro checks:
- at minute 30: design contract complete
- at minute 55: build contract complete

Artifact:
- templates/skills/design-agent.md
- templates/skills/build-agent.md

Checkpoint:
- design decision references ESS; build decision references acceptance criteria

If this fails, do this:
- add missing references and rerun on same issue

Definition of done:
- handoff traceability is visible in issue timeline

Teaches for next module:
- traceability across specialized roles

## Module 8 - Build verification and QA evidence loop

Goal:
- prove quality with machine and scenario evidence

Time box:
- 85 minutes

Concept:
- verification evidence vs QA evidence

Build exercise:
- run restore/build/test commands
- create QA report from checklist
- iterate once on a failing case
- run a peer QA review on one scenario

Required tasks:
- verification evidence posted
- QA report completed

Stretch tasks:
- add one regression scenario beyond core ACs

Micro checks:
- at minute 25: build/test evidence captured
- at minute 55: first QA pass executed

Artifact:
- verification summary comment + docs/qa-report-issue-001.md

Checkpoint:
- gate decisions are evidence-backed and reproducible

If this fails, do this:
- isolate first failing scenario and rerun only that branch

Definition of done:
- verification and QA outcomes are reproducible by another learner

Teaches for next module:
- confidence before merge

## Module 9 - Build GitHub state as source of truth

Goal:
- synchronize execution reality with project state

Time box:
- 70 minutes

Concept:
- canonical state fields and transition ownership

Build exercise:
- configure/verify project fields (reuse existing first)
- connect one issue and perform real state transitions during work

Required tasks:
- canonical fields verified
- transition history visible for one issue

Stretch tasks:
- add dashboard view filtered by next gate

Micro checks:
- at minute 20: fields verified
- at minute 45: first transition sequence complete

Artifact:
- project item with complete state fields and transition history

Checkpoint:
- project state, issue timeline, and PR evidence all agree

If this fails, do this:
- reconcile mismatch and record one correction note

Definition of done:
- state and evidence remain synchronized across artifacts

Teaches for next module:
- auditability and automation readiness

## Module 10 - Build first automation (low risk)

Goal:
- reduce repetitive manual transitions safely

Time box:
- 80 minutes

Concept:
- event-driven automation with explicit no-op/block behavior

Build exercise:
- add one workflow that updates state or posts check summary on PR events
- test on a real PR

Required tasks:
- workflow implemented
- one successful and one blocked/no-op behavior observed

Stretch tasks:
- add retry-safe idempotency guard

Micro checks:
- at minute 30: workflow file committed
- at minute 55: first automation event observed

Artifact:
- .github/workflows/state-transition.yml

Checkpoint:
- automation executes correctly and does not bypass policy checks

If this fails, do this:
- disable auto-transition and keep summary-only mode until fixed

Definition of done:
- automation behaves predictably on at least two event paths

Teaches for next module:
- controlled scaling without losing governance

## Module 11 - Build policy boundaries and approvals

Goal:
- keep speed while enforcing risk controls

Time box:
- 75 minutes

Concept:
- human approvals at risk boundaries

Note:
- policy boundaries were previewed in Module 1 and are fully enforced here.

Build exercise:
- configure branch protections and approval rules
- test medium/high-risk path with required approval

Required tasks:
- branch protections configured
- medium/high risk path tested

Stretch tasks:
- add exception handling template for emergency hotfix path

Micro checks:
- at minute 25: branch protections verified
- at minute 50: approval path tested

Artifact:
- repository policy settings + documented approval policy

Checkpoint:
- risky changes cannot merge without required approval path

If this fails, do this:
- tighten rule set and rerun merge simulation

Definition of done:
- policy controls block unauthorized merge attempts

Teaches for next module:
- safe autonomy at scale

## Module 12 - Capstone: run two real issues back-to-back

Goal:
- demonstrate repeatable performance with no gate drift

Time box:
- 90 minutes per issue run (two runs)

Concept:
- operational consistency and improvement loop

Build exercise:
- run two issues end-to-end using full workflow
- record cycle time, retry counts, blocker causes
- complete postmortem and improvement actions

Required tasks:
- two end-to-end issue runs
- one postmortem with concrete improvement actions

Stretch tasks:
- compare run metrics and propose one automation improvement

Micro checks:
- run 1 midpoint: verification evidence posted
- run 2 midpoint: QA report posted

Artifact:
- two closed issues with full evidence
- one postmortem report
- one improvement backlog item

Checkpoint:
- both issues meet definition of done and evidence standard

If this fails, do this:
- stop after first failing gate, perform root-cause fix, then rerun affected segment

Definition of done:
- two successful runs with complete evidence and stable policy compliance

Outcome:
- workshop completion with operational confidence, not just conceptual familiarity

## Cross-module standards

Use in every module:
- observable checkpoint wording: "You should see..."
- one required artifact before moving on
- one failure-recovery section: "If this fails, do this"
- one short reflection prompt: "What changed in your repo this module?"
- required vs stretch tasks clearly labeled
- module scorecard captured at end
- micro checks every 10-15 minutes during build

## Proposed replacement reading/build order

1. Module 1: tiny end-to-end run
2. Module 2: intake quality
3. Module 3: ESS
4. Module 4: gates
5. Module 5: loop safety
6. Module 6: intake skill
7. Module 7: design/build skills
8. Module 8: verification + QA
9. Module 9: GitHub state model
10. Module 10: first automation
11. Module 11: policy boundaries
12. Module 12: capstone run

## Migration plan from current files

Phase A (fast restructure):
- consolidate current 00-05 into new Modules 1-5 so building starts immediately
- move heavy conceptual depth into module sidebars, not primary path

Phase B (execution alignment):
- map current 06-16 into Modules 6-12
- remove duplicate instructions and normalize checkpoint style

Phase C (artifact and policy cleanup):
- retain best parts of 17-24 as support docs
- keep support docs optional and referenced only when needed

## Acceptance criteria for this redesign

- building starts in first module
- each module yields at least one concrete artifact
- each module has a pass/fail checkpoint
- each module sets up the next module directly
- no maintainer-facing or assistant-facing language in learner docs
- every module includes time box, required/stretch split, and definition of done
- every module includes failure recovery and scorecard metrics
