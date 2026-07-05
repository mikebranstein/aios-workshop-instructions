# Module 08 - First Agentic OS Run: Intake to Build with GitHub State

## Concept: contracts become a workflow

In Modules 6 and 7, you built three skill contracts—intake, design, and build. But they have been theoretical. You have not seen them work together. This module is where theory becomes real.

Up to now:
- Module 6 proved that a contract gives one role consistent, structured decisions.
- Module 7 proved that multiple contracts can be specialized by role and stage.
- Module 8 proves that contracts can sequence together as an automated workflow.

This is the pivot point. You are no longer studying contracts in isolation. You are building your first agentic OS—a system where one piece of work moves through multiple decision gates, each gate running a contract, each decision leaving a visible trail.

**What makes this work:** GitHub issues become your state machine. An issue starts as an idea. It flows through gates (intake → design → build). At each gate, a contract runs, a decision is made, and a comment is posted. The issue's state changes. Other stages see that state and know what to do next.

**Why this matters:** Once you see contracts working together this way, you will understand how to automate business processes. This is not a theoretical framework anymore. It is a working system you can extend.

### The simplest possible first workflow

```
Issue Created
     ↓
[Intake Contract]
     ↓ (decision: APPROVED)
[Design Contract]
     ↓ (decision: PASS)
[Build Contract]
     ↓ (decision: COMPLETE)
Issue Ready for Next Stage
```

Each arrow is a gate. Each gate is a contract. Each contract posts a decision as a comment in the issue. The issue's state is the proof that something happened.

### What an outside observer would see

Someone reading your GitHub issue after you run it through this workflow would see:
- The original issue description (intake input)
- A decision comment from intake: "APPROVED—this issue is well-formed and ready for design"
- A design comment: "PASS—here is the proposed solution shape"
- A build comment: "COMPLETE—code is implemented and ready for verification"
- The issue state updated at each stage

They could follow the trail, understand what was decided, and trust the result.

---

## Time Box

- Target: 75 minutes

## Required tasks

1. Create a new GitHub issue with realistic work scope.
2. Run the issue through intake contract → post decision.
3. Run the issue through design contract → post decision.
4. Run the issue through build contract → post decision.
5. Verify the issue has a complete decision trail.
6. Run 1–2 additional issues through the same workflow to prove repeatability.

## Stretch tasks

- Run three issues through the full workflow.
- Run the issues with varying risk levels and note how decisions change.

---

## Step 1 (10 minutes): Create a new GitHub issue

Create a realistic issue in your GitHub repository. Example scopes:
- Add a validation rule for user input
- Create a new report type
- Add error handling to an existing flow
- Build a simple feature (e.g., user preference saving)

Make sure the issue has:
- A clear description of what the work is
- Acceptance criteria (or a list of things that should work)
- A context or motivation (why is this work needed?)

**Why this step:** Intake contracts need real input. Your issue description is that input.

---

## Step 2 (15 minutes): Run intake contract and post the decision

Open GitHub Copilot Chat and paste this prompt (replace the issue details):

```text
You are an intake agent. Use templates/skills/intake-agent.md as your contract.

Evaluate this GitHub issue strictly against that contract.

Issue:
Title: [your issue title]
Description: [paste your issue description]
Acceptance Criteria: [paste your acceptance criteria or list]

Return only one markdown code block labeled `json` containing clean, valid output using the schema keys defined in the contract.
```

The contract will return a JSON decision: APPROVED, REVISE, or BLOCKED.

**If APPROVED:**
- Copy the JSON output.
- Go to your GitHub issue.
- Post a comment like this:

```markdown
## Intake Decision

**Decision:** APPROVED

**Reasoning:** [paste the reasoning from the JSON]

**Next Stage:** Ready for Design
```

**If REVISE or BLOCKED:**
- Post the decision as a comment.
- Clarify the issue (if REVISE) or escalate (if BLOCKED).
- Do not proceed to design until intake is APPROVED.

**What this demonstrates:** The intake gate worked. The issue is now officially in the "approved for design" state. The evidence is in GitHub.

---

## Step 3 (15 minutes): Run design contract and post the decision

Once intake is APPROVED, open a new Copilot Chat session and paste this prompt:

```text
You are a design agent. Use templates/skills/design-agent.md as your contract.

Evaluate this design request strictly against that contract.

Approved Intake Summary: [paste the intake decision reasoning]

Work Item:
- Title: [your issue title]
- Acceptance Criteria: [paste the acceptance criteria]
- Risk Level: [your assessment: Low, Medium, or High]
- Current Architecture Context: [describe the existing system and where this fits]

Non-Goals (what must NOT change): [list any explicit non-goals]

Return only one markdown code block labeled `json` containing clean, valid output using the schema keys defined in the contract.
```

The contract will return a JSON decision: PASS, REVISE, or BLOCKED.

**If PASS:**
- Copy the JSON output.
- Go to your GitHub issue.
- Post a comment like this:

```markdown
## Design Decision

**Decision:** PASS

**Solution Shape:** [paste the design_summary from the JSON]

**Interfaces Impacted:** [paste from JSON, or "none" if applicable]

**Data Model Impact:** [paste from JSON]

**Risks:** [paste from JSON]

**Next Stage:** Ready for Build
```

**If REVISE or BLOCKED:**
- Post the decision and reason.
- Clarify the design or escalate.
- Do not proceed to build until design is PASS.

**What this demonstrates:** Design is now approved. The issue knows what solution shape is acceptable. Build will inherit this, not reinvent it.

---

## Step 4 (15 minutes): Run build contract and post the decision

Once design is PASS, open a new Copilot Chat session and paste this prompt:

```text
You are a build agent. Use templates/skills/build-agent.md as your contract.

Evaluate this build request strictly against that contract.

Approved Design Summary: [paste the design_summary from the design decision]

Approved Interfaces Impacted: [paste from design decision]

Approved Data Model Impact: [paste from design decision]

Work Item:
- Title: [your issue title]
- Acceptance Criteria: [paste the acceptance criteria]
- Implementation Scope: [describe what you will implement and what you won't]
- Non-Goals: [paste from design or intake]
- Target Branch: [your feature branch name, e.g., feature/my-feature]

Return only one markdown code block labeled `json` containing clean, valid output using the schema keys defined in the contract.
```

The contract will return a JSON decision: COMPLETE, PARTIAL, or BLOCKED.

**If COMPLETE:**
- Copy the JSON output.
- Go to your GitHub issue.
- Post a comment like this:

```markdown
## Build Decision

**Decision:** COMPLETE

**What Was Implemented:** [paste changes_summary from JSON]

**Files Changed:** [paste from JSON]

**Tests Updated:** [paste from JSON]

**Acceptance Criteria Covered:** [paste from JSON]

**Next Stage:** Ready for Verification

**Branch:** [your branch name]
```

**If PARTIAL or BLOCKED:**
- Post the decision and reason.
- Identify what remains or what is blocked.
- Iterate: fix the code, rerun build contract, post updated decision.

**What this demonstrates:** Build completed the approved design. The issue now has code ready for the next stage (verification, which comes in Module 10). The evidence trail is complete: intake approved → design shaped it → build implemented it.

---

## Step 5 (10 minutes): Verify the decision trail

Go back to your GitHub issue and scroll through the comments. You should see:
1. Original issue description
2. Intake decision comment (APPROVED)
3. Design decision comment (PASS)
4. Build decision comment (COMPLETE)

This is your first evidence trail. Someone reading this issue would know exactly what was decided and why. This is what traceable, auditable work looks like.

**What to verify:**
- Each decision is clear (APPROVED, PASS, COMPLETE).
- Each comment has reasoning, not just a judgment.
- The flow is: approved → shaped → implemented.
- State progresses from one gate to the next.

---

## Step 6 (10 minutes): Run 1–2 additional issues through the same workflow

Create 1–2 more issues with different scope or risk level. Run each one through intake → design → build using the same prompts and process.

**Why this step:** One issue could be luck. Two or three issues prove the workflow is repeatable. You will see patterns: which gates approve quickly, which ask for revision, where decisions differ vs. where they are consistent.

**What to observe:**
- Do the decisions feel consistent across issues?
- Did any issue hit REVISE or BLOCKED? Why?
- How long did each gate take?
- Did lower-risk issues move faster?

---

## Micro checks

- **Minute 10:** GitHub issue created with clear scope and acceptance criteria.
- **Minute 25:** Intake decision posted (APPROVED or REVISE/BLOCKED with path forward).
- **Minute 40:** Design decision posted (PASS or needs revision).
- **Minute 55:** Build decision posted (COMPLETE or needs iteration).
- **Minute 75:** 1–2 additional issues run through the same workflow.

## You should see

- 2–3 GitHub issues with complete decision trails (intake → design → build).
- Each issue has comments showing decisions and reasoning.
- State progression is clear and traceable.
- Workflow is repeatable (second and third issues follow the same pattern).

## If this fails, do this

- **Intake keeps returning REVISE:** Make sure your issue description includes clear acceptance criteria and context. Intake contracts need well-formed inputs.
- **Design keeps returning REVISE:** Make sure you are providing clear non-goals and current architecture context. Design needs scope boundaries to approve.
- **Build keeps returning PARTIAL or BLOCKED:** Make sure the approved design is included in the build contract input. Build inherits design, it does not reinvent it.
- **Decision comments feel generic:** Add more specific reasoning. Generic comments mean the contract is working, but the input was vague. Refine the input and re-run.

## Definition of done

- 2–3 GitHub issues have traversed intake → design → build with documented decisions at each gate.
- Each issue has a comment trail showing the decision and reasoning at each stage.
- Workflow is repeatable: similar issues follow the same flow and decision pattern.
- Next stage reader can understand what was decided and why from the GitHub issue alone.
- You have proof that contracts work as a sequence, not in isolation.

## Next module

Continue to [09-module-9-github-state-source-of-truth.md](09-module-9-github-state-source-of-truth.md).