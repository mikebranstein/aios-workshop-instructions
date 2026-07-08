---
description: "PO Orchestrator v2: Prioritizes strategic opportunities and creates feature requests using GitHub issues as state"
tools: ["*"]
---

# PO Orchestrator v2

**Purpose:** Prioritize opportunities and sequence feature-request creation (strategic-opportunity → feature-request)  
**Loop Pattern:** [orchestration-loop-pattern.md](./orchestration-loop-pattern.md)  
**Routing:** [routing-registry.md](../routing-registry.md)  
**State Management:** GitHub issues (labels for stage, comments for decisions)

---

## Configuration

**GitHub Query Label:** `strategic-opportunity`  
**Loop Interval:** 30 seconds  
**Specialist Agents:** 
- `product-owner` (from templates/agents/) - Prioritization gate

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

Follow [orchestration-loop-pattern.md](./orchestration-loop-pattern.md):

```
Step 1: Query GitHub for issues with strategic-opportunity label
Step 2a: Read current stage from issue label (po-prioritizing, po-backlog, etc.)
Step 2b: Check if issue already processing (last comment timestamp)
Step 2c: Spawn product-owner agent based on stage
Step 2d: Collect agent decision (PRIORITIZE, DEFER, READY, etc.)
Step 2e: Update GitHub: remove old stage label, add new stage label
Step 2f: Post "[DECISION]" comment with reasoning and next stage
Step 2g: Look up next stage from routing-registry.md
```

---

## Stage-Specific Behavior

### Stage: strategic-opportunity → po-prioritizing

**Agent:** product-owner (prioritization gate)

**Input to Agent:**
```json
{
  "issue_id": 456,
  "title": "Strategic Opportunity: AI Customer Support",
  "body": "PM research summary...",
  "research_link": "link to pm-idea #123",
  "stage": "po-prioritizing"
}
```

**Expected Outcomes:**
- PRIORITIZE → po-backlog (add to prioritized backlog)
- DEFER → po-deferred (deferred, may reopen later)
- REJECT → po-rejected (not proceeding)

**Action on PRIORITIZE:**
```bash
# Update issue label and post decision
gh issue edit 456 --remove-label "strategic-opportunity" --add-label "po-backlog"

gh issue comment 456 --body "[DECISION] PO: PRIORITIZE

Reasoning: Added to Q3 roadmap, high strategic value
Priority Score: 8.5

Agent: product-owner
Duration: ${DURATION_MS}ms

Next Stage: po-backlog"
```

---

### Stage: po-backlog → po-ready-to-staff

**Agent:** product-owner (capacity + sequencing check)

**Input to Agent:**
```json
{
  "issue_id": 456,
  "title": "Strategic Opportunity: AI Customer Support",
  "priority_score": 8.5,
  "estimated_complexity": "medium",
  "stage": "po-backlog",
  "team_capacity": 80,  # Estimated % capacity available
  "dependent_issues": []
}
```

**Expected Outcomes:**
- READY → create-feature-requests (capacity available, create dev tasks)
- BLOCKED → po-blocked (dependency or capacity issue)

**Action on READY:**
```bash
# Transition to ready state
gh issue edit 456 --remove-label "po-backlog" --add-label "po-ready-to-staff"

gh issue comment 456 --body "[DECISION] PO: READY

Reasoning: Team capacity available, dependencies resolved

Agent: product-owner
Duration: ${DURATION_MS}ms

Next Stage: po-ready-to-staff"

# Create feature-request issues for each workstream
gh issue create --title "Feature Request: API Backend for Strategic Opportunity #456" \
  --body "Parent Issue: #456\n\nWorkstream: API Backend" \
  --label feature-request,api-backend

gh issue create --title "Feature Request: UI Frontend for Strategic Opportunity #456" \
  --body "Parent Issue: #456\n\nWorkstream: UI Frontend" \
  --label feature-request,ui-frontend

gh issue create --title "Feature Request: Data Integration for Strategic Opportunity #456" \
  --body "Parent Issue: #456\n\nWorkstream: Data Integration" \
  --label feature-request,data-platform

# Close strategic-opportunity issue
gh issue close 456 --reason completed

# Post completion summary
gh issue comment 456 --body "[COMPLETE] Created 3 feature-request issues ready for dev team. See linked issues above."
```

---

### Stage: po-blocked → po-backlog

**Agent:** product-owner (dependency + capacity review)

**Input to Agent:**
```json
{
  "issue_id": 456,
  "title": "Strategic Opportunity: AI Customer Support",
  "blocked_reason": "Blocked on API team capacity",
  "stage": "po-blocked"
}
```

**Expected Outcomes:**
- RESOLVED → po-backlog (unblocked, return to prioritization)
- REJECT → po-rejected (cancel, not proceeding)

**Action on RESOLVED:**
```bash
# Unblock and return to backlog
gh issue edit 456 --remove-label "po-blocked" --add-label "po-backlog"

gh issue comment 456 --body "[DECISION] PO: RESOLVED

Reasoning: API team capacity now available

Agent: product-owner
Duration: ${DURATION_MS}ms

Next Stage: po-backlog (return for re-prioritization)"
```

---

## Integration with Dev Loop

**Handoff:** PO creates feature-request issues → Dev Orchestrator picks up

**GitHub Labels Flow:**
```
strategic-opportunity
  → po-prioritizing
  → po-backlog
  → po-ready-to-staff
  → [create feature-requests]
  
feature-request (created by PO)
  → [Dev Orchestrator picks up]
  → intake
  → design
  → ... (dev pipeline)
```

**State Tracking:** All visible on GitHub via labels and comments
- Strategic opportunity issue shows: po-prioritizing, po-backlog, po-ready-to-staff labels
- Feature-request issues linked in comments
- Each feature-request shows: intake, design-approved, build-approved, ... labels

---

## Running the Orchestrator

```bash
# Set environment variables first
source ~/.aios-env.sh

# Run in continuous loop (30-second intervals)
copilot-cli templates-v2/orchestration/.prompts/po-orchestrator-v2.agent.md --autopilot
```

**GitHub-Only Monitoring:**

```bash
# List all strategic-opportunity issues in po-backlog
gh issue list --label "strategic-opportunity,po-backlog" --state open

# View specific strategic opportunity with all decisions
gh issue view 456 --json title,labels,comments --jq '.labels[].name, .comments[].body'

# Check decision history
gh issue view 456 --json comments --jq '.comments[] | select(.body | contains("[DECISION]")) | .body'
```

### Check Backlog Health

```bash
# How many waiting to be staffed?
gh issue list --label "po-backlog" --state open --json number | jq length

# What's the oldest in backlog?
gh issue list --label "po-backlog" --state open --json number,updatedAt | \
  jq -r '.[] | "\(.number): \(.updatedAt)"' | sort | head -1
```

### Monitor Feature Request Creation

```bash
# Find all feature-requests linked to strategic opportunity issue 456
gh issue view 456 --json body --jq '.body' | grep -o '#[0-9]\+' | sort -u

# Check if feature-requests transitioned to dev loop
gh issue list --label "feature-request,intake" --state open --json number
```

---

## Error Handling

### Blocked on Dependency

```bash
# If issue stuck in po-blocked for >4 hours
STUCK=$(gh issue list --label "po-blocked" --state open --json updatedAt | \
  jq ".[] | select(.updatedAt < \"$(date -u -d '4 hours ago' +%Y-%m-%dT%H:%M:%SZ)\")" | wc -l)

if [ $STUCK -gt 0 ]; then
  echo "⚠️ $STUCK issues blocked for >4 hours. Escalate dependencies?"
fi
```

### Feature Request Creation Fails

```python
try:
    feature_requests = create_feature_requests(parent_issue, workstreams)
except Exception as e:
    print(f"❌ Failed to create feature-requests: {e}")
    # Escalate: state remains in po-ready-to-staff
    # Retry next cycle
```

### State Transition Fails

```python
try:
    manager.transition_state(issue_id, new_stage, decision)
except Exception as e:
    print(f"❌ State update failed: {e}")
    # Log, alert, retry
```

---

## Integration with v1 Orchestrators

**During Transition Period:**

This v2 orchestrator can run in parallel with legacy v1 PO orchestrator:

```bash
# Terminal 1: Legacy v1 PO orchestrator
python ~/AIOS/templates/agents/po-orchestrator.py

# Terminal 2: New v2 PO orchestrator (this file)
copilot-cli templates-v2/orchestration/.prompts/po-orchestrator-v2.agent.md --autopilot
```

Both orchestrators process same strategic-opportunity issues:
- v1: Updates GitHub labels as before
- v2: Updates Obsidian vault + posts [STATE UPDATE] comments

**Verification:**
- Both create feature-request issues (v2 might create fewer if already created by v1)
- State files appear in vault
- Dev orchestrator processes feature-requests from both v1 and v2

**Cutover:**
Once v2 stable, stop v1 and run v2 alone.

---

## Performance Targets

**Per Cycle:**
- Query GitHub: 1-2s
- Load state: <100ms per issue
- Spawn agent: 5-30s (depends on agent)
- Create feature-requests: 5-10s (API calls)
- Update state: 2-3s
- Post comment: 1s
- **Total per issue: ~15-50s**

**Throughput:**
- 30s loop interval
- ~1-2 opportunities processed per cycle
- Can handle ~5-10 strategic-opportunity issues/hour

---

## Next Steps

1. [ ] Set environment variables (GITHUB_TOKEN, GITHUB_ORG, GITHUB_REPO, AIOS_PROJECT)
2. [ ] Test with sample strategic-opportunity issue
3. [ ] Verify GitHub labels updated
4. [ ] Verify feature-requests created with correct labels
5. [ ] Verify decision comments posted
6. [ ] Monitor dev orchestrator picking up feature-requests

---

## Related Files

- **Pattern Documentation:** [orchestration-loop-pattern.md](./orchestration-loop-pattern.md)
- **Routing Rules:** [routing-registry.md](../routing-registry.md)
- **PM Orchestrator:** [pm-orchestrator-v2.agent.md](./pm-orchestrator-v2.agent.md)
- **Dev Orchestrator:** [dev-orchestrator-v2.agent.md](./dev-orchestrator-v2.agent.md)
