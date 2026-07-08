# Cross-Functional Workflows for Product Owners

Clear workflows with each function (Design, BA, Eng, QA, Marketing) prevent handoff problems.

---

## Workflow 1: PO ↔ Product Manager (Strategic → Tactical)

### The PM Creates Strategic-Opportunity Issue

**What PM Provides:**
- Market research findings (customer interviews, support tickets, competitive analysis)
- Customer validation strength (1-2 customers vs. 10+ customers)
- Strategic alignment (which OKR does this support?)
- Recommended decision (CHAMPION / DEFER / BLOCK)
- Effort estimate (rough sizing)

**Example Issue:**
```
Title: [strategic-opportunity]: Mobile App for Field Teams

Research Summary:
- 12 support tickets from field teams ("can't check out from phone")
- 4 customer interviews (all field-heavy segments)
- Competitive analysis: 3 competitors have mobile (we don't)
- Market signal: 40% of leads are field-based teams

Validation:
- 4 customers who would adopt immediately (willing to beta)
- 8 additional customers potentially interested
- Competitive differentiation: 3-month lead if we ship first

PM Decision: CHAMPION (strong market signal, strategic alignment with Q3 mobile pillar)

Rough Effort: 10 weeks (backend API + iOS + Android)
```

### PO Reviews and Asks Clarifying Questions

**PO's Perspective:** \"Does this deserve backlog space?\"

**Questions to Ask:**
- \"How strong is the validation? 4 customers willing to beta, but what about the other 8? Do you have a commitment level?\"
- \"What's the competitive advantage timeline? If we don't ship in 10 weeks, can competitors copy in that time?\"
- \"Does this fit with our Q3 goals? Which OKR?\"
- \"What's the revenue impact? Per-customer value? Potential TAM?\"
- \"Is 10 weeks realistic? Any dependencies or technical risks?\"

**PO Decides:**
- Accept PM recommendation (move to backlog)
- Ask for more validation before deciding
- Override if backlog doesn't have capacity
- Suggest alternative scope (MVP instead of full app)

### PO Creates Feature-Request Issue

Once accepted, PO converts strategic-opportunity into tactical feature-request:

```
Title: [feature-request]: Mobile App - MVP: iOS Checkout for Field Teams

Linked to: strategic-opportunity #[X]

User Story:
As a field manager, I want to check out equipment from my iPhone,
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

---

## Workflow 2: PO ↔ Business Analyst (Feature → Acceptance Criteria)

### PO Provides (High-Level)

```
[feature-request]: Mobile App - iOS Checkout

User Story: As a field manager, I want to checkout equipment from my iPhone so I can avoid office trip.

Problem: Field teams currently return to office or ask colleagues to checkout.

Key Requirements:
1. Support offline (no WiFi at sites)
2. Auto-sync when reconnected
3. Reduce checkout time from 5 min (web) to 2 min (mobile)
4. Work on iPhone 11+ (not iPad)
```

### BA Asks Clarifying Questions

**In comments on feature-request issue:**

```
@[PO], I have clarifying questions before writing acceptance criteria:

1. Offline handling:
   - User can checkout without network connection?
   - What happens if network drops mid-checkout?
   - Can they complete later when reconnected?

2. Data sync:
   - If two phones both checkout same item offline, what happens?
   - Who wins? (First one syncs? Latest overwrites?)

3. Performance:
   - \"Reduce to 2 min\" - is this end-to-end checkout time?
   - Or just the mobile app interaction (not including backend)?

4. Device support:
   - iPhone 11+ means iOS 13+?
   - What about Android later - should we design for that now?

5. Features:
   - Can users browse equipment on mobile or just checkout known item?
   - Do they need receipt/confirmation on phone?

Let's sync to clarify before I write AC.
```

### PO Responds

```
Great questions! Here are my answers:

1. Offline handling:
   - Yes, complete checkout without network (core requirement)
   - If network drops mid-checkout: Auto-save and resume when reconnected
   - Yes, they can complete later

2. Data sync:
   - Shouldn't happen in practice (each person checks out different items)
   - If it does: Second checkout fails with \"item already checked out\" message (team resolves in system)

3. Performance:
   - End-to-end time from \"open app\" to \"confirmation screen\"
   - Backend should be fast; UX should be minimal clicks

4. Device support:
   - iOS 13+ correct
   - For Android: We'll decide in Phase 2 (don't design for now, but don't block it)

5. Features:
   - MVP: They know what they're checking out (ID only)
   - Search/browse added in Phase 2
   - Receipt: Yes, show on screen + email confirmation
```

### BA Writes Acceptance Criteria

```
## Acceptance Criteria (Given/When/Then)

### Scenario 1: Normal Checkout (Online)
Given: User has open network connection
When: User enters equipment ID and taps \"Checkout\"
Then: Equipment checked out + receipt shown within 2 seconds

### Scenario 2: Offline Checkout
Given: User has no network connection
When: User enters equipment ID and taps \"Checkout\"
Then: 
  - Checkout queued locally (not confirmed yet)
  - User sees \"Offline - will sync when connected\" message
  - Receipt shows \"Pending sync\"

### Scenario 3: Auto-Sync When Reconnected
Given: User checked out equipment while offline
And: Network is now available
When: User opens app or waits 10 seconds
Then:
  - Checkout syncs to backend (no user action needed)
  - Receipt shows \"Synced\"
  - Offline queue clears

### Scenario 4: Device Support
Given: User on iPhone 11 running iOS 13
When: User opens app
Then: App works correctly (all scenarios pass)

Given: User on iPhone 5 running iOS 10
When: User opens app
Then: \"This app requires iOS 13+\" error shown

### Scenario 5: Error Handling
Given: User enters invalid equipment ID
When: User taps \"Checkout\"
Then: Error message \"Equipment not found\" shown + form not cleared
```

### PO Approves

```
Approved! These AC are clear and testable. Ready for dev.

One clarification: In Scenario 3, can we make sync even faster?
(Thinking: Sync immediately upon reconnect, not wait 10 seconds)

Otherwise looks good.
```

---

## Meeting Cadences for Coordination

### Weekly Refinement Session (1 hour)

**Attendees:** PO, BA, Dev lead, Design  
**When:** Tuesday morning  
**Purpose:** Refine backlog for next sprint

**Agenda:**
1. **Review top 3-5 backlog items** (PO presents)
   - User story + problem statement
   - Value assessment
   - Any questions?

2. **BA clarifies requirements** (BA leads)
   - What questions do we have?
   - PO responds to clarify intent
   - Document any assumptions

3. **Design shows mockups** (Design presents)
   - Here's the interaction design
   - Edge cases covered?
   - PO approves or suggests changes

4. **Dev estimates effort** (Dev lead estimates)
   - How much work? 
   - Any risks?
   - Dependencies identified?

5. **PO makes scope trade-offs**
   - If effort too high: reduce scope or defer
   - If blockers: resolve or remove from sprint

**Outcome:** Sprint backlog is clear; dev ready to start Monday

### Daily Standups (15 min)

**Attendees:** Whole team  
**When:** 10 AM daily  
**Format:** Status + Blockers

```
- PO: \"What's the status on [Feature X]?\"
- Dev: \"We completed [part 1], working on [part 2]. One blocker: can you clarify [question]?\"
- PO: \"[Answers on the spot or says 'let me look into this']\"
- QA: \"No blockers from our side, ready to test whenever [Feature Y] is ready for QA\"
```

### Release Planning (1 hour, weekly during release window)

**Attendees:** PM, PO, Eng lead, QA lead, Infra lead  
**When:** Friday before release week  
**Purpose:** Coordinate release across teams

```
Agenda:
1. What shipped last week?
2. What ships this week?
3. Blockers? (dependency issues?)
4. Risks? (high-risk items need buffer time)
5. Go/no-go decision (safe to deploy?)
6. Rollback plan (tested and documented?)
```

### Post-Launch Review (1 hour, 2 weeks after launch)

**Attendees:** PO, PM, Eng, QA, Marketing  
**When:** After 2-week period  
**Purpose:** Evaluate feature health + learnings

```
Agenda:
1. Metrics review: Did we hit targets?
2. Support issues: Any blockers/complaints?
3. User feedback: NPS, CSAT?
4. Learnings: What would we do differently?
5. Decision: Iterate, scale, or kill?
```

---

## Implementation Checklist

- [ ] Schedule weekly refinement session
- [ ] Establish daily standup routine
- [ ] Create feature-request issue template (PO → BA → Dev)
- [ ] Define acceptance criteria format (Given/When/Then)
- [ ] Design mockup review process
- [ ] Establish QA test case design process
- [ ] Weekly release planning during release window
- [ ] Post-launch review cadence (2 weeks after launch)
- [ ] Create communication channels (Slack, wiki for decisions)
- [ ] Document blockers log (track what's stuck)