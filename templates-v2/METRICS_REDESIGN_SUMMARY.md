# Metrics System - Redesigned ✅

## What Changed

You were right - the original approach was too complex. Redesigned to follow the **wiki-manager utility pattern**:

### Old Approach ❌
- Added timing code to every agent
- Had agents call multiple reporter functions
- Stored metrics in GitHub issue comments
- Required complex jq queries to analyze
- Dashboard script needed to visualize

### New Approach ✅
- Agents call utility at completion (2 lines total)
- Orchestrators call utility at cycle end (1 call)
- Metrics stored in GitHub wiki pages (auto-organized)
- No instrumentation, no JSON formatting, no queries
- Wiki pages ARE the dashboard

---

## Files

### Core
- **[metrics-reporter.md](templates-v2/utilities/metrics-reporter.md)** — Utility script (like wiki-manager but for metrics)

### Documentation
- **[METRICS_INTEGRATION.md](templates-v2/METRICS_INTEGRATION.md)** — Copy-paste integration examples
- **[ORCHESTRATION_SYSTEM_AUDIT_v2.md](templates-v2/ORCHESTRATION_SYSTEM_AUDIT_v2.md)** — Updated Part 1b

### Deleted
- METRICS_QUICK_START.md (old approach)
- METRICS_COMPONENTS_INVENTORY.md (old approach)
- metrics-data-contract.md (old approach)
- metrics-dashboard.sh (old approach)

---

## Usage Pattern

### Agent Integration
```bash
# intake.agent.md - At startup
./utilities/metrics-reporter.md start --agent-id "intake" --issue-number "$ISSUE_NUMBER"

# ... agent does work ...

# At completion
./utilities/metrics-reporter.md report \
  --agent-id "intake" \
  --issue-number "$ISSUE_NUMBER" \
  --decision "PASS" \
  --confidence "0.98"
```

### Orchestrator Integration
```bash
# At cycle end
./utilities/metrics-reporter.md report-cycle \
  --orchestrator "dev" \
  --cycle-number "42" \
  --duration-seconds "90" \
  --issues-processed "5" \
  --issues-completed "3" \
  --agents-spawned "6"
```

---

## Wiki Pages Auto-Created

The utility automatically creates and maintains these pages:

| Page | Contains | Updated By |
|------|----------|-----------|
| `Metrics-YYYY-MM-DD` | All daily metrics | Both agents & orchestrators |
| `intake` | Intake agent history | Intake agent report calls |
| `design` | Design agent history | Design agent report calls |
| `build` | Build agent history | Build agent report calls |
| `qa` | QA agent history | QA agent report calls |
| `policy` | Policy agent history | Policy agent report calls |
| (other agents) | Per-agent histories | Respective agents |
| `Cycles-Dev` | Dev orchestrator cycles | Dev orchestrator report-cycle |
| `Cycles-Pm` | PM orchestrator cycles | PM orchestrator report-cycle |
| `Cycles-Po` | PO orchestrator cycles | PO orchestrator report-cycle |
| `Metrics` | Dashboard overview | (optional, manual) |

---

## View Metrics

### GitHub Wiki
Visit: `https://github.com/<owner>/<repo>/wiki`
- Browse daily summaries: `Metrics-2026-07-09`
- Check agent history: `intake`, `design`, `build`
- Review orchestrator cycles: `Cycles-Dev`

### CLI Queries
```bash
# Recent intake metrics
./utilities/metrics-reporter.md query-agent intake

# Slowest agents (last 7 days)
./utilities/metrics-reporter.md query-slowest

# Last 5 dev cycles
./utilities/metrics-reporter.md query-cycles dev 5
```

---

## Zero Complexity

✅ **No manual timing code** — Utility auto-calculates duration  
✅ **No environment variables** — Uses GitHub CLI context  
✅ **No JSON formatting** — Utility handles it  
✅ **No issue comments** — Stored in wiki  
✅ **No complex queries** — Simple utility commands  
✅ **No external DB** — GitHub wiki only  

---

## Implementation Checklist

**For Each Agent (14 agents: intake, design, build, qa, policy, ba, research, pm, po, idea-scout, foundation-research, foundation-architect, architecture-review, refactor-planner):**
- [ ] Add `./utilities/metrics-reporter.md start` at startup
- [ ] Add `./utilities/metrics-reporter.md report` at completion

**For Each Orchestrator (6: Foundation, Discovery, PM, PO, Dev, Architecture Review):**
- [ ] Add `./utilities/metrics-reporter.md report-cycle` at cycle end

**Verify:**
- [ ] Check wiki: `https://github.com/<owner>/<repo>/wiki/Metrics-YYYY-MM-DD`
- [ ] Query: `./utilities/metrics-reporter.md query-slowest`

---

## Next Steps

1. **Review** [METRICS_INTEGRATION.md](templates-v2/METRICS_INTEGRATION.md) for copy-paste examples
2. **Add** the 2 utility calls to one agent (e.g., intake) and test
3. **Verify** metrics appear in GitHub wiki
4. **Repeat** for remaining 13 agents and 6 orchestrators
5. **Monitor** via wiki pages or utility queries

---

## Key Difference from Old Approach

| Aspect | Old | New |
|--------|-----|-----|
| **Storage** | GitHub issue comments | GitHub wiki pages |
| **Agent code** | Add START_TIME, END_TIME, call 2 functions | Call 2 utility commands |
| **Querying** | jq + GitHub CLI | Simple utility query commands |
| **Dashboard** | Separate script | Wiki pages ARE dashboard |
| **Setup** | Create metrics issue, set env var | Just run utility |
| **Complexity** | High (instrumentation + querying) | Low (just call utility) |

This is **much cleaner** and follows the wiki-manager pattern you prefer.
