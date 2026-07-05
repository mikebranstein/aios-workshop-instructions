# Module 06 - First Intake Skill Contract

## Concept: what an intake skill contract is

Intake is the first quality check on a work item before implementation starts.

You use intake right after an issue is created (or updated) and before design/build work begins.

Brief example:
- A new issue describes a validation rule for a user action.
- Intake checks whether required details exist (like acceptance criteria and constraints).
- If details are complete, intake marks it READY.
- If key details are missing, intake marks it BLOCKED and asks targeted follow-up questions.

An intake skill contract is a shared rule sheet for how intake decisions are made.

Think of it like this:
- The issue is the worksheet.
- The contract is the grading rubric.
- The intake agent is the teacher grading the worksheet using that rubric.

Why this matters in the teacher/rubric analogy:
- Imagine one student submits the same test answers to two different teachers.
- In multiple-choice tests, answers are usually clear, so both teachers often grade the same.
- In essays or written exams, interpretation is broader, so grading can differ a lot.
- If no rubric exists, each teacher grades by personal judgment, so results can differ.
- One teacher may pass it. The other may mark it incomplete.

Intake works the same way:
- Issues and feature requests are essay-style inputs, not multiple-choice inputs.
- They contain written context, assumptions, and missing details that require interpretation.
- Without a contract, two people (or two prompts) can evaluate the same issue and produce different decisions.
- With a shared contract, both evaluations apply the same rubric, return the same output shape, and land on the same state transition.

### What the contract must define

At minimum, an intake contract defines:
1. required inputs (what must be present in the issue)
2. decision rules (how READY vs BLOCKED is determined)
3. fixed output schema (exact JSON keys to return)
4. escalation rule (what happens when data is missing or confidence is low)

### What the actual contract looks like

Example contract file content:

````markdown
# Intake Agent Contract

## Mission
Decide issue readiness using objective checks and return deterministic JSON only.

## Required Inputs
- Issue title
- User story
- Acceptance criteria
- Constraints

## Decision Rules
- If all required inputs are present: decision = READY, next_state = In Progress.
- If one or more required inputs are missing: decision = BLOCKED, next_state = Blocked.

## Output Schema (JSON only)
```json
{
	"decision": "READY | BLOCKED",
	"missing_fields": ["field_name"],
	"questions": ["question text"],
	"next_state": "In Progress | Blocked",
	"summary": "one-line rationale",
	"confidence": 0.0
}
```

## Guardrails
- Output must be valid JSON only.
- Do not add keys outside the schema.

## Escalation Rule
- If confidence < 0.70 or required fields are missing, keep decision BLOCKED and include escalation reason in summary.

## Trial Cases
- READY case: all required fields included.
- BLOCKED case: acceptance criteria missing.
````

## How this applies to GitHub Copilot workflows

In day-to-day Copilot usage, intake usually happens in a short chat before coding begins. The problem is that this chat often shifts based on how the question is phrased. You might ask Copilot whether an issue is ready, get a mostly correct answer, then ask a second intake question with slightly different wording and receive a different structure, different missing-field interpretation, or even a different state recommendation. Even when both answers are reasonable, the team cannot compare them cleanly, board transitions become inconsistent, and automation cannot reliably parse the result.

The contract changes this by moving decision logic out of prompt wording and into a stable rule set. Instead of improvising each time, you point Copilot to the intake contract and ask it to evaluate against that contract. The response is expected to use the same JSON keys on every run, so `decision` and `next_state` can map to the same board action every time. If required fields are missing or confidence is low, escalation behavior is triggered in a predictable way instead of being reinvented per prompt.

In practice, this makes prompts more interchangeable, outputs machine-usable, and handoffs safer because every reviewer reads the same structure. It also makes retries cheaper, since the missing information is explicit and actionable. This is the first step toward reliable skill automation and later end-to-end orchestration.

## Why this matters

Intake is the front door to your delivery system. If the front door is inconsistent, everything after it inherits that inconsistency.

When intake decisions drift, teams start implementation with different assumptions about scope, readiness, and risk. That creates avoidable churn later: design decisions get revisited, verification fails for reasons that were visible earlier, and escalation happens too late because the issue was never classified correctly at the start.

You already built the middle and late stages of control:
- feature intent (Module 2)
- implementation spec (Module 3)
- objective gates (Module 4)
- loop safety and escalation (Module 5)

This module stabilizes the first stage so those controls can actually work as a system. In other words, you are not adding process for process' sake; you are making sure that the same issue enters the pipeline the same way every time, with the same decision logic and the same evidence shape.

Once intake is deterministic, downstream work gets faster and safer. Build plans are based on clearer inputs, gate outcomes become easier to interpret, and blocked/escalation paths are triggered from objective signals instead of judgment calls. That is the practical reason this matters: better intake quality reduces rework, reduces ambiguity, and improves delivery reliability across the whole workflow.

## What you should learn in this module

By the end of this module, you should be able to:
- author a deterministic intake skill contract
- enforce JSON-only output with fixed keys
- validate the contract on one READY-style case and one BLOCKED-style case
- capture intake trial evidence in local/session notes

## Goal

Create a first deterministic intake skill contract and prove it produces consistent machine-readable decisions.

## Module rules for this exercise

- Continue using the same issue from Modules 2, 3, 4, and 5.
- Use the issue for shared context, but keep trial execution evidence in local/session notes.
- Use generic issue comment titles (no module names or numbers).
- In writing steps, define structure and content manually first; use Copilot prompts as fallback.
- Keep verification steps prompt-light and focused on objective checks.
- Require JSON-only decision output for intake trial results.

## Time Box

Target: 75 minutes

Suggested pacing:
- 10 min: confirm context and post intake objective check
- 25 min: review intake skill contract file
- 15 min: validate schema and decision rules
- 20 min: run two intake trials and capture local evidence

## What you will build

- one `templates/skills/intake-agent.md` contract file
- one local/session intake trial evidence record

## Required tasks

1. Define intake mission, required inputs, decision rules, and escalation rule.
2. Define and enforce a fixed JSON output schema.
3. Run two trial decisions (READY-style and BLOCKED-style).
4. Capture trial evidence in local/session notes.

## Stretch tasks

- add a short "low-confidence" handling note tied to escalation behavior.

## Build exercise (step-by-step)

### Step 1 (10 minutes): confirm context and set intake objective

Use the same feature issue from Modules 2 through 5.

Before continuing, confirm:
- `Gate Contracts` comment exists
- `Loop Safety Policy` comment exists
- issue status on the delivery board is `In Progress` or `Blocked`

Post a comment titled `Intake Objective Check` with:
- Objective
- Decision (Go | No-Go)
- Reason (one line)

If you want Copilot to draft this comment, use this prompt:

```text
Create a markdown issue comment titled "Intake Objective Check".

Requirements:
- Include one objective sentence for intake contract creation.
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

### Step 2 (25 minutes): review the intake skill contract section-by-section

Open the existing baseline file:

`templates/skills/intake-agent.md`

In this step, do not rewrite the contract by default. Review each section and identify why it matters.

Use this review checklist:
- `Mission`: confirm it is one sentence and explicitly says deterministic intake decisioning.
- `Required Inputs`: confirm the minimum field set is explicit (`issue_id`, `title`, `problem_statement`, `scope`, `acceptance_criteria`, `constraints`, `test_scenarios`, `risk_level`).
- `Decision Rules`: confirm the rules are objective, ordered, and produce deterministic READY/BLOCKED outcomes.
- `Output Schema (JSON only)`: confirm exactly six keys with no extras: `decision`, `missing_fields`, `questions`, `next_state`, `summary`, `confidence`.
- `Output Mapping`: confirm READY maps to `In Progress` and BLOCKED maps to `Blocked`.
- `Output Mapping`: confirm READY requires `missing_fields` to be an empty array.
- `Guardrails`: confirm the contract forbids invented data and prose outside JSON.
- `Escalation Rule`: confirm low confidence or missing required fields forces BLOCKED plus explicit escalation reason.
- `Trial Cases`: confirm there is one READY case and one BLOCKED case with expected outcomes, including explicit `next_state` assertions and array-count expectations (`missing_fields` and `questions`), with no duplicate assertions.
- `Trial Cases`: confirm expected outcomes are minimal and non-overlapping so each line checks one distinct condition.

As you review, write 1 to 2 lines per section describing the most important part of that section and what could break if it were ambiguous.

## **Optional Path: Regenerate Baseline with Copilot**

If you want Copilot to replace the file contents with a fresh baseline draft, use this single prompt:

```text
Generate a complete markdown contract file for templates/skills/intake-agent.md.

Context:
- Workflow states: To Do, In Progress, Done, Blocked
- Existing issue already has intake intent, ESS, gate contracts, and loop safety comments
- Use the current project and technology context already established in the issue and repository.

Requirements:
- Use exactly these sections:
	- Mission
	- Required Inputs
	- Decision Rules
	- Output Schema (JSON only)
	- Guardrails
	- Escalation Rule
	- Trial Cases
- In Output Schema, use exactly these keys and no extras:
	- decision
	- missing_fields
	- questions
	- next_state
	- summary
	- confidence
- decision must support READY and BLOCKED.
- next_state must map to In Progress or Blocked.
- confidence must be numeric from 0.0 to 1.0.
- if decision is READY, missing_fields must be an empty array.
- Require JSON-only output behavior (no prose around JSON).
- Include one READY-style trial case and one BLOCKED-style trial case.
- Include explicit expected `next_state` in both trial cases.
- Include explicit expected counts for `missing_fields` and `questions` in both trial cases.
- Avoid duplicate expected-outcome lines in trial cases.
- Keep expected-outcome lines minimal and non-overlapping.
- Keep language concise, objective, and testable.

Output format:
- Return markdown only (copy/paste ready).
- Return only final file content.
- Do not include explanation outside markdown.
```

This prompt is optional. Use it only if you want to replace the current baseline content.

If you run the optional prompt, verify the output still matches the required structure and rules before saving.

Before leaving Step 2, confirm your file still keeps the baseline decision semantics:
- `decision`: `READY | BLOCKED`
- `next_state`: `In Progress | Blocked`
- confidence threshold logic is explicit and measurable
- escalation behavior is explicit when confidence is low or required fields are missing

### Step 3 (15 minutes): validate contract quality

Validate `templates/skills/intake-agent.md` with these checks:

- all required sections exist and are non-empty
- output schema includes exactly six required keys
- decision rules are objective (not subjective language)
- escalation rule is explicit and measurable
- trial cases are clear, distinct, and testable (with expected outcomes that map cleanly to contract behavior)

If you want Copilot to validate the file for you, use this prompt:

```text
Review templates/skills/intake-agent.md and validate it against these exact criteria:
- Required sections exist and are non-empty: Mission, Required Inputs, Decision Rules, Output Schema (JSON only), Guardrails, Escalation Rule, Trial Cases.
- Output schema includes exactly these keys and no extras: decision, missing_fields, questions, next_state, summary, confidence.
- Decision rules are objective and deterministic.
- Escalation rule is explicit and measurable.
- Trial cases are clear, distinct, and testable, and expected outcomes align with the decision logic and state mapping.

Output format:
- Return markdown only.
- Use exactly these sections:
	- Validation Result (PASS | FAIL)
	- Checks Passed
	- Checks Failed
	- Required Fixes
	- Suggested Edits
- In "Checks Failed", reference the exact section name that failed.
- In "Required Fixes", provide concrete, minimal edits.
- Do not rewrite the whole file unless absolutely necessary.
```

If a check fails, edit the same file and fix it.

### Step 4 (20 minutes): run two intake trials and log evidence

Important intent for this module:
- You are validating the intake skill contract behavior now.
- You are not wiring GitHub auto-run triggers in this module.
- GitHub automation wiring comes in later automation modules.

Preferred path: actually use the intake skill contract for two runs (not just a manual thought exercise).

Use `templates/skills/intake-agent.md` as the contract and run it against two cases:
- Case A: READY-style issue data (required fields complete)
- Case B: BLOCKED-style issue data (required fields missing)

Practical way to run it now in Copilot Chat (fresh session per case):
1. Open `templates/skills/intake-agent.md` in the editor so the contract is visible.
2. Open GitHub Copilot Chat in VS Code.
3. Start a new chat session (use the New Chat button) so no prior prompts bias the result.
4. In that new chat, paste Case A input template and ask Copilot to evaluate strictly against `templates/skills/intake-agent.md` and return JSON only.
5. Run Case A.
6. Save the JSON output for Case A in your local/session notes.
7. Start another new chat session before Case B, paste Case B input template, and repeat.

Why use a fresh chat each time: it reduces carryover context and gives cleaner, more reliable trial results.

Before you run the cases, this is what you should expect from the contract behavior:
- Case A should resolve to `decision: READY` and `next_state: In Progress` with no missing required fields.
- Case B should resolve to `decision: BLOCKED` and `next_state: Blocked` with missing fields and follow-up questions.

Use these case input templates so Case A and Case B are clearly separated.

Case A input template (READY-style):

```text
Use templates/skills/intake-agent.md as the contract.
Evaluate the case input below strictly against that contract.
Return only one markdown code block labeled `json` containing clean, valid, pretty-printed output using the defined schema keys and types.
Use standard JSON formatting (double-quoted keys/strings, no trailing commas, 2-space indentation).
Do not add extra keys.

Case input:
issue_id: EQ-INTAKE-A
title: Prevent an invalid action when required conditions are not met
problem_statement: Users can trigger an action even when a required validation condition is not satisfied.
scope: Block the action when the required condition fails.
acceptance_criteria:
- Invalid action is rejected under the specified condition.
- User sees a clear feedback message.
- Existing valid flow remains unchanged.
constraints:
- No database schema changes.
- Preserve existing external API contract.
test_scenarios:
- invalid condition returns rejection and user message.
- valid condition allows the normal flow.
- concurrent requests do not bypass the validation rule.
risk_level: Medium
```

Case B input template (BLOCKED-style):

```text
Use templates/skills/intake-agent.md as the contract.
Evaluate the case input below strictly against that contract.
Return only one markdown code block labeled `json` containing clean, valid, pretty-printed output using the defined schema keys and types.
Use standard JSON formatting (double-quoted keys/strings, no trailing commas, 2-space indentation).
Do not add extra keys.

Case input:
issue_id: EQ-INTAKE-B
title: Prevent an invalid action when required conditions are not met
problem_statement: Users can trigger an action even when a required validation condition is not satisfied.
scope: Block the action when the required condition fails.
acceptance_criteria:
- <missing>
constraints:
- <missing>
test_scenarios:
- <missing>
risk_level: High
```

Fallback path: if you cannot run the skill directly in your environment, simulate both runs manually by applying the contract rules step-by-step and recording the outputs.

Capture the observed outputs from both runs (decision, next_state, confidence, and key evidence).

Keep the outputs in local/session notes as execution evidence for this step.

Do not change the real issue status based on these synthetic trial cases. Use the runs only to confirm that the contract behaves as expected.

## Micro checks

By minute 10 you should see `Intake Objective Check` posted.
By minute 35 you should see `templates/skills/intake-agent.md` reviewed section-by-section.
By minute 50 you should see contract validation fixes applied.
By minute 70 you should see `Intake Trial Results` recorded in local/session notes.

## You should see

A deterministic intake contract, two completed trial runs, and a clear understanding of whether the contract behaves the way you intended.

## Recap

In this module, you turned intake from an informal judgment call into a repeatable contract. You reviewed the structure of an intake skill, checked that its rules were objective, and made sure the output shape was stable enough for later automation. That matters because intake is where ambiguity first enters the system. If readiness decisions drift here, every later stage inherits that drift.

You also proved the contract against two simple cases: one that should pass cleanly and one that should fail for clear reasons. That trial work is the practical checkpoint for the module. It confirms that the contract is not just well-written on paper, but capable of producing predictable READY and BLOCKED outcomes when applied to real issue-shaped input.

The key takeaway from Module 6 is that a skill contract is not just documentation. It is the mechanism that makes future agent behavior more consistent, more reviewable, and easier to automate. That foundation matters because the next modules will build additional specialized contracts on top of the same idea.

## If this fails, do this

If output shape drifts, lock schema keys and forbid extras.
If decisions are inconsistent, tighten decision rules with explicit pass/fail criteria.
If confidence scoring is vague, define numeric boundaries for READY vs BLOCKED behavior.

## Definition of done

Module 6 is complete when all are true:

- `templates/skills/intake-agent.md` exists and follows required structure
- output schema is JSON-only with exact required keys
- two intake trials are executed (READY-style and BLOCKED-style)
- `Intake Trial Results` evidence is recorded in local/session notes
- module scorecard is completed

## Module scorecard template

```markdown
## Module Scorecard
- Module: 06
- Completion time (minutes):
- Trial consistency (0-100%):
- Primary intake risk:
- Evidence completeness (0-100%):
- Outcome: PASS | FAIL
```

## Next module

Continue to [07-module-7-design-build-skill-contracts.md](07-module-7-design-build-skill-contracts.md).