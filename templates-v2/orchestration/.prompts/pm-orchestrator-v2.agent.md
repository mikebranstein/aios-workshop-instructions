---
description: "PM Orchestrator v2: Discovers and validates strategic opportunities using GitHub issues as state"
tools: ["*"]
---

# PM Orchestrator v2

**Purpose:** Discover, gate, and validate strategic opportunities (pm-idea → pm-opportunity)  
**Loop Pattern:** [orchestration-loop-pattern.md](./orchestration-loop-pattern.md)  
**Routing:** [routing-registry.md](../routing-registry.md)  
**State Management:** GitHub issues (labels for stage, comments for decisions)

---

## Configuration

**GitHub Query Label:** `pm-idea`  
**Loop Interval:** 30 seconds  
**Specialist Agents:** 
- `product-manager` (from templates-v2/agents/) - Phase 1 & Phase 2 gate
- `research-agent` (autonomous) - Market research

---

## Environment Variables

Before running, set:

```bash
export GITHUB_TOKEN=${GITHUB_TOKEN:-}  # Optional (uses Copilot auth if empty)
export GITHUB_ORG=YOUR-ORG
export GITHUB_REPO=YOUR-REPO
export AIOS_PROJECT=aios                # Project identifier (single project)
export LOOP_INTERVAL=30
export STUCK_THRESHOLD=2               # Hours to consider issue stuck
```

---

## Orchestrator Loop

### Overview

```
1. Query GitHub: label:pm-idea state:open
2. For each issue:
   - Read current stage from issue label
   - Check if already processing (via recent comment)
   - Spawn specialist agent
   - Collect decision
   - Update issue: change label to next stage, post decision comment
   - Look up next stage from routing-registry.md
3. Sleep 30s
4. Repeat
```

### Implementation

Follow [orchestration-loop-pattern.md](./orchestration-loop-pattern.md):

```
Step 1: Query GitHub for issues with pm-idea label
Step 2a: Read current stage from issue label (e.g., pm-validating, pm-provisional-champion)
Step 2b: Check if issue already processing (last comment timestamp)
Step 2c: Spawn appropriate agent based on stage
Step 2d: Collect agent decision (PASS, BLOCK, REVISE)
Step 2e: Update GitHub: remove old stage label, add new stage label
Step 2f: Post "[DECISION]" comment with reasoning and next stage
Step 2g: Look up next stage from routing-registry.md
```

---

## Stage-Specific Behavior

### Stage: pm-idea → pm-validating

**Agent:** product-manager (Phase 1 quick gate)

**Input to Agent:**
```json
{
  "issue_id": 123,
  "title": "AI-powered customer support",
  "body": "Description of opportunity...",
  "stage": "pm-validating"
}
```

**Expected Outcomes:**
- PASS → Advance to pm-provisional-champion (spawn research agent)
- BLOCK → pm-blocked (issue closed, label added)

**Action:**
```bash
# After agent decides PASS:
gh issue edit 123 --remove-label "pm-idea" --add-label "pm-provisional-champion"

gh issue comment 123 --body "[DECISION] PM: PASS

Reasoning: $(echo '$AGENT_REASONING')

Agent: product-manager  
Duration: ${DURATION_MS}ms

Next Stage: pm-provisional-champion (Research In Progress)"

# Schedule research agent to run asynchronously (or let it run in next cycle)
```

---

### Stage: pm-provisional-champion (Research In Progress)

**Agent:** research-agent (autonomous market research)

**Note:** This stage has unique handling - research agent runs autonomously.

**Typical Flow:**
1. Issue enters pm-provisional-champion
2. Research agent spawns and runs (10-60 min)
3. Research agent updates issue with findings
4. Product-manager agent reviews research results
5. If priority-high + confidence-high: → pm-finalizing
6. If priority-low or confidence-low: → pm-deferred

**Considerations:**
- Research agent may take time (poll periodically)
- Orchestrator may move to next pm-idea while research runs
- Return to this issue when research complete

---

### Stage: pm-finalizing

**Agent:** product-manager (Phase 2 full validation)

**Input to Agent:**
```json
{
  "issue_id": 123,
  "title": "AI-powered customer support",
  "research_summary": "Market validation: high demand, 3 competitors",
  "stage": "pm-finalizing",
  "state": {
    "stage_history": [...],
    "latest_decision": { "research": "complete" }
  }
}
```

**Expected Outcomes:**
- PASS → pm-opportunity (close pm-idea, create strategic-opportunity)
- REVISE → pm-provisional-champion (more research needed)
- ESCALATE → pm-escalated (needs leadership decision)

**Action on PASS:**
```bash
# Update issue label and post decision
gh issue edit 123 --remove-label "pm-provisional-champion" --add-label "pm-opportunity"

gh issue comment 123 --body "[DECISION] PM: PASS (Phase 2 Complete)

Reasoning: Charter complete, team alignment strong

Agent: product-manager  
Duration: ${DURATION_MS}ms

Next Stage: pm-opportunity (Ready for PO)"

# Create strategic-opportunity issue for PO loop
gh issue create --title "Strategic Opportunity: ${ORIGINAL_TITLE}" \
  --body "Link to pm-idea: #123\n\nPM has validated and championed this opportunity." \
  --label strategic-opportunity

# Close original pm-idea issue
gh issue close 123 --reason completed
```

---

## Error Handling

### Issue Stuck in pm-provisional-champion

```bash
# If research is taking >2 hours
STAGE_ENTRY=$(gh issue view 123 --json comments --jq '.comments[] | select(.body | contains("pm-provisional-champion")) | .createdAt' | head -1)

if [ $(date +%s) - $(date -d "$STAGE_ENTRY" +%s) -gt 7200 ]; then
  gh issue comment 123 --body "⚠️ Research in progress for 2+ hours. Check for blockers."
  # Optionally escalate to team via another comment
fi
```

### Agent Timeout

```bash
# If agent doesn't respond within timeout
if [ $AGENT_DURATION_MS -gt 300000 ]; then  # 5 minutes
  gh issue comment 123 --body "⚠️ Agent timeout for issue #123. Escalating."
  gh issue edit 123 --add-label "pm-escalated"
  # Escalate or retry
fi
```

### GitHub API Failure

```bash
# If label update fails
if ! gh issue edit 123 --add-label "pm-opportunity" 2>/dev/null; then
  echo "❌ GitHub API error updating issue labels"
  # Retry, log error, alert team
fi
```

---

## Running the Orchestrator

```bash
# Set environment variables first
source ~/.aios-env.sh

# Run in continuous loop (30-second intervals)
copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --autopilot

# Or run once for debugging
copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md
```

**GitHub-Only Monitoring:**

No separate tools needed. All state visible on GitHub:

```bash
# List all pm-idea issues in pm-validating stage
gh issue list --label pm-idea,pm-validating --state open

# View specific issue with all decisions
gh issue view 123 --json title,labels,comments --jq '.labels[].name, .comments[].body'

# Check history of decisions for one issue
gh issue view 123 --json comments --jq '.comments[] | select(.body | contains("[DECISION]")) | .body'
```

---

## Monitoring & Debugging

### View Current States

```bash
# List all issues in pm-provisional-champion
gh issue list --label pm-provisional-champion --state open

# View specific issue state (current stage from labels)
gh issue view 123 --json labels --jq '.labels[] | select(.name | startswith("pm-")) | .name'
```

### Check Decision History

```bash
# See all decisions for specific issue
gh issue view 123 --json comments --jq '.comments[] | select(.body | contains("[DECISION]")) | .createdAt, .body'

# Count decisions by stage
gh issue list --label pm-idea --state open --json number,labels \
  | jq -r '.[] | .labels[].name' | sort | uniq -c
```

### Debug Agent Output

```bash
# Enable verbose logging in orchestrator
export DEBUG=1
copilot-cli pm-orchestrator-v2.agent.md --autopilot

# Watch for issue label changes
watch -n 5 'gh issue list --label pm-idea --state open --json number,labels'
```

---

## Performance Targets

**Per Cycle:**
- Query GitHub: 1-2s
- Load state: <100ms per issue
- Spawn agent: 5-30s (depends on agent)
- Update state: 2-3s
- Post comment: 1s
- **Total per issue: ~10-40s**

**Throughput:**
- 30s loop interval
- ~1-3 issues processed per cycle
- Can handle ~20 pm-idea issues/hour

---

## Next Steps

1. [ ] Set environment variables (GITHUB_TOKEN, GITHUB_ORG, GITHUB_REPO, AIOS_PROJECT)
2. [ ] Test with sample pm-idea issue
3. [ ] Verify GitHub labels updated
4. [ ] Verify decision comments posted
5. [ ] Monitor for 1-2 hours
6. [ ] Check integration with PO orchestrator

---

## Related Files

- **Pattern Documentation:** [orchestration-loop-pattern.md](./orchestration-loop-pattern.md)
- **Routing Rules:** [routing-registry.md](../routing-registry.md)
- **PO Orchestrator:** [po-orchestrator-v2.agent.md](./po-orchestrator-v2.agent.md)
- **Dev Orchestrator:** [dev-orchestrator-v2.agent.md](./dev-orchestrator-v2.agent.md)
- **Legacy v1:** [templates/agents/pm-orchestrator.agent.md](../../templates/agents/pm-orchestrator.agent.md)
