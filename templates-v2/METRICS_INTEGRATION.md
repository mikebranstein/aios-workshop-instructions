---
description: "Quick integration guide: add metrics to agents and orchestrators using the metrics-reporter utility (wiki-manager pattern)."
---

# Metrics Integration Guide

Simple, non-invasive metrics - just call the utility at the end. Zero agent instrumentation required.

---

## Agent Integration (2 lines per agent)

### Intake Agent Example

**Add at agent startup (very top):**
```bash
#!/bin/bash
# intake.agent.md

./utilities/metrics-reporter.md start \
  --agent-id "intake" \
  --issue-number "$ISSUE_NUMBER"

# ... existing agent code ...
```

**Add at agent completion (before or after posting decision):**
```bash
./utilities/metrics-reporter.md report \
  --agent-id "intake" \
  --issue-number "$ISSUE_NUMBER" \
  --decision "$DECISION" \
  --confidence "$CONFIDENCE"

# Then continue with your normal decision comment
gh issue comment "$ISSUE_NUMBER" --body "## Intake Decision: $DECISION"
```

### All Other Agents

Same pattern for: design, build, qa, policy, business-analyst, research, product-manager, product-owner, idea-scout

```bash
# At startup:
./utilities/metrics-reporter.md start --agent-id "<agent-id>" --issue-number "$ISSUE_NUMBER"

# At completion:
./utilities/metrics-reporter.md report \
  --agent-id "<agent-id>" \
  --issue-number "$ISSUE_NUMBER" \
  --decision "$DECISION_STATUS" \
  --confidence "$CONFIDENCE_SCORE"
```

---

## Orchestrator Integration (1 call per cycle)

### Dev Orchestrator Example

**At cycle end (after all spawned agents complete):**

```bash
#!/bin/bash
# dev-orchestrator-v2.agent.md (at cycle end)

ORCHESTRATOR="dev"
CYCLE_START_TIME=$(date +%s)

# ... existing cycle code (spawn agents, etc.) ...

CYCLE_END_TIME=$(date +%s)
CYCLE_DURATION=$((CYCLE_END_TIME - CYCLE_START_TIME))

# Report cycle metrics
./utilities/metrics-reporter.md report-cycle \
  --orchestrator "$ORCHESTRATOR" \
  --cycle-number "$CYCLE_NUMBER" \
  --duration-seconds "$CYCLE_DURATION" \
  --issues-processed "5" \
  --issues-completed "3" \
  --agents-spawned "6"

echo "Cycle $CYCLE_NUMBER: ${CYCLE_DURATION}s, 3/5 complete"
```

### PM Orchestrator & PO Orchestrator

Same pattern:

```bash
./utilities/metrics-reporter.md report-cycle \
  --orchestrator "pm" \
  --cycle-number "$CYCLE_NUMBER" \
  --duration-seconds "$CYCLE_DURATION" \
  --issues-processed "$ISSUES_FOUND" \
  --issues-completed "$COMPLETED_COUNT" \
  --agents-spawned "$AGENT_COUNT"
```

---

## What Gets Recorded

**Per-Agent Call:**
- Agent ID, issue #, decision (PASS/FAIL/BLOCKED/REVISE)
- Execution duration (auto-calculated from start → report)
- Confidence (0.0-1.0)
- Timestamp
- → Stored in: `Metrics-YYYY-MM-DD.md` + `<agent-id>.md`

**Per-Cycle Call:**
- Orchestrator name, cycle #, duration
- Issues processed & completed, agents spawned
- Success rate (auto-calculated)
- Timestamp
- → Stored in: `Cycles-<Orchestrator>.md` + `Metrics-YYYY-MM-DD.md`

---

## View Metrics

### Browse Wiki Pages
```
https://github.com/<owner>/<repo>/wiki
```

Pages created:
- `Metrics-2026-07-09` (daily summary)
- `intake`, `design`, `build`, `qa`, `policy` (agent pages)
- `Cycles-Dev`, `Cycles-Pm`, `Cycles-Po` (orchestrator pages)
- `Metrics` (optional overview)

### Query via Utility

```bash
# Recent runs for intake agent
./utilities/metrics-reporter.md query-agent intake

# Slowest agents (last 7 days)
./utilities/metrics-reporter.md query-slowest

# Last 5 dev cycles
./utilities/metrics-reporter.md query-cycles dev 5
```

---

## Integration Checklist

**For Each Agent (14 total: intake, design, build, qa, policy, ba, research, pm, po, idea-scout, foundation-research, foundation-architect, architecture-review, refactor-planner):**

- [ ] Add `start` call at agent initialization
- [ ] Add `report` call at agent completion
- [ ] Test with one execution (check wiki page appears)

**For Each Orchestrator (6 total: Foundation, Discovery, PM, PO, Dev, Architecture Review):**

- [ ] Add `report-cycle` call at cycle end
- [ ] Test with one cycle (check Cycles-* page appears)

**Validation:**

- [ ] Visit wiki: `https://github.com/<owner>/<repo>/wiki`
- [ ] See `Metrics-YYYY-MM-DD` page for today
- [ ] See agent pages (e.g., `intake`)
- [ ] See orchestrator pages (e.g., `Cycles-Dev`)
- [ ] Query slowest: `./metrics-reporter.md query-slowest`

---

## That's It

No environment variables. No JSON formatting. No issue comments. No dashboard scripts.

Just:
1. Call `start` at agent init
2. Call `report` at agent end
3. Call `report-cycle` at orchestrator cycle end
4. Check wiki pages

The utility handles the rest.
