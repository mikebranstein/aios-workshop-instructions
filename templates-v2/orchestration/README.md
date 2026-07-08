# Orchestration v2: Setup & Reference

**Purpose:** Three independent orchestration loops (PM, PO, Dev) using Obsidian state management  
**Pattern:** All orchestrators follow [orchestration-loop-pattern.md](./.prompts/orchestration-loop-pattern.md)  
**Status:** Implementation ready

---

## Quick Start

### 1. Prerequisites

Create separate state vault repository:

```bash
mkdir ~/aios-state-vault
cd ~/aios-state-vault
git init
mkdir -p state decisions
echo ".obsidian/" > .gitignore
echo ".DS_Store" >> .gitignore
git add . && git commit -m "Initial: state vault structure"
git remote add origin https://github.com/YOUR-ORG/aios-state-vault
git push -u origin main
```

Open vault in Obsidian:
- Launch Obsidian
- File → Open Vault
- Select ~/aios-state-vault folder

### 2. Deploy PM Orchestrator v2

Edit `.prompts/pm-orchestrator-v2.agent.md`:
- Replace `VAULT_PATH` with your vault location
- Replace `REPO_PATH` with your vault repo location
- Set GitHub token in env vars

Run orchestrator:
```bash
copilot-cli .prompts/pm-orchestrator-v2.agent.md --autopilot
```

Monitor output:
```bash
# In another terminal
ls -la ~/aios-state-vault/state/
# Should see issue-*.md files appearing
```

### 3. Deploy PO & Dev Orchestrators

Once PM is stable, deploy PO and Dev using same pattern.

---

## File Reference

### Orchestrators

- **[pm-orchestrator-v2.agent.md](./.prompts/pm-orchestrator-v2.agent.md)**
  - Discovers opportunities (pm-idea issues)
  - Phase 1: Quick gate (product-manager agent)
  - Phase 2: Full validation (research agent)
  - Creates strategic-opportunity issues

- **[po-orchestrator-v2.agent.md](./.prompts/po-orchestrator-v2.agent.md)**
  - Prioritizes opportunities
  - Creates feature-request issues
  - Closes strategic opportunities

- **[dev-orchestrator-v2.agent.md](./.prompts/dev-orchestrator-v2.agent.md)**
  - Executes feature requests
  - Manages dev pipeline stages
  - Handles feedback loops

### Reference Documentation

- **[orchestration-loop-pattern.md](./.prompts/orchestration-loop-pattern.md)**
  - Reusable 5-step loop all orchestrators follow
  - Read this to understand orchestrator structure

- **[routing-registry.md](./routing-registry.md)**
  - All stage transitions (PM, PO, Dev)
  - Feedback loops (Design REVISE → Intake, etc.)
  - Referenced by orchestrators for routing decisions

- **[test-sample.md](./test-sample.md)**
  - Example test fixture for development

---

## State Vault Structure

**Obsidian vault lives in separate repo: `aios-state-vault/`**

```
aios-state-vault/
├── state/
│   └── issue-{N}.md           # One file per issue
│       ├── Current Stage
│       ├── Stage Entry Time
│       ├── Priority Score
│       ├── Latest Decision (JSON)
│       └── Stage History
│
├── decisions/
│   └── issue-{N}-{stage}-{timestamp}.md    # Audit trail
│       ├── Outcome
│       ├── Reasoning
│       └── Full Decision JSON
│
└── routing-registry.md        # All transitions (synced from here)
```

---

## Routing Registry (Reference)

All stage transitions defined in [routing-registry.md](./routing-registry.md):

**PM Loop Stages:**
- pm-idea → pm-validating → pm-provisional-champion → pm-finalizing → pm-opportunity

**PO Loop Stages:**
- strategic-opportunity → po-prioritizing → feature-request → (backlog)

**Dev Loop Stages:**
- feature-request → intake-approved → design-approved → build-complete → qa-passed → verification-passed → policy-approved → released

**Feedback Loops:**
- Design REVISE → Intake
- QA INCOMPLETE → Design
- Verification FAIL → Design

---

## Testing

### Test with Single Issue

1. Create test issue on GitHub: `Test Issue #999`
2. Add label: `pm-idea`
3. Run PM orchestrator

Monitor:
```bash
# Check state file created
cat ~/aios-state-vault/state/issue-999.md

# Check decision audit
ls ~/aios-state-vault/decisions/issue-999*.md

# Check GitHub comment
# (View issue #999 on GitHub, should see "[STATE UPDATE]" comment)
```

### Verify State Consistency

Once all three orchestrators running:

```bash
# All issues should have exactly one stage
grep "Stage: " ~/aios-state-vault/state/*.md

# No orphaned stages (all in routing registry)
# Git history should show atomic state transitions
git -C ~/aios-state-vault log --oneline state/ | head -20
```

---

## Troubleshooting

**State files not created?**
- Check VAULT_PATH and REPO_PATH configuration in orchestrator
- Check file permissions
- Look for errors in orchestrator stderr

**Git sync failing?**
- Verify git credentials in environment
- Check push access to aios-state-vault repo
- Verify main branch exists (not master)

**GitHub comments not posting?**
- Check GitHub token scope (issues:write required)
- Verify comment format matches pattern
- Check issue number extraction working

**Routing not progressing?**
- Verify stage names match routing-registry.md exactly (case-sensitive)
- Check agent decision output format correct
- Review feedback loop conditions

---

## Performance

**Typical Cycle Time:**
- Query GitHub: 1-2s
- Load state files: <100ms per issue
- Spawn agent: 5-10s
- Update state + git: 2-3s
- **Total: ~10-15s per issue per orchestrator**

With 30s loop interval, each orchestrator can handle ~2-3 issues per cycle.

---

## Next Steps

1. [ ] Create aios-state-vault repository
2. [ ] Configure PM orchestrator with paths
3. [ ] Run PM orchestrator, verify state files
4. [ ] Deploy PO orchestrator
5. [ ] Deploy Dev orchestrator
6. [ ] Run all three in parallel
7. [ ] Monitor metrics.md for bottlenecks
