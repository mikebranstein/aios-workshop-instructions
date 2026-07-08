# Step-by-Step Guide: Templates-v2 Implementation

**Purpose:** Complete walk-through of setting up and deploying the new orchestration system  
**Timeline:** 1-2 weeks (2 phases)  
**Prerequisites:** GitHub account, Copilot CLI

---

## Overview: What You're Setting Up

The new v2 system modernizes your three-loop orchestration (PM, PO, Dev) with:
- **GitHub issues as state** (no external vault)
- **Three orchestrator agents** that follow a reusable pattern
- **Centralized routing** (no duplicated logic)
- **Full audit trail** (GitHub comments + issue history)

**Non-breaking approach:** v1 and v2 run in parallel. No existing code touched.

---

## Phase 1: Foundation Setup (1-2 hours)

### Step 1: Prerequisites Check

**What you need:**
- [ ] GitHub account (able to create repositories and issues)
- [ ] Copilot CLI installed (`copilot-cli --version`)
- [ ] A GitHub repository for your project

**Verify setup:**
```bash
copilot-cli --version
# Should show version number
```

---

### Step 2: Create GitHub API Token (Optional)

**Note:** If you're running orchestrators as Copilot agents (which you are), they use Copilot's built-in GitHub authentication. A token is only needed if:
- You prefer explicit credentials over relying on Copilot's context
- Git operations need explicit authentication (alternative: use SSH keys)

**If you want to use a token:**

**On GitHub:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token"
3. Name: `AIOS Orchestrator v2`
4. Select scopes:
   - ✅ `repo` (all, for full repository access)
   - ✅ `issues:write` (for posting comments)
5. Generate and copy token
6. **Save securely** (you won't see it again)

**Save as environment variable:**
```bash
export GITHUB_TOKEN=ghp_xxxxx  # Paste your token
```

---

### Step 3: Set Up Environment

**Create your environment file:**
```bash
cat > ~/.aios-env.sh << 'EOF'
#!/bin/bash

# AIOS Orchestrator v2 Environment Setup
export GITHUB_TOKEN=${GITHUB_TOKEN:-}    # Optional (uses Copilot auth if empty)
export GITHUB_ORG=YOUR-ORG
export GITHUB_REPO=your-repo
export AIOS_PROJECT=aios
export LOOP_INTERVAL=30
export STUCK_THRESHOLD=2

echo "✅ AIOS v2 environment loaded"
echo "  Project: $AIOS_PROJECT"
echo "  GitHub Repo: $GITHUB_REPO"
EOF

chmod +x ~/.aios-env.sh
```

**Load and verify:**
```bash
source ~/.aios-env.sh

# Verify
echo $AIOS_PROJECT    # Should show: aios
echo $GITHUB_REPO     # Should show: your-repo
```

---

### Step 4: Understand the Pattern

**Read the core pattern:**
```bash
cat ~/AIOS/aios-workshop-instructions/templates-v2/orchestration/.prompts/orchestration-loop-pattern.md
```

This explains the 5-step loop all orchestrators follow:
1. Query GitHub issues
2. Analyze with specialist agent
3. Collect decision
4. Update GitHub issue with new stage + decision comment
5. Loop

**Understand routing:**
```bash
cat ~/AIOS/aios-workshop-instructions/templates-v2/orchestration/routing-registry.md
```

This shows all valid stage transitions for each loop.

---

### Step 5: Create Test PM-Idea Issue

**On GitHub:**
1. Go to your repository
2. Create new issue: "Test Opportunity: AI Analytics"
3. Add label: `pm-idea`
4. Body:
```markdown
## Opportunity Description
AI-powered analytics dashboard for market research.

## Target Market
Enterprise SaaS companies ($50B TAM)

## Success Metrics
- 50% adoption among power users in 90 days
```

**Note the issue number** (e.g., #999)

---

## Phase 2: Deploy Orchestrators (2-4 hours)

### Step 6: Deploy PM Orchestrator v2

**In a new terminal:**
```bash
# Load environment
source ~/.aios-env.sh

# Navigate to repo
cd ~/AIOS/aios-workshop-instructions

# Start PM orchestrator (runs continuously, check GitHub for comments)
copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --autopilot
```

**Watch for:**
- GitHub issue label changes (e.g., `pm-idea` → `pm-validating`)
- Comments posted on issue with stage transition info
- Each cycle takes ~30 seconds

---

### Step 7: Create Feature Request Issue

**On GitHub:**
1. Create new issue: "Feature: Analytics Dashboard"
2. Add label: `feature-request`
3. Body:
```markdown
## Description
Real-time analytics dashboard for market data.

## Acceptance Criteria
- [ ] Display revenue trends by region
- [ ] Real-time filtering
- [ ] Export to CSV
```

**Expected flow (manual):**
- PM orchestrator processes `pm-idea` issues
- Creates `strategic-opportunity` issues
- PO orchestrator processes those and creates `feature-request` issues
- Dev orchestrator picks up `feature-request` and moves to `intake`

---

### Step 8: Deploy PO Orchestrator (Optional)

**In another terminal:**
```bash
source ~/.aios-env.sh
copilot-cli templates-v2/orchestration/.prompts/po-orchestrator-v2.agent.md --autopilot
```

---

### Step 9: Deploy Dev Orchestrator (Optional)

**In another terminal:**
```bash
source ~/.aios-env.sh
copilot-cli templates-v2/orchestration/.prompts/dev-orchestrator-v2.agent.md --autopilot
```

---

### Step 10: Monitor System

**Watch issue labels and comments:**
```bash
# View issue in browser
open https://github.com/YOUR-ORG/YOUR-REPO/issues/999

# Or use GitHub CLI:
gh issue view 999 --comments
```

**Expected state transitions:**
- Issue starts with `pm-idea`
- Orchestrator adds comment with decision
- Label changes to `pm-provisional-champion` (or rejected)
- Moves through stages based on decisions

---

## All Issues Run the Same Pipeline

All issues flow through:
```
intake → design → build → qa → verification → policy → released
```

Orchestrators handle:
- **PM**: `pm-idea` → `strategic-opportunity` evaluation
- **PO**: `strategic-opportunity` → `feature-request` prioritization  
- **Dev**: `feature-request` → Full pipeline (`intake` through `released`)

Each orchestrator queries issues with relevant labels, analyzes them, and updates GitHub with decisions.

---

## Troubleshooting

### Orchestrator not finding issues?
- Check issue has correct label (`pm-idea`, `strategic-opportunity`, `feature-request`)
- Verify `GITHUB_ORG` and `GITHUB_REPO` are set correctly:
  ```bash
  echo $GITHUB_ORG
  echo $GITHUB_REPO
  ```

### Comments not appearing on GitHub?
- Check orchestrator terminal for errors
- Verify token has `issues:write` scope
- Copilot context may be needed instead:
  ```bash
  unset GITHUB_TOKEN  # Fall back to Copilot auth
  ```

### How do I know what stage an issue is in?
- Check issue labels on GitHub
- Read latest comment (posted by orchestrator)
- Current stage is always in the label

---

## Next Steps

1. Let orchestrators run for a few cycles (5-10 minutes)
2. Observe issue label transitions on GitHub
3. Read orchestrator comments for decision rationale
4. Create more test issues and watch them flow through
5. When ready, integrate with your actual project issues

**Manual test of feedback loop:**
```bash
# Check issue state on GitHub
gh issue view 999 --json labels,comments

# Should show:
# - Label changed back to intake (if design returned REVISE)
# - Recent comment with [DECISION] explaining feedback
```

---

### Step 21: Validation Checklist

**GitHub State:**
- [ ] Labels applied correctly for all issues
- [ ] Stage transitions tracked correctly via label changes
- [ ] Decision comments posted to all processed issues
- [ ] All comments have clear reasoning

**GitHub Comments:**
- [ ] [DECISION] comments posted for all stage transitions
- [ ] Comments include agent outcome (PASS, REVISE, BLOCKED, etc.)
- [ ] Comments include reasoning

**Orchestrators:**
- [ ] PM orchestrator processing pm-idea issues
- [ ] PO orchestrator processing strategic-opportunity issues
- [ ] Dev orchestrator processing feature-request issues
- [ ] No errors in logs
- [ ] Cycles running every 30 seconds

**Feedback Loops:**
- [ ] Design REVISE → Intake transition working
- [ ] QA INCOMPLETE → Design transition working
- [ ] Verification FAIL → Design transition working

---

### Step 22: Performance Baseline

**Measure cycle time:**
```bash
# Run for 10 cycles and measure
for i in {1..10}; do
    echo "Cycle $i:"
    time copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --max-cycles=1
done
```

**Expected:** ~30-40s per cycle per orchestrator

**Monitor throughput:**
```bash
# Count issues processed per hour (check recent label changes)
gh issue list --state all --limit 1000 --json updatedAt,labels | wc -l
```

## Phase 5: Optimization & Scale (Optional)

### Step 23: View Metrics & Performance

**Query GitHub for stage metrics:**
```bash
# Count issues in each stage
echo "=== Current Pipeline Status ==="
for stage in intake design-approved build-approved qa-testing verification policy-approval released; do
    count=$(gh issue list --label $stage --state open | wc -l)
    echo "$stage: $count issues"
done
```

**Export metrics to CSV for analysis:**
```bash
# Get all issues with labels and timestamps
gh issue list --state all --limit 1000 --json number,labels,updatedAt,createdAt,closedAt > issues.json

# Process with jq to get stage distribution
cat issues.json | jq -r '.[] | "\(.number),\(.labels[].name),\(.createdAt),\(.updatedAt)"' > metrics.csv
```

**Analyze decision distribution:**
```bash
# Count decision outcomes from comments
gh issue view --state all | gh issue view 999 --json comments --jq '.comments[] | select(.body | contains("[DECISION]")) | .body' | grep -oE "Agent: \w+" | sort | uniq -c
```

---

### Step 24: GitHub Issue Metrics Dashboard

**Create a summary doc in your repo:**
```bash
cat > docs/METRICS_DASHBOARD.md << 'EOF'
# AIOS v2 System Metrics

**Last Updated:** 2026-07-08  
**Data Period:** Last 7 days

## Pipeline Health

Run this command to get current status:
```bash
gh issue list --state all --json number,labels | jq 'group_by(.labels[].name) | .[] | {stage: .[0].labels[].name, count: length}'
```

Expected output shows count by stage:
| Stage | Count | Avg Age |
|-------|-------|---------|
| intake | 3 | 8h |
| design-approved | 2 | 12h |
| build-approved | 1 | 24h |
| qa-testing | 2 | 6h |
| verification | 1 | 3h |
| policy-approval | 0 | - |
| released | 12 | - |

## Throughput (Last 7 Days)

- **Issues Created:** (see `gh issue list --state closed --created`)
- **Issues Completed:** (see `gh issue list --state closed`)
- **Average Cycle Time:** Calculate from closedAt - createdAt

## Key Insights

- Monitor issues stuck >4h in any stage (see TROUBLESHOOTING.md)
- Track DECISION comments for agent behavior patterns
- Use labels to filter by priority and project

## Recommendations

- [ ] Review issues in build-approved (longest stage)
- [ ] Check for stuck/blocked issues
- [ ] Evaluate agent decision patterns
EOF

git add docs/METRICS_DASHBOARD.md
git commit -m "Add metrics dashboard documentation"
git push origin main
```

---

### Problem: GitHub Comments Not Posting

**Symptoms:**
```
[STATE UPDATE] not appearing on GitHub issues
```

**Solutions:**
1. Verify token scope:
   ```bash
   curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user/repos | grep REPO_NAME
   ```

2. Check comment format in orchestrator:
   ```bash
   grep "\[STATE UPDATE\]" templates-v2/orchestration/.prompts/*-orchestrator*.agent.md
   ```

3. Check issue number extraction:
   ```bash
   # Verify issue numbers being queried
   grep "label:pm-idea" orchestrator logs
   ```

---

---

### Problem: Orchestrator Stuck/Not Progressing

**Symptoms:**
```
Orchestrator running but no state changes for >2 hours
```

**Solutions:**
1. Check for stuck issues:
   ```bash
   # View issues that haven't changed in 2+ hours
   gh issue list --state open --json updatedAt,labels,number | jq '.[] | select(.updatedAt < (now - 7200)) | .number'
   ```

2. Check orchestrator output:
   ```bash
   # Look for error patterns in logs
   tail -50 pm-orchestrator.log | grep -i "error\|fail"
   ```

3. See TROUBLESHOOTING.md for more detailed diagnostics

---

### Problem: GitHub API Issues

**Symptoms:**
```
API errors: 401, 403, 429, etc.
```

**Solutions:**
1. Check authentication:
   ```bash
   gh auth status
   ```

2. See TROUBLESHOOTING.md Issue 5 for rate limiting solutions

3. Verify token has correct scopes:
   ```bash
   gh api user --jq '.login'  # Should work
   ```

---

## Quick Reference

### Start All Orchestrators (Development)

**Save this script:**
```bash
cat > ~/start-aios-v2.sh << 'EOF'
#!/bin/bash

source ~/.aios-env.sh

cd ~/AIOS/aios-workshop-instructions

# Start all three orchestrators
echo "Starting AIOS v2 orchestrators..."
echo ""

# PM Orchestrator
echo "1️⃣  Starting PM Orchestrator..."
copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --autopilot &
PM_PID=$!

sleep 5

# PO Orchestrator
echo "2️⃣  Starting PO Orchestrator..."
copilot-cli templates-v2/orchestration/.prompts/po-orchestrator-v2.agent.md --autopilot &
PO_PID=$!

sleep 5

# Dev Orchestrator
echo "3️⃣  Starting Dev Orchestrator..."
copilot-cli templates-v2/orchestration/.prompts/dev-orchestrator-v2.agent.md --autopilot &
DEV_PID=$!

echo ""
echo "✅ All orchestrators started!"
echo "   PM PID:  $PM_PID"
echo "   PO PID:  $PO_PID"
echo "   Dev PID: $DEV_PID"
echo ""
echo "Monitor with: ~/monitor-aios.sh"
echo "Stop all:    pkill -P $$"

---

### Monitor System

```bash
# Check orchestrator status
ps aux | grep orchestrator-v2

# View recent GitHub updates
gh issue list --state all --order updated --json updatedAt,number,labels | head -10

# Check label distribution
gh issue list --state open --json labels | jq -r '.[].labels[].name' | sort | uniq -c

# Monitor specific issue
gh issue view 999 --json labels,updatedAt,comments
```

---

### Stop Orchestrators

```bash
# Stop individual orchestrator
pkill -f "pm-orchestrator-v2"
pkill -f "po-orchestrator-v2"
pkill -f "dev-orchestrator-v2"

# Stop all
pkill -f "orchestrator-v2"
```

---

## Validation: End-to-End Test

**Complete walkthrough (30 minutes):**

1. **Setup** (5 min):
   ```bash
   source ~/.aios-env.sh
   gh auth status  # Verify GitHub auth
   ```

2. **Create test issue** (2 min):
   - On GitHub, create issue with label `pm-idea`
   - Note the issue number

3. **Start PM orchestrator** (2 min):
   ```bash
   cd ~/AIOS/aios-workshop-instructions
   copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --autopilot
   ```

4. **Monitor GitHub** (5 min):
   ```bash
   watch -n 2 'gh issue view <ISSUE_NUMBER> --json labels'
   # Wait for label to change (e.g., pm-idea → pm-validating)
   ```

5. **Verify** (5 min):
   ```bash
   # Check for [DECISION] comments
   gh issue view <ISSUE_NUMBER> --json comments --jq '.comments[-1].body'
   # Should show [DECISION] comment with reasoning
   ```

6. **Success** (if all above working):
   - ✅ Issue label changed
   - ✅ [DECISION] comment posted
   - ✅ Ready for PO & Dev orchestrators

---

## Next Steps

**Week 1 - Foundation:**
- [ ] Complete Phase 1-2 (setup + PM Orchestrator)
- [ ] Run PM orchestrator for 1-2 weeks
---

## Next Steps

**Week 1 - Foundation:**
- [ ] Complete Phase 1-2 (setup + PM Orchestrator)
- [ ] Run PM orchestrator for 1-2 weeks
- [ ] Validate issue labels and comments

**Week 2 - Full Orchestration:**
- [ ] Deploy PO Orchestrator
- [ ] Deploy Dev Orchestrator
- [ ] Run all three together

**Week 3 - Validation:**
- [ ] Monitor for 1-2 weeks (parallel with v1)
- [ ] Collect metrics (see METRICS_DASHBOARD.md)
- [ ] Test feedback loops

**Week 4+ - Cutover:**
- [ ] Stop v1 orchestrators
- [ ] Move to v2 full-time
- [ ] Archive v1 configuration

---

## Support Resources

**Documentation:**
- [templates-v2/README.md](../README.md) - Overview
- [orchestration-loop-pattern.md](./.prompts/orchestration-loop-pattern.md) - Core pattern
- [routing-registry.md](./routing-registry.md) - Stage transitions
- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - Diagnostics
- [FAQ.md](../FAQ.md) - Common questions

**Reference Files:**
- [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) - One-page operations guide

**Monitoring:**
- View orchestrator status: `ps aux | grep orchestrator-v2`
- Check GitHub: `gh issue list --state all | head -20`
- View metrics: See METRICS_DASHBOARD.md

---

**Questions?** Refer to TROUBLESHOOTING.md or FAQ.md for help.
