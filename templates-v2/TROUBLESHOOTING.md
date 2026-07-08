# Troubleshooting Guide: AIOS v2 Orchestration

**Quick diagnosis and resolution for common issues**

---

## Diagnosis Framework

**Before troubleshooting, check:**

```bash
# 1. GitHub authentication working?
gh auth status
# Should show: "Logged in to github.com"

# 2. GitHub environment variables set?
echo $GITHUB_ORG       # Should show your org
echo $GITHUB_REPO      # Should show your repo
echo $AIOS_PROJECT     # Should show: aios

# 3. Issues exist on GitHub with correct labels?
gh issue list --label pm-idea --state open
# Should show issues if any exist

# 4. Orchestrator running?
ps aux | grep orchestrator-v2
# Should show process running
```

---

## Issue 1: Orchestrator Not Processing Issues

### Symptoms
```
gh issue list --label pm-idea --state open
# Shows issues, but labels haven't changed in 10+ minutes
# No comments posted to issues
```

### Diagnosis

**Step 1: Check GitHub authentication**
```bash
gh auth status
# Must show logged in
```

**Step 2: Verify issues have correct labels**
```bash
# Check pm-idea label exists
gh issue list --label pm-idea --state open --json number

# Check if labels changed recently
gh issue view <ISSUE_NUMBER> --json labels,updatedAt
```

**Step 3: Check for GitHub API errors**
```bash
# Look for API error patterns in orchestrator logs
tail -100 pm-orchestrator.log | grep -i "api\|error\|rate limit"
# Might show: 403 (auth), 422 (invalid), 429 (rate limit)
```

**Step 4: Verify orchestrator environment**
```bash
# Check if orchestrator has env vars
echo $GITHUB_ORG
echo $GITHUB_REPO
echo $AIOS_PROJECT

# All must be set
```

### Solutions

**Solution A: Restart orchestrator**
```bash
# Kill existing process
pkill -f "pm-orchestrator-v2"

# Re-source environment
source ~/.aios-env.sh

# Restart
copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --autopilot
```

**Solution B: Check GitHub API rate limits**
```bash
# View current rate limit
gh api rate_limit --paginate

# If you hit limit, wait 1 hour or use personal token
export GITHUB_TOKEN=ghp_xxxxx  # Your personal access token
```

**Solution C: Verify issue labels are correct**
```bash
# Create test issue if needed
gh issue create --title "Test PM Idea" --label pm-idea

# Check if orchestrator processes it within 30 seconds
sleep 30
gh issue view <NEW_ISSUE_NUMBER> --json labels
# Should show updated label (pm-validating if agent ran)
```

---

## Issue 2: Agent Decision Not Posted as Comment

### Symptoms
```
gh issue view 999 --json comments
# Returns empty comments array, but labels changed
# OR comments exist but no [DECISION] prefix
```

### Diagnosis

**Step 1: Check issue labels are changing**
```bash
# View label history
gh issue view 999 --json labels,updatedAt
# Should show recent update
```

**Step 2: Verify orchestrator has write permission**
```bash
# Try to post a comment manually
gh issue comment 999 --body "Test comment from troubleshooting"

# If fails: "You do not have permission", then token issue
# If succeeds: "Comment added", then orchestrator auth issue
```

**Step 3: Check orchestrator logs for comment posting errors**
```bash
tail -50 pm-orchestrator.log | grep -i "comment\|post"
# Might show specific GitHub API errors
```

### Solutions

**Solution A: Verify GitHub token has issues:write scope**
```bash
# Check token scopes
gh auth status --show-token

# If missing issues:write:
# 1. Generate new token with proper scopes at github.com/settings/tokens
# 2. Update GITHUB_TOKEN: export GITHUB_TOKEN=ghp_xxxxx
# 3. Restart orchestrator
```

**Solution B: Post comment manually to test**
```bash
# Test posting to an issue
gh issue comment 999 --body "Testing manual comment"

# If succeeds, orchestrator may not be running
# If fails, token/permission issue
```

---

## Issue 3: Stuck Issues (Labels Not Updating)

### Symptoms
```
gh issue view 999 --json labels
# Shows same label for 2+ hours
# updatedAt hasn't changed in 2+ hours
```

### Diagnosis

**Step 1: Check if issue is actually in any stage**
```bash
# Show current label
gh issue view 999 --json labels
# Should show one label like pm-validating, intake, design-approved, etc.
```

**Step 2: See recent comments to understand why**
```bash
# View recent comments and decisions
gh issue view 999 --json comments --jq '.comments[-5:] | .[] | .body'
# Should show [DECISION] comments with reasoning
```

**Step 3: Check for agent errors in comment**
```bash
# Look for error messages in comments
gh issue view 999 --json comments --jq '.comments[] | select(.body | contains("ERROR")) | .body'
# Might show agent failure, missing data, etc.
```

### Solutions

**Solution A: Check if issue is blocked**
```bash
# Look for BLOCKED decision in comments
gh issue view 999 --json comments --jq '.comments[] | select(.body | contains("BLOCKED"))'

# If found, issue is intentionally blocked (e.g., prerequisite missing)
# Resolve blocker and post manual comment to unstick
```

**Solution B: Check for feedback loops**
```bash
# Look for recent feedback loop comment
gh issue view 999 --json comments --jq '.comments[] | select(.body | contains("Feedback loop"))'

# If found, issue cycled back to earlier stage (design→intake, etc.)
# This is expected behavior, not stuck
```

**Solution C: Manually advance if truly stuck**
```bash
# Only if issue has been stuck >4 hours and agent not responding
gh issue edit 999 --remove-label "current-stage" --add-label "new-stage"
gh issue comment 999 --body "[MANUAL] Manually advancing stage due to stuck detection. Please investigate."

# Then investigate agent logs to see why it failed
```

---

## Issue 4: Wrong Label Applied

### Symptoms
```
gh issue view 999 --json labels
# Shows unexpected stage label (e.g., pm-opportunity when should be intake)
```

### Diagnosis

**Step 1: Check recent decision**
```bash
# View most recent comment/decision
gh issue view 999 --json comments --jq '.comments[-1] | .body'
# Should explain why label changed
```

**Step 2: Understand routing decision**
```bash
# Check routing registry for this transition
# Look in: orchestration/routing-registry.md

# Example: if intake → design-approved, that's correct
# If intake → pm-validating, that's wrong
```

**Step 3: Check if manual edit was made**
```bash
# View full comment history
gh issue view 999 --json comments --jq '.comments[] | .createdAt, .body' | tail -20
# Look for manual edits or non-orchestrator changes
```

### Solutions

**Solution A: Verify label is actually correct**
```bash
# Double-check routing registry
# Example: Design agent returns PASS → should route to build-approved

# If label is correct, issue may just be further along than expected
```

**Solution B: Manually fix label if wrong**
```bash
# Remove incorrect label and add correct one
gh issue edit 999 --remove-label "wrong-label" --add-label "correct-label"
gh issue comment 999 --body "[MANUAL] Corrected label from wrong-label to correct-label"
```

---

## Issue 5: GitHub API Rate Limiting

### Symptoms
```
Orchestrator logs show:
"429 Too Many Requests" or "Rate limit exceeded"
Labels stop updating
```

### Diagnosis

**Step 1: Check current rate limit**
```bash
gh api rate_limit

# Look for:
# rate.limit: 60 (public) or 5000 (authenticated)
# rate.remaining: should be > 0
# rate.reset: shows when limit resets
```

**Step 2: Calculate API usage**
```bash
# Estimate: each orchestrator cycle uses ~5-10 API calls
# With 30-second interval: ~200-400 calls/hour per orchestrator
# With 3 orchestrators: ~600-1200 calls/hour
# GitHub limit: 5000/hour = max 8-4 cycles/hour without hitting limit
```

### Solutions

**Solution A: Use GitHub token with higher limit**
```bash
# Get personal access token from github.com/settings/tokens
# Generate with: repo, read:org, admin:repo_hook scopes

# Export and use
export GITHUB_TOKEN=ghp_xxxxx
echo "Token set with 5000 req/hour limit"
```

**Solution B: Increase orchestrator sleep interval**
```bash
# Change LOOP_INTERVAL to reduce API calls
export LOOP_INTERVAL=60  # 60 seconds instead of 30
# This cuts API usage in half but increases latency
```

**Solution C: Batch process issues in orchestrator**
```bash
# Process multiple issues per cycle to reduce total queries
# (Already implemented in latest orchestrators)
```

---

## Issue 6: Environment Variables Not Loading

### Symptoms
```
Orchestrator starts but immediately fails
Logs show: "GITHUB_ORG not set" or "GITHUB_REPO not set"
```

### Diagnosis

**Step 1: Check if env file exists**
```bash
ls -la ~/.aios-env.sh
# Should exist and be readable
```

**Step 2: Source the file manually**
```bash
source ~/.aios-env.sh
echo "GITHUB_ORG: $GITHUB_ORG"
echo "GITHUB_REPO: $GITHUB_REPO"
# Should print values
```

**Step 3: Check file syntax**
```bash
# Verify no syntax errors
bash -n ~/.aios-env.sh
# Should run silently (no errors)
```

### Solutions

**Solution A: Recreate environment file**
```bash
cat > ~/.aios-env.sh << 'EOF'
export GITHUB_TOKEN=${GITHUB_TOKEN:-}
export GITHUB_ORG=YOUR-ORG
export GITHUB_REPO=your-repo
export AIOS_PROJECT=aios
export LOOP_INTERVAL=30
export STUCK_THRESHOLD=2
EOF

source ~/.aios-env.sh
echo "✅ Environment loaded"
```

**Solution B: Add to shell startup**
```bash
# For bash
echo "source ~/.aios-env.sh" >> ~/.bashrc
source ~/.bashrc

# For zsh
echo "source ~/.aios-env.sh" >> ~/.zshrc
source ~/.zshrc
```

---

## Issue 7: Orchestrator Process Crash

### Symptoms
```
ps aux | grep orchestrator-v2
# No process found (or crashed a few minutes ago)

# Check logs
tail pm-orchestrator.log
# Shows errors or crash dump
```

### Diagnosis

**Step 1: Check last error in logs**
```bash
tail -50 pm-orchestrator.log | grep -i "error\|fatal\|exception"
# Look for the actual failure reason
```

**Step 2: Try restarting orchestrator**
```bash
# If it starts and stays up, was just a transient error
copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --autopilot &
sleep 5
ps aux | grep orchestrator-v2
# Should show running
```

**Step 3: Check for disk space or resource issues**
```bash
# Disk space
df -h
# Look for space < 10%

# Memory
free -h
# Look for available > 100MB

# CPU
top -n 1 | head -20
```

### Solutions

**Solution A: Restart with debug output**
```bash
# Run with verbose logging
export DEBUG=1
copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --autopilot

# Watch for first error, fix it, restart
```

**Solution B: Check GitHub API status**
```bash
# GitHub might be having issues
curl -s https://www.githubstatus.com | grep -i "degraded\|outage"

# If GitHub is down, orchestrator will fail
# Wait for GitHub to recover
```

---

## Quick Diagnostic Script

```bash
#!/bin/bash
# save as: ~/aios-diagnose.sh

echo "=== AIOS v2 Diagnostic Report ==="
echo
echo "1️⃣  GitHub Authentication"
gh auth status
echo
echo "2️⃣  Environment Variables"
echo "GITHUB_ORG: $GITHUB_ORG"
echo "GITHUB_REPO: $GITHUB_REPO"
echo "AIOS_PROJECT: $AIOS_PROJECT"
echo
echo "3️⃣  GitHub API Status"
gh api rate_limit | grep -E 'limit|remaining|reset'
echo
echo "4️⃣  Sample Issues"
echo "pm-idea issues:"
gh issue list --label pm-idea --state open --json number | wc -l
echo "feature-request issues:"
gh issue list --label feature-request --state open --json number | wc -l
echo
echo "5️⃣  Orchestrator Status"
echo "PM Orchestrator:"
ps aux | grep pm-orchestrator-v2 | grep -v grep || echo "NOT RUNNING"
echo
echo "✅ Diagnostic complete. Review output above."
```

**Run it:**
```bash
bash ~/aios-diagnose.sh
```

---

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Bad or missing GitHub token | Check GITHUB_TOKEN, generate new token |
| `403 Forbidden` | Token lacks permissions | Regenerate with issues:write scope |
| `404 Not Found` | Repo or org incorrect | Check GITHUB_ORG, GITHUB_REPO |
| `422 Unprocessable` | Invalid label or data | Check label names match routing-registry.md |
| `429 Too Many Requests` | Rate limited | Use personal token, increase LOOP_INTERVAL |
| `ENOTFOUND` network error | No internet connection | Check network connectivity |

---

## Next Steps

If the above doesn't resolve your issue:

1. **Collect diagnostics:** Run the diagnostic script above
2. **Check logs:** `tail -100 pm-orchestrator.log`
3. **Manual test:** Try `gh issue list --label pm-idea` to verify basic GitHub access
4. **Restart orchestrator:** Kill and restart process
5. **Contact:** Reference diagnostics output when asking for help
```bash
# Add debug output to orchestrator
# Look for these log messages:
# - "State manager initialized: /path/to/vault"
# - "Querying GitHub for issues..."
# - "Processing issue #999..."

# If missing, orchestrator might not be starting properly
```

**Solution C: Restart orchestrator with verbose output**
```bash
export DEBUG=1
copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --autopilot 2>&1 | tee pm-orchestrator-debug.log

# Then check log:
grep -i "stage\|state\|vault" pm-orchestrator-debug.log
```

---

## Issue 2: GitHub Comments Not Posting

### Symptoms
```
Issues processed but no [STATE UPDATE] comments on GitHub
```

### Diagnosis

**Step 1: Check GitHub token scope**
```bash
# View token capabilities
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
# Look for: "X-OAuth-Scopes" header (should include "repo")

# View all tokens
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/authorizations
```

**Step 2: Test manual comment posting**
```bash
# Try posting comment manually
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  https://api.github.com/repos/$GITHUB_ORG/$GITHUB_REPO/issues/999/comments \
  -d '{"body":"[STATE UPDATE] Test comment"}'

# If succeeds: token is good, issue is with orchestrator
# If fails: token issue or repo/issue doesn't exist
```

**Step 3: Check issue number extraction**
```bash
# Look in orchestrator logs:
grep "issue\|#\|number" orchestrator-output.log | head -20

# Should show: "Processing issue #999" or similar
```

**Step 4: Verify comment format**
```bash
# Check source code for comment template
grep -A 5 "\[STATE UPDATE\]" templates-v2/orchestration/.prompts/*-orchestrator*.agent.md | head -20
```

### Solutions

**Solution A: Regenerate GitHub token**
1. Go to https://github.com/settings/tokens
2. Delete old token if needed
3. Create new token with:
   - ✅ `repo` scope (all)
   - ✅ `issues:write` included
4. Update `$GITHUB_TOKEN`:
   ```bash
   export GITHUB_TOKEN=ghp_new_token_xxxxx
   ```

**Solution B: Test with curl before deploying**
```bash
# Before running orchestrator, verify manual flow:
ISSUE_NUM=999

# 1. Query issue
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$GITHUB_ORG/$GITHUB_REPO/issues/$ISSUE_NUM

# 2. Post comment
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  https://api.github.com/repos/$GITHUB_ORG/$GITHUB_REPO/issues/$ISSUE_NUM/comments \
  -d '{"body":"Test comment from $(date)"}'

# 3. Verify on GitHub
# Visit https://github.com/YOUR-ORG/YOUR-REPO/issues/999
# Comment should appear
```

**Solution C: Check orchestrator comment logic**
```bash
# Look for comment posting code
grep -n "add_comment\|post_comment" templates-v2/orchestration/.prompts/*.agent.md

# If not found, add it manually to orchestrator:
# After state update, add:
# issue.add_comment(f"[STATE UPDATE] {decision_outcome} → {next_stage}")
```

---

## Issue 3: Orchestrator Stuck/Not Progressing

### Symptoms
```
Orchestrator running but:
- No state changes for >2 hours
- Same issues being processed repeatedly
- Or process hanging
```

### Diagnosis

**Step 1: Check if orchestrator alive**
```bash
ps aux | grep orchestrator-v2 | grep -v grep
# If no output: orchestrator crashed

# Check process status
pgrep -f "orchestrator-v2" && echo "Running" || echo "Not running"
```

**Step 2: Check for stuck issues**
```bash
# Run monitoring script
~/monitor-aios.sh

# Look for "Stuck Issues" section
# If issues stuck >2 hours, they're blocked

# Get details:
cat ~/aios-state-vault/state/issue-999.md | grep -A 20 "## Current State"
```

**Step 3: Check agent responses**
```bash
# Look in decisions folder for recent changes
ls -lrt ~/aios-state-vault/decisions/ | tail -10

# If no recent decisions: agent not running
# If decisions exist: check what they say

cat ~/aios-state-vault/decisions/issue-999-intake*.md | head -20
```

**Step 4: Check git operations**
```bash
cd ~/aios-state-vault
git status
# If there are uncommitted changes: git push might be failing

git push origin main
# Try manual push to see error message
```

### Solutions

**Solution A: Restart orchestrator**
```bash
# Stop
pkill -f "pm-orchestrator-v2"
sleep 2

# Verify stopped
ps aux | grep "pm-orchestrator-v2" | grep -v grep
# Should be empty

# Start again
source ~/.aios-env.sh
cd ~/AIOS/aios-workshop-instructions
copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --autopilot
```

**Solution B: Check agent logs for specific error**
```bash
# Search for error patterns
tail -500 orchestrator-output.log | grep -i "error\|exception\|timeout\|fail"

# Look specifically for:
# - "Agent timeout"
# - "State update failed"
# - "Git operation failed"
```

**Solution C: Manual issue push through pipeline**
```bash
cd ~/aios-state-vault

# If issue is truly stuck, manually advance it
cat > state/issue-999.md << 'EOF'
# Issue 999: Feature Title

## Current State
- **Stage:** design-approved
- **Stage Entry Time:** 2026-07-08T16:00:00Z
- **Priority Score:** 8.0
- **Status:** ⏳ In Progress

## Stage History
1. **intake** (2026-07-08T15:00:00Z → 2026-07-08T15:30:00Z) ✅ (30m)

## Latest Decision
```json
{"decision": "PASS", "reasoning": "Manual push"}
```
EOF

# Commit
git add state/issue-999.md
git commit -m "Manual: Issue #999 intake → design (stuck recovery)"
git push origin main
```

**Solution D: Check for infinite loops**
```bash
# Count transitions for single issue
git -C ~/aios-state-vault log --oneline -- state/issue-999.md | wc -l
# Should be reasonable count (e.g., <20)

# If very high: issue might be in feedback loop
# Check stage history:
cat ~/aios-state-vault/state/issue-999.md | grep "^[0-9]" | head -20

# Look for pattern like:
# 1. intake
# 2. design
# 3. intake  ← Loop!
# 4. design
```

---

## Issue 4: Git Sync Failing

### Symptoms
```
⚠️ Git operation failed
Commits not appearing in vault
Push rejected
```

### Diagnosis

**Step 1: Check git status**
```bash
cd ~/aios-state-vault
git status

# Expected output:
# - "On branch main"
# - "Your branch is up to date"
# - OR "nothing to commit"
```

**Step 2: Check git configuration**
```bash
git config --global user.name
git config --global user.email

# Should both be set to valid values
```

**Step 3: Test git operations manually**
```bash
cd ~/aios-state-vault

# Try pull
git pull origin main
# Should succeed

# Try push
git push origin main
# Should succeed (or "Everything up-to-date")
```

**Step 4: Check credentials**
```bash
# GitHub token valid?
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user

# Should return user info, not 401 Unauthorized
```

### Solutions

**Solution A: Configure git credentials**
```bash
git config --global user.email "your-email@example.com"
git config --global user.name "Your Name"

# Verify
git config --global user.email
git config --global user.name
```

**Solution B: Check branch name**
```bash
cd ~/aios-state-vault
git branch -a
# Should show main (not master)

# If on master, switch to main:
git checkout main
# or
git branch -M master main
```

**Solution C: Force git sync**
```bash
cd ~/aios-state-vault

# Fetch latest
git fetch origin

# Reset to match remote
git reset --hard origin/main

# Verify
git status
# Should show: "Your branch is up to date with 'origin/main'"
```

**Solution D: Check token expiry**
```bash
# If token was created long ago, it might have expired
# Go to https://github.com/settings/tokens
# Check "Expires" column

# If expired: delete and create new token
# Update $GITHUB_TOKEN environment variable
```

---

## Issue 5: State Vault Out of Sync

### Symptoms
```
Local files don't match remote
Commits showing on GitHub but not locally
"fast-forward" errors
```

### Diagnosis

**Step 1: Check sync status**
```bash
cd ~/aios-state-vault
git status
git log --oneline -5 origin/main
git log --oneline -5 HEAD

# Compare the two logs
```

**Step 2: Check for uncommitted changes**
```bash
git diff state/
git status --short
```

### Solutions

**Solution A: Pull latest changes**
```bash
cd ~/aios-state-vault
git pull origin main

# If conflicts, resolve them:
git mergetool
# or
git checkout --theirs state/issue-*.md
git commit -m "Resolve merge: accept remote state"
git push origin main
```

**Solution B: Hard reset to remote**
```bash
cd ~/aios-state-vault
git fetch origin
git reset --hard origin/main

# Verify
git status
# Should show clean
```

**Solution C: Rebase if behind**
```bash
cd ~/aios-state-vault
git fetch origin

# Check if behind
git log origin/main ^HEAD --oneline

# Rebase
git rebase origin/main

# If conflicts: resolve and continue
git rebase --continue
# or abort
git rebase --abort
```

---

## Issue 6: Orchestrator Crashing

### Symptoms
```
Orchestrator terminates unexpectedly
Exit code non-zero
No error message
```

### Diagnosis

**Step 1: Check exit code**
```bash
# Run orchestrator and capture exit code
copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --max-cycles=1
echo $?
# If 0: success
# If non-zero: error
```

**Step 2: Run with debug output**
```bash
copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --max-cycles=1 2>&1 | tee debug.log

cat debug.log | tail -100
```

**Step 3: Check system resources**
```bash
# Disk space
df -h

# Memory
free -h

# CPU
top -b -n 1 | head -10
```

### Solutions

**Solution A: Increase verbosity**
```bash
export DEBUG=1
export VERBOSE=1
copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --autopilot
```

**Solution B: Run with timeout**
```bash
timeout 60 copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --max-cycles=1

# If times out (exit code 124), orchestrator is hanging
```

**Solution C: Check for memory leaks**
```bash
# Monitor memory usage while running
watch -n 2 'ps aux | grep orchestrator-v2 | grep -v grep'

# If memory keeps growing: memory leak in orchestrator
```

---

## Issue 7: Feedback Loop Not Working

### Symptoms
```
Design REVISE should go to intake, but doesn't
Stage stays in design instead of reverting to intake
```

### Diagnosis

**Step 1: Check routing registry**
```bash
grep -A 5 "## Design REVISE → Intake" templates-v2/orchestration/routing-registry.md

# Should show transition rule
```

**Step 2: Check agent decision output**
```bash
cat ~/aios-state-vault/decisions/issue-999-design*.md | grep -i "revise"

# Should show: "decision": "REVISE"
```

**Step 3: Check state file history**
```bash
cat ~/aios-state-vault/state/issue-999.md | grep -A 20 "## Stage History"

# Look for: design-approved followed by intake
# If not present: feedback loop didn't trigger
```

### Solutions

**Solution A: Verify routing registry**
```bash
# Check that routing rule exists
grep "design.*REVISE.*intake" templates-v2/orchestration/routing-registry.md

# If not found: add it
# Format: "- REVISE → intake"
```

**Solution B: Check orchestrator routing logic**
```bash
# Look for where routing is applied
grep -n "routing\|next_stage" templates-v2/orchestration/.prompts/dev-orchestrator-v2.agent.md | head -10

# If missing: add routing check after decision
```

**Solution C: Manual feedback loop push**
```bash
# Force issue back to intake
cat > ~/aios-state-vault/state/issue-999.md << 'EOF'
# Issue 999: Feature Title

## Current State
- **Stage:** intake
- **Stage Entry Time:** 2026-07-08T16:00:00Z
- **Priority Score:** 8.0

## Stage History
1. **design-approved** (...) (feedback loop)
2. **intake** (started) ⏳ In Progress

## Latest Decision
```json
{"decision": "REVISE", "reasoning": "Feedback loop: design needs revision"}
```
EOF

git -C ~/aios-state-vault add -A
git -C ~/aios-state-vault commit -m "Manual: feedback loop issue #999 design→intake"
git -C ~/aios-state-vault push origin main
```

---

## Issue 8: High CPU/Memory Usage

### Symptoms
```
Orchestrator using lots of CPU/memory
System slow or unresponsive
```

### Diagnosis

**Step 1: Monitor resource usage**
```bash
# Real-time monitoring
watch -n 1 'ps aux | grep orchestrator | grep -v grep'

# Look for: high %CPU or high %MEM column
```

**Step 2: Check process details**
```bash
# Get orchestrator PID
PID=$(pgrep -f "orchestrator-v2" | head -1)

# Check open files
lsof -p $PID | wc -l
# If very high (>1000): file descriptor leak

# Check threads
ps -o nlwp -p $PID
# If very high (>100): thread leak
```

### Solutions

**Solution A: Reduce loop interval**
```bash
# Increase sleep between cycles
export LOOP_INTERVAL=60  # Instead of 30

# Restart orchestrator
```

**Solution B: Limit issues per cycle**
```bash
# Don't process all issues at once
# Add to orchestrator: process only first 5 issues per cycle
# Then continue next cycle
```

**Solution C: Restart orchestrator periodically**
```bash
# Create restart script
cat > ~/restart-orchestrator.sh << 'EOF'
#!/bin/bash

# Run orchestrator for 1 hour, then restart
while true; do
    echo "Starting orchestrator..."
    timeout 3600 copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --autopilot
    
    echo "Orchestrator stopped, waiting before restart..."
    sleep 60
done
EOF

chmod +x ~/restart-orchestrator.sh
~/restart-orchestrator.sh
```

---

## Quick Diagnostic Script

**Run this to get system status:**

```bash
cat > ~/diagnose-aios.sh << 'EOF'
#!/bin/bash

echo "╔════════════════════════════════════════════╗"
echo "║       AIOS v2 Diagnostic Report            ║"
echo "╚════════════════════════════════════════════╝"
echo ""

echo "1️⃣  Environment"
echo "─────────────────────────────────────────────"
echo "GitHub Token: $(echo $GITHUB_TOKEN | cut -c1-20)..."
echo "Vault Path: $VAULT_PATH"
echo "Repo Path: $REPO_PATH"
echo ""

echo "2️⃣  Vault Status"
echo "─────────────────────────────────────────────"
if [ -d "$VAULT_PATH" ]; then
    echo "✅ Vault directory exists"
    echo "   State files: $(ls $VAULT_PATH/state/*.md 2>/dev/null | wc -l)"
    echo "   Decision files: $(ls $VAULT_PATH/decisions/*.md 2>/dev/null | wc -l)"
else
    echo "❌ Vault directory missing: $VAULT_PATH"
fi
echo ""

echo "3️⃣  Git Status"
echo "─────────────────────────────────────────────"
cd $VAULT_PATH 2>/dev/null
if git status >/dev/null 2>&1; then
    echo "✅ Git repo healthy"
    echo "   Branch: $(git branch --show-current)"
    echo "   Commits: $(git log --oneline | wc -l)"
else
    echo "❌ Git repo error"
fi
echo ""

echo "4️⃣  Orchestrators"
echo "─────────────────────────────────────────────"
pm_pid=$(pgrep -f "pm-orchestrator-v2" | head -1)
po_pid=$(pgrep -f "po-orchestrator-v2" | head -1)
dev_pid=$(pgrep -f "dev-orchestrator-v2" | head -1)

[ -n "$pm_pid" ] && echo "✅ PM Orchestrator (PID: $pm_pid)" || echo "❌ PM Orchestrator not running"
[ -n "$po_pid" ] && echo "✅ PO Orchestrator (PID: $po_pid)" || echo "❌ PO Orchestrator not running"
[ -n "$dev_pid" ] && echo "✅ Dev Orchestrator (PID: $dev_pid)" || echo "❌ Dev Orchestrator not running"
echo ""

echo "5️⃣  GitHub API"
echo "─────────────────────────────────────────────"
if curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user > /dev/null 2>&1; then
    echo "✅ GitHub API accessible"
else
    echo "❌ GitHub API error"
fi
echo ""

echo "6️⃣  Recent Activity"
echo "─────────────────────────────────────────────"
cd $VAULT_PATH
echo "Last 5 commits:"
git log --oneline -5 state/
echo ""

echo "📊 System Resources"
echo "─────────────────────────────────────────────"
echo "Disk: $(df -h $VAULT_PATH | tail -1 | awk '{print $5 " used"}')"
echo "Memory: $(free -h | grep Mem | awk '{print $3 " used"}')"
echo ""
EOF

chmod +x ~/diagnose-aios.sh
~/diagnose-aios.sh
```

---

## When All Else Fails

**Nuclear options (use carefully):**

```bash
# 1. Completely reset vault to remote
cd ~/aios-state-vault
git fetch origin
git reset --hard origin/main
git clean -fd

# 2. Restart all orchestrators
pkill -f "orchestrator-v2"
sleep 5

# 3. Reinitialize environment
source ~/.aios-env.sh

# 4. Restart services
cd ~/AIOS/aios-workshop-instructions
copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --autopilot &
sleep 5
copilot-cli templates-v2/orchestration/.prompts/po-orchestrator-v2.agent.md --autopilot &
sleep 5
copilot-cli templates-v2/orchestration/.prompts/dev-orchestrator-v2.agent.md --autopilot &

# 5. Monitor
~/monitor-aios.sh
```

---

## Getting Help

**If issue persists:**

1. **Collect diagnostic data:**
   ```bash
   ~/diagnose-aios.sh > ~/diagnostic-report.txt
   tail -100 orchestrator-output.log >> ~/diagnostic-report.txt
   git -C ~/aios-state-vault log --oneline -20 >> ~/diagnostic-report.txt
   cat ~/diagnostic-report.txt
   ```

2. **Check documentation:**
   - [GETTING_STARTED.md](./GETTING_STARTED.md)
   - [README.md](./README.md)
   - [test-sample.md](./test-sample.md)

3. **Review logs:**
   - Orchestrator output
   - Git history
   - State file evolution

4. **Manual verification:**
   - Create test issue manually
   - Verify state file created
   - Check GitHub comment posted
   - Inspect git commit

---

**Last Updated:** 2026-07-08

**Questions?** Refer to [GETTING_STARTED.md](./GETTING_STARTED.md) for complete walkthrough.
