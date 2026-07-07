# Continuous Learning Cycles for Product Decisions

Don't wait 3 months for a retrospective. Use 2-sprint feedback loops to make fast decisions about what to build, what to iterate, and when to kill.

---

## The Problem with Long Feedback Loops

**Old way (quarterly review):**

```
Week 1: Ship feature
Weeks 2-12: Radio silence (nobody uses it)
Week 12: Retrospective: "Why didn't this work?"
Week 13-14: Analyze and decide to kill (1-2 weeks too late, team demoralized)
```

**Cost:** 3 months of wasted engineering, team momentum lost, wrong conclusions ("customers don't want this" vs. "we shipped it wrong").

---

## The New Way: 2-Sprint Feedback Loops

Every feature/experiment gets 2 sprints (4 weeks) of intensive feedback, then a clear decision.

### Timeline

```
SPRINT 1 (Weeks 1-2): BUILD
- Ship feature to 100% of users (or controlled rollout)
- Feature is "rough but usable"
- Goal: Get real users on it

SPRINT 2 (Week 3): COLLECT FEEDBACK
- Monitor adoption (% of users activating feature)
- Interview 10-15 users (qualitative)
- Check metrics (is it reducing churn? increasing engagement?)
- Review support feedback
- Competitor monitoring

SPRINT 2 (Week 4): DECIDE
- Adopt the decision tree (below)
- Commit to Iterate, Pivot, or Kill
- Communicate decision to team
```

### Decision Tree

```
IS ADOPTION >20% IN FIRST 2 WEEKS?

└─ YES (20%+)
   └─ PHASE 2: Iterate & Improve
      - Customers validate value
      - Invest in polish, performance, edge cases
      - Next milestone: 50% adoption (3-6 months)
      - Revenue opportunity confirmed

└─ NO (<20%)
   ├─ Diagnosis: Why low adoption?
   │  ├─ Discovery broken? (Users don't know feature exists)
   │  │  └─ Action: Better onboarding, education, tutorials
   │  │  └─ Re-test in 2 weeks (revised rollout)
   │  │
   │  ├─ UX broken? (Users find it confusing)
   │  │  └─ Action: UX redesign, simplification
   │  │  └─ Re-test in 2 weeks (redesigned feature)
   │  │
   │  ├─ Audience wrong? (Built for SMB, only enterprise using)
   │  │  └─ Action: Re-target marketing, messaging
   │  │  └─ Re-test in 2 weeks (new audience)
   │  │
   │  ├─ Value not there (Users try it, don't see ROI)
   │  │  └─ Action: Kill it (probably unfixable in short term)
   │  │  └─ Decision: KILL
   │  │
   │  └─ Market moved? (Competitors shipped faster)
   │     └─ Action: Kill it (no longer differentiator)
   │     └─ Decision: KILL
   │
   └─ IF FIXABLE IN 1-2 SPRINTS
      - Re-test after fix (2 more weeks)
      - If >20% adoption after fix → PHASE 2
      - If still <20% → KILL

IF KILL: Ship removal (even if small % use it)
- Users with data: Export before removal
- Docs: Explain why removed, alternatives
- Team: Learn & share (quarterly postmortem)
```

---

## Implementation Checklist

- [ ] For next feature ship: Plan a 2-sprint feedback loop
- [ ] Create decision tree before shipping (know your kill criteria upfront)
- [ ] Week 3 of release: Collect quantitative + qualitative feedback
- [ ] Week 4: Make explicit decision (Iterate, Pivot, or Kill)
- [ ] Document decision + evidence
- [ ] 3 months post-ship: Cohort review (proceed to Phase 2 or re-evaluate)
- [ ] Kill with clarity: Communicate why, thank early adopters, move on
- [ ] Monthly learning backlog review: Prioritize next assumptions to test
- [ ] Quarterly: Celebrate kills (they're learning opportunities, not failures)