# Module 12 - Adding Policy: Governance and Human Approval Gates

## Concept: Selective human approval for high-risk changes

Modules 1-11 built a fully automated pipeline: issues flow through intake → design → build → verification → QA → release. But not every decision should be autonomous. Some changes affect architecture, impose risk, or require human judgment.

**Module 12 introduces selective policy gates:** governance checkpoints that activate **only for high-risk or complex features**. Low-risk changes skip policy review and auto-merge; high-risk changes get human approval.

The key distinction:
- **Automated gates** (Intake, Design, Build, Verification, QA): Deterministic, repeatable, rule-based. The agent makes the decision and applies a label.
- **Design-triggered governance flag** (`policy-review-required`): Design agent flags features that need human oversight.
- **Policy gates** (Policy Review): Human-driven. A reviewer reads the decision trail, evaluates risk and impact, then approves or escalates. Applied selectively, not to everything.

Policy gates add **selective oversight** without removing **velocity**. You automate routine work and bypass policy review for low-risk changes, but keep humans in the loop for decisions that matter.

## When does a feature trigger policy review?

Design agent flags `policy-review-required` if **any** of these apply:
- **Risk level:** High
- **Breaking changes:** APIs, data models, authentication
- **PII/compliance/security:** Data access patterns, retention, encryption changes
- **Impact radius:** 3+ critical subsystems
- **Database schema:** Migrations, table changes, structural modifications
- **New external dependencies:** Third-party integrations, new services
- **Critical workflow changes:** Checkout, payments, auth workflow modifications

Otherwise: Low-risk changes auto-merge after QA passes (no policy review).

## How this extends the pipeline

```
Issue Created
     ↓
[Intake Contract] → APPROVED
     ↓
[Design Contract] → PASS
     │
     ├─ [FLAGGED for governance?] → YES: Apply policy-review-required label
     │  │
     │  └─ Risk level High? Breaking changes? PII/security? Impact radius? DB schema? External deps? Critical workflow?
     │     YES → policy-review-required label applied
     │     NO → No flag (low-risk path)
     │
[Business Analyst] → CLARIFIED (if needed)
     ↓
[Build Contract] → COMPLETE (PR created)
     ↓
[Verification Contract] → PASS (tests pass, lint clean, build successful)
     ↓
[QA Contract] → PASS (comprehensive test suite passes)
     ↓
  ┌─ [policy-review-required label?]
  │  ├─ YES → [Policy Contract] → APPROVED by human reviewer → MERGE
  │  └─ NO → Auto-merge to main (skip policy review)
  │
PR Merged to Main
```

**Key difference from v6:** Low-risk changes bypass policy review entirely. Policy gates are selective, not universal.

## Time Box

- Target: 75 minutes

## Required tasks

1. Generate policy rules tailored to your project (Copilot prompt).
2. Populate the policy skill contract with your generated rules.
3. Create `policy-review-required`, `policy-approved`, `policy-escalated`, `policy-blocked` labels.
4. Review the policy agent and understand the evaluation process.
5. Extend Design agent to apply `policy-review-required` label for high-risk features.
6. Extend orchestrator to v7 with conditional policy routing (policy gate only if flagged).
7. Run Feature 1 through the complete 7-stage pipeline, observing conditional routing.

---

## Step 1 (10 minutes): Define policy rules for your organization

Before creating a policy gate, you need policy rules. These rules tell the policy reviewer when to approve vs. escalate.

Use this prompt to generate policy rules tailored to your project:

```
You are helping me author the decision framework for my agentic OS policy contract.

Here's my project context:
[Describe your project, tech stack, team structure, and risk tolerance. Example: "Team Equipment Checkout Tracker. Node.js backend, React frontend. 5-person team. We run weekly releases. Database changes are high-risk."]

Generate the "Decision Framework" section for a policy contract. This section should define clear, testable criteria for:

### APPROVE if all of the following are true:
[Generate 5-7 specific APPROVE criteria that match my project context and risk profile. Example: "Risk level: Low or Medium", "Impact is isolated to one subsystem", "No breaking changes to APIs", "QA test results: 100% pass rate", etc.]

### ESCALATE if any of these conditions apply:
[Generate 5-7 specific ESCALATE criteria. Example: "Risk level is High", "Breaking changes to public APIs", "Security review needed", "Changes to payment processing", etc.]

### BLOCK if any of these conditions apply:
[Generate 5-7 specific BLOCK criteria. Example: "Acceptance criteria not met", "Test coverage below 70%", "Known regressions in critical workflows", etc.]

Make each criterion specific, measurable, and relevant to my project. Use language a busy reviewer can quickly scan and apply.
```

Copy this prompt, fill in your project context, and run it in Copilot. The output is markdown that you can copy directly into the **"Decision Framework" section** of `templates/skills/policy-contract.md`.

**Key principle:** Policy rules are **human-readable decision criteria**, not code. They guide you (the policy reviewer) on when automation is sufficient and when you need to hold a feature for leadership review.

---

## Step 2 (5 minutes): Review the policy skill contract

The policy contract is in `templates/skills/policy-contract.md`. It has three sections:

1. **Scope:** Defines your role as policy reviewer
2. **Decision Framework:** Your APPROVE/ESCALATE/BLOCK criteria (populated with your Copilot-generated rules from Step 1)
3. **Process:** The 9 steps you'll follow when reviewing a feature
4. **Gate Rules:** How your decision maps to labels and orchestrator routing
5. **Decision Output:** The JSON structure you'll post to GitHub

**Key insight:** The contract is your decision reference. When you get to policy review (Step 6), you'll read this contract and apply its criteria. No guessing—just follow the Decision Framework.

**What to do now:**
- Paste the Copilot-generated Decision Framework from Step 1 into the Decision Framework section of `templates/skills/policy-contract.md`
- Read the entire contract to understand the Process section (Steps 1-9)
- Understand the Gate Rules: your decision maps directly to labels (`policy-approved`, `policy-escalated`, `policy-blocked`)

---

## Step 3 (5 minutes): Create policy labels in GitHub

Add four new labels for the conditional policy stage:

```bash
gh label create "policy-review-required" --color "ffcc00" --description "Design flagged this feature for policy review (high-risk or governance trigger)"
gh label create "policy-approved" --color "0e8a16" --description "Policy review approved - ready for release"
gh label create "policy-escalated" --color "ff9800" --description "Policy review escalated for leadership decision"
gh label create "policy-blocked" --color "d73a49" --description "Policy review blocked - return to design"
```

Or in GitHub UI:
1. Go to **Issues** → **Labels**
2. Create `policy-review-required` (yellow `#ffcc00`)
3. Create `policy-approved` (green `#0e8a16`)
4. Create `policy-escalated` (orange `#ff9800`)
5. Create `policy-blocked` (red `#d73a49`)

**How they work together:**
- **Design agent applies** `policy-review-required` when risk is high or governance criteria are met
- **Orchestrator checks** for this label: If present after QA passes → spawn policy review; if absent → auto-merge
- **Policy reviewer applies** `policy-approved`, `policy-escalated`, or `policy-blocked` based on evaluation

---

## Step 4 (5 minutes): Review the policy agent

The policy agent is your guide for policy review. It's in `templates/agents/policy.agent.md` and walks you through:
1. Understanding the feature request
2. Reviewing the complete decision trail (Intake → Design → Build → Verification → QA)
3. Checking for operational concerns (performance, rollback, staging, dependencies)
4. Extracting risk and scope from Design
5. Applying the policy contract decision framework
6. Posting your decision (JSON comment)
7. Applying the label

**Key insight:** The policy agent is **not autonomous**. It's a checklist for *you* to follow when reviewing a feature. It only runs when Design flags `policy-review-required`. Read it now to understand the evaluation process.

---

## Step 5 (5 minutes): Update Design agent to flag high-risk features

The Design agent already includes logic to apply `policy-review-required` label when:
- Risk level is High
- Breaking changes to APIs, data models, or authentication
- PII/compliance/security implications
- Impact affects 3+ critical subsystems
- Database schema changes
- New external dependencies
- Changes to critical workflows (checkout, payments, auth)

**Verify:** The updated Design agent (`templates/agents/design.agent.md`) includes:
1. Risk assessment step during design evaluation
2. Logic to apply `policy-review-required` label for high-risk/governance triggers
3. Output messages indicating when policy review is flagged

This is the **gating mechanism**: Design decides if a feature needs governance review, not every feature goes through policy.

---

## Step 6 (5 minutes): Extend the orchestrator to include conditional policy gates (v7)

Copy the orchestrator v7 file:

```bash
cp templates/agents/orchestrator.v7.agent.md .github/agents/orchestrator.agent.md
```

**What v7 adds (selective policy routing):**
- **If `qa-passed` + `policy-review-required`:** Route to policy review (high-risk path)
- **If `qa-passed` (no `policy-review-required`):** Auto-merge to main directly (low-risk path)
- If Policy approves: auto-merges the PR to main
- If Policy escalates: holds the issue for leadership decision
- If Policy blocks: routes back to design for re-evaluation

**Key distinction from v6:**
- **v6 (Module 11):** QA runs test suite and auto-merges on PASS. No human gate.
- **v7 (Module 12):** QA passes → check if `policy-review-required` → conditional human gate. Low-risk changes skip policy review.

---

## Step 7 (20 minutes): Run Feature 1 through the pipeline with conditional routing

Start the orchestrator:

```bash
# Start orchestrator in a terminal
node orchestrator.js
```

**Scenario 1: Low-risk Feature (auto-merge path)**

If Feature 1 is low-risk (no `policy-review-required` label after Design):
1. Orchestrator detects Feature 1 has `qa-passed` label
2. Orchestrator checks for `policy-review-required` label → NOT present
3. Orchestrator auto-merges PR directly to main
4. Feature released without policy review

**Scenario 2: High-risk Feature (policy review path)**

If Feature 1 is high-risk (Design applied `policy-review-required` label):
1. Orchestrator detects Feature 1 has `qa-passed` label
2. Orchestrator checks for `policy-review-required` label → PRESENT
3. Orchestrator routes to Policy agent
4. **You (the policy reviewer) manually:**
   - Read the issue and all decision comments
   - Evaluate against policy rules
   - Post a policy decision comment (with JSON)
   - Apply either `policy-approved`, `policy-escalated`, or `policy-blocked` label
5. Orchestrator detects your decision on the next cycle:
   - If `policy-approved`: auto-merges PR to main
   - If `policy-escalated`: holds issue pending leadership input
   - If `policy-blocked`: routes back to design

**Your choice:** Run Feature 1 as either low-risk or high-risk to see both paths in action.

---

## Step 8 (10 minutes): Observe the pipeline routing

Watch the orchestrator process Feature 1 through the entire pipeline:

**If Feature 1 is low-risk (no policy-review-required):**
```
--- Orchestrator Cycle Summary (Cycle N) ---
Issue focused on: #1 [Feature Title] -> QA passed, low-risk (no policy-review-required)
  ... [Auto-merge to main] ...
  -> Feature released to main.
```

**If Feature 1 is high-risk (policy-review-required) and Policy approves:**
```
--- Orchestrator Cycle Summary (Cycle N) ---
Issue focused on: #1 [Feature Title] -> QA passed, flagged for policy review
  -> Routed to policy reviewer.
  
--- Orchestrator Cycle Summary (Cycle N+1) ---
Issue focused on: #1 [Feature Title] -> Policy approved, auto-merging
  ... [PR merge to main] ...
  -> Feature released to main.
```

**If Feature 1 is high-risk (policy-review-required) and Policy escalates:**
```
--- Orchestrator Cycle Summary (Cycle N) ---
Issue focused on: #1 [Feature Title] -> QA passed, flagged for policy review
  -> Routed to policy reviewer.
  
--- Orchestrator Cycle Summary (Cycle N+1) ---
Issue focused on: #1 [Feature Title] -> Policy escalated for leadership
  -> Issue awaits executive decision. Held pending approval.
```

**If Feature 1 is high-risk (policy-review-required) and Policy blocks:**
```
--- Orchestrator Cycle Summary (Cycle N+1) ---
Issue focused on: #1 [Feature Title] -> Policy blocked, routing back to design
  -> Issue routed back to design for re-evaluation.
```

---

## Step 9 (Optional - 10 minutes): Test both pathways

To understand the conditional routing:

**Test Scenario A: Low-risk feature (auto-merge)**
1. Create a simple feature that doesn't trigger governance criteria (low risk, isolated scope, no PII/security/breaking changes)
2. Run it through Intake → Design (no `policy-review-required` flag applied) → Build → Verification → QA
3. Observe: Orchestrator auto-merges to main (policy review skipped entirely)
4. This demonstrates velocity: low-risk changes don't need human approval

**Test Scenario B: High-risk feature (policy review required)**
1. Create a high-risk feature (risk level High, breaking API changes, PII implications, or 3+ subsystem impact)
2. Run it through Intake → Design (Design applies `policy-review-required` flag) → Build → Verification → QA
3. Observe: Orchestrator routes to policy reviewer (you)
4. Post a policy decision (APPROVE, ESCALATE, or BLOCK)
5. Observe: Orchestrator routes based on your decision

This demonstrates selective governance: complex changes get human oversight.

---

## Step 10 (Optional - 10 minutes): Simulate leadership override

If a feature is marked `policy-escalated`, simulate leadership review:

1. Review the escalation reason (why policy reviewer escalated)
2. Post a follow-up comment: "Leadership review: [APPROVED to proceed / REJECTED - rework needed]"
3. Apply new label: `leadership-approved` or `leadership-rejected`
4. Orchestrator can be configured to recognize these labels and proceed accordingly

This demonstrates that escalation is not a dead-end; it's a pause point for human judgment, with a clear path for leadership override.

---

## Definition of Done

✅ You have successfully completed Module 12 when:

1. **Policy rules generated and integrated** (Step 1)
   - Copilot prompt executed
   - Decision Framework section populated in policy contract
   - Criteria are tailored to your project risk profile

2. **Policy skill contract completed** (Step 2)
   - Contract has Scope, Decision Framework, Process, Gate Rules, and Decision Output sections
   - Decision Framework reflects your generated rules (12 APPROVE + 10 ESCALATE + 10 BLOCK criteria)
   - JSON output structure with all 12 verified_criteria fields

3. **Policy agent reviewed** (Step 4)
   - You understand the 10-step evaluation process
   - You know how to extract risk/scope from Design
   - You know how to check operational concerns (performance, rollback, staging, dependencies)
   - You know how to post the JSON decision comment and apply labels

4. **Policy labels created** (Step 3)
   - `policy-review-required` (yellow) — Design applies this for high-risk features
   - `policy-approved` (green) — Policy reviewer approves
   - `policy-escalated` (orange) — Policy reviewer escalates for leadership
   - `policy-blocked` (red) — Policy reviewer rejects

5. **Design agent updated** (Step 5)
   - Applies `policy-review-required` label when: High risk, breaking changes, PII/security implications, 3+ subsystems, DB schema changes, new dependencies, critical workflow changes
   - This is the **gating mechanism**: Design decides if a feature needs governance review

6. **Orchestrator extended to v7 with conditional routing** (Step 6)
   - If `qa-passed` + `policy-review-required` → route to policy review (high-risk path)
   - If `qa-passed` (no flag) → auto-merge to main (low-risk path)
   - Routes policy-approved → auto-merge to main
   - Routes policy-escalated → hold for leadership
   - Routes policy-blocked → back to design

7. **Feature 1 tested through conditional pipeline** (Steps 7-9)
   - Feature 1 reached qa-passed state
   - Verified at least ONE pathway (either low-risk auto-merge OR high-risk policy review)
   - If policy-required: You (policy reviewer) read the complete decision trail, applied the Decision Framework criteria, posted a decision comment (JSON), and applied the appropriate label
   - If not policy-required: Observed automatic merge to main

8. **Full 7-stage conditional pipeline validated**
   - Intake → Design (with governance flag) → Build → Verification → QA → [Conditional: Policy | Auto-merge] → Release
   - Human reviewer only involved for high-risk features
   - Low-risk features bypass policy review entirely
   - Feature 1 either released via auto-merge OR via policy approval

9. **Optional: Both pathways tested** (Steps 9-10)
   - At least one low-risk feature auto-merged (skipped policy review)
   - At least one high-risk feature went through policy review
   - Optional: Leadership override tested for escalated features
   - Demonstrated that policy gates are selective, not universal

## Stretch Goals

- Create a policy dashboard showing approval SLAs and decision patterns
- Add role-based policy rules (different policies for different feature types)
- Implement policy appeals: if policy-blocked, allow designer to respond and request re-review
- Add approval workflows (e.g., 2 reviewers must approve before release)

---

## Reflection

After completing Module 12, reflect on:
- **Where did policy gates add value?** Did they catch anything?
- **Were the policy rules clear?** Did you know when to approve vs. escalate?
- **What would you change?** Too strict? Too loose? Missing criteria?
- **How does this fit your real workflow?** Where do you actually need human oversight?

This is the foundation for **Module 13**, where you'll run the complete, mature agentic OS with full governance in place.
