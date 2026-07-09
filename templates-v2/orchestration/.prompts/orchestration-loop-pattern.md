# Orchestration Loop Pattern

**Purpose:** Reusable loop pattern that all orchestrators (Foundation, Discovery, PM, PO, Dev, Architecture Review) follow  
**Status:** Template for all orchestrators  
**File Location:** Referenced by orchestrators, not executed directly  

---

## Overview

There are two orchestration loop patterns:

1. Continuous loop (PM, PO, Dev): always-on polling with 30s sleep.
2. Bounded run (Foundation, Discovery, Architecture Review): single run with explicit caps and timeout.

Continuous-loop orchestrators follow this fundamental loop:

```
1. Query GitHub for unprocessed issues (with specific label)
2. For each issue:
   a. Read current stage from GitHub issue label
   b. Check if already processing (to avoid re-entrance)
   c. Spawn specialist agent (from .github/agents/)
   d. Collect decision from agent
   e. Update GitHub issue: change label to next stage, post decision comment
   f. Look up next stage from routing-registry.md
3. Sleep 30 seconds
4. Loop (repeat)
```

This pattern ensures:
- ✅ Consistent state management across all orchestrators
- ✅ Single source of truth: GitHub issues (labels + comments)
- ✅ Reusable structure (easy to add new orchestrator)
- ✅ Decoupled from specific business logic
- ✅ Clear error handling and recovery

Bounded-run orchestrators (like Discovery) use the same decision/update principles but stop when limits are reached (batch cap, creation cap, timeout).

---

## Step 0: Repository Metadata Bootstrap (Required)

Before querying issues, ensure required labels and issue templates exist.

### Labels

Use `gh label create` only when a label is missing:

```bash
EXISTING_LABELS=$(gh label list --limit 500 --json name --jq '.[].name')

ensure_label() {
  local label_name="$1"
  local color="$2"
  local description="$3"
  if ! echo "$EXISTING_LABELS" | grep -Fxq "$label_name"; then
    gh label create "$label_name" --color "$color" --description "$description"
    echo "Created missing label: $label_name"
  fi
}
```

### Issue Templates

If an issue template file is missing, create it in `.github/ISSUE_TEMPLATE/` before first issue creation.

```bash
mkdir -p .github/ISSUE_TEMPLATE

if [ ! -f .github/ISSUE_TEMPLATE/feature_request.md ]; then
  cat > .github/ISSUE_TEMPLATE/feature_request.md <<'EOF'
---
name: Feature request
about: Suggest an idea for this project
title: "[feature-request]: "
labels: ''
assignees: ''
---

## Problem Statement

## Scope

## Non-Goals

## Acceptance Criteria
- [ ] AC1:
- [ ] AC2:
- [ ] AC3:

## Test Scenarios
- Scenario 1:
- Scenario 2:

## Risk Level
Low / Medium / High

## Dependencies

## Notes
EOF
  echo "Created missing issue template: feature_request.md"
fi

if [ ! -f .github/ISSUE_TEMPLATE/architecture_review.md ]; then
  cat > .github/ISSUE_TEMPLATE/architecture_review.md <<'EOF'
---
name: Architecture review
about: Trigger architecture review cycle
title: "[architecture-review]: "
labels: 'arch-review-pending'
assignees: ''
---

## Review Trigger

## Scope Window

## Objectives
EOF
  echo "Created missing issue template: architecture_review.md"
fi
```

Persist missing-template fixes using normal repo workflow:
- Commit directly if branch policy allows.
- If branch protection blocks direct push, open a PR with the template files.

### Special Requirements

- Label creation requires GitHub issues write permission.
- Template creation requires repository contents write permission (commit/PR access).
- If permissions are missing, post a bootstrap comment on the relevant issue with exact missing assets and continue with inline issue bodies.

---

## Step-by-Step Pattern

### Step 1: Query GitHub

```bash
# Query for issues with specific orchestrator label:
gh issue list --label pm-idea --state open --json number,title,labels

# PM Orchestrator: issues with `pm-idea` label
# PO Orchestrator: issues with `strategic-opportunity` label
# Dev Orchestrator: issues with `feature-request` label
# Foundation Orchestrator (bounded): foundation-needed/foundation-in-progress
# Discovery Orchestrator (bounded): scans signals, creates `pm-idea` + `pm-idea-auto`
# Architecture Review Orchestrator (bounded): arch-review-pending and architecture-debt

# Filter out issues already being processed:
# - Skip if issue has label indicating current stage (e.g., `pm-validating`)
# - Skip if last comment from orchestrator is <5 minutes old (processing)
```

### Step 2a: Read Current Stage from GitHub

```bash
# Get current stage from issue labels
gh issue view 123 --json labels --jq '.labels[].name'

# Result example: pm-validating, design-approved, qa-in-progress, etc.
# All stage labels follow pattern: {orchestrator}-{stage-name}
```

Returns current stage name from label. If no stage label exists, issue is new → assign initial stage:
```bash
# For new issue, determine initial stage based on trigger label:
# - Has `pm-idea` label → initial stage: pm-validating
# - Has `strategic-opportunity` label → initial stage: po-prioritizing  
# - Has `feature-request` label → initial stage: intake
```

### Step 2b: Check If Already Processing

```bash
# Get last comment to see if orchestrator is currently processing
gh issue view 123 --json comments --jq '.comments[-1]'

# If last comment from orchestrator (contains "[DECISION]") timestamp <5 min ago:
#   → Skip this issue (still processing)
# Else:
#   → Proceed to spawn agent
```

### Step 2c: Determine Current Stage

```bash
# Read stage label for current issue
STAGE=$(gh issue view 123 --json labels --jq '.labels[] | select(.name | startswith("pm-")) | .name' | sed 's/.*-//')

# If no stage label found:
if [ -z "$STAGE" ]; then
    # First time seeing this issue, assign initial stage label
    STAGE="{initial_stage}"  # e.g., pm-validating, intake, po-prioritizing
    gh issue edit 123 --add-label "${ORCHESTRATOR_PREFIX}-${STAGE}"
fi
```

### Step 2d: Spawn Specialist Agent

**Agent routing is determined by stage.**

The agent to run depends on the current stage and orchestrator:
- **PM Orchestrator**: pm-validating → product-manager, pm-provisional-champion → research-agent, pm-finalizing → product-manager
- **PO Orchestrator**: strategic-opportunity → product-owner
- **Dev Orchestrator**: feature-request → intake-agent, intake-approved → design-agent, design-approved → build-agent, build-complete → qa-agent, qa-passed → policy-agent

**Call agent with issue data:**
```bash
# Pass issue data to agent
AGENT_RESULT=$(copilot-cli .github/agents/${AGENT_NAME}.agent.md --input '{
  "issue_id": 123,
  "title": "Issue Title",
  "stage": "'$STAGE'",
  "body": "Full issue body",
  "labels": ["label1", "label2"]
}')

# Agent returns JSON: {"decision": "PASS", "reasoning": "...", ...}
```

### Step 2e: Collect Decision

```bash
# Extract decision and reasoning from agent output
DECISION=$(echo "$AGENT_RESULT" | jq -r '.decision')
REASONING=$(echo "$AGENT_RESULT" | jq -r '.reasoning')

# Validate decision is recognized (PASS, REVISE, BLOCKED, ESCALATE)
if [[ ! "$DECISION" =~ ^(PASS|REVISE|BLOCKED|ESCALATE)$ ]]; then
  echo "ERROR: Unknown decision: $DECISION"
  exit 1
fi

echo "Decision: $DECISION - $REASONING"
```

### Step 2f: Update GitHub Issue

```bash
# Look up next stage from routing-registry.md
NEXT_STAGE=$(grep -A1 "^$CURRENT_STAGE$" .github/orchestration/routing-registry.md | grep "$DECISION" | awk '{print $2}')

# Remove old stage label and add new one
OLD_LABEL="${ORCHESTRATOR_PREFIX}-${CURRENT_STAGE}"
NEW_LABEL="${ORCHESTRATOR_PREFIX}-${NEXT_STAGE}"

gh issue edit 123 --remove-label "$OLD_LABEL" --add-label "$NEW_LABEL"

# Post decision comment to GitHub
gh issue comment 123 --body "[DECISION] $ORCHESTRATOR: $DECISION

Reasoning: $REASONING

Next Stage: $NEXT_STAGE"
```

---

## Routing Registry

Orchestrators consult [routing-registry.md](../orchestration/routing-registry.md) to determine next stage based on current stage + decision.

Example:
```
pm-validating + PROVISIONAL_CHAMPION → pm-provisional-champion
design-approved + PASS → build-approved  
qa-testing + INCOMPLETE → design-approved (feedback loop)
```

---

## Error Handling

### Issue Stuck in Stage

```bash
# Monitor for issues stuck >2 hours
for stage in pm-validating intake design-approved; do
  STUCK_ISSUES=$(gh issue list --label "$stage" --state open --json updatedAt | \
    jq ".[] | select(.updatedAt < \"$(date -u -d '2 hours ago' +%Y-%m-%dT%H:%M:%SZ)\")" | wc -l)
  
  if [ $STUCK_ISSUES -gt 0 ]; then
    echo "⚠️ $STUCK_ISSUES issues stuck in $stage for >2 hours"
  fi
done
```

### Agent Fails to Respond

```bash
# If agent doesn't respond within timeout
if [ $DURATION_MS -gt 300000 ]; then
  echo "❌ Agent timeout for issue. Escalating..."
  gh issue edit 123 --add-label "escalated"
fi
```

### GitHub API Failure

```bash
# If label update fails
if ! gh issue edit 123 --add-label "$NEW_LABEL" 2>/dev/null; then
  echo "❌ GitHub API error updating issue labels"
  exit 1
fi
```

---

## Loop Summary

**Each cycle (30 second interval):**

1. Query GitHub for issues with orchestrator label (pm-idea, strategic-opportunity, feature-request)
2. For each issue:
   - Read current stage from issue label
   - Check if already processing
   - Spawn appropriate agent
   - Collect decision
   - Update issue: remove old label, add new label
   - Post decision comment
3. Sleep 30 seconds
4. Repeat

**Bounded run summary (Discovery):**

1. Query signal sources for candidate hypotheses
2. Spawn Idea Scout with bounded controls
3. Create up to creation cap `pm-idea` issues
4. Output run summary
5. Stop

**Bounded run summary (Foundation and Architecture Review):**

1. Query required labels/issues for that loop
2. Spawn specialized agents for that loop
3. Apply contract-mapped transitions
4. Emit run summary
5. Stop

---

## State Taxonomy (Explicit)

### Foundation States

- `foundation-needed`
- `foundation-in-progress`
- `foundation-review`
- `foundation-approved`
- `foundation-blocked`

### Architecture Review States

- `arch-review-pending`
- `arch-review-in-progress`
- `arch-review-no-action`
- `arch-refactor-planned`
- `arch-refactor-requests-created`
- `arch-review-escalated`

### Architecture Debt States

- `architecture-debt`
- `debt-triaged`
- `debt-scheduled`
- `debt-resolved`
- `debt-deferred`

### Fitness Outcome States

- `fitness-pass`
- `fitness-warn`
- `fitness-fail-critical`

**All state visible on GitHub:** Labels show stage, comments show decisions
- 100 issues: ~3-5 cycles to process all
- 1000 issues: ~30-50 cycles (still reasonable)
- >1000 issues: Consider batch processing or parallel orchestrators

---

## Next Steps

1. Copy this pattern documentation
2. Create orchestrator file using pattern
3. Specialize for PM/PO/Dev (change query label, agent registry)
4. Test with sample issues
5. Deploy alongside legacy orchestrators (v1)
6. Monitor for stability
7. Gradually migrate issues from v1 to v2
