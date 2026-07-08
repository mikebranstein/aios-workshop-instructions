# FAQ: AIOS v2 Orchestration System

**Frequently Asked Questions & Answers**

---

## Getting Started

### Q: Why is v2 better than v1?

**A:** v2 improves on v1 in key areas:

| Area | v1 | v2 |
|------|-----|-----|
| **State Management** | Scattered GitHub labels | GitHub-native (labels + comments, no external vault) |
| **Routing Logic** | Duplicated in 3 files | Centralized (routing-registry.md) |
| **Auditability** | Limited comments | Full decision audit trail via GitHub comments |
| **Observability** | Manual checking | All state visible on GitHub, no external tools |
| **Maintainability** | Hard to extend | Reusable pattern, easy to add stages |
| **Scaling** | Works but cluttered | Designed for growth, minimal dependencies |

**Note:** v1 and v2 can run in parallel. No breaking changes.

---

### Q: Do I have to migrate from v1 to v2?

**A:** No. v2 is optional:

- **Phase 1-2:** Run v2 in parallel with v1 (1-2 weeks)
- **Evaluate:** See if you prefer v2
- **Phase 3:** Keep v1 OR cutover to v2 (your choice)

We recommend at least testing v2 to see the benefits.

---

### Q: How long does setup take?

**A:** Depends on phase:

- **Foundation (Phase 1):** 1-2 hours (PM orchestrator setup)
- **Full (Phase 2):** +2-3 hours (add PO & Dev orchestrators)
- **Validation (Phase 3):** 1-2 weeks (parallel testing with v1)
- **Optimization (Phase 4):** Ongoing (optional)

Setup is simpler now with GitHub-only state (no vault needed).

---

## Multi-Project Questions

### Q: Can I use v2 for multiple projects?

**A:** Absolutely. v2 is designed for multi-project scenarios:

- Single shared state vault (`~/aios-state-vault/`)
- Each project isolated in separate directory: `state/<project-id>/`
- Each orchestrator scoped to one project via `AIOS_PROJECT` env var
- Perfect for organizations with multiple products/teams

**Example:**
```bash
# Project A (marketing)
export AIOS_PROJECT=marketing
export GITHUB_REPO=marketing-repo
copilot-cli pm-orchestrator-v2.agent.md --autopilot

# Project B (platform)
export AIOS_PROJECT=platform
export GITHUB_REPO=platform-repo
copilot-cli pm-orchestrator-v2.agent.md --autopilot

# Both running simultaneously, completely isolated
# State: ~/aios-state-vault/state/marketing/
# State: ~/aios-state-vault/state/platform/
```

---

### Q: How do I set up a new project?

**A:** Three simple steps:

**1. Create .aios-config.sh in your project repo:**
```bash
# .aios-config.sh
export AIOS_PROJECT=my-new-project
export GITHUB_ORG=your-org
export GITHUB_REPO=my-new-project-repo
export VAULT_PATH=~/aios-state-vault
export REPO_PATH=~/aios-state-vault
```

**2. Source the config before running orchestrators:**
```bash
source .aios-config.sh
source ~/.aios-env.sh  # Shared token
copilot-cli pm-orchestrator-v2.agent.md --autopilot
```

**3. State files auto-created:**
```bash
ls ~/aios-state-vault/state/my-new-project/
# Shows: issue-1.md, issue-2.md, etc.
```

That's it! Your project now has its own isolated orchestration state.

---

### Q: Do projects share routing logic?

**A:** Yes, the routing-registry.md is shared. But you can customize:

- **Shared approach:** All projects use same stages (recommended)
- **Custom approach:** Fork routing-registry.md per project
- **Hybrid:** Share core stages, add project-specific ones

Most organizations use shared routing for consistency.

---

### Q: What if two projects have same issue number?

**A:** No problem, they're in different directories:

```
~/aios-state-vault/
├── state/
│   ├── project-a/issue-1.md     ← Project A's issue #1
│   └── project-b/issue-1.md     ← Project B's issue #1
```

Same number, different projects, completely isolated.

---

### Q: Can I migrate issues between projects?

**A:** Yes, manually:

```bash
# Move from project-a to project-b:
cp ~/aios-state-vault/state/project-a/issue-123.md \
   ~/aios-state-vault/state/project-b/issue-456.md

# Update project field in file
sed -i 's/project_id: project-a/project_id: project-b/' \
    ~/aios-state-vault/state/project-b/issue-456.md

# Commit
git -C ~/aios-state-vault add state/project-b/issue-456.md
git -C ~/aios-state-vault commit -m "Migrate: issue-456 from project-a to project-b"
git -C ~/aios-state-vault push origin main
```

---

### Q: Can I merge projects later?

**A:** Yes, consolidate directories:

```bash
# Merge project-temp into project-main:
cp ~/aios-state-vault/state/project-temp/*.md \
   ~/aios-state-vault/state/project-main/

# Update project field in all files
sed -i 's/project_id: project-temp/project_id: project-main/' \
    ~/aios-state-vault/state/project-main/*.md

# Remove old project directory
rm -rf ~/aios-state-vault/state/project-temp
rm -rf ~/aios-state-vault/decisions/project-temp

# Commit
git -C ~/aios-state-vault add -A
git -C ~/aios-state-vault commit -m "Consolidate: merge project-temp into project-main"
git -C ~/aios-state-vault push origin main
```

---

## Technical Questions

### Q: How does state management work?

**A:** Simple design (project-scoped):

```
1. Issue created on GitHub with label (e.g., pm-idea)
2. Orchestrator queries label (with AIOS_PROJECT env var)
3. State manager loads state/<project>/issue-N.md from vault
4. If missing, creates initial state
5. Orchestrator spawns agent
6. Agent makes decision
7. State manager updates state/<project>/issue-N.md
8. State manager commits to git automatically with project tag
9. Orchestrator posts [STATE UPDATE] comment on GitHub
10. Next cycle: repeat from step 3 (using updated state)
```

**Key:** Vault is source of truth (project-scoped), GitHub is audit trail.

---

### Q: What if git sync fails?

**A:** The orchestrator logs the error and continues:

- **First failure:** Logged as warning
- **Subsequent failures:** Queued for retry
- **Manual recovery:** Can manually push state changes

**Prevention:**
- Ensure git credentials configured
- Check GitHub token hasn't expired
- Verify push access to vault repo

---

### Q: Can two orchestrators conflict?

**A:** Unlikely but theoretically possible:

**Scenario:** PM and PO both try to update same issue at same time

**Resolution:**
- Git uses "last write wins"
- Orchestrator that pushes last prevails
- No data loss (git history preserves all)
- In practice: each orchestrator has different labels (pm-idea vs strategic-opportunity) so rare collision

**Mitigation:** If concerned, run orchestrators sequentially (not simultaneously) or add file locking.

---

### Q: How do feedback loops work?

**A:** Example: Design REVISE → Intake

```yaml
Stage: design-approved
Agent: design-agent
Decision: REVISE (stakeholder feedback needed)
  ↓
Routing Registry lookup:
  design-approved + REVISE → intake
  ↓
State Updated: Stage = intake
  ↓
Next Cycle:
  Orchestrator queries feature-request issues
  Finds this issue, Stage = intake
  Spawns intake-agent to recollect requirements
```

**Key:** Feedback loops are just reverse transitions defined in routing registry.

---

### Q: What happens if an agent crashes?

**A:** Graceful handling:

1. Orchestrator tries to spawn agent
2. Agent fails/times out
3. Orchestrator catches exception
4. Issue state NOT updated (stays in current stage)
5. Error logged
6. Orchestrator continues with next issue
7. Next cycle: retry same issue

**Result:** Failed agent doesn't break pipeline.

---

## Operational Questions

### Q: How do I scale to 100+ issues?

**A:** v2 is designed for scale:

**Current capacity:**
- ~1-3 issues per cycle per orchestrator
- 30s loop interval
- ~10-20 issues/hour per orchestrator
- **Total: ~50+ issues in flight simultaneously**

**If you need more:**
1. **Parallel orchestrators:** Run multiple instances (different machine)
2. **Longer loop interval:** Trade responsiveness for throughput
3. **Batch agents:** Process multiple issues in one agent call
4. **Database indexing:** Cache state for fast lookup (if >500 issues)

**We recommend:** v2 handles 100-200 issues comfortably.

---

### Q: Can I customize the pipeline?

**A:** Absolutely. v2 designed for extension:

**Add new stage:**
1. Add row to routing-registry.md
2. Create agent (or use existing)
3. Add agent to orchestrator agent_registry
4. Test end-to-end

**Add new loop:**
1. Copy dev-orchestrator-v2.agent.md
2. Change query label (e.g., "design-review" instead of "feature-request")
3. Change initial stage
4. Adjust routing for your stages
5. Deploy new orchestrator

**Example:** Could add "security-review" loop between verification and policy.

---

### Q: How do I monitor performance?

**A:** Multiple approaches:

**Option 1: Quick dashboard**
```bash
~/monitor-aios.sh  # Shows pipeline health
```

**Option 2: Git history**
```bash
git -C ~/aios-state-vault log --since="1 day ago" --oneline state/ | wc -l
# Issues processed in last day
```

**Option 3: Stage duration analysis**
```bash
# Extract stage timings from state files
grep "Completed" ~/aios-state-vault/state/*.md | grep -o "[0-9.]*h"
```

**Option 4: Metrics dashboard** (create in metrics.md)
```markdown
# Metrics
- Throughput: 15 issues/day
- Avg cycle time: 12 hours
- Bottleneck: design-approved (2h avg)
```

---

### Q: How do I test a change without affecting production?

**A:** Multiple options:

**Option 1: Shadow mode**
- Create test issue with prefix "TEST-"
- Monitor in test vault
- Compare with production after 1 cycle

**Option 2: Separate vault**
- Clone prod vault: `git clone ... test-vault`
- Point test orchestrator to test vault
- Make changes safely

**Option 3: Max cycles**
```bash
copilot-cli orchestrator.agent.md --max-cycles=1
# Process only 1 cycle to test
```

**Option 4: Debug mode**
```bash
export DEBUG=1
copilot-cli orchestrator.agent.md
# Verbose logging without production changes
```

---

## Troubleshooting Questions

### Q: Orchestrator says "No agents found"

**A:** Routing points to agent that doesn't exist.

**Fix:**
1. Check routing-registry.md for stage name
2. Verify agent exists in agent_registry
3. Check agent class name matches exactly (case-sensitive)

---

### Q: State files full of garbage characters

**A:** Likely encoding issue.

**Fix:**
```bash
# Check file encoding
file ~/aios-state-vault/state/issue-999.md

# Should say: UTF-8 text
# If not: re-encode
iconv -f ISO-8859-1 -t UTF-8 issue-999.md > issue-999-fixed.md
mv issue-999-fixed.md issue-999.md
```

---

### Q: GitHub API rate limited

**A:** You've hit GitHub's request limit.

**Limits:**
- 60 requests/hour (unauthenticated)
- 5000 requests/hour (authenticated)

**Fix:**
- Ensure GITHUB_TOKEN set (gets 5000 limit)
- Increase loop interval (query less often)
- Run fewer orchestrators
- GitHub limits reset hourly

**Check remaining:**
```bash
curl -i -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit | grep X-RateLimit
```

---

### Q: Vault repo out of disk space

**A:** State files accumulated.

**Check:**
```bash
du -sh ~/aios-state-vault
# Should be <100MB for 1000 issues
```

**Cleanup (optional):**
```bash
# Archive old decisions
tar -czf decisions-archive-$(date +%Y%m%d).tar.gz decisions/
rm -rf decisions/
mkdir decisions
```

---

## Advanced Questions

### Q: Can I integrate with Slack/email?

**A:** Yes, add post-processing:

```python
# After state update, send notification
if decision == "BLOCKED":
    slack.notify(f"Issue #{issue_id} blocked: {reasoning}")
    email.send(manager, f"Issue blocked: {issue_id}")
```

**Where to add:**
- In orchestrator after `transition_state()`
- Or in separate notification service that watches vault

---

### Q: Can I export metrics to dashboard (Grafana, etc.)?

**A:** Yes, export metrics to JSON:

```python
# In orchestrator, periodically export:
metrics = {
    'timestamp': datetime.now().isoformat(),
    'issues_in_intake': len(manager.get_all_issues_in_stage('intake')),
    'issues_in_design': len(manager.get_all_issues_in_stage('design')),
    'stuck_issues': len(manager.get_stuck_issues('design', hours=2))
}

with open('metrics.json', 'w') as f:
    json.dump(metrics, f)
```

Then ingest metrics.json into your dashboard.

---

### Q: Can I run orchestrators on different machines?

**A:** Yes, with shared vault:

**Setup:**
1. Create vault on shared storage (git repo)
2. Each machine: `git clone` vault
3. Each machine: run orchestrator
4. Orchestrators coordinate through git

**Considerations:**
- Git push/pull adds latency
- "Last write wins" for simultaneous updates
- Works fine for 100+ issues

---

### Q: Can I version orchestrator agents?

**A:** Yes, track in git:

```bash
# Version orchestrators
templates-v2/orchestration/.prompts/
├── pm-orchestrator-v2.0.agent.md
├── pm-orchestrator-v2.1.agent.md
└── pm-orchestrator-v3.0.agent.md

# Commit each version
git add pm-orchestrator-v2.1.agent.md
git commit -m "Release: pm-orchestrator v2.1 (improved error handling)"
```

---

### Q: Can I roll back a bad state change?

**A:** Yes, git makes it easy:

```bash
# View history
git -C ~/aios-state-vault log --oneline state/issue-999.md

# Revert specific commit
git -C ~/aios-state-vault revert abc123def --no-edit

# Or reset to specific state
git -C ~/aios-state-vault checkout abc123def -- state/issue-999.md
git -C ~/aios-state-vault commit -m "Rollback: issue-999 to previous state"
```

---

## Cost & Resource Questions

### Q: How much infrastructure do I need?

**A:** Minimal:

- **GitHub:** Free (public) or paid (private)
- **Vault storage:** <100MB for 1000 issues
- **Compute:** 1 small VM or laptop
- **Total monthly cost:** $0-20

**Scaling up:**
- 10,000 issues: ~1GB storage, 1 VM
- 100,000 issues: ~10GB storage, 2-3 VMs

---

### Q: What's the time investment?

**A:**

- **Setup:** 4-8 hours (one-time)
- **Operations:** <30 min/day (monitoring)
- **Maintenance:** <2 hours/week (updates, optimization)

**ROI:** Typically pays for itself in 1-2 weeks through time saved on manual orchestration.

---

## Philosophy Questions

### Q: Why Obsidian (markdown) instead of database?

**A:** Trade-offs:

**Markdown:**
- ✅ Human readable (can audit by eye)
- ✅ Version controlled (full history)
- ✅ No infrastructure (just git)
- ❌ Slower queries (<100ms vs <1ms)

**Database:**
- ✅ Fast queries
- ✅ Complex aggregations
- ❌ Requires setup/maintenance
- ❌ Less transparent

**Answer:** For 100-500 issues, markdown wins. For 10,000+, consider hybrid (markdown + cache layer).

---

### Q: Why separate orchestrators (PM, PO, Dev) instead of one?

**A:** Independent loops are better:

**Benefits:**
- ✅ Parallel execution (3 loops run simultaneously)
- ✅ Clear separation of concerns
- ✅ Easy to pause one without stopping others
- ✅ Easier to extend (add new loop)

**Alternative:** Single orchestrator with all stages. But then PM ideas would be delayed while waiting for dev issues. Independent loops solve this.

---

### Q: Why 30s loop interval?

**A:** Balance:

- **Too fast (1s):** High CPU, GitHub API rate limiting
- **Too slow (5min):** Slow response time, high latency
- **30s:** Good balance for most systems

**Adjust as needed:** `export LOOP_INTERVAL=60` for more relaxed polling.

---

## End-to-End Examples

### Example 1: Adding Security Review Stage

**Goal:** Add security-review between verification and policy

**Steps:**
1. Add to routing-registry.md:
```yaml
### verification
- PASS → security-review

### security-review  
- PASS → policy-approval
- BLOCKED → feature-blocked
```

2. Create agent: `templates/agents/security-agent.md`

3. Add to dev orchestrator:
```python
agent_registry = {
    ...
    'security-review': SecurityAgent,
    ...
}
```

4. Deploy and test with sample issue

---

### Example 2: Querying Issues by Decision

**Goal:** Find all issues that were blocked

**Query:**
```bash
grep -r '"decision": "BLOCKED"' ~/aios-state-vault/decisions/
# Shows all decision files with BLOCKED outcome
```

**Extract issue numbers:**
```bash
grep -r '"decision": "BLOCKED"' ~/aios-state-vault/decisions/ | cut -d- -f2 | sort | uniq
# List of issue IDs
```

---

### Example 3: Measuring Stage Duration

**Goal:** How long does design-approved stage take?

**Analysis:**
```bash
# For each issue, calculate time in design stage
for state_file in ~/aios-state-vault/state/*.md; do
    grep "design" "$state_file" | grep -oP '\(\K[^)]+' | head -1
done

# Extract durations and average
# e.g., (2h), (1.5h), (3h) → average 2.1h
```

---

## Support & Community

### Q: Where can I get help?

**A:** Multiple resources:

1. **Documentation:**
   - [GETTING_STARTED.md](./GETTING_STARTED.md) - Full walkthrough
   - [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues
   - [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - Commands cheat sheet

2. **Code Reference:**
   - [orchestration-loop-pattern.md](./.prompts/orchestration-loop-pattern.md) - Architecture
   - [routing-registry.md](./routing-registry.md) - Stage definitions
   - [state-manager/README.md](../state-manager/README.md) - API docs

3. **Examples:**
   - [test-sample.md](./test-sample.md) - Test fixtures
   - [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - Execution report

---

### Q: How do I report a bug?

**A:**

1. **Gather diagnostics:**
   ```bash
   ~/diagnose-aios.sh > diagnostic-report.txt
   ```

2. **Describe issue:**
   - What were you trying to do?
   - What happened?
   - What did you expect?

3. **Share:**
   - Diagnostic report
   - Error logs
   - Reproduction steps

---

### Q: Can I contribute improvements?

**A:** Absolutely! v2 is designed for extension:

**Ideas for contribution:**
- New agents (for different stage types)
- Alternative state storage backends
- Obsidian plugin for visualization
- Integration with Slack/Discord
- Performance optimizations

**Process:** Submit PR with:
- Clear description of improvement
- Testing done
- Documentation update

---

## Last Resort

### Q: Things are completely broken. Where do I start?

**A:** Follow this sequence:

1. **Run diagnostic:**
   ```bash
   ~/diagnose-aios.sh
   ```
   Check: environment, vault, git, orchestrators, GitHub API

2. **Reset vault:**
   ```bash
   cd ~/aios-state-vault
   git reset --hard origin/main
   ```

3. **Restart orchestrators:**
   ```bash
   pkill -f orchestrator-v2
   source ~/.aios-env.sh
   # Redeploy
   ```

4. **Test with single issue:**
   - Create GitHub issue with label
   - Run orchestrator for 1 cycle
   - Check state file created

5. **Check documentation:**
   - [GETTING_STARTED.md](./GETTING_STARTED.md)
   - [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

6. **Consult audit:**
   - [ORCHESTRATION_AUDIT.md](../../ORCHESTRATION_AUDIT.md)

---

## Quick Links

- 📖 [Getting Started](./GETTING_STARTED.md)
- 🔧 [Quick Reference](./QUICK_REFERENCE.md)  
- 🐛 [Troubleshooting](./TROUBLESHOOTING.md)
- 📚 [Full Documentation](./README.md)
- 🏗️ [Architecture Audit](../../ORCHESTRATION_AUDIT.md)

---

**Last Updated:** 2026-07-08

**Didn't find your answer?** Check the full documentation files or review the IMPLEMENTATION_SUMMARY.md for complete context.
