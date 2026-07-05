# Module 07 - Design and Build Skill Contracts

## Concept: why split one contract into multiple specialized contracts

In Module 6, you learned that a contract gives one role a consistent way to make decisions. In this module, you take the next step: instead of asking one general agent to do everything, you define separate contracts for separate jobs.

That matters because design and build are not the same kind of work.

Design work is about deciding the shape of the solution before code is written. It is where you decide what should change, what must stay stable, what risks exist, and what boundaries the implementation must respect.

Build work is about carrying out that approved shape in code. It is where you translate an approved design into files, logic, tests, and next-state behavior without reopening design questions that should already be settled.

Design work answers questions like:
- what should change?
- what interfaces or data structures are affected?
- what risks need to be managed before coding begins?

Build work answers different questions:
- what code should be changed right now?
- what files are in scope?
- what should happen next if implementation succeeds or fails?

Another way to say it is this:
- design decides the blueprint
- build follows the blueprint

If the blueprint is unclear, build work drifts.
If build starts rewriting the blueprint, the workflow loses traceability.

If one contract tries to do both jobs, the outputs usually become blurry. The design part becomes too implementation-specific, and the build part starts making architectural decisions it should have inherited instead of inventing.

> You might be thinking: "Why can't I just keep using the intake agent or one general-purpose skill for this too?"
>
> That is a reasonable thought, especially right after Module 6. The answer is that intake, design, and build are not just three prompts for the same job. They are three different decision stages. Intake decides whether work is ready. Design decides what shape the solution should take. Build decides how to implement that approved shape. If one skill tries to own all three stages, it stops being clear which decisions belong where.

The practical point of Module 7 is not only to explain that separation. It is to build out the skill contract descriptions that make the separation executable.

Just like Module 6 gave you an intake contract, Module 7 gives you two more contracts:
- one for design
- one for build

Later, those contracts can become separate skills and eventually separate agents running in sequence or, in some workflows, concurrently against shared state. This module is where that structure starts.

## A simple way to think about it

If Module 6 was about creating one clear rubric for intake, Module 7 is about recognizing that different classes have different kinds of exams.

A physics class has a physics exam.
An English class has an English exam.
A PE class has a PE exam.

They are all still exams, but they are not testing the same thing, so they should not use the same rules.

Design and build work follow the same pattern. They are both part of delivery, but they are testing different kinds of decisions.
- The design contract tests whether the proposed solution is coherent.
- The build contract tests whether implementation can proceed within that approved solution.

> You might also be thinking: "But both are still about building software, so why not use one contract and save time?"
>
> That would save time only at the beginning. Later, it usually costs time because the contract becomes vague. Once the same skill is allowed to both decide architecture and implement code, it becomes harder to review, harder to trace, and harder to automate safely.

That is why you now need multiple contracts instead of one.

## How this connects to Module 6

Module 6 established the foundation:
- contracts reduce interpretation drift
- outputs should be structured and machine-usable
- trial cases prove whether a contract behaves predictably

Module 7 extends that same idea into role specialization.

Instead of asking, "Is this issue ready?" you are now asking two new questions:
- "What should the design agent be responsible for deciding?"
- "What should the build agent be responsible for deciding?"

This module is more technical than Module 6 because the contracts are closer to implementation work. But the core idea is the same: make each role explicit, bounded, reviewable, and ready to become part of a larger agent workflow.

## How this applies to GitHub Copilot and agent workflows

Without specialized contracts, AI agents can blur planning and execution together. A design run may start proposing code before the design is stable. A build run may quietly make architecture decisions that were never reviewed. Over time, that creates hidden drift between what was intended and what was implemented.

> You might be thinking: "If Copilot is good enough, won't it just figure out the right boundary on its own?"
>
> Sometimes it will. But workshop design should not depend on lucky behavior. The point of the contract is to remove guesswork from the workflow. Instead of hoping the model stays in role, you define the role explicitly and then validate whether it followed it.

Specialized contracts reduce that blur. The design contract makes an agent explain the technical shape of the change before coding starts. The build contract makes an agent focus on implementation within that approved shape. This improves traceability because design outputs can point back to ESS and acceptance criteria, while build outputs can point back to the approved design.

This matters beyond just the two contracts in this module. In an Agentic OS model, you do not want one large static agent doing everything. You want a modular system where roles can be separated, improved, replaced, or inserted as needed.

Today, that might mean intake, design, build, and verification.
Later, you may decide to add:
- a security agent
- a product-owner agent
- a compliance agent
- a documentation agent

That only works cleanly if each role has a contract that defines what it owns, what it inherits, and what it hands off. Otherwise, adding a new role just creates more ambiguity.

In practical terms, Module 7 is about creating a cleaner handoff between planning and execution while also laying the groundwork for a modular agent system. The better those contracts are, the easier it becomes to automate later stages without losing control, and the easier it becomes to add new agent roles without redesigning the whole workflow.

## Why this matters

As delivery work becomes more agent-assisted, the biggest quality problems often show up in the gaps between stages, not just inside a stage. One agent says what should happen. Another agent changes code. If the handoff between them is vague, the second agent fills the gap with guesswork.

That is what this module is trying to prevent.

You already created an intake contract so readiness decisions are stable. Now you need design and build contracts so readiness turns into design in a controlled way, and design turns into implementation in a controlled way.

When these contracts are clear, each stage inherits context instead of reinventing it. That reduces rework, lowers the chance of scope drift, and makes later verification more trustworthy because you can trace implementation decisions back to design decisions.

## What you should learn in this module

By the end of this module, you should be able to:
- explain why design and build need different contracts
- explain what each contract should own and what it should inherit
- review a design contract and a build contract section-by-section
- shape both contracts so they could later operate as separate skills or agents
- recognize whether each contract uses the right inputs, outputs, and escalation boundaries
- run one issue-shaped case through both contracts and check whether the handoff stays traceable

## Goal

Create and review specialized design and build skill contracts so planning and implementation stay separate, traceable, reusable, and ready for later automation.

## Module rules for this exercise

- Continue using the same issue from Modules 2 through 6.
- Use the issue for shared context, but keep contract trial evidence in local/session notes unless a step explicitly asks for an issue update.
- Use generic issue comment titles (no module names or numbers).
- In writing steps, review structure manually first; use Copilot prompts as optional helpers.
- Keep validation steps focused on role boundaries, output shape, and handoff clarity.
- Treat design and build as distinct responsibilities; do not let one contract absorb the other role's work.

## Time Box

Target: 80 minutes

Suggested pacing:
- 10 min: confirm context and set specialization objective
- 25 min: review the design skill contract
- 20 min: review the build skill contract
- 20 min: run one issue-shaped case through both contracts and capture local evidence
- 5 min: read recap and note the key takeaway

## What you will build

- one reviewed `templates/skills/design-agent.md` contract
- one reviewed `templates/skills/build-agent.md` contract
- one local/session evidence record showing design-to-build traceability on the same case

## Required tasks

1. Review the design contract and identify its decision boundaries.
2. Review the build contract and identify its implementation boundaries.
3. Run one issue-shaped case through both contracts.
4. Confirm the build contract clearly inherits design context instead of inventing it.

## Build exercise (step-by-step)

### Step 1 (10 minutes): confirm context and set specialization objective

Use the same feature issue from Modules 2 through 6.

Before continuing, confirm:
- `Intake Objective Check` exists
- `Gate Contracts` comment exists
- `Loop Safety Policy` comment exists
- issue status on the delivery board is `In Progress` or `Blocked`

Post a comment titled `Skill Specialization Objective Check` with:
- Objective
- Decision (Go | No-Go)
- Reason (one line)

If you want Copilot to draft this comment, use this prompt:

```text
Create a markdown issue comment titled "Skill Specialization Objective Check".

Requirements:
- Include one objective sentence for design/build contract specialization.
- Include decision: Go | No-Go.
- Include one-line reason.

Output format:
- Return markdown only (copy/paste ready).
- Use exactly these sections:
	- Objective
	- Decision
	- Reason

Current issue context:
<paste issue title + short summary here>
```

### Step 2 (25 minutes): review the design skill contract

Open:

`templates/skills/design-agent.md`

In this step, review the design contract section-by-section before changing anything.

As you read, keep this framing in mind: the design contract should decide the shape of the solution, not perform the build.

Use this review checklist:
- `Mission`: confirm it focuses on turning approved work into an actionable design, not implementation.
- `Required Inputs`: confirm it depends on ESS, acceptance criteria, risk, and architecture context.
- `Output Schema`: confirm outputs describe design decisions, interfaces, model impact, risks, and next state.
- `Guardrails`: confirm the contract prevents design approval when requirements are still ambiguous.
- `Escalation Rule`: confirm it catches breaking changes or cross-team dependencies.
- `Gate Rule`: confirm build begins only after design passes.

As you review, write 1 to 2 lines per section describing the most important responsibility of the design contract and what would go wrong if that section were weak.

For example, the design contract is valuable when it forces a question like: "Are we changing an interface or data model?" before build starts. Without that boundary, the build stage may discover architectural impact too late.

## **Optional Path: Regenerate Design Baseline with Copilot**

If you want Copilot to replace the design contract with a fresh baseline draft, use this single prompt:

```text
Generate a complete markdown contract file for templates/skills/design-agent.md.

Context:
- Existing issue already has intake intent, ESS, gate contracts, and loop safety context
- Use the current project and technology context already established in the issue and repository.

Requirements:
- Use exactly these sections:
	- Mission
	- Required Inputs
	- Output Schema (JSON only)
	- Guardrails
	- Escalation Rule
	- Gate Rule
- Design outputs must focus on solution shape, not code implementation.
- Required inputs must include ESS draft, acceptance criteria, non-goals, risk level, and current architecture context.
- Output schema should support decision, design summary, interfaces impacted, data model impact, risks, mitigations, and next state.
- decision must support PASS, REVISE, and BLOCKED.
- next_state must support In Design, In Build, and Blocked.
- design_summary should briefly explain what is changing, what stays stable, and why the design is acceptable.
- Guardrails should prevent approval when acceptance criteria are still ambiguous.
- Guardrails should prevent the design contract from turning into a build plan or file-by-file implementation list.
- Guardrails should make PASS, REVISE, and BLOCKED meaningfully distinct.
- Escalation should trigger on breaking changes, cross-team dependencies, or unjustified architectural changes.
- Gate Rule should explicitly map decision to next_state.
- Keep language concise, objective, and testable.

Output format:
- Return markdown only (copy/paste ready).
- Return only final file content.
- Do not include explanation outside markdown.
```

This prompt is optional. Use it only if you want to replace the current baseline content.

### Step 3 (20 minutes): review the build skill contract

Open:

`templates/skills/build-agent.md`

In this step, review the build contract section-by-section.

Keep this framing in mind: the build contract should implement the approved design, not redesign the work item.

Use this review checklist:
- `Mission`: confirm it is implementation-focused.
- `Required Inputs`: confirm it clearly depends on approved design context, acceptance criteria, implementation scope, and branch constraints.
- `Output Schema`: confirm it returns implementation decisions, changed files, updated tests, acceptance-criteria coverage, remaining work or blocker reason, design dependencies used, and next-state behavior instead of design-analysis outputs.
- `Guardrails`: confirm it stays within scope, does not silently expand the change, and makes COMPLETE/PARTIAL/BLOCKED meaningfully distinct.
- `Escalation Rule`: confirm it catches blocked implementation conditions rather than architectural ambiguity that should have been handled in design.
- `Gate Rule`: confirm decision-to-next_state mapping is explicit and the next stage only begins when build output passes its own contract boundary.

As you review, write 1 to 2 lines per section describing what the build contract is responsible for and what it should inherit rather than invent.

For example, the build contract should not decide whether a breaking API change is acceptable. That should already have been surfaced in design. The build contract should focus on implementing what design approved.

## **Optional Path: Regenerate Build Baseline with Copilot**

If you want Copilot to replace the build contract with a fresh baseline draft, use this single prompt:

```text
Generate a complete markdown contract file for templates/skills/build-agent.md.

Context:
- Existing issue already has intake context, ESS, and design/build separation goals
- Use the current project and technology context already established in the issue and repository.

Requirements:
- Use exactly these sections:
	- Mission
	- Required Inputs
	- Output Schema (JSON only)
	- Guardrails
	- Escalation Rule
	- Gate Rule
- Build outputs must focus on implementation progress, scope, blockers, and next state.
- The contract must assume design decisions are inputs, not questions to rediscover.
- Required inputs must include approved design summary, interfaces impacted, data model impact, acceptance criteria, implementation scope, non-goals, and target branch.
- Output schema should support decision, changes summary, files changed, tests updated, acceptance criteria covered, remaining work, blocker reason, risks, design dependencies used, and next state.
- decision must support COMPLETE, PARTIAL, and BLOCKED.
- next_state must support In Build, In Verification, and Blocked.
- changes_summary should briefly explain what was implemented, what remains incomplete if anything, and why the current implementation state is acceptable.
- Guardrails should keep the implementation inside approved scope.
- Guardrails should prevent the build contract from introducing new architectural decisions.
- Guardrails should make COMPLETE, PARTIAL, and BLOCKED meaningfully distinct.
- Guardrails should require explicit traceability back to implemented acceptance criteria.
- remaining_work should be empty when decision is COMPLETE.
- blocker_reason should be null unless decision is BLOCKED.
- Escalation should trigger when implementation is blocked, not when new architecture is being invented.
- Escalation should also trigger when implementation conflicts with approved design, non-goals, or branch policy.
- Gate Rule should explicitly map decision to next_state.
- Keep language concise, objective, and testable.

Output format:
- Return markdown only (copy/paste ready).
- Return only final file content.
- Do not include explanation outside markdown.
```

This prompt is optional. Use it only if you want to replace the current baseline content.

### Step 4 (20 minutes): run one case through both contracts and check the handoff

Important intent for this module:
- You are validating role separation and traceability.
- You are not wiring GitHub auto-run triggers in this module.
- You are checking whether build cleanly inherits design context.

Preferred path: actually use both contracts in Copilot Chat on the same case.

Practical way to run it:
1. Open `templates/skills/design-agent.md` and `templates/skills/build-agent.md` in the editor.
2. Open GitHub Copilot Chat in VS Code.
3. Start a new chat session for the design run (steps below).
4. Save the design output in local/session notes.
5. Start a second new chat session for the build run (steps below).
6. Save the build output in local/session notes.

Why use fresh chats: it reduces carryover context and makes it easier to judge whether each contract stands on its own inputs.

---

#### Design: what you should expect

- The design output should reference ESS, acceptance criteria, interface impact, and risks
- The design output should clearly define scope boundaries (what changes, what stays stable)
- The contract should catch incomplete inputs and ask for clarification before approval

**Design case (EQ-DESIGN-01) — what you will see:**
- This case is intentionally incomplete—it omits `non_goals`, which the design contract requires.
- **Expected outcome: REVISE** (not PASS)
- **What you should see:** The contract catches the missing scope boundary and returns to Design phase with a mitigation: "Provide non_goals clarifying what must not change."
- **Why this matters:** Design approval requires clear negative space. Without it, build cannot inherit trustworthy constraints.

#### Run the design case

Paste this into a new Copilot Chat session:

```text
Use templates/skills/design-agent.md as the contract.
Evaluate the case input below strictly against that contract.
Return only one markdown code block labeled `json` containing clean, valid, pretty-printed output using the defined schema keys and types.
Use standard JSON formatting (double-quoted keys/strings, no trailing commas, 2-space indentation).
Do not add extra keys.

Case input:
work_item_id: EQ-DESIGN-01
ess_draft: Add a validation rule that blocks an invalid user action without changing the external API contract.
acceptance_criteria:
- Invalid action is rejected under the specified condition.
- User sees a clear feedback message.
- Existing valid flow remains unchanged.
risk_level: Medium
current_architecture_context: Existing controller, service, and persistence layers already handle the current workflow.
```

---

#### Build: what you should expect

- The build output should inherit the approved design shape instead of rediscovering architecture
- The build output should make it obvious which acceptance criteria are already covered and what remains unfinished or blocked
- The contract should reject build requests that lack real approved design inputs (not placeholders)

**Build case (EQ-BUILD-01) — what you will see:**
- This case uses placeholder text for `approved_design_summary`, `approved_interfaces_impacted`, and `approved_data_model_impact` instead of actual design outputs.
- Additionally, the design case (EQ-DESIGN-01) never reached PASS state—so there is no approved design to inherit.
- **Expected outcome: BLOCKED** (not COMPLETE or PARTIAL)
- **What you should see:** The contract rejects placeholder values and explains the dependency: "Design must be approved (PASS) before build inputs are valid."
- **Why this matters:** Build cannot proceed without real design decisions. This demonstrates the contract enforcing the workflow boundary.

#### Run the build case

Paste this into a new Copilot Chat session:

```text
Use templates/skills/build-agent.md as the contract.
Evaluate the case input below strictly against that contract.
Return only one markdown code block labeled `json` containing clean, valid, pretty-printed output using the defined schema keys and types.
Use standard JSON formatting (double-quoted keys/strings, no trailing commas, 2-space indentation).
Do not add extra keys.

Case input:
work_item_id: EQ-BUILD-01
approved_design_summary: <paste design output summary here>
approved_interfaces_impacted: <paste design output interfaces_impacted here>
approved_data_model_impact: <paste design output data_model_impact here>
acceptance_criteria:
- Invalid action is rejected under the specified condition.
- User sees a clear feedback message.
- Existing valid flow remains unchanged.
implementation_scope: Update the relevant validation and request-handling flow only. Do not change the external API contract.
non_goals:
- Do not redesign the broader workflow.
- Do not introduce schema changes.
target_branch: feature/validation-rule-update
```

---

#### Review your outputs

Capture both outputs in local/session notes and check these questions:
- Does the design output clearly define what build should inherit?
- Does the build output stay inside that inherited design?
- If something is missing, is it obvious whether the gap belongs to design or build?

**The lesson:** Both cases intentionally show validation and dependency enforcement. This is not a testing error—it is the contracts working as designed. You are seeing what happens when preconditions are incomplete or invalid.

## Micro checks

By minute 10 you should see `Skill Specialization Objective Check` posted.
By minute 35 you should see `templates/skills/design-agent.md` reviewed.
By minute 55 you should see `templates/skills/build-agent.md` reviewed.
By minute 75 you should see one design output and one build output recorded in local/session notes.

## You should see

Two specialized contracts that divide planning and implementation cleanly, plus one trial run that makes the handoff between them visible.

## Recap

In Module 6, you proved that one contract could make intake decisions more consistent. In Module 7, you extended that idea by splitting one generalized workflow into specialized roles. That is the deeper lesson here: consistency does not come only from structure, but from giving each stage a clear job.

The design contract exists so that architectural and scope decisions are made before coding starts. The build contract exists so implementation can inherit those decisions instead of recreating them. When those boundaries are clear, the system becomes easier to review and easier to automate later because each agent has a narrower, more defensible responsibility.

The key takeaway from Module 7 is that specialization is not overhead. It is what keeps multi-stage agent workflows from collapsing back into one large ambiguous prompt.

## If this fails, do this

If design output is too implementation-heavy, move architectural reasoning back into the design contract and narrow build scope.
If build output starts inventing requirements, add stronger inherited-input expectations to the build contract.
If the handoff is unclear, add or tighten fields that explicitly carry design decisions into build.

## Definition of done

Module 7 is complete when all are true:

- `templates/skills/design-agent.md` exists and follows a clear role-specific structure
- `templates/skills/build-agent.md` exists and follows a clear role-specific structure
- both contracts have been reviewed section-by-section
- one case has been run through both contracts
- local/session notes show the design-to-build handoff clearly
- module scorecard is completed

## Module scorecard template

```markdown
## Module Scorecard
- Module: 07
- Completion time (minutes):
- Design/build handoff clarity (0-100%):
- Primary specialization risk:
- Evidence completeness (0-100%):
- Outcome: PASS | FAIL
```

## Next module

Continue to [08-module-8-verification-qa-evidence-loop.md](08-module-8-verification-qa-evidence-loop.md).