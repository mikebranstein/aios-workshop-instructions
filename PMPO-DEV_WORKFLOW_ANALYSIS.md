# PM ↔ PO ↔ Dev Orchestrator Integration Analysis

**Date:** 2026-07-07  
**Focus:** Workflow coherence across Product Manager → Product Owner → Development pipeline

---

## Executive Summary

✅ **Overall Integration: STRONG** — The PM → PO → Dev workflow is well-designed and clear. Both orchestrators (PM-PO and Development) are decoupled and run independently. However, there are **3 clarification opportunities** in documentation that would improve handoff clarity.

---

## Workflow Overview

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    PM ORCHESTRATOR (Strategic)                   │
│                                                                   │
│  pm-idea (user input) → Research → Validation → Decision          │
│                      ↓                         ↓                  │
│                  [Comments: Findings]    [Decision: CHAMPION]     │
│                                              ↓                    │
│                                     strategic-opportunity #42     │
│                                   (+ research + validation)        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ (Link)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PO ORCHESTRATOR (Tactical)                    │
│                                                                   │
│  Read strategic-opportunity #42 → Ask clarifying Qs → Decide     │
│         (PM's research context)                  ↓               │
│                            feature-request #89 (with AC draft)    │
│                          (links back to strategic-opportunity)    │
│                                    ↓                             │
│                     Position in "Ready for Development"           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ (Pull)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  DEV ORCHESTRATOR (Execution)                    │
│                                                                   │
│  Pull feature-request #89 from "Ready for Development"           │
│         (includes user story, draft AC, success metrics)          │
│                      ↓                                           │
│         Intake Agent validates requirements clarity               │
│              (escalates if unclear to PO)                        │
│                      ↓                                           │
│         BA Agent refines AC + success metrics                     │
│                      ↓                                           │
│    8-Stage Pipeline (Design → Build → QA → Release)              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Handoff 1: PM → PO (`strategic-opportunity` issues)

### What PM Creates

**Issue Type:** `strategic-opportunity` (labeled `pm-opportunity`)

**Contains:**
- ✅ Research findings (support tickets, customer signals, market size, competitive analysis)
- ✅ Validation assessment (strategic alignment, competitive advantage, customer validation strength, effort estimate)
- ✅ Strategic decision (CHAMPION/DEFER/BLOCK)
- ✅ Link to source `pm-idea` issue

**Example Structure** (from pm-orchestrator.agent.md):

```markdown
Title: Strategic Opportunity - Mobile App for Field Teams

Link to source: pm-idea #34

Research Findings:
- 12 support tickets from field teams this month
- 4 customer interviews (all field-heavy segments)
- Competitive analysis: 3 competitors have mobile
- Market signal: 40% of leads are field-based teams

Validation Assessment:
- Strategic fit: Yes (aligns with Q3 mobile pillar)
- Customer validation: Strong (4 customers willing to beta)
- Competitive advantage: 3-month lead if we ship first
- Effort estimate: 10 weeks (backend + iOS + Android)

Decision: CHAMPION
Rationale: Market signal is strong, strategic alignment clear, competitive window tight

[Post research findings & validation as comments]
```

### What PO Receives & Does

**PO Workflow:**
1. **Read** strategic-opportunity (access all PM research, validation, decision)
2. **Ask clarifying questions** in comments:
   - "How strong is the customer signal? 4 customers vs. 10+?"
   - "Does this fit with our Q3 priorities?"
   - "Is 10 weeks realistic? Any blockers?"
3. **Wait** for PM to respond
4. **Decide** whether to create feature-request (or ask for more validation)

**Key Point:** PO has full context of PM's research before deciding to bring work into tactical backlog.

### Integration Quality: ✅ **STRONG**

- ✅ Clear input/output structure
- ✅ PM's CHAMPION decision is prerequisite for PO work
- ✅ PO can ask clarifying Qs; PM has visibility
- ✅ Documented in pm-orchestrator.agent.md (Stage 1 → Stage 2 flow)
- ✅ GitHub links are explicit (strategic-opportunity references pm-idea)

---

## Handoff 2: PO → Dev (`feature-request` issues)

### What PO Creates

**Issue Type:** `feature-request` (labeled `feature-request` + `po-prioritized`)

**Structure:**

Per the PO agent (line 48), create feature-request including:
- ✅ Link to source `strategic-opportunity` issue
- ✅ User story
- ✅ Acceptance criteria (draft)
- ✅ Value assessment (user value, business value, complexity)
- ✅ Priority score
- ✅ Success metrics

**Template Reference:**

The PO agent explicitly directs:
```
Use the template you customized in Module 2 - Intake Quality Template
```

**Example from PO Agent:**

```markdown
Title: Mobile App - iOS Checkout for Field Teams

Linked to: strategic-opportunity #42

User Story:
As a field manager, I want to check out equipment from my phone,
so that I don't need to return to office.

Problem:
Field teams do 40% of checkouts. Currently they:
- Return to office (30 min roundtrip) to use web checkout
- Use colleague's phone (inefficient)
- Checkpoint location doesn't have WiFi (offline needed)

Value Scores:
- User value: 5 (solves critical pain)
- Business value: 4 (12 support tickets, revenue enabler)
- Complexity: 4 (new platform, backend changes)
- Priority score: (5+4)/(4*1.5) = 1.2 (Strategic bet)

MVP Scope:
- iOS only (Android in Phase 2)
- Checkout flow only (no browse/search)
- Online + offline support (basic caching)
- Estimated effort: 6 weeks (vs. 10 weeks for full app)

Success Metrics:
- 50% adoption among field teams in first month
- Completion rate 85% (vs. web 90%)
- Churn reduction for field teams: 5% improvement
```

### What Dev Receives & Does

**Dev Orchestrator Expectation** (from orchestrator.development.agent.md):

```
Inputs: feature-request from "Ready for Development" column
- Linked to source strategic-opportunity (PM research)
- Includes: user story, acceptance criteria (draft), value assessment, priority score
- Already prioritized by PO; ready to execute

Process:
1. Read feature-request and extract: title, user story, acceptance criteria, success metrics
2. Validate requirements are clear
   - If unclear: ask BA for early clarification
   - If clear: proceed
3. Move issue to "In Development" column
4. Route to BA Agent for requirements refinement
```

### Integration Quality: ⚠️ **GOOD, WITH CLARIFICATION NEEDED**

**Strengths:**
- ✅ Clear linkage back to strategic-opportunity (traceability)
- ✅ PO must include user story + scope + value + success metrics
- ✅ Explicit template reference (Module 2 intake-quality)
- ✅ Feature must be in "Ready for Development" column before dev pulls
- ✅ Dev knows to escalate to PO if scope changes

**Clarification Needed:**

**Issue 1: Acceptance Criteria Guidance is Contradictory**

The PO agent has conflicting guidance on acceptance criteria:

- **Line 48 (Example workflow):** "Include: Strategic context link, user story, acceptance criteria, value scores, priority position"
- **Line 268 (GitHub Issue Structure template):** "DO NOT include: Acceptance criteria (BA will add these)"

**Reality:** Should be "Include DRAFT acceptance criteria to frame discussion, but BA will refine during Intake"

**Recommended Fix:** Clarify the GitHub Issue Structure template section to say:

```
## Acceptance Criteria (Draft)
[Provide initial AC to frame the discussion. BA will refine these during Intake.]

Examples:
- User can checkout equipment on iPhone
- Checkout completes offline (no network required)
- Auto-syncs when reconnected
```

**Issue 2: Handoff Checklist Missing**

The PO agent should explicitly state: "Before moving feature-request to 'Ready for Development', ensure:"

```
☑ Strategic context is clear (link to strategic-opportunity)
☑ User story written in "As a... I want... so that..." format
☑ Problem statement documented (why does this matter?)
☑ Scope is bounded (MVP identified, Phase 2+ listed)
☑ Value scores assigned (user value, business value, complexity)
☑ Priority score calculated
☑ Success metrics defined (how will we know this succeeded?)
☑ Draft acceptance criteria provided (BA will refine)
☑ Dependencies identified (blockers? cross-team work?)
☑ Acceptance criteria are in "Confirmation" state (Given/When/Then format preferred)
☑ Moved to "Ready for Development" column in project board
```

Currently, this checklist is implicit but not explicit. Dev orchestrator expects it to be there.

---

## Integration Points Summary

| Handoff | From | To | Status | Notes |
|---------|------|-----|--------|-------|
| 1. PM Idea Input | User | PM Agent | ✅ Clear | `pm-idea` labeled issues trigger PM discovery |
| 2. PM Research → Strategic-opportunity | PM | PO | ✅ Clear | `strategic-opportunity` contains research + decision |
| 3. PO Review & Clarification | PO | PM | ✅ Clear | Comments on strategic-opportunity; async discussion |
| 4. PO Creates Feature-request | PO | Dev | ⚠️ Good with clarifications | See Issue 1 & 2 above |
| 5. Dev Intake → Acceptance Criteria Refinement | Dev/BA | Dev Pipeline | ✅ Clear | Intake validates; BA refines AC; documented in dev orchestrator |
| 6. Feature → Pipeline → Release | Dev | Customer | ✅ Clear | 8-stage pipeline well-documented |

---

## What's Working Well

### 1. **Clear Decoupling of Orchestrators**

PM-PO orchestrator runs **independently** from Development orchestrator:
- ✅ PM-PO never blocks development (backlog always has "Ready for Development" items)
- ✅ Development never waits for PM-PO decisions (pulls from pre-prioritized backlog)
- ✅ Reduces organizational friction

### 2. **Strategic → Tactical → Execution Flow**

- ✅ PM validates market opportunity (research, customer interviews, strategic fit)
- ✅ PO converts to tactical backlog priority (user value, business value, complexity)
- ✅ Dev executes from clear requirements (AC, success metrics)
- ✅ Each role has clear input, decision-making, output

### 3. **Traceability**

- ✅ `feature-request` links to `strategic-opportunity` links to `pm-idea`
- ✅ Complete audit trail from customer problem → strategic decision → tactical work → execution
- ✅ Enables retrospectives ("Did we solve the original problem?")

### 4. **Cross-Functional Workflows**

New skill file [cross-functional-workflows.md](templates/skills/cross-functional-workflows.md) explicitly documents:
- ✅ PM ↔ PO workflow (strategic opportunity review)
- ✅ PO ↔ BA workflow (AC refinement, iterative clarification)
- ✅ PO ↔ Engineering workflow (clarity, daily standups)
- ✅ PO ↔ QA workflow (AC verification, test case design)
- ✅ Meeting cadences (weekly refinement, release planning, post-launch review)

### 5. **Data-Driven Prioritization**

PO agent includes:
- ✅ Prioritization formula (User Value + Business Value) / (Complexity × 1.5)
- ✅ AARRR framework (identify what's broken first)
- ✅ Decision framework (QUICK_WIN vs. STRATEGIC_BET vs. DEFER)

---

## Clarifications Needed

### **Clarification 1: Acceptance Criteria in Feature-Request**

**Current state:**
- Line 48: Include AC in feature-request
- Line 268: Don't include AC (BA will add)
- Section "3 C's Framework": AC written by BA after creation, approved by PO

**Confusion:** Should PO include AC or not?

**Correct interpretation:**
- PO includes DRAFT AC (to frame discussion during Intake)
- BA refines AC to "Confirmation" state (Given/When/Then format)
- Dev builds to refined AC

**Recommended fix:**

Update the "GitHub Issue Structure" section (line 228-270) to clarify:

```markdown
## Acceptance Criteria (Draft - for discussion framing)

Include initial acceptance criteria as discussion starters. These will be refined by BA during Intake.

Format: Starting Point (BA will refine to Given/When/Then)

Examples:
- ☑ User can checkout equipment on iPhone (no website needed)
- ☑ Checkout works offline (no network required)
- ☑ Pending checkouts auto-sync when reconnected

**Important:**
- Keep draft AC brief and outcome-focused
- BA will refine these into testable Given/When/Then format
- DO focus on business outcomes, not implementation
- DO NOT write technical specifications here
```

### **Clarification 2: "Ready for Development" Checklist**

**Current state:**

The PO agent mentions "Ready for Development" column 5+ times but never explicitly lists what makes an issue "Ready."

**Problem:** Dev orchestrator expects issues in this column to be complete. But if PO forgets a field, dev work stalls.

**Recommended addition to PO Agent:**

Add a new section after "Prioritization Decision Process":

```markdown
## Handoff to Development: "Ready for Development" Checklist

Before moving a feature-request to "Ready for Development" in the project board, ensure:

- [ ] Strategic context: Links to source strategic-opportunity issue
- [ ] User story: Follows "As a [role], I want [action], so that [benefit]" format
- [ ] Problem statement: Explains why this matters (not just what)
- [ ] Scope: Clearly bounded (MVP defined; Phase 2+ deferred)
- [ ] Value assessment: User value (1-5), Business value (1-5), Complexity (1-5)
- [ ] Priority score: Calculated using formula; interpreted as QUICK_WIN / STRATEGIC_BET / DEFER
- [ ] Success metrics: Defined how we'll measure this feature's impact (not just completion)
- [ ] Draft acceptance criteria: Included as framing for BA to refine
- [ ] Dependencies: Identified (is this blocked? does it block others?)
- [ ] No ambiguities: Is there anything BA might question?
- [ ] Linked to PM research: Dev can trace back to customer validation

**If any item is missing:** Don't move to "Ready for Development". Dev will reject it, and you'll be blocked.

**If dev escalates:** They'll create a comment; respond promptly to clarify.
```

### **Clarification 3: BA-PO Collaboration During Intake**

**Current state:**

The "3 C's Framework" section explains BA refinement well, but it's positioned as a general framework, not as a required step in the PO → Dev handoff.

**Problem:** PO might think their job ends when they create the issue. But BA needs PO engagement during Intake.

**Recommended note in PO Agent:**

Add after "Step 5: Collaborate with BA":

```markdown
## Acceptance Criteria Refinement (During Intake)

The BA will refine draft AC during Intake using the "3 C's Framework":

1. **Conversation:** BA asks clarifying questions
   - "What if network drops mid-checkout?"
   - "Do we support iPad or iPhone only?"
   - "What's acceptable performance? <2 sec? <5 sec?"

2. **You respond:** Provide context + make trade-off decisions
   - "Online + offline, auto-sync on reconnect"
   - "iPhone only for MVP, iPad in Phase 2"
   - "<2 seconds for best-case, <5 seconds for worst-case"

3. **Confirmation:** BA writes Given/When/Then criteria
   - "Given: User on mobile with network, When: submits checkout, Then: confirms <2 seconds"
   - "Given: Network drops mid-submit, When: reconnected, Then: auto-syncs"

**Your role:** Be responsive to BA questions. This happens in Intake; don't disappear.
```

---

## Specific Asset Flow Verification

### Inputs to PM Agent

✅ **Source:** `pm-idea` labeled GitHub issues  
✅ **Content:** 1-3 sentence feature idea + optional context  
✅ **Trigger:** Orchestrator checks for `pm-idea` label every N hours  
✅ **Example:** "Mobile app for field teams" (from pm-orchestrator.agent.md)

### Outputs from PM Agent

✅ **Target:** `strategic-opportunity` GitHub issues (labeled `pm-opportunity`)  
✅ **Contains:** Research findings, validation assessment, decision (CHAMPION/DEFER/BLOCK)  
✅ **Links to:** Source `pm-idea` issue  
✅ **Routable:** PO reads and prioritizes (or defers)

### Inputs to PO Agent

✅ **Source:** `strategic-opportunity` issues from PM  
✅ **Content:** Research findings, customer validation, strategic decision  
✅ **Process:** PO reads, asks clarifying Qs in comments, waits for PM response  
✅ **Example:** Mobile checkout strategic-opportunity from PM

### Outputs from PO Agent

✅ **Target:** `feature-request` GitHub issues (labeled `feature-request` + `po-prioritized`)  
✅ **Contains:** User story, problem, value scores, priority, success metrics, draft AC  
✅ **Links to:** Source `strategic-opportunity` issue  
✅ **Routable:** Dev pulls from "Ready for Development" column

### Inputs to Dev Orchestrator

✅ **Source:** `feature-request` issues in "Ready for Development" column  
✅ **Content:** User story, value scores, priority, success metrics, draft AC, dependencies  
✅ **Links to:** Source `strategic-opportunity` (full PM research chain)  
✅ **Trigger:** Dev orchestrator pulls highest-priority issue from column  
✅ **Process:** Intake Agent validates clarity; escalates to PO if needed

---

## Skill File Alignment

### PM Agent Skills (Existing)

✅ [prioritization-frameworks.md](templates/skills/prioritization-frameworks.md) — RICE, Value vs. Effort, OKR alignment  
✅ [financial-modeling.md](templates/skills/financial-modeling.md) — Revenue, LTV, CAC, ROI calculations  
✅ [stakeholder-alignment.md](templates/skills/stakeholder-alignment.md) — Disagreement resolution, escalation  
✅ [learning-cycles.md](templates/skills/learning-cycles.md) — 2-sprint feedback loops, kill decisions

### PO Agent Skills (Newly Created)

✅ [release-coordination.md](templates/skills/release-coordination.md) — Release planning, staging gates, feature flags  
✅ [metrics-and-experimentation.md](templates/skills/metrics-and-experimentation.md) — AARRR, funnel analysis, A/B testing  
✅ [stakeholder-alignment-po.md](templates/skills/stakeholder-alignment-po.md) — Saying no, priority communication  
✅ [feedback-loops-and-learning.md](templates/skills/feedback-loops-and-learning.md) — A.C.A.F. framework, NPS, 5+ rule  
✅ [cross-functional-workflows.md](templates/skills/cross-functional-workflows.md) — PM ↔ PO, PO ↔ BA, PO ↔ Eng workflows

### Integration

✅ Both PM and PO agents link to their respective skill files  
✅ Both follow same modular structure (inline guidance + external skills)  
✅ Cross-functional-workflows.md explicitly covers PO ↔ BA handoff (Intake refinement)  
✅ Cross-functional-workflows.md explicitly covers PO ↔ Engineering workflow (clarity, standups)

---

## Recommendations

### Immediate (High-Priority Clarifications)

1. **Update "GitHub Issue Structure" section** to clarify AC guidance:
   - Change "DO NOT include: Acceptance criteria" to "Include DRAFT AC for discussion framing"
   - Provide example of draft AC format
   - Explain that BA will refine to Given/When/Then

2. **Add "Ready for Development Checklist"** to PO Agent:
   - Explicit list of requirements before moving issue to column
   - Prevents incomplete handoffs to dev
   - Serves as quality gate

3. **Add "BA-PO Collaboration During Intake"** section:
   - Clarify that PO stays engaged during Intake
   - Explain conversation/confirmation steps
   - Set expectation for response time

### Short-term (Enhancement)

4. **Add workflow diagram** to pm-orchestrator.agent.md:
   - Visual representation of PM discovery → decision → PO intake → feature-request creation
   - Helps new team members understand flow

5. **Create integration guide** (new file) that documents:
   - Complete PM → PO → Dev flow
   - Issue templates (pm-idea, strategic-opportunity, feature-request)
   - Column states (To Do → Ready for Development → In Progress → etc.)
   - What makes an issue "ready" for each stage

6. **Add "Escalation to PO" guidance** to dev orchestrator:
   - Currently mentions escalation but not details
   - Example: When would Intake escalate to PO?
   - What's the response time expectation?
   - How does dev unblock?

### Long-term (Validation)

7. **Test full workflow end-to-end:**
   - Create a `pm-idea` issue
   - Run PM agent autonomously
   - Create `strategic-opportunity`
   - Run PO agent to create `feature-request`
   - Run Dev orchestrator intake
   - Verify traceability (pm-idea → strategic-opportunity → feature-request → build)

---

## Conclusion

**The PM ↔ PO ↔ Dev workflow melts together well.** The three orchestrators (PM, PO, Dev) form a cohesive pipeline with clear handoffs, traceability, and decoupling.

**Key strengths:**
- ✅ Strategic research feeds tactical prioritization
- ✅ Tactical prioritization feeds execution
- ✅ Execution never blocks PM-PO; PM-PO never blocks execution
- ✅ Traceability from problem → decision → execution
- ✅ Cross-functional workflows documented

**Clarifications needed:**
- ⚠️ Acceptance criteria guidance (draft vs. final)
- ⚠️ "Ready for Development" checklist (explicit requirements)
- ⚠️ BA-PO collaboration during Intake (when PO needs to respond)

**Recommendation:** Implement the three immediate clarifications above. They're quick wins that will make the workflow crystal clear for new team members and prevent handoff surprises.

---

## Files Referenced

- `templates/agents/orchestrator.pm-po.agent.md` — PM-PO orchestrator logic
- `templates/agents/product-manager.agent.md` — PM agent workflow
- `templates/agents/product-owner.agent.md` — PO agent workflow
- `templates/agents/orchestrator.development.agent.md` — Dev orchestrator logic
- `templates/skills/cross-functional-workflows.md` — PM ↔ PO, PO ↔ BA, PO ↔ Dev workflows
- `docs/02-module-2-intake-quality-template.md` — Intake quality template (referenced by PO agent)

---

## Next Steps

1. Review the three clarifications above
2. Implement changes to PO agent (clarifications 1-3)
3. Schedule end-to-end workflow test
4. Gather feedback from actual PM, PO, and dev team usage
