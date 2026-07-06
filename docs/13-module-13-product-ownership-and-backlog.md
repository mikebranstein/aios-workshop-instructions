# Module 13 - Product Leadership: Strategy and Execution

## Concept: The product is driven by two complementary leaders

Modules 1-12 focused on **how** to build and release features efficiently: intake → design → build → verification → QA → policy → release. But someone needs to decide **what** to build and **why**—and someone else needs to execute that strategy tactically.

**Module 13 introduces the complete product leadership layer**: the product manager (strategic direction) and the product owner (tactical execution). Together, they ensure every feature shipped is strategically important *and* valuable to the business.

**Key distinctions:**
- **Product Manager (Strategic)**: Sets long-term product vision, discovers market opportunities, understands competition, evaluates trade-offs at the strategic level. Asks: "What market problems should we solve? Where is the product heading?"
- **Product Owner (Tactical)**: Prioritizes the backlog, ensures execution aligns with strategy, works daily with development team. Asks: "Which features should we build next to execute that vision?"

**Why both roles matter:**
- Without a PM, the product becomes reactive (chasing every customer request) instead of strategic (building toward a vision)
- Without a PO, the strategy stays theoretical (never gets executed) instead of practical (features ship regularly)

Together, they form the **two-tier leadership model**: PM sets direction → PO executes it through the backlog → Development pulls from backlog continuously.

## Where product leadership fits in the system

**Two independent, concurrent orchestrator loops:**

```
┌─────────────────────────────────────────────────────────────┐
│ PM-PO Orchestrator Loop (runs continuously, independent)    │
│                                                             │
│ [PM Discovery] → [PM Validation] → [PO Prioritization]    │
│ ├─ Research market opportunities                          │
│ ├─ Validate with customers                                │
│ ├─ Make CHAMPION/DEFER/BLOCK decisions                    │
│ └─ Order backlog by priority score                         │
│                                                             │
│ Output: "Ready for Development" column (pre-prioritized)   │
└─────────────────────────────────────────────────────────────┘
                         ↓ (async pull)
┌─────────────────────────────────────────────────────────────┐
│ Development Orchestrator Loop (runs continuously, pulls)    │
│                                                             │
│ [Intake] → [BA] → [Design] → [Build]                      │
│ → [Verification] → [QA] → [Policy] → [Release]            │
│                                                             │
│ - Never waits for PM-PO                                    │
│ - Pulls next-priority issue from backlog                   │
│ - Executes 8-stage pipeline                                │
│ - Ships to production                                      │
└─────────────────────────────────────────────────────────────┘
```

**Why two independent loops:**
- PM-PO can continuously research, validate, and re-prioritize opportunities without blocking the development pipeline
- Development can keep shipping from the backlog without waiting for product decisions
- When market conditions change, PM can reprioritize without halting mid-development work
- Both teams work autonomously at the speed that suits their work

## Time Box

- Target: 90 minutes (understanding both PM and PO roles, how they collaborate, and running features through both tiers)

## Required Tasks

1. Understand the product manager role and strategic discovery process.
2. Understand the product owner role and tactical prioritization process.
3. Define your product vision and strategic priorities.
4. Review the product manager agent (`templates/agents/product-manager.agent.md`).
5. Review the product owner agent (`templates/agents/product-owner.agent.md`).
6. Research market opportunities and validate with stakeholders or customers.
7. Create backlog items based on validated opportunities.
8. Practice PM ↔ PO collaboration (PM proposes → PO prioritizes).

---

## Step 1 (10 minutes): Understand the Product Manager role

A product manager is responsible for **strategic product direction**. They sit at the intersection of business, market, and technology.

**What PMs do:**
- **Set product vision:** Where is the product headed? What market are we trying to own? What competitive advantage are we building?
- **Discover market opportunities:** Talk to customers, analyze competition, identify problems that need solving. PMs are customer detectives.
- **Validate ideas:** Before building anything, confirm that customers actually want it and it aligns with strategy.
- **Make strategic trade-offs:** When capacity is limited (always), decide what's important and what can wait.
- **Channel opportunities to PO:** Hand off validated ideas to the Product Owner for tactical prioritization.

**What PMs do NOT do:**
- Define acceptance criteria (BA does this)
- Design architecture (Design does this)
- Prioritize the day-to-day backlog (PO does this)
- Manage sprint execution (PO does this)

**Key PM question:** "What market problems should we solve? Is this strategically important?"

---

## Step 2 (10 minutes): Understand the Product Owner role

A product owner is responsible for **tactical execution** of the PM's strategic vision. They work daily with the development team.

**What POs do:**
- **Manage the backlog:** Order features by priority. Quick wins first (high value + low complexity), then strategic bets (high value + high complexity), then maintenance work.
- **Collaborate with BA:** Clarify requirements, ask clarifying questions, work through ambiguities.
- **Create issues:** Turn validated opportunities into GitHub issues with structure and clarity.
- **Prioritize:** Use a formula to assess (User Value + Business Value) / (Complexity × 1.5). Higher score = higher priority.
- **Escalate to PM:** If a customer request conflicts with strategy or needs strategic context, ask PM for input.

**What POs do NOT do:**
- Set product strategy (PM does this)
- Conduct market research (PM does this)
- Define acceptance criteria (BA does this)
- Build features (Design and Build do this)

**Key PO question:** "Which features should we build next to execute our strategy? What's the business value vs. effort?"

---

## Step 3 (15 minutes): Three Issue Types in Product Leadership

Product leadership uses three distinct issue types to separate concerns and make hand-offs explicit.

### Creating Custom Labels

First, create the labels that the issue templates will auto-apply.

**Option 1: GitHub Web UI**

1. Go to your repository main page on GitHub
2. Click **Settings** (top right)
3. In the left sidebar, click **Labels**
4. Click **New label**
5. In the **Label name** field, type: `pm-idea`
6. Add a description (optional): "Feature idea submitted for product discovery"
7. Click **Create label**
8. Click **New label** again
9. In the **Label name** field, type: `pm-opportunity`
10. Add a description (optional): "Validated market opportunity ready for PO prioritization"
11. Click **Create label**

**Option 2: GitHub CLI (faster)**

If you have `gh` (GitHub CLI) installed, run these commands in your terminal:

```bash
gh label create pm-idea --description "Feature idea submitted for product discovery" --color "E8F4F8"
gh label create pm-opportunity --description "Validated market opportunity ready for PO prioritization" --color "D4E8F7"
```

Once both labels exist, they'll be available for your issue templates to auto-apply.

---

### Issue Type 1: `pm-idea` — User Submission

**Who creates:** Anyone (customer, sales, support, user, PM themselves)  
**What it is:** Lightweight feature idea (1-3 sentences)  
**When it's created:** Anytime someone thinks of a feature worth exploring

**Example:**
```
Title: Mobile app for field teams
Labels: pm-idea
Body: 
- 4 support tickets this week about "can't checkout from field"
- 2 enterprise customers mentioned in recent calls
- Competitor X doesn't have mobile; Competitor Y has basic iOS
- Fits Q3 priority "mobile-first experience"
```

**Now create the `pm-idea` template:**

1. Go to your repository main page on GitHub
2. Click **Add file** → **Create new file**
3. In the filename field, type exactly: `.github/ISSUE_TEMPLATE/pm-idea.md`
4. Copy and paste this content into the file:

```markdown
---
name: PM Idea
about: Submit a feature idea for product discovery
title: "[PM Idea]: "
labels: 'pm-idea'
assignees: ''

---

## Feature Idea (1-3 sentences)
[Describe your feature idea here]

## Customer Context (optional)
- Who mentioned this?
- Support tickets or customer calls?

## Competitive Context (optional)
- What do competitors do?
- What's our advantage?
```

5. Click **Commit changes** at the bottom right

---

### Issue Type 2: `strategic-opportunity` — PM's Research & Validation

**Who creates:** Product Manager agent (after autonomous research/validation)  
**What it is:** Market research findings, customer validation evidence, strategic decision  
**When it's created:** After PM completes discovery, validation, and makes CHAMPION/DEFER/BLOCK decision

**Example:**
```
Title: Strategic Opportunity - Mobile app for field teams

Research Findings:
- 12 support tickets about field checkout over 4 weeks
- 4 customers interviewed; all confirmed critical pain point
- Competitor A has basic mobile; Competitor B doesn't
- Affects ~35% of enterprise customer base

Validation Assessment:
- Strategic alignment: ✅ (aligns with Q3 mobile-first priority)
- Market opportunity: High (multiple enterprise upsell opportunities)
- Competitive advantage: Real-time + FM system integration (competitors lack this combo)
- Effort estimate: 3-4 weeks
- Customer validation: Strong (4/4 customers volunteered to beta-test)

Decision: CHAMPION → Ready for PO prioritization
```

**Now create the `strategic-opportunity` template:**

1. Click **Add file** → **Create new file** again
2. In the filename field, type exactly: `.github/ISSUE_TEMPLATE/strategic-opportunity.md`
3. Copy and paste this content into the file:

```markdown
---
name: Strategic Opportunity
about: PM research, validation, and strategic decision
title: "[Strategic Opportunity]: "
labels: 'pm-opportunity'
assignees: ''

---

## Strategic Summary
[Link to source pm-idea or standalone summary]

## Research Findings
- Support tickets: [X mentions]
- Customer validation: [Talked to Y customers; Z confirmed]
- Competitive landscape: [Competitor analysis]
- Market size: [~X% of target customers affected]

## Validation Assessment
- Strategic alignment: ✅ or ❌
- Market opportunity: High/Medium/Low
- Competitive advantage: [What makes ours unique?]
- Effort estimate: [X weeks]
- Customer validation strength: Strong/Medium/Weak

## Decision
- **Decision:** CHAMPION / DEFER / BLOCK
- **Rationale:** [Why this decision?]
```

4. Click **Commit changes** at the bottom right

---

### Issue Type 3: `feature-request` — PO's Prioritized Task

**Who creates:** Product Owner (after reading strategic-opportunity)  
**What it is:** Ready-to-build development task  
**When it's created:** After PO prioritizes a CHAMPION strategic-opportunity

**The hand-off:** PO creates `feature-request` issues → Development pulls them from "Ready for Development" → Executes the 8-stage pipeline.

You've already created and customized the `feature-request` template in Module 2. Use it as-is, and add a **Strategic Context** line at the top linking back to the source `strategic-opportunity`.

See [Module 2 - Intake Quality Template](02-module-2-intake-quality-template.md) for the template.

**Verify all templates are working:**

Go to your repository, click **New issue**, and you should see **PM Idea**, **Strategic Opportunity**, and **Feature Request** in the template list.

---

## Step 4 (10 minutes): Review the Product Manager agent

The PM agent (`templates/agents/product-manager.agent.md`) walks you through:

1. Strategic discovery: How to find market problems
2. Research methods: User interviews, competitor analysis, support feedback, data trends
3. Validation framework: Does this problem affect many customers? Is it strategically aligned?
4. **Creates `strategic-opportunity` issues** as output (not just making decisions internally)
5. **Autonomy Mode**: Submit a `pm-idea` and have the agent autonomously research, validate, and create `strategic-opportunity` issues

**Key insight:** PM agent reads `pm-idea` issues → researches → creates `strategic-opportunity` issues for PO to consume.

**See also**: [templates/pm-discovery-README.md](../../templates/pm-discovery-README.md) for step-by-step guide on autonomous PM discovery.

---

## Step 5 (10 minutes): Review the Product Owner agent

The PO agent (`templates/agents/product-owner.agent.md`) walks you through:

1. **Consumes:** `strategic-opportunity` issues from PM
2. **Evaluates:** Value, business impact, complexity
3. **Prioritizes:** Calculates priority score and backlog position
4. **Creates:** `feature-request` issues with user stories, acceptance criteria, success metrics
5. **Hands off:** `feature-request` issues ready for development

**Key insight:** PO agent reads `strategic-opportunity` → creates `feature-request` for development to consume.

---

## Step 6 (15 minutes): Conduct PM discovery and create strategic opportunities

Using market anchor definition (from PM agent), discover 2-3 market opportunities:

**For each opportunity:**

1. **Research:** Talk to customers (or stakeholders if you don't have customers). What problems do they mention unprompted? What frustrates them? What do they wish existed?

2. **Validate:** Does this problem affect multiple people? Can you find 2-3 customers or stakeholders who mention it?

3. **Assess strategic fit:** Does this align with your market anchor? Is it competitive? Is it unique?

4. **Evaluate effort:** Is this a quick win (low effort) or a bigger investment? Is it even feasible?

5. **Make decision:** CHAMPION (move to PO) / DEFER (real problem but not strategic now) / BLOCK (doesn't fit strategy)

**Create 2-3 `strategic-opportunity` issues** using the template from Step 3 (or submit 2-3 `pm-idea` issues and let the PM agent autonomously create the strategic-opportunities):

**Example `strategic-opportunity` issue created by PM agent:**

```
Title: Strategic Opportunity - Mobile app for field teams
Labels: pm-opportunity

## Research Findings
- Found 12 support tickets mentioning field checkout issues
- Talked to 4 facility managers; all confirmed pain point
- Competitor X has no mobile; Competitor Y has basic iOS
- Estimated 80% of enterprise field users affected

## Validation Assessment
- Strategic alignment: ✅ Aligns with "field operations" market anchor
- Market opportunity: High (80%+ customer segment affected)
- Competitive advantage: Real-time + FM integrations (competitors lag here)
- Effort estimate: 3-4 weeks for MVP

## Decision
- **Decision:** CHAMPION
- **Rationale:** Strong validation, strategic fit, achievable effort
- **Next step:** Ready for PO prioritization
```

### Synthesize what you learned

After discovery, update your market anchor into a fuller vision:

- **Market definition:** Based on who you talked to, who's the core customer?
- **Problem statement:** What problem kept coming up in research?
- **Competitive advantage:** What are competitors missing? What's your angle?
- **3-6 month priorities:** Which of your validated opportunities should ship first?

**Example synthesis (after discovery):**
```
Market anchor (before): "Mid-market facility managers who manually track equipment checkout"

Research findings:
- 12 facility managers interviewed; 10 mentioned equipment checkout pain
- Competitor X has no mobile; Competitor Y has basic iOS
- Top 3 problems: mobile checkout, integration with FM systems, real-time visibility
- Interest level: 4 customers willing to beta; strong repeat interest

Updated vision (after discovery):
Market: Mid-market facility managers (50-500 employee companies)
Problem: Manual equipment checkout in field wastes 2-3 hours/day; mobile-first competitors emerging
Advantage: Real-time checkout + integrations with existing FM systems (competitors don't have this combo)
Q3 priorities: Mobile checkout (highest demand), FM integrations (quick win), analytics dashboard (strategic)
```

Your vision is now grounded in customer research, not guesses.

---

## Step 8 (20 minutes): Create feature issues as Product Owner

Now switch roles. You're the PO receiving `strategic-opportunity` issues from the PM.

**For each CHAMPION `strategic-opportunity` issue the PM validated:**

1. **Read** the PM's research and validation (from the strategic-opportunity issue)
2. **Assess value:** Based on PM's market data, what's the business value? User value? (Rate 1-5)
3. **Assess complexity:** How much effort? Is it a quick build or a major project? (Rate 1-5)
4. **Calculate priority score:** (User Value + Business Value) / (Complexity × 1.5)
5. **Position in backlog:** Quick wins at top (score > 2.5), strategic bets next (1.5-2.5), defer lower-scoring items
6. **Create `feature-request`:** Use the template from Step 3, link to strategic-opportunity, write user story and acceptance criteria

**Example (as PO creating a feature-issue from strategic-opportunity):**

```
Strategic-opportunity Issue #42: "Strategic Opportunity - Mobile app for field teams"
├─ Research findings: 12 support tickets, 4 customer confirmations
├─ Strategic alignment: ✅ 
├─ Competitive advantage: ✅ Real-time + FM integrations
├─ Effort: 3-4 weeks

PO reads this and creates feature-request:

Title: Mobile app: iOS/Android checkout for field teams
Labels: feature-request, po-prioritized

**Strategic Context** (Linked to strategic-opportunity #42)
- Market opportunity: Field teams lose 2-3 hours/day to equipment checkout. 80% of customers affected.
- Customer validation: 4 customers confirmed; willing to beta-test
- Competitive advantage: Real-time checkout + FM system integrations (competitors lack this combo)

## User Story
As a field manager, I want to check out equipment from my phone, 
so that I don't lose 2+ hours running back to the office.

## Acceptance Criteria (Testable)
1. [ ] Mobile app (iOS + Android) loads in <2 seconds on 4G
2. [ ] User can view and select equipment from device inventory
3. [ ] Checkout data syncs to central system within 30 seconds
4. [ ] Offline mode caches last 50 items for field use
5. [ ] System shows "checkout successful" confirmation

## Value Assessment
- User value: 5 (all field teams need it; critical pain point)
- Business value: 4 (upsell to field-heavy customers; retention impact)
- Complexity: 4 (3-4 weeks estimated; new platform)
- Priority score: (5 + 4) / (4 × 1.5) = 1.5 (strategic bet)

## Success Metrics
- 80% adoption by field users within 4 weeks
- Time-to-checkout reduced by 50%
- Churn from field-heavy segment reduced by 10%

## Priority Position
Strategic bet - Top 3 backlog
```

**Create 2-3 `feature-request` issues** for your CHAMPION strategic-opportunities. Each feature-request should reference its strategic-opportunity and include:
- User story (from PM's research context)
- Acceptance criteria (testable requirements)
- Value scores and priority calculation
- Success metrics
Value: High business value (upsell opportunity) + High user value (critical pain point)
Complexity: Moderate-high (3-4 week estimate)
Success metrics: Mobile app adopted by 80% of active field users; time-to-checkout reduced by 50%

Backlog position: Top 3 (after quick wins, this is highest business value)
```

**Create 2-3 GitHub issues for your prioritized opportunities.** Make them ready for BA to refine.

---

## Step 9 (15 minutes): Practice PM ↔ PO collaboration

Real PM-PO work involves back-and-forth. The PM creates `strategic-opportunity` issues; the PO creates `feature-issue` issues; they collaborate to ensure alignment.

**Simulate this collaboration:**

1. **As PM:** On one of your `strategic-opportunity` issues, post the research findings, customer validation, strategic rationale in comments

2. **As PO:** Review the `strategic-opportunity` issue. Ask clarifying questions in comments: "How many customers mentioned this?" "What's our competitive advantage?"

3. **As PM:** Respond with additional context and analysis

4. **As PO:** Based on PM's research, create the corresponding `feature-issue` linking back to the strategic-opportunity

**Example dialogue:**

```
[PM creates strategic-opportunity #42]
Research: 12 support tickets, 4 customer interviews
Validation: Strong signal, competitive advantage
Effort: 3-4 weeks

[PO comments]
"Great research. Mobile app or API integrations first?"

[PM responds]
"Mobile unblocks immediate revenue. Integrations can wait 2 sprints."

[PO creates feature-issue #89]
Linked to strategic-opportunity #42
Ready for development pipeline
```

---

## Definition of Done

✅ You have successfully completed Module 13 when:

1. **Market anchor defined** (Step 4)
   - 1-2 sentence description of customer segment + problem space you're exploring

2. **Three issue types understood** (Step 3)
   - `pm-idea` (user input): 1-3 sentences
   - `strategic-opportunity` (PM output): research, validation, decision
   - `feature-issue` (PO output): user story, acceptance criteria, value scores

3. **Product Manager role understood** (Step 1)
   - Can explain: strategic discovery, validation, opportunity evaluation, decision-making
   - Understand what PM does (research, validate, create `strategic-opportunity` issues) vs. what PO does (create `feature-issue` issues for development)

4. **Product Owner role understood** (Step 2)
   - Can explain: consuming `strategic-opportunity` issues, value assessment, priority scoring, creating `feature-issue` issues
   - Understand relationship: PM validates market opportunities; PO converts them to actionable development tasks

5. **2-3 `strategic-opportunity` issues created** (Step 7)
   - Each includes: research findings, customer validation evidence, strategic alignment assessment, effort estimate, CHAMPION/DEFER/BLOCK decision
   - Research documented with credible evidence

5. **2-3 `feature-request` issues created from strategic-opportunities** (Step 8)
   - Each linked to its source `strategic-opportunity`
   - Each includes: user story (from PM's market research), acceptance criteria (testable), value assessment, complexity estimate, priority score, success metrics
   - Issues ordered in backlog by priority (quick wins → strategic bets)

7. **PM ↔ PO collaboration demonstrated** (Step 9)
   - Created `strategic-opportunity` issue with research
   - PO asked clarifying questions in comments
   - PM responded with additional context
   - PO created `feature-issue` from the validated opportunity
   - Shows full hand-off trail from market validation to development task

8. **PM and PO agents reviewed**
   - Can articulate: What PM discovers (creates `strategic-opportunity` issues), what PO prioritizes (creates `feature-issue` issues)
   - Understand the two-tier leadership model and three-issue-type architecture
   - Can explain PM ↔ PO collaboration pattern
   - Understand autonomous PM discovery mode and quarterly re-checks

9. **Orchestration reviewed** — Product Manager and Product Owner orchestrator
    - Understand: Independent PM-PO loop (never blocks development)
    - Understand: PM discovery trigger (Step 0.5) and quarterly re-evaluation
    - Understand: PO backlog ordering and "Ready for Development" column
    - Understand: Development consumes `feature-issue` issues independently (orchestrator.development.agent.md)

## Stretch Goals

- Run a 30-minute customer interview (in-person or simulated). Document what problems you discover.
- Create a competitive analysis: What features do 3 competitors have? What don't they have? What's our differentiation?
- Build a product roadmap showing quarterly goals and how backlog items map to them
- Create a market sizing estimate: How many customers face this problem? What's the TAM (Total Addressable Market)?
- Document a strategic trade-off decision: "We're not building X because Y is more strategic."

---

## Reflection

After completing Module 13, reflect on:

- **What makes a good market opportunity?** How do you differentiate between "real market problem" and "nice-to-have feature"?
- **How does strategy guide decisions?** How would you explain your product vision to a new team member?
- **How do PM and PO collaborate?** What questions should PO ask PM? When should PM escalate to leadership?
- **What's the relationship between strategy and execution?** How does PM vision flow into PO prioritization into development pipeline?

Next: **Module 14 — Capstone: Full System End-to-End Run** — You'll run 2-3 features through the complete 10-stage pipeline (PM → PO → Intake → BA → Design → Build → Verification → QA → Policy → Release) with real market opportunities and strategic context. By the end, you'll have a complete, strategic, production-ready product organization.
