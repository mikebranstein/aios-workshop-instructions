---
description: "⚠️ DEPRECATED - Orchestrator v8 has been split into two independent loops. See orchestrator.pm-po.agent.md and orchestrator.development.agent.md instead."
tools: ["*"]
---

# ⚠️ DEPRECATED: Orchestrator v8

**This file is deprecated.** Orchestrator v8 has been split into **two independent, concurrent orchestrator loops** that do not block each other.

## Use These Instead

1. **[orchestrator.pm-po.agent.md](orchestrator.pm-po.agent.md)** — Product Manager + Product Owner loop
   - Runs continuously and independently
   - Discovers opportunities, validates with customers, prioritizes backlog
   - Outputs: Pre-prioritized backlog in "Ready for Development" column
   - **Never blocked by development; never blocks development**

2. **[orchestrator.development.agent.md](orchestrator.development.agent.md)** — Development pipeline loop
   - Runs continuously and independently
   - Pulls from PM-PO backlog, executes Intake through Release
   - Inputs: Pre-prioritized issues from "Ready for Development" column
   - **Never waits for PM-PO decisions**

## Why the Split?

Previous architecture: PM-PO-Intake-Development were sequential, causing bottlenecks:
- If PM-PO argued about priorities, development couldn't start
- If development hit a blocker, PM-PO had to wait

New architecture: Two independent loops running concurrently:
- PM-PO can iterate, prioritize, and re-prioritize without blocking development
- Development always pulls from a pre-prioritized backlog and never waits
- Throughput is maximized; no blocking dependencies

---

## Historical Reference (Deprecated Content Below)

The rest of this file contains the old v8 orchestrator for historical reference. **Do not use it.** Refer to the split orchestrators above.

### Cycle Start: Ensure Authoritative State

Before each cycle, establish authoritative context:

```bash
# Step 0: Return to main and refresh skill files
git checkout main
git pull origin main

# Why: Product Manager and Product Owner need access to latest skill contracts, 
# agents, and strategic frameworks. After any feature branch work, reset to main 
# to reference authoritative versions and get fresh GitHub state.
```

### Step 0.5: Trigger PM Discovery Agent (if new ideas exist)

Before entering the PO prioritization stage, check for new PM discovery work:

```bash
# Check for issues with pm-idea label (new feature ideas submitted)
PM_IDEAS=$(gh issue list --label pm-idea)

if [ ! -z "$PM_IDEAS" ]; then
  # Trigger PM discovery agent on each new idea
  for ISSUE in $PM_IDEAS; do
    echo "Triggering PM discovery for: $ISSUE"
    PM_AGENT autonomous-discover $ISSUE
  done
fi
```

**Why**: Ensures new feature ideas are validated by PM before PO prioritizes. PM validation happens asynchronously; orchestrator waits for all PM discoveries to complete before moving to PO stage.

**What happens**:
1. PM agent reads issue with `pm-idea` label
2. Agent autonomously runs discovery, validation, decision
3. Agent posts research findings, validation results, decision as comments
4. Agent applies labels and moves issue to Projects board
5. If CHAMPION: Issue is ready for PO prioritization
6. Orchestrator notifies PO of new opportunities

**See**: [pm-discovery-README.md](../pm-discovery-README.md) for user guide

### Stage 1: Product Manager — Strategic Opportunity Discovery

**Who:** Product Manager (strategic leadership)

**Inputs:** Market research, customer feedback, competitive analysis

**Process:**
1. Discover customer problems through user interviews, support feedback, competitive analysis
2. Validate opportunities with customers (do they confirm this is a problem? Strong signal?)
3. Evaluate against strategic vision and priorities (does this align?)
4. Post decision: CHAMPION / VALIDATE_PILOT / DEFER / BLOCK
5. If CHAMPION: Create GitHub issue with strategic context (market opportunity, validation, business impact)

**Decision states:**
- **CHAMPION:** Validated opportunity that aligns with strategy. Route to PO immediately.
- **VALIDATE_PILOT:** Promising but needs more customer validation. Run pilot before full commitment.
- **DEFER:** Real problem but not strategically important now. Revisit in next quarter.
- **BLOCK:** Not aligned with strategy or not validated. Skip it.

**Output:** GitHub issue labeled `pm-opportunity` with decision comment

**Routing (from Stage 1):**
- If CHAMPION → Move to Stage 2 (Product Owner)
- If VALIDATE_PILOT → Create pilot issue; run parallel discovery; return to Stage 1 when ready
- If DEFER or BLOCK → Close issue; archive in decision log

### Stage 2: Product Owner — Tactical Prioritization

**Who:** Product Owner (tactical execution)

**Inputs:** Strategic opportunities from PM; customer requests; support feedback; business metrics

**Process:**
1. Review PM-championed opportunity
2. Assess against tactical backlog: What's the business value? How complex is it?
3. Use prioritization framework: (User Value + Business Value) / (Complexity × 1.5)
4. Decide: Where in backlog does this go? Quick win? Strategic bet? Defer?
5. Collaborate with BA if requirements are unclear
6. Move to Stage 3 (Intake) when ready

**Decision states:**
- **PRIORITIZED_HIGH:** Quick win (high value + low complexity) or strategic priority. Move to Intake immediately.
- **PRIORITIZED_MID:** Medium priority. Queue for development in next 2 sprints.
- **BACKLOG:** Lower priority. Keep in backlog; revisit monthly.
- **BLOCKED:** Can't build without dependencies. Wait for blocker to clear.

**Output:** GitHub issue labeled `po-prioritized` with decision comment; positioned in GitHub Projects backlog

**Routing (from Stage 2):**
- If PRIORITIZED_HIGH → Move to Stage 3 (Intake)
- If PRIORITIZED_MID or BACKLOG → Hold in backlog; revisit during next prioritization cycle
- If BLOCKED → Add label `blocked-on` with dependency reference; revisit when blocker clears

### Stage 3: Intake → BA → Design → Build → Verification → QA → Policy → Release

**Who:** Intake Agent (first step in development pipeline)

**Process:**
1. Pull next highest-priority issue from backlog (from Stage 2)
2. Validate requirements are clear (if not, ask BA for clarification)
3. Route to BA for requirements definition
4. Intake through the complete 8-stage pipeline (established in Modules 8-12)

**Routing (full pipeline):**
```
Intake → BA → Design → Build → Verification → QA

If QA passes:
  ├─ If design flagged `policy-review-required` → Policy review
  └─ If no policy flag → Auto-merge to main (low-risk)

If policy review:
  ├─ If `policy-approved` → Merge and release
  ├─ If `policy-escalated` → Hold for leadership decision
  └─ If `policy-blocked` → Back to Design for re-evaluation

Release → Deployed to production
```

---

## PM ↔ PO Collaboration Points

### Collaboration 1: Strategic Priority Alignment

**When:** Quarterly or when strategy changes

**What happens:**
1. PM presents strategic vision and priorities for next quarter
2. PO reviews backlog against new priorities
3. If priorities changed, PO re-prioritizes backlog accordingly
4. Team gets updated roadmap

**Example:**
```
PM: "Market analysis shows enterprise segment is our growth opportunity. 
Q3 priorities shift: Mobile app now #1, API integrations #2. 
Defer cosmetic improvements."

PO: "Understood. I'll re-prioritize backlog. Mobile app moves to top. 
API integrations queued for mid-Q3. Cosmetic work deferred to Q4."
```

### Collaboration 2: Opportunity Validation

**When:** PM discovers opportunity that needs PO input

**What happens:**
1. PM posts opportunity decision with validation
2. PO reviews and assesses business value
3. PO advises: "Resonates with customers" / "Low demand" / "Different problem than expected"
4. PM uses feedback for refinement

**Example:**
```
PM: "Market research shows 15/25 customers frustrated with manual reports. 
Proposing: Auto-generated daily dashboard."

PO: "Good signal. I've heard similar from sales. 3 customers willing to beta-test. 
I'd prioritize this for Q3."

PM: "Great. I'll champion it. You prioritize when ready."
```

### Collaboration 3: Customer Request Escalation

**When:** Customer requests feature during sales call or support

**What happens:**
1. Sales/Support flags request to PO
2. PO escalates to PM: "Is this strategic? Should we prioritize?"
3. PM assesses: Strategic fit, customer validation, competitive value
4. PM advises: "Strategic priority" / "Customer-specific need" / "Defer"
5. PO uses input for backlog decision

**Example:**
```
Sales: "Enterprise customer ABC wants custom branding in reports."

PO: @[PM] Is custom branding strategic or customer-specific?

PM: "Checked with other customers. Only ABC mentioned it. 
It's a customer-specific need, not a market opportunity. 
I'd deprioritize it; offer as custom services instead."

PO: "Agreed. I'll tell sales to position as a premium service, not feature."
```

### Collaboration 4: Backlog Refinement

**When:** Weekly or bi-weekly PO sync with PM

**What happens:**
1. PO shows top 5 backlog items to PM
2. PM validates they're aligned with strategy
3. PM provides context: "This customer request came from competitor pressure" / "This came from user research"
4. PO adjusts priority if needed based on PM context

---

## Decision Framework: When to Escalate Between Stages

### Does PM escalate to leadership (not pictured)?

**When:** Strategic decision requires C-level input

Examples:
- Entering new market segment (revenue/risk decision)
- Pivoting product direction (strategy shift)
- M&A implications (new capabilities we should acquire)

### Does PO escalate back to PM?

**When:** Prioritization decision depends on strategic context

Examples:
- Two features competing for same resources; need strategic tiebreaker
- Customer request conflicts with roadmap; need PM judgment
- Effort doubled; does this feature still make strategic sense?

### Does Intake/BA escalate to PO?

**When:** Requirements are ambiguous or conflict with backlog

Examples:
- Requirements don't match original feature opportunity from PM
- Customer request changed; scope has grown
- Design complexity suggests feature should be split

---

## GitHub Workflow

### Labels Used

- `pm-opportunity` — Feature proposed by Product Manager
- `po-prioritized` — Feature prioritized by Product Owner; ready for development
- `blocked-on` — Feature blocked by dependency; includes reference to blocking issue
- `development` — Feature in active development (Intake through Release)
- `policy-review-required` — Flagged by Design; requires policy gate
- `qa-passed` — QA validated; ready for policy or release
- `policy-approved` — Policy gate approved; ready to merge and release
- `policy-escalated` — Policy gate escalated; awaiting leadership decision
- `policy-blocked` — Policy gate blocked; back to Design

### GitHub Projects Board

```
Columns:
1. PM Discovery (opportunities being researched)
2. PO Backlog (prioritized items waiting for development)
3. In Development (Intake through Release)
4. Policy Review (if flagged as high-risk)
5. Released (shipped to production)
6. Blocked (waiting for dependency)
7. Deferred (strategic hold; revisit quarterly)
```

---

## Timing: How Long Does It Take?

**Typical flow (single feature):**
- PM opportunity discovery: 1-2 weeks (research, validation)
- PO prioritization: 1-2 weeks (backlog assessment, BA alignment)
- Development pipeline: 2-4 weeks (Intake → Release)
- **Total: 4-8 weeks from opportunity to production** (depending on complexity)

**Parallel flows:**
- While Feature A is in development, PM discovers Feature B
- While Feature B is in PO prioritization, Feature A ships
- Multiplies throughput without adding people

---

## Model Selection by Capability

Use different PM and PO agents based on feature complexity and risk:

**Product Manager Agents:**
- **Tier 1 (Strategic Director):** Enterprise market analysis, competitive strategy, multi-quarter roadmap
- **Tier 2 (Senior PM):** Customer discovery, opportunity validation, prioritization advice
- **Tier 3 (PM):** Feature research, customer interview summaries, competitive analysis

**Product Owner Agents:**
- **Tier 1 (Executive PO):** Cross-product backlog prioritization, strategic trade-offs, roadmap alignment
- **Tier 2 (Senior PO):** Backlog management, BA collaboration, customer feedback prioritization
- **Tier 3 (PO):** Issue creation, GitHub workflow, sprint planning

---

## Expected Outcomes

After completing PM → PO orchestration:

✅ Strategic opportunities are discovered and validated before building
✅ Features in development align with product vision
✅ Backlog is ordered by strategic importance + business value
✅ PM and PO collaborate effectively (strategy → execution)
✅ Development pipeline receives well-prioritized, market-validated features
✅ Fewer surprises ("Why are we building this?"); more clarity ("This aligns with strategy")
✅ Product evolution is directional and defensible, not reactive
✅ New ideas flow through autonomous PM discovery (users input 1-3 sentences, agent validates)
✅ State tracked in GitHub (transparent, auditable, continuously updated)

---

## Quarterly Cycle: PM Re-evaluation

Every quarter, trigger PM agent in quarterly-review mode to ensure strategy stays current:

```bash
# Quarterly PM re-check (run at start of each quarter)
PM_AGENT quarterly-review

# What the agent does:
# 1. Queries all issues with label: pm-opportunity
# 2. For each issue:
#    - Posts: "Quarterly review: Re-assessing customer interest and market fit"
#    - Re-evaluates market signals (customer demand still strong?)
#    - Checks for competitive changes (did market shift?)
#    - Verifies strategic alignment (still fits Q[next] priorities?)
#    - Recommends: maintain CHAMPION, demote to DEFER, or BLOCK
# 3. Updates labels and decision if needed
# 4. Posts final quarterly verdict as comment
```

**Why**: Market conditions and strategic priorities change. Quarterly re-checks ensure:
- ✅ Opportunities remain strategically important
- ✅ Customer interest hasn't waned
- ✅ Competitive landscape hasn't shifted
- ✅ Business goals still align

**Output**: Issues labeled `pm-opportunity` have a quarterly review comment.

---

## Troubleshooting

**Issue: Features keep getting deprioritized**
- **Root cause:** Feature doesn't align with current strategic priorities
- **Fix:** PM needs to revisit strategy. Run quarterly review to determine if CHAMPION status should change.

**Issue: PO and PM disagree on prioritization**
- **Root cause:** Misalignment on strategic importance or market validation
- **Fix:** PM and PO sync together. Escalate to leadership if needed.

**Issue: Feature ships but customers aren't happy**
- **Root cause:** Opportunity validation was weak. Didn't uncover enough customer signals.
- **Fix:** PM needs to increase research depth in discovery phase.

**Issue: Development backlog grows but nothing ships**
- **Root cause:** Features are poorly scoped or have hidden dependencies
- **Fix:** PO and BA need better upfront refinement. Design needs to flag complexity earlier.

**Issue: PM discovery agent isn't finding the right opportunities**
- **Root cause:** Agent doesn't have enough context or data to evaluate ideas
- **Fix:** Provide richer GitHub issue body (customer quotes, ticket references, competitive context). Agent learns from context.

**Issue: Too many deferred ideas accumulating**
- **Root cause:** Ideas are valid but not strategic *right now*
- **Fix:** Quarterly re-checks will reassess. Market conditions may change priority. Keep deferred list manageable (max 10-15 ideas).
