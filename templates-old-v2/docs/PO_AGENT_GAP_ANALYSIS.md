# PO Agent Gap Analysis: Current Coverage vs. Great PO Practices

**Analysis Date:** 2026-07-07
**Current Agent File:** `templates/agents/product-owner.agent.md` (~300 lines, ~11 KB)
**Methodology:** Comprehensive research on 12 PO dimensions + line-by-line comparison to existing agent

---

## EXECUTIVE SUMMARY

### Current Coverage
The existing PO agent covers **~40% of great PO practices** with strength in **tactical backlog prioritization** but significant gaps in **stakeholder management, data-driven decisions, release coordination, and post-launch learning**.

### Key Strengths
✅ **Backlog evaluation framework** — Clear prioritization formula, scoring guidance  
✅ **GitHub issue structure** — Good template with user story + value assessment  
✅ **Anti-patterns** — Helpful checklist of what to avoid  
✅ **Strategic-opportunity intake** — Clear workflow for receiving PM input  

### Critical Gaps (Impact: High)
❌ **Release planning & multi-team coordination** — No dependency mapping, feature flags, rollback strategy  
❌ **Post-launch measurement & iteration** — No adoption tracking, kill decisions, continuous learning  
❌ **Data-driven decisions** — No metrics framework, experimentation velocity, cohort analysis  
❌ **Stakeholder management** — No "saying no" frameworks, communication cadences, managing priority pressure  

### Medium-Impact Gaps
⚠️ **Acceptance criteria clarity** — Missing 3 C's framework, INVEST checklist, Given/When/Then examples  
⚠️ **Continuous feedback loops** — Missing A.C.A.F. (Ask/Categorize/Act/Follow-up), NPS/CSAT, support integration  
⚠️ **Roadmap communication** — Missing OKR structure, quarterly planning, stakeholder communication cadence  

### Low-Impact Gaps
❌ **Discovery & validation** — PO role in lean validation, A/B testing, volume assessment (mostly PM responsibility, but PO should understand)  
❌ **Technical debt balance** — No framework for 20% allocation, prioritizing in active-dev areas  
❌ **Risk management** — No probability × impact framework, staged rollout planning, de-risking strategies  

---

## DETAILED COVERAGE BY DIMENSION

### **1. Core PO Responsibilities** 
**Research Standard:** Set strategic vision (done by PM), manage backlog as prioritized list, bridge stakeholders & developers, make scope/priority trade-offs, protect team

**Current Agent Coverage:** ✅ 70%
- ✅ Backlog management: Clear prioritization formula, positioning framework
- ✅ Feature-request creation with proper structure
- ✅ Trade-off decision process documented
- ✅ Anti-patterns section includes "protect team" concept
- ❌ Missing: Daily interrupt management, stakeholder shield practices, cross-team orchestration

**Gap Impact:** Medium (missing coordination tactics, not strategic frameworks)

**Recommendation for Gap:** Add section on "Protecting Team Capacity" with interrupt management patterns, weekly review of unplanned work, stakeholder communication to manage expectation-setting

---

### **2. Discovery & Validation** 
**Research Standard:** JTBD interviews, lean validation, 15-20 customer interviews/quarter, 5+ customer rule for signals, volume-based assessment, A/B testing

**Current Agent Coverage:** ❌ 5%
- ❌ Agent assumes strategic-opportunity is already validated by PM
- ❌ No guidance for PO to run their own validation (e.g., with power users)
- ❌ No JTBD framework
- ❌ No "5+ customer rule" for assessing volume
- ❌ Minimal mention of asking clarifying questions (one example line)

**Gap Impact:** Medium (validation is mostly PM's job, but PO should understand and question)

**Recommendation for Gap:** Add subsection "Validating PM Research" with:
- Questions to ask PM in comments (customer signal strength, competitive data quality, market size)
- 5+ customer rule explanation
- How to spot weak validation before moving to backlog
- JTBD basics (for understanding PM's research)

---

### **3. Acceptance Criteria & Requirement Clarity**
**Research Standard:** 3 C's (Card/Conversation/Confirmation), INVEST checklist, Given/When/Then format, testability criteria, BA collaboration patterns

**Current Agent Coverage:** ⚠️ 30%
- ✅ Mentions BA will clarify requirements
- ✅ GitHub issue structure includes acceptance criteria note ("DO NOT include")
- ❌ Missing: 3 C's framework explanation
- ❌ Missing: INVEST checklist
- ❌ Missing: Given/When/Then format examples
- ❌ Missing: BA collaboration patterns (iterative refinement)
- ❌ Missing: "Testable" vs. "vague" criteria guidance
- ❌ Missing: Acceptance criteria review cadence (before dev starts)

**Gap Impact:** High (vague AC creates rework downstream)

**Recommendation for Gap:** Add section "Ensuring Acceptance Criteria Clarity" with:
- 3 C's framework (Card → Conversation → Confirmation)
- INVEST checklist template
- Given/When/Then examples
- BA collaboration workflow
- Anti-pattern examples (vague AC)

---

### **4. Stakeholder Management**
**Research Standard:** Saying "no" strategically, explicit priority frameworks, impact vs. effort trade-off, "squeaky wheel" bias management, quarterly business reviews, monthly stakeholder communication

**Current Agent Coverage:** ⚠️ 25%
- ✅ Trade-off decisions section mentions explaining WHY
- ✅ Anti-patterns mention "squeaky wheel bias"
- ❌ Missing: Frameworks for saying "no" (explicit priority ranking, strategic alignment filter)
- ❌ Missing: Stakeholder communication cadences (weekly/monthly/quarterly)
- ❌ Missing: How to weight customer requests (volume + business value)
- ❌ Missing: Managing executive pressure with data
- ❌ Missing: "Disagree and commit" culture patterns
- ❌ Missing: Quarterly business review structure

**Gap Impact:** High (stakeholder alignment prevents endless backlog growth, misalignment)

**Recommendation for Gap:** Add section "Stakeholder Management & Priority Communication" with:
- Framework for "saying no" (explicit priority list, strategic alignment, impact/effort)
- Stakeholder communication cadences (weekly status, monthly leadership update, quarterly business review)
- Trade-off communication template ("We chose A over B because...")
- Customer request weighting model (volume + enterprise value)
- Handling executive pressure with metrics/data

---

### **5. Release Planning & Coordination**
**Research Standard:** Multi-team dependency mapping, staging gates, feature flags, staged rollout (1% → 10% → 100%), launch checklist, rollback planning, cross-team sync cadence

**Current Agent Coverage:** ❌ 0%
- ❌ Completely absent
- No mention of multi-team coordination
- No feature flag strategy
- No rollout planning
- No launch checklist
- No dependency tracking
- No rollback planning
- No cross-team release ownership

**Gap Impact:** Critical (needed for enterprise/scaling teams; creates chaos without it)

**Recommendation for Gap:** Add section "Release Planning & Multi-Team Coordination" with:
- Dependency mapping (identify blockers, sequence work)
- Staging gates (feature-complete → design review → QA → product approval)
- Risk sequencing (risky items first with more testing time)
- Feature flag strategy (rollout 1% → 10% → 100%)
- Launch checklist (support training, docs, marketing, monitoring, on-call)
- Rollback planning (30-min rollback for each release)
- Cross-team release sync cadence

---

### **6. Data-Driven Decision Making**
**Research Standard:** Pre-launch metrics definition, AARRR framework, funnel analysis, cohort analysis, churn impact analysis, A/B testing, statistical significance, feature-level metrics

**Current Agent Coverage:** ⚠️ 15%
- ✅ Simple priority formula (user value, business value, complexity)
- ❌ Missing: Pre-launch metrics definition (what we'll measure before shipping)
- ❌ Missing: AARRR framework (Acquisition → Activation → Retention → Referral → Revenue)
- ❌ Missing: Funnel analysis ("Where do we lose users?")
- ❌ Missing: Cohort analysis ("Are recent cohorts stickier?")
- ❌ Missing: Churn analysis ("What features improve retention?")
- ❌ Missing: A/B testing decision framework
- ❌ Missing: Statistical significance guidance
- ❌ Missing: How to use analytics to re-prioritize backlog

**Gap Impact:** Critical (data-driven decisions prevent feature creep, validate priorities)

**Recommendation for Gap:** Add section "Data-Driven Backlog Prioritization" with:
- AARRR framework (identify which metric is broken first)
- Pre-launch metrics definition (primary vs. secondary)
- Funnel analysis to identify drop-offs
- Cohort analysis for retention improvements
- Churn correlation analysis (which features improve retention?)
- A/B testing decision framework
- Experimentation velocity

---

### **7. Post-Launch Measurement & Iteration**
**Research Standard:** Success metrics tracking cadence, adoption curve monitoring, kill decisions (adoption <5% after 2 months), continuous learning loops, weekly metrics review, support integration

**Current Agent Coverage:** ❌ 0%
- ❌ Completely absent
- No success metrics tracking
- No adoption curve guidance
- No kill decision framework
- No continuous learning loops
- No weekly review cadence
- No support ticket integration post-launch
- No deprecation/sunset path

**Gap Impact:** Critical (without post-launch learning, team ships wrong things repeatedly)

**Recommendation for Gap:** Add section "Post-Launch Learning & Iteration" with:
- Success metrics definition (pre-launch, before you build)
- Adoption tracking cadence (week 1, week 2-4, month 2-3, month 3+)
- Kill decision tree (adoption <5%? → investigate → improve or kill)
- Continuous learning loops (weekly metrics, support integration)
- Feature deprecation path (hide → deprecate → remove)
- 3-month cohort review (proceed to Phase 2 or de-prioritize)

---

### **8. Roadmap Communication**
**Research Standard:** OKR framework, quarterly planning, strategic pillars, 1-year vision, public vs. private, monthly stakeholder email, quarterly all-hands, trade-off narratives

**Current Agent Coverage:** ⚠️ 10%
- ✅ Trade-off decisions should be documented
- ❌ Missing: OKR structure (quarterly + annual planning)
- ❌ Missing: Strategic pillars (3-4 focus areas)
- ❌ Missing: 1-year vision framework
- ❌ Missing: Quarterly breakdown guidance
- ❌ Missing: Public vs. private roadmap strategy
- ❌ Missing: Stakeholder communication cadences (weekly, monthly, quarterly)
- ❌ Missing: All-hands roadmap review structure
- ❌ Missing: Trade-off narrative (Why did we deprioritize X?)

**Gap Impact:** High (without clear roadmap communication, stakeholders feel blindsided, backlog bloats with "nice-to-haves")

**Recommendation for Gap:** Add section "Roadmap Communication & Strategic Alignment" with:
- OKR-based planning (quarterly + annual cycles)
- Strategic pillars (3-4 focus areas for 12 months)
- Quarterly breakdown (what ships Q1, Q2, what's planned Q3/Q4)
- Public vs. private strategy (share 2-3 quarters; hold Q4+ flexible)
- Stakeholder communication cadence (monthly email: top 3 things shipping + rationale)
- All-hands roadmap presentation structure
- Trade-off communication examples

---

### **9. Continuous Learning & Feedback Loops**
**Research Standard:** A.C.A.F. loop (Ask/Categorize/Act/Follow-up), NPS/CSAT/CES metrics, in-app surveys, support ticket categorization, volume assessment, churn interviews, close-the-loop

**Current Agent Coverage:** ❌ 5%
- ✅ Mentions "collaboration with support/analytics" implied
- ❌ Missing: A.C.A.F. framework (Ask → Categorize → Act → Follow-up)
- ❌ Missing: NPS/CSAT/CES metrics guidance
- ❌ Missing: In-app survey strategy
- ❌ Missing: Support ticket categorization/tagging
- ❌ Missing: "5+ customer rule" for volume assessment
- ❌ Missing: Churn interviews (Why did customers leave?)
- ❌ Missing: Close-the-loop communication (tell customers you fixed their request)

**Gap Impact:** High (without systematic feedback loops, customer insights don't make it to backlog)

**Recommendation for Gap:** Add section "Continuous Customer Feedback Loops" with:
- A.C.A.F. framework (Ask → Categorize → Act → Follow-up)
- NPS/CSAT/CES cadences
- In-app survey strategy
- Support ticket categorization (product vs. bug vs. UX)
- Volume assessment (1 complaint ≠ pattern; 5+ ≈ signal)
- Churn interviews (systematic exit reasons)
- Close-the-loop communication (transparency to customers)

---

### **10. Technical Debt & Maintenance Balance**
**Research Standard:** 20% capacity allocation, active-dev area prioritization, debt tracking, deliberate vs. accidental debt, continuous refactoring during features

**Current Agent Coverage:** ❌ 0%
- ❌ Completely absent
- No tech debt decision framework
- No allocation guidance
- No prioritization guidance
- No debt tracking in backlog

**Gap Impact:** Medium (important for sustaining velocity long-term, but not immediately critical)

**Recommendation for Gap:** Add section "Technical Debt & Maintenance Prioritization" with:
- Tech debt types (deliberate, accidental, bit rot)
- Decision framework (IF affects active dev → tackle during feature; IF slowing team → prioritize)
- 20% allocation recommendation (20% capacity reserved for debt/QA)
- Tracking in backlog (visible, not hidden)
- Continuous refactoring during feature development

---

### **11. Risk Management**
**Research Standard:** Probability × impact scoring, feature risk categories, de-risking strategies, staged rollout, rollback planning, risk review cadence

**Current Agent Coverage:** ❌ 0%
- ❌ Completely absent
- No risk scoring framework
- No risk categories
- No de-risking strategies
- No staged rollout
- No rollback planning
- No risk review cadence

**Gap Impact:** Medium (important for enterprise/scaling, prevents surprises)

**Recommendation for Gap:** Add section "Risk Management & De-Risking" with:
- Risk scoring framework (Probability × Impact)
- Risk categories (assumption, technical, dependency, scale)
- De-risking strategies (MVP, spike work, staged rollout)
- Feature flag strategy for risky work
- Rollback planning per release
- Risk review cadence (weekly, monthly, pre-release)

---

### **12. Cross-Functional Collaboration**
**Research Standard:** Clear workflows with PM, BA, Design, Eng, QA, Marketing; back-and-forth patterns; meeting cadences (refinement, standups, release planning, post-launch review)

**Current Agent Coverage:** ⚠️ 35%
- ✅ Mentions "Collaboration Patterns" (3 basic patterns)
- ✅ Anti-patterns section touches on collaboration
- ✅ Mentions BA role briefly
- ❌ Missing: Detailed PM ↔ PO workflow (commenting on strategic-opportunity, questions to ask)
- ❌ Missing: BA collaboration patterns (iterative refinement, AC review before dev)
- ❌ Missing: Design collaboration (early involvement, trade-off discussion)
- ❌ Missing: Engineering collaboration (clarity questions, blockers, standups)
- ❌ Missing: QA collaboration (AC verification, edge cases)
- ❌ Missing: Marketing feedback loop
- ❌ Missing: Meeting cadences (weekly refinement, release sync, post-launch review)

**Gap Impact:** High (without clear collaboration, teams work in silos, misalignment)

**Recommendation for Gap:** Add/expand section "Cross-Functional Collaboration Workflows" with:
- PM ↔ PO: Strategic-opportunity review checklist (questions to ask)
- PO ↔ BA: Acceptance criteria refinement (back-and-forth pattern)
- PO ↔ Design: Early involvement, trade-off discussion
- PO ↔ Engineering: Clarity, blocker resolution
- PO ↔ QA: AC verification, edge case discovery
- PO ↔ Marketing: Feature messaging, launch coordination
- Meeting cadences (weekly refinement, daily standups, release planning, post-launch review)

---

## COVERAGE SUMMARY TABLE

| Dimension | Coverage | Strength | Gap | Impact |
|-----------|----------|----------|-----|--------|
| 1. Core Responsibilities | 70% | Backlog prioritization | Daily orchestration | Medium |
| 2. Discovery & Validation | 5% | Assumes PM does it | PO validation role | Medium |
| 3. Acceptance Criteria | 30% | Template provided | 3 C's, INVEST, BA patterns | High |
| 4. Stakeholder Management | 25% | Anti-pattern aware | Communication cadence, saying no | **High** |
| 5. Release Planning | **0%** | — | Multi-team coordination, gates | **Critical** |
| 6. Data-Driven Decisions | 15% | Simple formula | Metrics framework, experimentation | **Critical** |
| 7. Post-Launch Measurement | **0%** | — | Adoption tracking, kill decisions | **Critical** |
| 8. Roadmap Communication | 10% | Mentions documentation | OKRs, quarterly planning | High |
| 9. Feedback Loops | 5% | Aware of support/analytics | A.C.A.F., volume assessment | High |
| 10. Tech Debt Balance | **0%** | — | Prioritization framework | Medium |
| 11. Risk Management | **0%** | — | Probability×Impact scoring | Medium |
| 12. Cross-Functional Collab | 35% | 3 patterns mentioned | Detailed workflows, cadences | High |

**Overall Coverage:** ~25% of great PO practices  
**Gaps Requiring External Skills:** 5-7 frameworks (depending on scope)

---

## RECOMMENDED ADDITIONS (BY PRIORITY)

### TIER 1: Critical (Blocks PO from being effective)
1. **Release Planning & Multi-Team Coordination** (new section ~300 words)
   - Dependency mapping, staging gates, feature flags, rollout planning, launch checklist, rollback
   
2. **Post-Launch Learning & Iteration** (new section ~350 words)
   - Metrics tracking, adoption curves, kill decisions, continuous learning loops
   
3. **Data-Driven Backlog Prioritization** (new section ~250 words)
   - AARRR framework, funnel analysis, cohort analysis, churn analysis, experimentation

4. **Stakeholder Management & Priority Communication** (new section ~300 words)
   - Saying "no" frameworks, communication cadences, trade-off narratives

### TIER 2: High (Improves quality, prevents mistakes)
5. **Acceptance Criteria Clarity** (expand existing ~200 words)
   - 3 C's, INVEST, Given/When/Then, BA collaboration patterns

6. **Continuous Customer Feedback Loops** (new section ~250 words)
   - A.C.A.F., NPS/CSAT, support categorization, volume assessment

7. **Cross-Functional Collaboration Workflows** (expand existing ~300 words)
   - PM/BA/Design/Eng/QA/Marketing workflows, meeting cadences

8. **Roadmap Communication & Strategic Alignment** (new section ~200 words)
   - OKRs, quarterly planning, stakeholder cadences

### TIER 3: Medium (Nice-to-have, polishes craft)
9. **Technical Debt & Maintenance Prioritization** (new section ~150 words)
10. **Risk Management & De-Risking** (new section ~150 words)

---

## FILE SIZE IMPLICATIONS

**Current PO Agent:** ~11 KB

**If All Additions Inline:** ~11 KB + ~2.5 KB (estimate) = ~13.5 KB (still healthy)

**Strategic Recommendation:** Modular approach (like PM agent)
- Keep Tier 1 + Tier 2 core sections in agent (~2 KB)
- Externalize complex frameworks to skill files (~3-4 new files, ~15-20 KB distributed)
- Suggested skill files:
  1. **release-coordination.md** — Release planning, dependency mapping, rollout, launch readiness
  2. **metrics-and-experimentation.md** — AARRR, funnel analysis, A/B testing, success metrics
  3. **stakeholder-alignment.md** (reference PM's version or extend) — Saying no, priority communication
  4. **feedback-loops.md** — A.C.A.F., NPS/CSAT, customer insight categorization
  5. **cross-functional-collaboration.md** — BA, Design, Eng, QA, Marketing workflows

**Result:** Agent stays ~13-14 KB (compact, optimal), detailed frameworks available in external skills (~18-22 KB)

---

## CONFIDENCE LEVELS

- **High confidence gaps** (present in research, clearly missing): Release planning, post-launch measurement, data-driven decisions, stakeholder management
- **Medium confidence gaps** (important but less commonly formalized): Feedback loops, roadmap communication, cross-functional workflows
- **Low confidence gaps** (nice-to-have, context-dependent): Tech debt balance, risk management

---

## NEXT STEPS (Pending User Approval)

1. **Validate gaps:** Does this gap analysis align with your priorities and experience?
2. **Prioritize fixes:** Should we tackle all Tier 1 items, or focus subset first?
3. **Modular strategy:** Do you want modular approach (external skills) or inline?
4. **Timeline:** How much coverage should we target? (60%, 80%, 90%?)

Once approved, I can proceed with creating the enhanced PO agent + skill files following the same approach as the PM agent.
