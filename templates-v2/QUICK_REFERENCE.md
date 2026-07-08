# Quick Reference Card: AIOS v2 Orchestration (GitHub-Only)

**Print this or keep in a terminal window for quick lookup**

---

## One-Time Setup

```bash
# 1. (Optional) Create token at https://github.com/settings/tokens if not using Copilot's auth
export GITHUB_TOKEN=ghp_xxxxx

# 2. Create env file
cat > ~/.aios-env.sh << 'EOF'
export GITHUB_TOKEN=${GITHUB_TOKEN:-}    # Optional (uses Copilot auth if empty)
export GITHUB_ORG=YOUR-ORG
export GITHUB_REPO=your-repo
export AIOS_PROJECT=aios
export LOOP_INTERVAL=30
export STUCK_THRESHOLD=2
EOF

# 3. Load environment
source ~/.aios-env.sh
```

---

## Deploy Orchestrators

```bash
# Load environment first
source ~/.aios-env.sh

# Terminal 1: PM Orchestrator
copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --autopilot

# Terminal 2: PO Orchestrator (optional)
copilot-cli templates-v2/orchestration/.prompts/po-orchestrator-v2.agent.md --autopilot

# Terminal 3: Dev Orchestrator (optional)
copilot-cli templates-v2/orchestration/.prompts/dev-orchestrator-v2.agent.md --autopilot
```

---

## Monitor Issues

```bash
# View issue in browser
open https://github.com/YOUR-ORG/YOUR-REPO/issues/999

# View with GitHub CLI
gh issue view 999 --comments

# List issues by label
gh issue list --label pm-idea
gh issue list --label strategic-opportunity
gh issue list --label feature-request
gh issue list --label intake

# Watch for label changes in real-time
watch -n 5 'gh issue list --label pm-idea --state all'
```

---

## Create Test Issues

```bash
# Manual: Go to GitHub and create issues with labels:
#  - pm-idea
#  - strategic-opportunity
#  - feature-request

# Or use GitHub CLI:
gh issue create --title "Test Opportunity" --label pm-idea --body "Description here"
gh issue create --title "Test Feature" --label feature-request --body "Description here"
```

---

## Check Orchestrator Status

```bash
# View issue comments (orchestrator decisions)
gh issue view 999 --comments

# Recent comments only
gh issue view 999 --comments | grep -A 2 "DECISION\|DECISION:"

# Check all stages on an issue
gh issue view 999 --comments | grep "Stage"
```

---

## Troubleshooting

```bash
# If issues aren't being processed:
# 1. Check environment
echo $GITHUB_ORG $GITHUB_REPO $AIOS_PROJECT

# 2. Verify issue has correct label
gh issue view 999

# 3. Check orchestrator logs (in terminal where it runs)

# 4. Fall back to Copilot auth (remove token)
unset GITHUB_TOKEN
```

---

## Common Workflows

```bash
# Move issue to next stage (manually, for testing)
gh issue edit 999 --remove-label intake --add-label design

# Add decision comment
gh issue comment 999 --body "[DECISION] Orchestrator: APPROVED"

# Check history
git log --oneline | grep -i "issue\|decision"

# List all issues in a stage
gh issue list --label design --state open
```

# Find issues by decision
grep -r '"decision": "PASS"' ~/aios-state-vault/decisions/ | wc -l

# Export issue states to CSV (advanced)
python3 << 'EOF'
import csv, os
from pathlib import Path

vault = Path(os.path.expanduser("~/aios-state-vault"))
issues = []

for file in (vault / "state").glob("*.md"):
    content = file.read_text()
    issue_id = file.stem.split('-')[1]
    stage = content.split("**Stage:** ")[1].split("\n")[0]
    issues.append([issue_id, stage])

with open("issues.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["Issue ID", "Stage"])
    writer.writerows(issues)

print(f"Exported {len(issues)} issues to issues.csv")
EOF
```

---

## Verify Orchestrator Status

```bash
# Check if orchestrator running
ps aux | grep orchestrator-v2

# Check recent logs
tail -50 orchestrator-output.log

# Check for errors
grep -i "error\|fail" orchestrator-output.log

# Monitor in real-time
tail -f orchestrator-output.log

# Count cycles completed
grep "Cycle" orchestrator-output.log | wc -l

# Time since last cycle
tail -1 orchestrator-output.log
```

---

## Troubleshoot Issues

```bash
# Git sync failed?
cd ~/aios-state-vault
git status        # Check what's uncommitted
git push origin main  # Try manual push

# GitHub API error?
curl -i -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$GITHUB_ORG/$GITHUB_REPO/issues/999

# State file corrupt?
cat ~/aios-state-vault/state/issue-999.md  # Inspect
git -C ~/aios-state-vault checkout state/issue-999.md  # Restore

# Stuck issue?
# 1. Check state file: cat ~/aios-state-vault/state/issue-999.md
# 2. Check for agent errors in logs
# 3. Manual intervention: edit state file + commit

# Vault out of sync?
cd ~/aios-state-vault
git pull origin main
git status
git log --oneline -10
```

---

## Workflow: Creating New Issue Type

```bash
# 1. Add stage to routing-registry.md
#    Define: entry_stage, decision outcomes, next_stages

# 2. Create new agent (from templates/agents/)
#    Implement: execute(issue_data) → decision

# 3. Add agent to orchestrator
#    Map stage → agent in agent_registry

# 4. Test end-to-end
#    Create issue, observe transitions

# 5. Monitor state vault
#    Verify state files created, decisions recorded
```

---

## Performance Baseline

```bash
# Measure single cycle time
time copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --max-cycles=1

# Expected: ~30-40s total
# Breakdown:
#   - Query GitHub: 1-2s
#   - Load state: <100ms per issue
#   - Spawn agent: 5-30s (agent-dependent)
#   - Update vault: 2-3s
#   - Post comment: 1s

# Monitor throughput
watch -n 30 'echo "Cycles:" && git -C ~/aios-state-vault log --since="30 seconds ago" --oneline state/ | wc -l'

# Expected: ~1 issue processed per 30-50s
```

---

## Vault Structure Reference

```
~/aios-state-vault/
├── state/
│   └── issue-999.md          (Current state, one per issue)
├── decisions/
│   └── issue-999-stage-timestamp.md  (Decision audit trail)
├── metrics.md                (System statistics)
├── .gitignore
├── README.md
└── .git/                     (Git history)
```

---

## State File Anatomy

```markdown
# Issue 999: Feature Title

## Current State
- **Issue Number:** 999
- **Stage:** intake          ← Current stage (KEY)
- **Stage Entry Time:** ISO datetime  ← When entered (KEY)
- **Priority Score:** 0-10
- **Status:** ⏳ In Progress

## Stage History
1. **prev_stage** (entry → exit) ✅ (duration)

## Latest Decision
```json
{
  "decision": "PASS|REVISE|BLOCKED|ESCALATE",
  "reasoning": "Why?",
  "agent": "agent-name",
  "timestamp": "ISO datetime",
  "duration_ms": 3500
}
```

## Related Issues
Links to parent/dependent issues
```

---

## Decision Outcomes Reference

```
PM Loop:
  pm-idea → PASS/BLOCK
  pm-validating → PASS/BLOCK
  pm-finalizing → PASS/REVISE/ESCALATE

PO Loop:
  strategic-opportunity → PRIORITIZE/DEFER/REJECT
  po-backlog → READY/BLOCKED

Dev Loop:
  intake → PASS/REVISE/BLOCKED
  design → PASS/REVISE/BLOCKED
  build → PASS/PARTIAL/BLOCKED
  qa → PASS/INCOMPLETE/FAIL
  verification → PASS/FAIL/BLOCKED
  policy → APPROVE/ESCALATE/BLOCK

Feedback Loops:
  Design REVISE → intake
  QA INCOMPLETE → design
  Verification FAIL → design
```

---

## Emergency Procedures

```bash
# Restart all orchestrators
pkill -f orchestrator-v2
sleep 2
source ~/.aios-env.sh
# (Redeploy in terminals)

# Revert last state change
cd ~/aios-state-vault
git log --oneline state/ | head -1  # Note commit
git revert COMMIT_SHA  # Revert commit

# Manually update state (emergency)
cd ~/aios-state-vault
# Edit state/issue-999.md manually
git add state/issue-999.md
git commit -m "Manual update: issue-999 → stage"
git push origin main

# Force sync vault
cd ~/aios-state-vault
git fetch origin
git reset --hard origin/main
```

---

## Documentation Links

- **Full Setup:** [GETTING_STARTED.md](./GETTING_STARTED.md)
- **Overview:** [README.md](./README.md)
- **Pattern:** [orchestration-loop-pattern.md](./.prompts/orchestration-loop-pattern.md)
- **Routing:** [routing-registry.md](./routing-registry.md)
- **State API:** [state-manager/README.md](../state-manager/README.md)
- **Tests:** [test-sample.md](./test-sample.md)

---

**Saved at:** `~/AIOS/aios-workshop-instructions/templates-v2/QUICK_REFERENCE.md`

**Last Updated:** 2026-07-08

**Pro Tip:** Bookmark this file or print it. Most operations fit on one page!
