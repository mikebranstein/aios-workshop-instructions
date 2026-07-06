# PM Agent Enhancement Plan: Closing Critical Gaps

This document provides ready-to-implement improvements to `product-manager.agent.md` based on the revised gap analysis.

---

## TIER 1: CRITICAL ADDITIONS (1-2 hours implementation)

### 1️⃣ WIN/LOSS ANALYSIS SUBSECTION

**Location:** Add after "Step 2: Discover market opportunities through research"

**Content to Insert:**

```markdown
### Step 2d: Win/Loss Analysis & Competitive Understanding

Understanding why customers choose you or competitors is crucial for strategy.

**Win/Loss Analysis Process:**

Run this quarterly with Sales team.

**Win Analysis (why do customers choose us?):**

Track these data points for every closed deal:

1. **What problem did they have?** (paint point)
2. **How did they find us?** (discovery channel)
3. **Why did they choose us over competitors?** (key differentiators)
4. **Which competitor did they consider?** (competitive set)
5. **What was the deciding factor?** (price, features, service, brand, timing)

Example:

```
Customer: Acme Corp (Enterprise)
Problem: Equipment tracking across 5 facilities
Considered: Competitor A (enterprise-focused), Competitor B (budget option)
Decision: Chose us because of real-time GPS + API ecosystem
Differentiator quote: "They're the only one who integrates with our FM system"
Timeline: 8-week sales cycle
```

**Loss Analysis (why do customers choose competitors?):**

For every lost deal, conduct brief exit interview:

1. **What problem were they trying to solve?**
2. **Which competitor won?**
3. **Why did they choose competitor?** (what did we miss?)
4. **Was it solvable?** (product gap, price, timing, sales execution)
5. **How confident are they in that choice?** (strong signal if they're worried)

Example:

```
Prospect: Mid-market manufacturing company
Problem: Equipment tracking for field teams
Lost to: Competitor C
Reason: Cheaper pricing ($2K/year vs. our $5K/year)
Product gap: We don't have mobile app yet (they need field access)
Avoidable?: Yes - if we had mobile app + matched pricing
Buyer confidence: Medium (they liked our feature set; price was barrier)

Action: Track as "price-sensitive SMB" segment; mobile app could win back
```

**Quarterly Win/Loss Meeting:**

1. **Aggregate data:** 15-20 wins + 5-10 losses from sales team
2. **Find patterns:**
   - Which differentiators win consistently? (our moats)
   - What do competitors win on? (our weaknesses)
   - Which customer segments do we win/lose in?
   - What's the most common objection? (product, price, timing, competition)
3. **Strategic implications:**
   - Is this changing our strategy? (market shift)
   - Do we have a product gap? (OKR priority?)
   - Should we adjust pricing or positioning?
4. **Document:** Store in strategic decision log

**Key Insight:** Win/loss analysis reveals what customers actually value, vs. what you think they value. Patterns of losses in a specific segment = product or go-to-market gap to address.
```

---

### 2️⃣ EXECUTIVE COMMUNICATION SUBSECTION

**Location:** Add to "Communication Cadence & Documentation" section

**Content to Insert:**

```markdown
**Monthly executive briefing (30 min with CEO + CFO + Board):**

Separate from QBR (which is quarterly). Monthly briefing keeps execs aligned and catches issues early.

Content:
- Top 3 OKR metrics: On track? Trending up or down? (2 min)
- 1 risk to mitigate: What could go wrong with current strategy? (2 min)
- 1 opportunity to decide: What new market/feature should we prioritize? (2 min)
- Last month's wins: What did we ship? Customer impact? (1 min)
- Blocker/escalation: Do we need exec decision on anything? (3 min)

Format: 1-page doc with charts (not long narrative). Execs should understand in 2 minutes.

Why separate from QBR? QBR is deep strategic review (2 hours). Monthly briefing is "stay in sync" (30 min).

Example briefing:

```
**[COMPANY] Product Monthly Briefing | July 2026**

**OKR Progress:**
- Mobile adoption: 45% (target: 50% by EOQ). On track. +8% month-over-month.
- Enterprise NPS: 7.8 (target: 8.0). Slight dip from privacy concerns post-launch.
- API ecosystem: 8 integrations live (target: 10). On track.

**1 Risk to Mitigate:**
- Competitor A just launched mobile app (we predicted September; they shipped July).
- Impact: May slow mobile adoption if they undercut on price.
- Mitigation: Sales team emphasizing our API moat + enterprise features.
- Decision needed: Should we accelerate any feature?

**1 Opportunity:**
- Win/loss analysis shows 40% of mid-market losses are due to lack of reporting dashboard.
- Market size: 50+ mid-market prospects in pipeline.
- Build effort: 6 weeks.
- Recommendation: Add "Advanced Reporting" to Q4 roadmap. Could unlock $300K ARR.
- Decision needed: Prioritize vs. other Q4 work?

**Last Month Wins:**
- Shipped GPS equipment tracking (8% adoption, 2.1% user churn impact = net positive).
- Customer testimonial: Acme Corp (Fortune 500) considering buying 3x more seats.
- New integration: Partnered with Salesforce for CRM sync.

**Blocker:**
- None. Execution on track.
```
```

---

### 3️⃣ LAUNCH OPERATIONS SUBSECTION

**Location:** Add after "Launch playbook (create before build starts)" subsection

**Content to Insert:**

```markdown
**Launch operations (critical first 48 hours):**

Launch week is high-risk. Have operational structure in place.

**Daily standup during launch week (5-10 min, 9 AM):**

Participants: PM, Eng lead, Design, BA, Support lead, QA.

Agenda:
- Any critical issues overnight? (bugs, performance, support volume spike)
- Metrics: adoption %, churn, support tickets, performance.
- Should we roll back? (if success criteria missed)

Decision rights:
- If adoption <5% in first 24h: investigate (bad UX? wrong target? discovery issue?)
- If churn spike >2%: investigate (did we break something?)
- If support volume >5 tickets/1000 users: investigate (is feature confusing?)
- If critical bug: rollback immediately; diagnose in parallel

**On-call rotation (first 48 hours after launch):**

Designate on-call lead with authority to:
- Rollback feature (if critical issue)
- Page engineers if performance degradation
- Communicate status to exec team if issue is customer-facing

On-call lead: PM or Eng lead (whoever has decision authority)

**Escalation path:**

Issue severity → escalation time:
- Critical (down for customers): Page eng lead immediately
- High (major bug, churn spike): Notify PM + eng lead within 15 min
- Medium (support tickets piling up): Address in daily standup
- Low (UI polish): Address in retrospective

**Rollback decision framework:**

Roll back if ANY of these hit:
- Critical bug (data corruption, security, downtime)
- Adoption <2% after 24 hours (likely UX or discovery problem)
- Churn spike >3% (we broke something important)
- Support volume >8 tickets/1000 users (confusing feature)

Document the rollback decision + learnings. Plan to re-launch after fixing.

**Communication during launch:**

- Status page: Update every hour if there's an active issue
- Slack channel: Create #launch-gps-tracking for real-time updates
- Customer escalations: PM owns communication to affected customers
- Post-incident report: Within 24 hours if we had any issues
```

---

## TIER 2: IMPORTANT ADDITIONS (2-4 hours implementation)

### 4️⃣ PRIORITIZATION FRAMEWORKS COMPARISON

**Location:** Add new subsection in "Step 3: Evaluate and validate opportunities" 

**Content to Insert:**

```markdown
### Step 3c: Prioritization Frameworks Comparison

Different frameworks work for different contexts. Use the right tool for your situation.

**RICE Framework (Reach, Impact, Confidence, Effort)**

Best for: Objective comparison of many initiatives

Formula: (Reach × Impact × Confidence) / Effort = Priority Score

- **Reach:** How many customers affected per quarter? (e.g., 500 users)
- **Impact:** What's the value created per customer? (3x = 3 months impact; 2x = 2 months impact; 1x = 1 month impact; 0.5x = minimal impact)
- **Confidence:** How confident are you in the estimate? (100% = certain; 50% = moderate; 25% = low)
- **Effort:** How many weeks of engineering effort?

Score interpretation:
- >100: Quick win (do immediately)
- 50-100: High priority
- 25-50: Medium priority
- <25: Low priority (defer)

Example:

```
Initiative A: GPS Equipment Tracking
- Reach: 150 customers (30% of base) = 150
- Impact: Reduces support tickets by 20% = 2x = 2 months value
- Confidence: 60% (guessing on adoption) = 0.6
- Effort: 6 weeks

Score: (150 × 2 × 0.6) / 6 = 30

Initiative B: Mobile App
- Reach: 400 customers (80% of base) = 400
- Impact: Increases retention by 5% = 1.5x = 1.5 months value
- Confidence: 80% (strong customer demand) = 0.8
- Effort: 10 weeks

Score: (400 × 1.5 × 0.8) / 10 = 48

Ranking: Mobile App (48) > GPS Tracking (30)
```

**Value vs. Effort Matrix (2x2)**

Best for: Quick visual prioritization; cross-functional alignment

Axes:
- X-axis: Effort (Low → High)
- Y-axis: Value (Low → High)

Quadrants:
- **High Value, Low Effort:** QUICK WINS. Do these first.
- **High Value, High Effort:** STRATEGIC BETS. Plan these carefully.
- **Low Value, Low Effort:** NICE-TO-HAVE. Do these if time permits.
- **Low Value, High Effort:** AVOID. Don't waste time here.

Use when: You have 8-12 initiatives to prioritize quickly with stakeholders.

**OKR-Based Prioritization**

Best for: Strategic alignment; clear north star

Method:
1. Define annual OKRs
2. For each initiative: "Which OKR does this ladder to?"
3. Prioritize initiatives by OKR importance
4. Within each OKR, order by effort

Example:

```
OKR 1: Achieve 60% mobile adoption (highest priority)
- Mobile app (required for OKR)
- Push notifications (enables feature discovery)
- Mobile redesign (improves stickiness)

OKR 2: Build API ecosystem (medium priority)
- Salesforce integration (requested by 10 customers)
- Slack bot (nice-to-have)

OKR 3: Land Fortune 500 (medium priority)
- Enterprise SSO (required for deals)
- Advanced analytics dashboard (differentiator)

Prioritized list (by OKR + effort):
1. Mobile app (OKR 1, critical)
2. Enterprise SSO (OKR 3, required)
3. Push notifications (OKR 1, accelerator)
4. Salesforce integration (OKR 2, high value)
5. Advanced analytics (OKR 3, nice-to-have)
```

**When to Use Each Framework:**

| Situation | Best Framework | Why |
|-----------|---|---|
| Comparing 15+ initiatives objectively | RICE | Numbers are unbiased; easy to explain |
| Quick prioritization with team in room | Value vs. Effort | Visual; collaborative; fast |
| Aligning to strategy | OKR-based | Ensures everything serves north star |
| Mix of new features + tech debt | RICE + OKR-based | RICE for initial rank; OKR for strategy fit |

**Recommendation:** Use RICE for quarterly planning (objective). Use Value vs. Effort in sprint planning (collaborative). Use OKR-based for strategy reviews (alignment check).
```

---

### 5️⃣ FINANCIAL MODELING SUBSECTION

**Location:** Add to "Step 2c: Quantitative analysis and metrics framework"

**Content to Insert:**

```markdown
### Step 2d: Financial Modeling & Forecasting

Numbers tell a strategic story. Use financial models to forecast impact and justify investment.

**3-Year Revenue Projection Model:**

Build this annually. Update quarterly.

Inputs:
- Current cohort: DAU, MAU, average revenue per user (ARPU)
- Cohort retention: What % of users from each month stay?
- Churn rate: Monthly churn %
- CAC (customer acquisition cost)
- LTV (lifetime value = ARPU / monthly churn rate)

Calculate:
- Year 1 ARR (current cohort + new users)
- Year 2 ARR (cohorts mature; churn impacts)
- Year 3 ARR (steady state)

Example:

```
Current State (July 2026):
- DAU: 5,000
- Monthly churn: 5%
- ARPU: $500/user/year = $42/user/month
- CAC: $50

Cohort Retention (Jul 2026 cohort):
- Month 1: 100% (5,000 users)
- Month 3: 92% (4,600 users, 8% churned)
- Month 6: 82% (4,100 users, 18% churned)
- Month 12: 60% (3,000 users, 40% churned)
- Month 24: 35% (1,750 users, 65% churned)

3-Year Revenue Model:

Year 1 (2026):
- Jul cohort: 5,000 users × $500 × 6 months = $1.5M
- Aug cohort: 4,000 users × $500 × 5 months = $833K
- Sep-Dec cohorts: Similar ramp
- Year 1 Total ARR: ~$3M

Year 2 (2027):
- Year 1 cohorts churn; new users added
- Jul 2026 cohort: 1,800 users × $500 = $900K (at 36% retention)
- Full year of new cohorts: ~4M new users added
- Year 2 Total ARR: ~$8M

Year 3 (2028):
- Steady state: churn balanced by new acquisition
- Year 3 Total ARR: ~$12M
```

**Unit Economics Check:**

For each customer cohort:

- **CAC payback period:** How many months to recover acquisition cost?
  - Formula: CAC / (ARPU / 12) = months to payback
  - Target: <12 months (ideally <6 months)
  - Example: $50 CAC / ($42/month ARPU) = 1.2 months (excellent)

- **LTV:CAC ratio:** Lifetime value vs. acquisition cost
  - Formula: LTV / CAC = ratio
  - Target: >3:1 (ideally >5:1)
  - Example: ($500/user LTV) / ($50 CAC) = 10:1 (excellent)

**Financial Impact of Decisions:**

For each significant initiative, estimate financial impact:

```
Initiative: Mobile App

Scenario 1 (Optimistic):
- Increases retention from 60% to 75% year 1 (15 point improvement)
- Attracts 1,000 new mobile-first users/month
- Revenue impact: +$500K ARR year 1; +$2M ARR year 2

Scenario 2 (Base Case):
- Increases retention from 60% to 70% year 1 (10 point improvement)
- Attracts 500 new mobile users/month
- Revenue impact: +$250K ARR year 1; +$1M ARR year 2

Scenario 3 (Conservative):
- Increases retention from 60% to 65% year 1 (5 point improvement)
- Attracts 200 new mobile users/month
- Revenue impact: +$50K ARR year 1; +$300K ARR year 2

Build cost: 10 weeks; assume +$1.5M/year operating cost

ROI Analysis:
- Base case payback: +$250K year 1 revenue - $1.5M cost = -$1.25M (loss)
- But: +$1M ARR year 2 + $1.2M year 3 = net positive by year 3
- Conclusion: Strategic investment; expected positive ROI year 2-3

Decision: CHAMPION (strategic moat, positive LTV impact)
```

**Quarterly Financial Review:**

Track actual vs. forecast:

- Is retention improving as expected?
- Are new cohorts better or worse than modeled?
- Should we adjust the 3-year forecast?
- What's our path to profitability?

Update financial model quarterly. Share with CFO and board.

**Key Insight:** Financial models don't predict the future (they're always wrong). But they force you to articulate your assumptions. "If we get 70% retention and 5% monthly growth, we hit $10M ARR by year 3" is a clearer strategy than "let's build mobile and see what happens."
```

---

### 6️⃣ STAKEHOLDER ALIGNMENT & DISAGREEMENT HANDLING

**Location:** Add new subsection to "Communication Cadence & Documentation"

**Content to Insert:**

```markdown
**Handling Strategic Disagreement (PM ↔ PO ↔ Exec):**

Not every stakeholder will agree with your strategy. Build a process to resolve disagreement.

**When PM and PO disagree on priority:**

Example: PM wants to build "Enterprise SSO" (strategic, but complex). PO wants "Customer reporting dashboard" (customer-requested, faster to build).

Process:

1. **Surface the disagreement explicitly** (don't ignore it)
   - PM: "I think Enterprise SSO is strategic priority for Fortune 500 landing goal."
   - PO: "I think reporting dashboard will reduce churn faster."
   - Execs: "So we have a strategic choice here."

2. **Gather data** (not just opinions)
   - PM: "Win/loss analysis shows 8/10 enterprise prospects cite 'needs SSO' as requirement."
   - PO: "Churn analysis shows customers using reports 2x more likely to stay."
   - Both: Quantify the impact

3. **Discuss tradeoffs** (what are we giving up?)
   - Option A (SSO): Unlock enterprise market ($5M TAM) but delay reporting (risk churn)
   - Option B (Reporting): Reduce churn 2% but slow enterprise landing (miss $5M opportunity)

4. **"Disagree and Commit" decision** (executive owns final call)
   - CEO: "I'm going with SSO. PM's data on enterprise wins is compelling. PO, let's plan reporting for Q4."
   - PO: "I disagree, but I commit. Let's execute SSO strategy."
   - Document in decision record: "Chose SSO over reporting. Dissenting opinion: PO believes reporting reduces churn faster. Revisit in Q4."

5. **No surprises** (stakeholder already knows the decision)
   - Decision is not a surprise to execs
   - PO had input
   - All parties understand the rationale

**When PM and Exec disagree:**

Example: CEO wants to "build for Fortune 500 (enterprise)." PM wants to "dominate SMB first (faster revenue)."

Process:

1. **Frame as strategic choice** (not PM vs. CEO)
   - PM: "I'm proposing SMB-first go-to-market. Here's the data."
   - CEO: "I'm proposing enterprise-first. Here's my rationale."

2. **Present evidence** (not opinions)
   - PM data: "SMB adoption 3x faster; payback 6 months vs. 18 months for enterprise."
   - CEO data: "Fortune 500 customers worth 10x SMB. One whale is 100 minnows."

3. **CEO decides** (they own strategy)
   - CEO: "I'm going enterprise-first. I'm willing to take slower adoption for larger deal size."
   - PM: "Understood. I'll adjust strategy. Implications: need enterprise sales team, longer sales cycle, higher CAC."

4. **PM executes** (even if you disagree)
   - Don't say "I told you so" if enterprise strategy takes longer
   - Document assumption: "Assumed enterprise TAM = $100M; actual = $40M"
   - Adjust strategy quarterly based on results

**Documentation of disagreement:**

Add to decision record:

```
# Decision: Enterprise vs. SMB First

## Recommendation
Go enterprise-first. Focus on Fortune 500 market.

## Dissenting Opinion
PM recommended SMB-first. Rationale: Faster adoption, quicker revenue, lower CAC. Risk: Might get stuck at SMB; hard to move upmarket.

## Decision Maker
CEO

## Why We Chose This
- Enterprise customers worth 10x more
- Slower adoption acceptable for larger deal size
- Competitive advantage: Our moat (API ecosystem) matters more to enterprise

## How We'll Know If We're Right
- Close first Fortune 500 customer by Q4
- Enterprise deal size >$50K ACV
- Enterprise NPS >8
- If any metric misses by Q4, reassess strategy

## Revisit Date
Q4 2026 business review
```

**Key Insight:** Disagreement is healthy. Document it. Decide decisively. Execute committed. Learn from results. No surprises.
```

---

### 7️⃣ CONTINUOUS LEARNING CYCLES

**Location:** Add to "Step 5: Make strategic trade-offs" section (after monthly optimization)

**Content to Insert:**

```markdown
### Step 5b: Continuous Learning Cycles (Every 2 Sprints)

Post-launch isn't just waiting 3 months for retrospective. Use continuous 2-sprint feedback loops to iterate fast.

**2-Sprint Feedback Loop:**

After launch, every 2 sprints:

1. **Week 1-2: Build & Ship** (standard sprint work)

2. **Week 3: Collect Feedback** (end of sprint)
   - Pull adoption data: How many users enabled feature?
   - Support feedback: What questions are users asking?
   - User research: Interview 5-10 active users + non-users
   - Metrics: Churn impact? Session impact? Revenue impact?

3. **Week 4: Decide to Iterate or Pivot** (sprint planning)
   - Adopt more (users love it): Invest in Phase 2 (optimization, new variants)
   - Stalled adoption (users don't care): Either fix UX or kill feature
   - Mixed results (some users love, some hate): Segment and optimize

Decision tree:

```
Is adoption >20% in first 2 weeks?

YES → Keep feature. Plan Phase 2 improvements.
       Interview heavy users; find delight moments.
       Invest in second sprint of iteration.

NO → Diagnose.
     - Is UX confusing? (user research)
     - Is feature discovery bad? (only 5% even know it exists)
     - Is feature solving wrong problem? (wrong user segment)
     
     Fix if fixable in 1-2 sprints.
     Kill if unfixable or low priority.
```

Example:

```
Feature: GPS Equipment Tracking
Sprint 1-2 (Launch): 18% adoption. Mixed sentiment.

2-Sprint Feedback:
- User interviews: Power users love GPS (9/10 satisfaction). Casual users don't use it (2/10).
- Support tickets: "Battery drains too fast" (most common complaint)
- Metrics: GPS users have 2.1% churn vs. 3.2% non-users (positive)
- Revenue: No direct ARR yet; value is retention

Decision: ITERATE
- Problem: Battery drain; fix with geofence-based GPS
- Opportunity: Power users are sticky; can expand to more user types
- Phase 2 sprint focus: Reduce battery drain; add privacy controls; improve discovery

Sprint 3-4 (Phase 2): After geofence fix + privacy dashboard
- Adoption: 22% (up from 18%)
- Churn among GPS users: 1.8% (further improvement)
- Decision: INVEST (working; double down on optimization)
```

**3-Month Kill/Invest Checkpoint:**

At 3 months post-launch, make final decision:

```
Metrics Checklist:

☐ Adoption ≥ 25%? (strong signal)
☐ Churn positive? (users stickier than non-users)
☐ Support volume <3 tickets/1k users? (not broken)
☐ Revenue impact positive? (generating ARR)
☐ Competitive advantage held? (not copied yet)

If ≥4/5: INVEST. Plan Phase 3 (expand to new segments, build ecosystem).
If 2-3/5: ITERATE. Another 2-sprint cycle to improve.
If ≤1/5: KILL. Shut down; reallocate team.
```

**Continuous Learning Backlog:**

Maintain a "learning backlog" of insights discovered through feedback loops:

```
GPS Equipment Tracking - Learning Backlog

- Users want export to Excel (feature request, 3 mentions)
- Mobile UX works; desktop needs work (UI/UX insight)
- Privacy concerns more intense than anticipated (cultural insight)
- High-volume customers value GPS more (segmentation insight)
- Competitor X now has GPS too (competitive threat)

Next cycle decisions:
- Export to Excel (high-impact, low-effort, add to Phase 3)
- Privacy dashboard (addressed in Phase 2)
- Focus enterprise sales on GPS differentiator
- Monitor competitor GPS feature adoption
```

**Key Insight:** Don't wait 3 months for retrospective. Feedback loop every 2 sprints. Iterate or kill fast. Learning compounds. Kill bad bets early; invest in winners.
```

---

## Implementation Checklist

### TIER 1 ADDITIONS (Must add before release)

- [ ] **Win/Loss Analysis Subsection** (after Step 2: Discover)
  - Location: `product-manager.agent.md` line ~250 (after Step 2)
  - Effort: 30 minutes
  - Content: Win/loss template, quarterly meeting structure, key insight
  
- [ ] **Executive Communication** (in Communication Cadence section)
  - Location: `product-manager.agent.md` line ~850 (after Monthly metrics review)
  - Effort: 20 minutes
  - Content: 30-min briefing structure, example briefing

- [ ] **Launch Operations** (after Launch playbook)
  - Location: `product-manager.agent.md` line ~650 (after launch playbook)
  - Effort: 20 minutes
  - Content: Daily standups, on-call rotation, escalation path, rollback framework

**Total Tier 1 Effort:** ~70 minutes

### TIER 2 ADDITIONS (Should add in v1.1)

- [ ] **RICE Framework** (in Step 3)
  - Location: `product-manager.agent.md` line ~450 (new Step 3c after decision matrix)
  - Effort: 45 minutes
  - Content: RICE formula, examples, comparison table, when to use

- [ ] **Financial Modeling** (in Step 2c)
  - Location: `product-manager.agent.md` line ~400 (after leading indicators)
  - Effort: 45 minutes
  - Content: 3-year model, unit economics, financial impact template

- [ ] **Stakeholder Alignment** (in Communication Cadence)
  - Location: `product-manager.agent.md` line ~900 (new subsection)
  - Effort: 40 minutes
  - Content: Disagreement process, documentation template

- [ ] **Continuous Learning Cycles** (after Post-launch iteration)
  - Location: `product-manager.agent.md` line ~750 (after kill decision)
  - Effort: 40 minutes
  - Content: 2-sprint loop, decision tree, learning backlog

**Total Tier 2 Effort:** ~170 minutes (~3 hours)

### TIER 3 ADDITIONS (v2.0, can wait)

- [ ] Async communication patterns
- [ ] Data visualization guidance
- [ ] Competitive monitoring post-launch

---

## Recommendation

**Phase 1 (Immediate):** Add all Tier 1 additions. Effort: ~1 hour. Impact: Closes 3 critical gaps. Makes agent 85% complete.

**Phase 2 (v1.1, 1-2 weeks):** Add Tier 2 additions. Effort: ~3 hours. Impact: Brings agent to 90% complete. Makes all critical PM practices covered.

**Phase 3 (v2.0, future):** Add Tier 3 additions + comprehensive PM toolkit (templates, checklists, worksheets).
