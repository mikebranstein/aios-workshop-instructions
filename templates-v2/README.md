# Templates-v2: Orchestration Modernization

**Status:** New implementation (non-breaking, parallel with legacy templates/)  
**Date:** 2026-07-08  
**Purpose:** Clean v2 orchestration architecture with GitHub-native state management  

---

## Overview

Templates-v2 is a refactored implementation of the three-loop orchestration system (PM, PO, Dev) with these improvements:

- ✅ **GitHub as state** (issue labels + comments, no external vault)
- ✅ **Centralized routing logic** (routing-registry.md, not duplicated in 3 files)
- ✅ **Reusable orchestration pattern** (all orchestrators follow same loop)
- ✅ **Full audit trail** (GitHub comments and issue history)
- ✅ **Non-breaking** (legacy templates/ untouched, can run v1 and v2 side-by-side)

---

## Architecture

### Three Independent Loops

**PM Loop** (`pm-orchestrator-v2.agent.md`)
- Discovers opportunities (pm-idea issues)
- Validates via product-manager agent
- Creates strategic-opportunity issues

**PO Loop** (`po-orchestrator-v2.agent.md`)
- Prioritizes strategic opportunities
- Creates feature-request issues in backlog order
- Closes completed opportunities

**Dev Loop** (`dev-orchestrator-v2.agent.md`)
- Executes feature requests through pipeline
- Stages: intake → design → build → qa → policy → release
- Handles feedback loops (Design REVISE → Intake, etc.)

### State Management

All state lives in **GitHub issues**:

- **Current Stage:** Issue label (e.g., `pm-idea`, `intake`, `design`)
- **Decision History:** Issue comments posted by orchestrator
- **Audit Trail:** GitHub issue history (comments and label changes)
- **Project Scoping:** Issues tagged with project identifier in `AIOS_PROJECT`

**Simple, observable:** All state visible directly on GitHub—no external sync needed.

### Reusable Orchestration Pattern

All three orchestrators follow the same loop (see [orchestration-loop-pattern.md](orchestration/.prompts/orchestration-loop-pattern.md)):

```
1. Query GitHub for issues with specific label
2. For each unprocessed issue:
   a. Determine current stage (from issue label)
   b. Spawn specialist agent (from templates/agents/)
   c. Collect decision
   d. Update issue label to new stage
   e. Post "[DECISION]" comment to GitHub with reasoning
   f. Look up next stage in routing-registry.md
3. Sleep 30 seconds
4. Repeat
```

---

## Folder Structure

```
templates-v2/
├── README.md (this file)
│
├── orchestration/
│   ├── README.md (setup guide)
│   ├── routing-registry.md (all stage transitions declaratively)
│   ├── test-sample.md (example test fixture)
│   │
│   └── .prompts/
│       ├── orchestration-loop-pattern.md (reusable loop documentation)
│       ├── pm-orchestrator-v2.agent.md (PM loop)
│       ├── po-orchestrator-v2.agent.md (PO loop)
│       └── dev-orchestrator-v2.agent.md (Dev loop)
```

---

## Getting Started

**Setup takes ~1-2 hours:**

1. **Create environment file:**
```bash
cat > ~/.aios-env.sh << 'EOF'
export GITHUB_TOKEN=${GITHUB_TOKEN:-}    # Optional (uses Copilot auth if empty)
export GITHUB_ORG=YOUR-ORG
export GITHUB_REPO=your-repo
export AIOS_PROJECT=aios
export LOOP_INTERVAL=30
export STUCK_THRESHOLD=2
EOF
```

2. **Load and verify:**
```bash
source ~/.aios-env.sh
echo $AIOS_PROJECT  # Should show: aios
```

3. **Create test issue on GitHub with label `pm-idea`**

4. **Deploy PM orchestrator:**
```bash
copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --autopilot
```

5. **Watch issue labels update on GitHub**

---

## Full Documentation

- [GETTING_STARTED.md](GETTING_STARTED.md) - Step-by-step setup and deployment
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command reference
- [INDEX.md](INDEX.md) - Navigation guide for all docs

---

## Key Design Decisions

**GitHub-native:** All state visible on GitHub—no separate tools needed  
**Minimal setup:** Just GitHub + Copilot CLI  
**Non-breaking:** Run v1 and v2 in parallel indefinitely  
**Single loop pattern:** Reusable across PM, PO, and Dev loops

**Week 2:** Validate v2 stability
- All issues processed correctly
- State consistency verified
- All three orchestrators working

---

## Key Files Reference

- [orchestration-loop-pattern.md](orchestration/.prompts/orchestration-loop-pattern.md) - The core loop all orchestrators follow
- [routing-registry.md](orchestration/routing-registry.md) - All stage transitions
- [pm-orchestrator-v2.agent.md](orchestration/.prompts/pm-orchestrator-v2.agent.md) - PM loop implementation

---

## Differences from v1

| Concern | v1 (templates/agents/) | v2 (templates-v2/) |
|---------|-------|-------|
| **State Source** | GitHub labels (scattered) | GitHub labels + comments (centralized) |
| **Routing Logic** | Scattered in each orchestrator file | Centralized routing-registry.md |
| **Reusability** | Hard to share patterns | All follow orchestration-loop-pattern.md |
| **Audit Trail** | Comments only | Full comments + issue history |
| **Setup Complexity** | Multiple components | Just GitHub + Copilot CLI |
| **Observability** | GitHub issues only | Visible directly on GitHub |

---

## Troubleshooting

**Orchestrator not finding issues?**
- Verify issue has the correct label (`pm-idea`, `feature-request`, etc.)
- Check `GITHUB_ORG` and `GITHUB_REPO` settings
- Review orchestrator logs in terminal

**GitHub comments not posting?**
- Verify GitHub token has "issues:write" scope (or use Copilot auth)
- Check issue exists and is accessible
- Look for orchestrator errors

**Routing not working?**
- Verify stage names match routing-registry.md exactly (case-sensitive)
- Review feedback loop definitions
- Check orchestrator logs for routing errors

---

## Next Steps

1. ✅ Architecture updated (GitHub-only)
2. ⏳ Run PM orchestrator v2 end-to-end
3. ⏳ Deploy PO orchestrator v2
4. ⏳ Deploy Dev orchestrator v2
5. ⏳ Validate all three orchestrators working together
