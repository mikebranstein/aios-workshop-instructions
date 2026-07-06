# Module 13 - Product Ownership: Strategic Direction and Backlog Management

## Concept: The product owner guides what gets built and why

Modules 1-12 focused on **how** to build features efficiently: intake → design → build → verification → QA → policy → release. But someone needs to decide **what** to build and **why**—that's the product owner.

**Module 13 introduces the product owner role:** the strategic decision-maker who defines product vision, suggests features based on user needs and business goals, prioritizes the backlog, and ensures the development pipeline works on the most valuable items.

The key distinction:
- **Product Manager** (strategic): Market research, competitive analysis, overall product strategy
- **Product Owner** (execution): Translate strategy into specific features, prioritize backlog, work with development team

**Product owners are the voice of the product.** They balance:
- User needs: "What problems do our users have?"
- Business goals: "What drives revenue and growth?"
- Team capacity: "What can we realistically build?"
- Technical constraints: "What's feasible given our architecture?"

Product owners don't write acceptance criteria or design systems. They decide what to build and why. The BA, Design, and Build teams take it from there.

## Where the product owner fits in the workflow

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│ [Product Owner]                                          │
│ ├─ Define product vision & strategy                     │
│ ├─ Identify user needs and business opportunities       │
│ ├─ Create & refine backlog items                        │
│ ├─ Prioritize features (what to build next)             │
│ └─ Create GitHub issues and order them                  │
│                                                          │
│ ↓ (feature idea flows downstream)                       │
│                                                          │
│ [Intake] → [BA] → [Design] → [Build]                   │
│ ↓                                                        │
│ [Verification] → [QA] → [Policy] → [Release]           │
│                                                          │
│ ↑ (feedback loops back to PO for refinement)            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

Product owner is **upstream** of Intake—the source of feature ideas.

## Time Box

- Target: 60 minutes (focused on understanding the PO role and orchestration with BA)

## Required Tasks

1. Understand the product owner role and decision-making framework.
2. Define your product vision and strategic goals.
3. Review the product owner agent (`templates/agents/product-owner.agent.md`).
4. Create or refine backlog in GitHub (create a few feature ideas).
5. Practice orchestration: Product Owner suggests → BA clarifies → iterate.
6. Verify backlog ordering reflects priorities.

---

## Step 1 (10 minutes): Understand the product owner role

A product owner is responsible for:

**Vision & Strategy**
- Define where the product is headed
- Ensure features align with business goals
- Communicate the "why" behind decisions

**Backlog Management**
- Create and refine feature ideas
- Prioritize based on value, urgency, user impact
- Order items for the development team to work on

**Stakeholder Communication**
- Translate between executives (who think in terms of revenue), customers (who need problems solved), and developers (who think in code)
- Field questions about timelines and priorities
- Protect the team from too many interruptions

**Scope & Priority Decisions**
- Decide what to build, what to defer, what to cut
- Make trade-off decisions (building Feature A means not building Feature B)
- Use data and feedback to guide decisions

**Collaboration**
- Work with BA to clarify requirements
- Work with Design to understand feasibility
- Work with QA to validate shipped features

**Key insight:** Product owners decide WHAT to build and WHY. They do NOT:
- Define acceptance criteria (BA does this)
- Design architecture (Design does this)
- Implement code (Build does this)
- Write test cases (QA does this)

Your job is **strategic vision and prioritization**, not execution details.

---

## Step 2 (10 minutes): Define your product vision

Every product owner needs a clear vision to guide decisions.

**Vision framework:**
- **Who are your users?** (personas, pain points)
- **What problem does the product solve?** (core value proposition)
- **What makes it different?** (competitive advantage)
- **How do you measure success?** (metrics: user satisfaction, revenue, retention, etc.)
- **What's the 3-6 month roadmap?** (strategic direction)

**Example (Team Equipment Checkout Tracker):**
- **Users:** Facility managers, employees
- **Problem:** Manual equipment tracking is time-consuming and error-prone
- **Differentiator:** Real-time availability + automated notifications
- **Success metrics:** Reduce checkout time by 50%, improve asset utilization by 30%
- **Roadmap:** MVP (basic checkout) → Smart notifications → Mobile app → Analytics dashboard

**Write this down.** You'll use it to evaluate feature ideas and make prioritization decisions.

---

## Step 3 (5 minutes): Review the product owner agent

The product owner agent is your guide for suggesting and prioritizing features. It's in `templates/agents/product-owner.agent.md` and walks you through:

1. Evaluating feature ideas against product vision
2. Assessing value (user impact, business impact, technical complexity)
3. Creating GitHub issues with proper structure
4. Prioritizing the backlog using a decision framework
5. Collaborating with BA if requirements need clarification

**Key insight:** The PO agent helps you stay disciplined about what gets into the backlog. Not every idea is a good idea—the agent helps you evaluate.

---

## Step 4 (15 minutes): Create backlog items and prioritize

Using your product vision as a guide, brainstorm 3-5 feature ideas:

**For each idea, consider:**
- **User value:** Does this solve a real user problem? High/Medium/Low
- **Business value:** Does this drive revenue, retention, or strategic goals? High/Medium/Low
- **Technical complexity:** How hard is this to build? High/Medium/Low
- **Dependencies:** Does this depend on other features?

**Create GitHub issues** for your top ideas:

```bash
# Example: Create a feature issue
gh issue create \
  --title "Smart notifications: Alert checkout conflicts" \
  --body "Users should be notified when equipment they need is checked out by someone else. Include option to reserve or request return." \
  --label "feature,backlog" \
  --project "Team Equipment Checkout Tracker"
```

**Order the backlog** by priority. GitHub Projects allows you to order issues in a backlog view.

**Prioritization framework:**
1. **Quick wins** (High user value + Low complexity) → Do first
2. **Strategic bets** (High user value + High complexity) → Plan and sequence
3. **Small enhancements** (Low user value + Low complexity) → Fill gaps
4. **Big rocks** (High business value but Low/Medium user visibility) → Schedule strategically

---

## Step 5 (15 minutes): Orchestrate with BA

The Product Owner suggests; the BA clarifies and refines.

**Workflow:**
1. **PO creates issue:** "Smart notifications for checkout conflicts"
2. **BA reads issue** and posts clarifying questions:
   - "What's the 'notification' medium? In-app, email, SMS, all three?"
   - "When exactly should the notification fire? Immediately or on next check-in?"
   - "Should users be able to disable notifications?"
3. **PO responds** with answers based on user research or business priorities
4. **BA refines** the issue with acceptance criteria
5. **Intake agent** validates and marks ready for Design

This back-and-forth ensures the PO's vision is clear before it goes to technical teams.

**Do this iteration for 1-2 of your backlog items.** See how collaboration works between PO and BA.

---

## Step 6 (5 minutes): Verify backlog is ordered and ready

Before moving to Module 14 (Capstone), verify:

- ✅ Backlog items are ordered by priority (top items are highest value)
- ✅ Quick wins are at the top (get early momentum)
- ✅ Strategic bets are sequenced (planned in phases)
- ✅ Each item has clear user value and business justification
- ✅ Dependencies are noted (if Feature X depends on Feature Y)

This ordered backlog is what the orchestrator will process: highest-priority items first.

---

## Definition of Done

✅ You have successfully completed Module 13 when:

1. **Product vision defined** (Step 2)
   - Clear articulation of: users, problem solved, differentiators, success metrics, 3-6 month roadmap
   - Vision document exists and is accessible to the team

2. **Product owner agent reviewed** (Step 3)
   - You understand the decision framework for feature evaluation
   - You know the prioritization criteria (user value, business value, complexity)
   - You can explain what the PO does vs. what BA/Design/Build do

3. **Backlog created with 3-5 feature ideas** (Step 4)
   - GitHub issues created for each feature
   - Each issue includes: description, user value assessment, business value assessment, complexity estimate
   - Features are ordered by priority (highest value first)

4. **Orchestration practiced with BA** (Step 5)
   - At least 1-2 features went through PO ↔ BA iteration
   - PO asked clarifying questions; BA responded
   - Refined issues ready for Intake

5. **Backlog verified and ready** (Step 6)
   - Top items are quick wins (high value + low complexity)
   - Strategic bets are sequenced
   - Dependencies noted
   - Backlog ordered in GitHub Projects

6. **Product owner role understood**
   - Can articulate: PO decides WHAT and WHY
   - BA defines HOW requirements are structured
   - Design handles technical architecture
   - Build implements
   - You know the boundaries of the PO role

## Stretch Goals

- Create a product roadmap showing quarterly goals and how backlog items map to them
- Implement a user feedback loop: customers → feature ideas → backlog refinement
- Add business metrics to each feature (revenue impact, user retention impact, etc.)
- Define feature gates: criteria for when to pause development and reassess priorities
- Build a competitive analysis showing how each feature differentiates you from alternatives

---

## Reflection

After completing Module 13, reflect on:
- **What defines a good feature idea?** What's your criteria?
- **How did you prioritize?** What was your reasoning?
- **How did you collaborate with BA?** What worked, what was unclear?
- **How would you communicate priorities to the team?** How would you explain WHY something is prioritized high?

Next: **Module 14 — Capstone: Full System End-to-End Run** — You'll run the complete agentic OS (PO → Intake → BA → Design → Build → Verification → QA → Policy → Release) with real features from your backlog.
