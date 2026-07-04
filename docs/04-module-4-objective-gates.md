# Module 04 - Objective Gate Contracts

## Concept: what a gate contract is

A gate contract is a written pass/fail checkpoint that uses evidence instead of opinion.

In this workshop, a gate contract is the next layer on top of the work you already produced:
- Module 2 gave you a concrete feature issue with testable intent.
- Module 3 gave you an ESS comment that explains how implementation should happen.
- Module 4 now defines the exact evidence required to move that same issue forward safely.

Think of a gate as a yes/no test before work moves forward. If the gate says "pass," you can point to specific proof. If the gate says "fail," you can point to exactly what is missing.

Concrete carry-forward example using your current issue:
1. Module 2 artifact: feature issue defines scope and pass/fail acceptance criteria.
2. Module 3 artifact: ESS comment defines implementation approach, risks, rollback, and verification commands.
3. Module 4 artifact: gate contracts define what evidence must exist before Design, Verification, QA, and Merge decisions can pass.

Without Module 4, you still have ambiguity: people can read the same issue and ESS and make different pass/fail calls.
With Module 4, those decisions become consistent because the evidence rules are explicit.

Subjective gate example (weak):
"Code quality looks good."

Objective gate example (strong):
"`dotnet restore`, `dotnet build --configuration Release`, and `dotnet test --configuration Release` all pass, and links to outputs are included in the issue."

A good gate contract answers four questions:
- What inputs are required?
- What exact result counts as pass?
- What exact signal counts as fail?
- What evidence must be linked?

## Why this matters

Objective gates prevent subjective pass/fail calls.

When gate rules are vague, teams disagree and work stalls. When gate rules are concrete, two reviewers can reach the same decision from the same evidence.

## What you should learn in this module

By the end of this module, you should be able to:
- define gate criteria so a maker and checker can independently reach the same decision
- separate opinion from evidence in pass/fail decisions
- use gate evidence to justify delivery board progression

## How this applies to prior modules

Modules 2 and 3 created the feature issue and ESS comment.

This module uses those exact artifacts as required gate inputs. You are not starting from scratch.

The practical sequence is:
- Module 2: define what should be built.
- Module 3: define how it will be built.
- Module 4: define how to judge whether each stage has enough evidence to proceed.

This is how flow continuity is preserved from Module 3 into Module 4.

## Goal

Turn your current feature issue and ESS into clear gate contracts that tell the team exactly when work can move forward and when it must stop.

## Module rules for this exercise

- Do not create a new feature issue in this module.
- Continue using the same issue from Modules 2 and 3.
- Do not create or update files in this module.
- Track all gate state in comments on the same GitHub issue.
- Generate gate content in Step 2 using a single build prompt.
- Steps 3 and 4 are verification-only (no refinement prompts).

## Time Box

Target: 70 minutes

Suggested pacing:
- 10 min: confirm issue context and set gate objective
- 25 min: generate full gate contracts
- 10 min: validate Design and Verification gates
- 15 min: validate QA and Merge gates
- 10 min: maker-checker review and gate handoff note

## What you will build

- one `Gate Contracts` comment on the existing feature issue
- one maker-checker gate decision note on the existing feature issue
- one clear handoff signal to continue implementation in `In Progress`

## Required tasks

1. Define Design, Verification, QA, and Merge gate criteria.
2. Include required evidence for each gate.
3. Run a maker-checker review on the current issue.
4. Post a gate handoff note in the issue.

## Stretch tasks

- Add one edge-case fail signal per gate.

## Build exercise (step-by-step)

### Step 1 (10 minutes): confirm context and set gate objective

Use the same feature issue from Modules 2 and 3.

Before continuing, confirm:
- Module 3 ESS handoff note exists
- issue status on the delivery board is `In Progress`

Write one gate objective sentence in this format:
- "Define objective pass/fail rules for Design, Verification, QA, and Merge so two reviewers can reach the same decision from the same evidence."

Then post a comment on the same issue titled `Gate Objective Check` with:
- Objective
- Decision (Go | No-Go)
- Reason (one line)

If you want Copilot to draft this objective check comment, use this prompt:

```text
Create a markdown issue comment titled "Gate Objective Check".

Requirements:
- Include one objective sentence for gate contract creation.
- Include decision: Go | No-Go for gate drafting.
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

### Step 2 (25 minutes): generate full gate contracts

Create one new comment on the existing issue.

Comment title:
`Gate Contracts`

Use this single build prompt in Copilot Chat:

```text
Generate a complete markdown issue comment titled "Gate Contracts".

Context:
- App: Team Equipment Checkout Tracker
- Stack: .NET 10 classic ASP.NET Core MVC + xUnit
- Workflow states: To Do, In Progress, Done
- Gates to define: Design, Verification, QA, Merge

Requirements:
- For each gate include exactly these sections:
	- Required Inputs
	- Pass Criteria
	- Fail Signals
	- Required Evidence
- Keep criteria objective, measurable, and evidence-based.
- Use PASS/FAIL style language where possible.
- Keep wording concise and implementation-focused.
- Include verification commands under Verification Gate evidence:
	- dotnet restore
	- dotnet build --configuration Release
	- dotnet test --configuration Release
- Do not include subjective wording like "looks good" or "seems fine".

Output format:
- Return markdown only (copy/paste ready).
- Return only the final issue comment body.
- Do not include explanation outside markdown.
```

Post the generated markdown as a new comment on the same issue.

### Step 3 (10 minutes): validate Design and Verification gates

Verify the Design and Verification sections in the `Gate Contracts` comment:

- each has all 4 required sections
- pass criteria are objective and testable
- fail signals are explicit and observable
- required evidence is concrete and linkable

If a check fails, edit the same issue comment and fix it.

### Step 4 (15 minutes): validate QA and Merge gates

Verify the QA and Merge sections in the `Gate Contracts` comment:

- each has all 4 required sections
- pass criteria are objective and testable
- fail signals are explicit and observable
- required evidence is concrete and linkable

If a check fails, edit the same issue comment and fix it.

### Step 5 (10 minutes): maker-checker review and gate handoff note

Run a maker-checker review on the current issue using the updated gates.

Post this comment when review is complete:

```markdown
## Gate Handoff Note
- Design gate decision: PASS | FAIL
- Verification gate decision: PASS | FAIL
- QA gate decision: PASS | FAIL
- Merge gate decision: PASS | FAIL
- Inter-rater agreement achieved: Yes | No
- Follow-up fixes needed: Yes | No
```

If you want Copilot to generate this comment, use this prompt:

```text
Generate a markdown issue comment titled "Gate Handoff Note".

Requirements:
- Use exactly these fields:
	- Design gate decision: PASS | FAIL
	- Verification gate decision: PASS | FAIL
	- QA gate decision: PASS | FAIL
	- Merge gate decision: PASS | FAIL
	- Inter-rater agreement achieved: Yes | No
	- Follow-up fixes needed: Yes | No
- Be strict. If evidence is weak, mark FAIL or No.

Output format:
- Return markdown only (copy/paste ready).
- Do not include explanation outside the comment.

Current gate review notes:
<paste reviewer notes here>
```

Keep issue status as `In Progress` unless your team policy explicitly allows moving forward.

## Micro checks

By minute 20 you should see gate objective confirmed and Step 2 prompt ready.
By minute 40 you should see full `Gate Contracts` comment drafted.
By minute 55 you should see validation fixes applied.
By minute 70 you should see maker-checker note posted.

## You should see

Two reviewers can reach the same gate decision from the same evidence.

## If this fails, do this

If decisions differ, remove subjective wording and tighten pass/fail criteria.
If evidence is unclear, add explicit evidence requirements per gate.
If gates are too broad, split criteria into smaller observable checks.

## Definition of done

Module 4 is complete when all are true:

- `Gate Contracts` comment defines Design, Verification, QA, and Merge with required sections
- gate criteria are objective and evidence-based
- maker-checker review completed on one issue
- gate handoff note is posted in the issue
- inter-rater agreement is achieved on at least one pass/fail decision
- module scorecard is posted

## Module scorecard template

```markdown
## Module Scorecard
- Module: 04
- Completion time (minutes):
- Retry count by gate:
- Primary blocker cause:
- Evidence completeness (0-100%):
- Outcome: PASS | FAIL
```

## Next module

Continue to [05-module-5-loop-safety-and-escalation.md](05-module-5-loop-safety-and-escalation.md).