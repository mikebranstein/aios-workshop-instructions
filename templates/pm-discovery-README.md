# PM Discovery Process: Autonomous Feature Opportunity Validation

## Overview

The Product Manager discovery process lets you input a 1-3 sentence feature idea and have the PM agent autonomously:
1. Research the idea (support trends, competitor analysis, market signals)
2. Validate with customers and market data
3. Make a decision (CHAMPION / DEFER / BLOCK)
4. Track state in GitHub so the decision is auditable and reviewable

The PM agent runs continuously as part of orchestration, checking for new `pm-idea` issues and processing them autonomously.

---

## How to Start a PM Discovery

### Step 1: Create a GitHub issue

```bash
gh issue create \
  --title "[pm-idea]: Mobile app for field teams" \
  --body "4 support tickets this week about checking out equipment from the field" \
  --label "pm-idea"
```

**Minimal example:**
- **Title** (required): 1-3 sentence feature idea
- **Label** (required): `pm-idea`
- **Body** (optional but recommended): Customer trigger, competitive context, support ticket references, or strategic rationale

**Rich example:**
```
Title: [pm-idea]: Mobile app for field teams
Body:
- Support tickets: #245, #312, #478 (all mention "can't checkout from field")
- Customer signal: 4 enterprise customers mentioned this in recent calls
- Competitive advantage: Competitor X doesn't have mobile; 6-month head start possible
- Strategic fit: Supports Q3 priority "mobile-first experience"
```

The more context you provide, the better the PM agent can research and validate.

---

## The Autonomous PM Workflow

Once you create a `pm-idea` issue, the PM agent automatically:

### Phase 1: Research (posted as comment)
Agent discovers signals about the idea:
- **Support trends**: How many tickets mention this? What's the customer pain?
- **Competitor analysis**: Do competitors have this? If yes, how do they implement it? If no, it's a differentiation opportunity.
- **Market size**: Estimate how many customers are affected (1-2 = niche, 20%+ = major opportunity)
- **Macro trends**: Does this align with market trends (remote work, AI, automation, etc.)?
- **Timeline**: Is market timing right? Is this urgent or can it wait?

**Agent posts**: Research findings as a GitHub comment with evidence

### Phase 2: Validation (posted as comment)
Agent evaluates the idea against strategic criteria:
- **Strategic fit**: ✅ or ❌ Does this align with product vision and current Q3 priorities?
- **Market opportunity**: High/Medium/Low — how many customers, how severe, how unique?
- **Competitive advantage**: ✅ or ❌ Can we do this better than competitors? Is it defensible?
- **Feasibility**: Quick win (1-2 weeks) / Moderate (3-4 weeks) / Significant (5+ weeks)
- **Customer validation strength**: Weak (1 person asked) / Medium (3-5 mentions) / Strong (10+ customers or willing to pilot)

**Agent posts**: Validation results as a GitHub comment with scores and analysis

### Phase 3: Decision (posted as comment)
Agent makes a decision:
- **CHAMPION**: Strategically important, validated with customers, achieves competitive advantage → Ready for PO prioritization
- **DEFER**: Valid idea but not strategic right now → Revisit next quarter
- **BLOCK**: Doesn't fit strategy or market signal is weak → Not pursuing

**Agent posts**: Decision JSON as a GitHub comment with detailed rationale

**Example decision JSON:**
```json
{
  "role": "Product Manager",
  "opportunity": "Mobile app for field teams",
  "research_findings": "12 support tickets mentioning field checkout, 4 enterprise customers confirmed need",
  "strategic_alignment": "✅ Supports Q3 priority 'mobile-first experience'",
  "market_opportunity": "High - affects 80% of enterprise customers",
  "competitive_advantage": "✅ Competitors don't have mobile; 6-month head start possible",
  "effort_estimate": "Moderate - 3-4 weeks for MVP",
  "customer_validation_strength": "Strong - 12 tickets + 4 customer interviews",
  "decision": "CHAMPION",
  "rationale": "Addresses real customer pain, aligns with strategic priority, achieves competitive differentiation, effort is reasonable",
  "next_step": "Ready for PO prioritization. Recommend high priority given customer demand."
}
```

---

## State Tracking: How to Read Progress

The GitHub issue is the source of truth for state. Track progress:

### 1. **Labels show current status**

| Label | Meaning | Action |
|-------|---------|--------|
| `pm-idea` | Submitted, awaiting research | None — agent will pick up |
| `pm-validating` | Agent is researching/validating | Wait for research comment |
| `pm-opportunity` | Validated and CHAMPION'd | Send to PO for prioritization |
| `pm-deferred` | Valid but not strategic now | Revisit quarterly |
| `pm-blocked` | Blocked or doesn't fit strategy | Archive or closed |

### 2. **Comments show detailed progress**

Open the issue and scroll through comments:
- **Comment 1** (Research): "Found 12 support tickets mentioning this problem..."
- **Comment 2** (Validation): "Strategic alignment: ✅ Market opportunity: High..."
- **Comment 3** (Decision): JSON with final decision and rationale
- **Comment 4+** (Quarterly reviews): "Quarterly review [date]: Still seeing strong customer interest..."

### 3. **Projects board shows workflow**

Visual progress at a glance:
```
Ideas → Discovery → Validating → Ready for PO → Deferred → Blocked
```

Each issue moves across columns as it progresses.

---

## What Happens After CHAMPION?

If the PM agent decides CHAMPION:

1. **Agent posts notification**: "Validated and ready for PO prioritization"
2. **Label applied**: `pm-opportunity`
3. **Issue moved to**: "Ready for PO" column in Projects
4. **PO is notified**: GitHub notification so PO knows a new opportunity is ready
5. **PO reviews**: Checks PM research and validation
6. **PO prioritizes**: Adds to backlog, calculates priority score, queues for development

The issue now flows from PM ownership to PO ownership.

---

## What Happens After DEFER or BLOCK?

### DEFER
- Issue labeled `pm-deferred`
- Moved to "Deferred" column in Projects
- Agent posts: "Revisit next quarter. Customer interest may change."
- **Quarterly re-check**: Agent will automatically re-evaluate next quarter

### BLOCK
- Issue labeled `pm-blocked`
- Can be closed or moved to "Blocked" column
- Agent posts: "Blocking reasons: [reason]"
- **When to unblock**: If blocking reason changes, user can re-open and re-submit

---

## Quarterly Re-Checks: Staying Current

Every quarter, the PM agent automatically re-evaluates all `pm-opportunity` issues:

```bash
# This runs automatically at start of each quarter
PM_AGENT quarterly-review
```

**What the agent checks:**
- ✅ Is customer interest still strong?
- ✅ Has market shifted (new competitor, regulatory change, macro trend)?
- ✅ Does this still align with strategic priorities?
- ✅ Should we maintain CHAMPION or demote to DEFER?

**Agent posts quarterly comment:**
```
Quarterly Review [Q4 2026]:
Customer interest: Still strong (2 new support tickets this quarter)
Competitive landscape: No changes
Strategic alignment: ✅ Still fits Q4 priorities
Recommendation: Maintain CHAMPION
Status: Ready for continued PO prioritization
```

If recommendation changes, agent updates labels and decision.

---

## Best Practices

### ✅ DO
- **Provide context**: Richer issue body = better research by agent
- **Link to evidence**: Reference support tickets, customer names, competitive URLs
- **Include strategic rationale**: "This supports Q3 priority [X]"
- **Review quarterly**: Read agent's quarterly re-check comments
- **Act on CHAMPION**: Once PM validates, PO should prioritize quickly

### ❌ DON'T
- **Submit vague ideas**: "Improve UX" won't help agent validate
- **Ignore research findings**: Agent posts evidence; review it before deciding
- **Let deferred ideas accumulate**: Archive or close ideas that won't be revisited
- **Override agent decision without reason**: If you disagree, document why in a comment

---

## Example: Full PM Discovery Lifecycle

### Day 1: User submits idea
```
Issue Title: [pm-idea]: Mobile app for field teams
Label: pm-idea
Body: 4 support tickets this week about checkout from field. Competitor X doesn't have mobile.
```

### Day 2: PM agent researches
```
[COMMENT 1]
Research Findings:
- Found 12 support tickets mentioning field checkout
- 4 enterprise customers mentioned in recent calls
- Competitor X doesn't have mobile; Competitor Y has basic iOS app
- Market timing: Right now (remote work trend increasing)
- Effort signal: 3-4 weeks estimated for MVP
```

### Day 2: PM agent validates
```
[COMMENT 2]
Validation Results:
- Strategic alignment: ✅ Q3 priority "mobile-first experience"
- Market opportunity: HIGH (80% of enterprise customers affected)
- Competitive advantage: ✅ 6-month head start possible
- Feasibility: Moderate effort
- Customer validation: STRONG (12 tickets + 4 customer confirmations)
Score: 9/10 — Strong opportunity
```

### Day 2: PM agent decides
```
[COMMENT 3 - DECISION]
{
  "decision": "CHAMPION",
  "rationale": "Validated with customers, strategic fit, competitive advantage",
  "next_step": "Ready for PO prioritization"
}
```

**Labels updated**: `pm-idea` → `pm-opportunity`
**Projects moved**: Idea column → Ready for PO
**PO notified**: GitHub notification sent

### Day 3: PO reviews and prioritizes
PO reads PM validation, checks priority formula, adds to backlog.

### Q4 (next quarter): PM agent re-checks
```
[COMMENT 4 - QUARTERLY REVIEW]
Quarterly Review [Q4]:
Customer interest: Still strong (3 new support tickets)
Competitive landscape: Competitor Y announced mobile roadmap
Strategic alignment: ✅ Still Q4 priority
Recommendation: Maintain CHAMPION (may become even higher priority given competitor move)
```

---

## Troubleshooting

**Q: PM agent didn't process my idea. Why?**
A: Check label (`pm-idea` applied?) and wait for orchestrator cycle. If agent still hasn't processed after 24 hours, manually trigger:
```bash
PM_AGENT autonomous-discover <issue-number>
```

**Q: I disagree with the PM agent's decision. What do I do?**
A: Post a comment on the issue with your reasoning. You can override the decision, but document why for audit trail.

**Q: Can I submit multiple ideas at once?**
A: Yes. Create multiple issues with `pm-idea` label. Agent processes them in parallel.

**Q: What if the PM agent finds the idea invalid? Can I resubmit?**
A: If DEFER: Wait for quarterly review, market may change. If BLOCK: Understand the reason, fix the underlying issue, then resubmit as new idea.

---

## Integration with Orchestrator

The PM discovery process is built into the PM-PO orchestration loop (separate from development):

1. **Cycle Start (Step 0.5)**: Orchestrator checks for `pm-idea` issues
2. **Trigger PM Agent**: If ideas exist, orchestrator starts PM autonomous discovery
3. **Wait for Completion**: PM agent processes all ideas, posts decisions
4. **PO Stage**: Orchestrator then moves to PO prioritization with validated opportunities
5. **Backlog Handoff**: Prioritized issues move to "Ready for Development" column
6. **Development Picks Up**: Development orchestrator pulls from backlog independently
7. **Quarterly**: PM orchestrator triggers quarterly re-evaluation

See [orchestrator.pm-po.agent.md](agents/orchestrator.pm-po.agent.md) for PM-PO orchestration flow.
See [orchestrator.development.agent.md](agents/orchestrator.development.agent.md) for development pipeline (runs independently, pulls from PM-PO backlog).
