# Module 09 - Requirements Clarification: The Business Analyst Agent

## Concept: Who fills the gaps in incomplete requirements?

In Modules 6-8, you defined skill contracts and built an orchestrator with intake, design, and build specialists. But what happens when intake says "blocked—requirements incomplete" or when design says "revise—I need clarity on acceptance criteria"?

**Module 9 introduces the Business Analyst agent.** This is the specialist who authorsand clarifies requirement details when gaps exist. They're not making design decisions (that's design's job), and they're not validating structure (that's intake's job). They're filling reasonable gaps in what's been provided: making vague acceptance criteria specific, identifying edge cases, and documenting assumptions.

The BA agent runs in two scenarios:
1. **Intake-blocked:** Issue body is missing critical fields or has ambiguous acceptance criteria. BA author-fills those gaps.
2. **Design-revise (requirements feedback):** Design says "I need more clarity on requirements before I can design this." BA refines requirements based on design feedback, then intake re-validates.

This creates a feedback loop: **incomplete requirements → BA authors → intake validates → design designs → (if REVISE) → BA refines → intake re-validates → design again.**

## How this extends the pipeline

```
Issue Created
     ↓
[Intake Contract] → APPROVED or BLOCKED
     ↓
    (if BLOCKED: requirements incomplete)
     ↓
[Business Analyst] → CLARIFIED
     ↓
[Intake Contract] → Re-validated (should now APPROVE)
     ↓
[Design Contract] → PASS, REVISE, or BLOCKED
     ↓
    (if REVISE: needs requirement clarity)
     ↓
[Business Analyst] → REFINED based on design feedback
     ↓
[Intake Contract] → Re-validated with refined requirements
     ↓
[Design Contract] → Re-evaluated (should now PASS or ESCALATE)
     ↓
[Build & Verify]
```

## Time Box

- Target: 90 minutes

## Required tasks

1. Create the business analyst skill contract and agent.
2. Add two new labels for requirements feedback.
3. Extend the orchestrator v3 to include BA routing (creating v3.5).
4. Modify Module 8 features to deliberately have incomplete or ambiguous requirements.
5. Watch intake block, BA clarify, intake re-approve, design approve.
6. See design return REVISE, BA refine based on feedback, intake re-approve, design re-evaluate.

---

## Step 1 (10 minutes): Understand the BA contract and agent

The BA operates under a skill contract defining when and how they author requirements. Unlike intake (deterministic validation) or design (architectural reasoning), BA uses domain knowledge and creative problem-solving to author reasonable details.

Review (but don't modify):

```bash
cat templates/skills/business-analyst-agent.md
cat templates/agents/business-analyst.agent.md
```

**Key aspects of the BA contract:**
- **Do not make architecture decisions.** Focus on *what*, not *how*.
- **Do not add scope creep.** Only fill explicit gaps.
- **Document assumptions.** If "show checkout history" could mean different things, pick the most reasonable one and explain why.
- **Preserve author voice.** Authored requirements should feel like a continuation of the original issue.
- **Ready for intake?** BA's goal is to make the next intake re-validation likely to pass.

---

## Step 2 (10 minutes): Set up BA labels in GitHub

Add two new labels for requirements feedback:

```bash
gh label create "requirements-clarified"      --color "0075ca" --description "BA clarified requirements"
gh label create "requirements-needs-human"    --color "fbca04" --description "Requirements need human input; BA escalated"
```

Or in GitHub UI:
1. Go to **Issues** → **Labels**
2. Create `requirements-clarified` (blue `#0075ca`)
3. Create `requirements-needs-human` (orange `#fbca04`)

---

## Step 3 (15 minutes): Deploy the BA agent to `.github/agents/`

Copy the BA agent and skill contract into your repo:

```bash
cp templates/agents/business-analyst.agent.md .github/agents/
cp templates/skills/business-analyst-agent.md templates/skills/
```

These are fresh files (you created them in the earlier setup). The BA agent references the skill contract to apply its decision logic.

---

## Step 4 (20 minutes): Extend the orchestrator to include BA routing

Update the orchestrator to route intake-blocked issues to the BA agent, and to handle design REVISE feedback:

```bash
cp templates/agents/orchestrator.v4.agent.md .github/agents/orchestrator.agent.md
```

**What v4 adds to v3:**
- After `intake-blocked` label is applied (for requirements incomplete), route to BA
- BA clarifies/authors requirements, applies `requirements-clarified` label
- Orchestrator recognizes `requirements-clarified`, re-routes to intake for re-validation
- After `design-blocked` label with REVISE decision (requirements feedback), route to BA if feedback is about requirements
- BA refines requirements based on design feedback
- Issue returns to intake for re-validation

**Depth-first routing remains:** The orchestrator processes one issue at a time through all stages.

---

## Step 5 (15 minutes): Create a deliberately incomplete feature

Create Feature 5 with vague, incomplete requirements that will trigger intake-blocked:

```bash
gh issue create --title "[feature-request]: Improve checkout history" \
  --body "We need to show more information about past checkouts so users can see what they've borrowed."
```

Notice this body has NO acceptance criteria, no specifics, no edge cases, no constraints. It's intentionally vague.

**Watch intake react:**
- Next orchestrator cycle: Issue routes to intake
- Intake evaluates and posts BLOCKED decision with `missing_fields`: ["acceptance_criteria", "edge_cases", "explicit_constraints"]
- Applies `intake-blocked` label
- Output: "Issue #N: intake BLOCKED - missing critical fields"

---

## Step 6 (20 minutes): Watch BA clarify and intake re-approve

**On the next orchestrator cycle:**
- Orchestrator sees `intake-blocked` label
- Reads intake decision JSON to confirm reason is "requirements incomplete"
- Routes Feature 5 to BA
- BA posts clarification comment with authored details:
  - Acceptance criteria (specific and testable)
  - Edge cases identified
  - Constraints noted
  - Assumptions documented (e.g., "show last 20 checkouts sorted by date descending")
- BA applies `requirements-clarified` label

**On the following cycle:**
- Orchestrator recognizes `requirements-clarified` label
- Re-routes Feature 5 to intake for re-validation
- Intake evaluates the now-complete requirements
- Intake posts APPROVED decision
- Applies `intake-approved` label

**You should see on Feature 5:**
- Three comments: Intake (BLOCKED), BA (CLARIFIED), Intake (Re-validated, APPROVED)
- Three labels: `intake-blocked`, `requirements-clarified`, `intake-approved`
- Feature 5 now ready to advance to design

---

## Step 7 (15 minutes): See design REVISE request requirements refinement

After Feature 5 is approved, design evaluates it. For this exercise, design intentionally returns REVISE with feedback on requirements.

**On next cycle:**
- Orchestrator routes Feature 5 to design
- Design posts decision: `decision: REVISE`, with `clarifications_needed` like "Need to clarify: does 'checkout history' include failed checkout attempts? Should we show quantity borrowed?"

**On next cycle:**
- Orchestrator reads design decision, sees REVISE with requirements-related feedback
- Routes Feature 5 back to BA (not intake)
- BA posts refined requirements addressing design feedback
- BA applies `requirements-clarified` label (again)

**On next cycle:**
- Orchestrator re-routes to intake
- Intake re-validates with refined requirements
- Intake approves
- Feature 5 advances to design again with updated requirements

**You should see:**
- Feature 5 label sequence: `intake-blocked` → `requirements-clarified` → `intake-approved` → `design-revise` (REVISE) → `requirements-clarified` (again) → `intake-approved` (again) → `design-approved`
- Comment trail showing the complete feedback loop
- Each BA comment addresses specific design questions

---

## Micro checks

- Minute 10: BA contract and agent reviewed
- Minute 20: Two requirements labels created
- Minute 35: BA agent deployed to `.github/agents/`
- Minute 55: Orchestrator v3.5 deployed (includes BA routing)
- Minute 70: Feature 5 created with incomplete requirements
- Minute 80: Feature 5 routed to intake → blocked
- Minute 85: Feature 5 routed to BA → clarified
- Minute 90: Feature 5 re-routed to intake → approved

---

## You should see

- `.github/agents/` now has: intake, design, build, verification, orchestrator, business-analyst
- `templates/skills/` now has: intake-agent, design-agent, build-agent, verification-agent, business-analyst-agent
- **Feature 5:** Complete feedback loop: intake-blocked → BA clarified → intake-approved → design-revise → BA refined → intake-approved → design-approved
- BA comments include structured clarifications and documented assumptions
- Labels showing the full state progression with requirements feedback

---

## What you learned

- **Requirements authoring is a separate expertise from validation or design.** BA fills gaps using domain knowledge and reasonable assumptions, not creative interpretation.
- **Incomplete requirements are recoverable.** Intake-blocked doesn't stay stuck; BA moves it forward by authoring reasonable details.
- **Design can request requirement refinement.** When design says REVISE with requirements feedback, BA handles it (not a blocker, an action).
- **Feedback loops are built-in.** BA → Intake → Design can cycle multiple times until requirements are clear and design is ready.
- **Assumptions are explicit.** BA documents what they assumed and why, creating an audit trail.
- **Depth-first routing now includes requirements.** Issues flow intake → [BA] → design → [BA] → build → verify, all depth-first.
- **Contracts separate concerns.** Intake validates. Design architecs. BA authors. Each has its own domain expertise and guardrails.
