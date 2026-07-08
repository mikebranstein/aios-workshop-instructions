# Documentation Index: AIOS v2 Complete Guide

**Complete navigation for all templates-v2 documentation**

---

## 🚀 Start Here

### New to v2? Start with one of these:

1. **[GETTING_STARTED.md](./GETTING_STARTED.md)** ⭐ **START HERE**
   - 5 phases with step-by-step instructions
   - Takes you from zero to fully deployed
   - Real commands you can copy-paste
   - Estimated time: 2-3 weeks (implementation + validation)
   - Best for: First-time setup

2. **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** 
   - One-page reference card
   - Commands, environment, common tasks
   - Print and keep handy
   - Best for: Operators & quick lookup

3. **[FAQ.md](./FAQ.md)**
   - 50+ common questions answered
   - Philosophy, technical, operational
   - Real examples and use cases
   - Best for: Understanding the why & how

---

## 📚 Complete Documentation

### Architecture & Design

- **[README.md](./README.md)** - High-level overview of v2 approach
  - GitHub-only state management
  - Architecture overview (3-loop model)
  - Non-breaking implementation strategy
  - Migration path
  - ~2000 words

### Operational Guides

- **[GETTING_STARTED.md](./GETTING_STARTED.md)** - Complete setup walkthrough
  - Phase 1: Foundation setup (environment + GitHub auth)
  - Phase 2: Deploy PM orchestrator
  - Phase 3: Deploy PO & Dev orchestrators
  - Phase 4: Testing & validation
  - Phase 5: Optimization (optional)
  - Troubleshooting for each phase

- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - Operator's cheat sheet
  - Environment setup (one-time)
  - Deploy commands (copy-paste)
  - Monitor system (real-time GitHub queries)
  - Common commands (organized by task)
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Problem solving guide
  - 7 major issue categories
  - Diagnosis steps for each
  - Multiple solutions per issue
  - Diagnostic script
  - When all else fails (GitHub troubleshooting)

### Technical Reference

- **[.prompts/orchestration-loop-pattern.md](./.prompts/orchestration-loop-pattern.md)** - Core pattern template
  - 5-step loop all orchestrators follow
  - GitHub CLI commands (not Python)
  - Error handling patterns
  - Performance notes
  - How to create new orchestrator
  - ~1500 words

- **[routing-registry.md](./routing-registry.md)** - Routing logic reference
  - PM loop stages & transitions (6 stages)
  - PO loop stages & transitions (4 stages)
  - Dev loop stages & transitions (7 stages)
  - Feedback loops (Design, QA, Verification)
  - Terminal states
  - How to add new stages

### Agents & Implementation

- **[.prompts/pm-orchestrator-v2.agent.md](./.prompts/pm-orchestrator-v2.agent.md)** - PM loop implementation
  - Discovers opportunities (pm-idea label)
  - Phase 1: Quick gate (product-manager agent)
  - Phase 2: Full validation (research agent)
  - Creates strategic-opportunity issues
  - Configuration & environment setup
  - Integration with v1 (parallel testing)
  - Error handling

- **[.prompts/po-orchestrator-v2.agent.md](./.prompts/po-orchestrator-v2.agent.md)** - PO loop implementation
  - Prioritizes opportunities
  - Sequences into backlog
  - Checks team capacity
  - Creates feature-request issues
  - Hands off to Dev loop
  - Monitoring & debugging

- **[.prompts/dev-orchestrator-v2.agent.md](./.prompts/dev-orchestrator-v2.agent.md)** - Dev loop implementation
  - Manages full dev pipeline (7 stages)
  - 6 specialist agents (intake, design, build, qa, verification, policy)
  - Feedback loop handling
  - Terminal states (released, blocked)
  - Monitoring & observability

### Summary & Reports

- **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** - Project completion report (DEPRECATED)
  - Historical record of vault-based v2
  - **See instead:** [README.md](./README.md) for current GitHub-only approach
  - **See instead:** [GETTING_STARTED.md](./GETTING_STARTED.md) for current setup

---

## 📖 Reading Paths

### Path 1: I'm New - Show Me Everything

1. Read: [README.md](./README.md) (15 min) - Understand what v2 is
2. Read: [FAQ.md](./FAQ.md) (30 min) - Answer your questions
3. Read: [GETTING_STARTED.md](./GETTING_STARTED.md) (30 min) - Learn setup
4. Do: Follow GETTING_STARTED step-by-step (4-6 hours)
5. Reference: [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - Keep handy
6. Troubleshoot: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - If stuck

**Total Time:** 2-3 weeks (including hands-on deployment)

---

### Path 2: I'm an Operator - Get Me Running

1. Read: [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) (10 min) - Commands overview
2. Read: [GETTING_STARTED.md](./GETTING_STARTED.md) Phase 1-2 (20 min) - Setup steps
3. Do: Follow Phase 1-2 instructions (4-6 hours)
4. Reference: [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - For daily ops
5. Monitor: [README.md](./orchestration/README.md) - Monitoring section
6. Troubleshoot: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - If issues

**Total Time:** 1 week to fully operational

---

### Path 3: I'm a Developer - Show Me Architecture

1. Read: [ORCHESTRATION_AUDIT.md](../../ORCHESTRATION_AUDIT.md) (45 min) - Full audit
2. Read: [.prompts/orchestration-loop-pattern.md](./.prompts/orchestration-loop-pattern.md) (30 min) - Core pattern
3. Read: [routing-registry.md](./routing-registry.md) (20 min) - Routing logic
4. Read: [state-manager/README.md](./state-manager/README.md) (20 min) - State API
5. Study: [.prompts/dev-orchestrator-v2.agent.md](./.prompts/dev-orchestrator-v2.agent.md) - Example implementation
6. Reference: [state-manager/state_manager.py](./state-manager/state_manager.py) - Code reference

**Total Time:** 3 hours to understand architecture

---

### Path 4: I Want to Extend - Show Me How

1. Read: [.prompts/orchestration-loop-pattern.md](./.prompts/orchestration-loop-pattern.md) - Pattern to follow
2. Read: [routing-registry.md](./routing-registry.md) - How to add stages
3. Study: [.prompts/pm-orchestrator-v2.agent.md](./.prompts/pm-orchestrator-v2.agent.md) - Reference implementation
4. Read: [state-manager/README.md](./state-manager/README.md) - State API usage
5. Reference: [FAQ.md](./FAQ.md#example-1-adding-security-review-stage) - Adding new stage example

**Total Time:** 4-6 hours to implement custom stage/loop

---

### Path 5: Something's Broken - Fix It

1. Run: [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - Diagnostic script
2. Read: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Find your issue
3. Follow: Solution steps for your issue
4. Reference: [FAQ.md](./FAQ.md#last-resort) - Last resort procedures

**Total Time:** 15 min to 1 hour (depending on severity)

---

## 🗂️ File Structure

```
templates-v2/
├── README.md                          (High-level overview)
├── GETTING_STARTED.md                 (Complete setup guide)
├── QUICK_REFERENCE.md                 (One-page cheat sheet)
├── TROUBLESHOOTING.md                 (Problem solving)
├── FAQ.md                             (Common questions)
├── IMPLEMENTATION_SUMMARY.md          (Historical - vault-based v2)
├── INDEX.md                           (This file)
│
└── orchestration/
    ├── README.md                      (Setup & monitoring)
    ├── routing-registry.md            (Stage transitions)
    └── .prompts/
        ├── orchestration-loop-pattern.md    (Core pattern)
        ├── pm-orchestrator-v2.agent.md      (PM loop)
        ├── po-orchestrator-v2.agent.md      (PO loop)
        └── dev-orchestrator-v2.agent.md     (Dev loop)
```

**Total Documentation:** 10 files, ~4000 lines (GitHub-only)

---

## 🎯 Quick Navigation by Topic

### GitHub-Only State Management
- Overview: [README.md](./README.md#state-management)
- Setup: [GETTING_STARTED.md](./GETTING_STARTED.md#phase-1-foundation)
- Quick reference: [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)

### Orchestrators
- Overview: [README.md](./README.md#architecture)
- Pattern: [.prompts/orchestration-loop-pattern.md](./.prompts/orchestration-loop-pattern.md)
- PM: [.prompts/pm-orchestrator-v2.agent.md](./.prompts/pm-orchestrator-v2.agent.md)
- PO: [.prompts/po-orchestrator-v2.agent.md](./.prompts/po-orchestrator-v2.agent.md)
- Dev: [.prompts/dev-orchestrator-v2.agent.md](./.prompts/dev-orchestrator-v2.agent.md)

### Routing & Stages
- All transitions: [routing-registry.md](./routing-registry.md)
- How to extend: [FAQ.md](./FAQ.md#can-i-add-new-stages)
- Feedback loops: [routing-registry.md](./routing-registry.md#feedback-loops-cross-stage-transitions)

### Deployment & Operations
- Step-by-step: [GETTING_STARTED.md](./GETTING_STARTED.md)
- Quick commands: [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)
- Monitoring: [GETTING_STARTED.md](./GETTING_STARTED.md#step-24-github-issue-metrics-dashboard)

### Testing & Validation
- Validation checklist: [GETTING_STARTED.md](./GETTING_STARTED.md#step-21-validation-checklist)
- End-to-end test: [GETTING_STARTED.md](./GETTING_STARTED.md#validation-end-to-end-test)

### Troubleshooting
- Common issues: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- FAQ: [FAQ.md](./FAQ.md)
- Quick reference: [QUICK_REFERENCE.md](./QUICK_REFERENCE.md#emergency-procedures)

### Extending & Customizing
- Adding new stage: [FAQ.md](./FAQ.md#example-1-adding-security-review-stage)
- Adding new loop: [FAQ.md](./FAQ.md#q-can-i-customize-the-pipeline)
- Integration: [FAQ.md](./FAQ.md#q-can-i-integrate-with-slackemail)

---

## 📊 Document Statistics

| Document | Type | Lines | Purpose |
|----------|------|-------|---------|
| README.md | Overview | 250 | High-level intro to v2 |
| GETTING_STARTED.md | Guide | 1200 | Complete 5-phase setup |
| QUICK_REFERENCE.md | Reference | 300 | One-page cheat sheet |
| TROUBLESHOOTING.md | Guide | 600 | Problem solving |
| FAQ.md | FAQ | 700 | Common questions |
| IMPLEMENTATION_SUMMARY.md | Report | 250 | Execution summary |
| orchestration-loop-pattern.md | Technical | 400 | Core pattern |
| routing-registry.md | Reference | 350 | All transitions |
| pm-orchestrator-v2.agent.md | Code | 150 | PM loop |
| po-orchestrator-v2.agent.md | Code | 150 | PO loop |
| dev-orchestrator-v2.agent.md | Code | 200 | Dev loop |
| state-manager/README.md | API | 200 | State API docs |
| state-manager/state_manager.py | Code | 450 | Python implementation |
| test-sample.md | Examples | 300 | Test fixtures |
| orchestration/README.md | Setup | 200 | Orchestration setup |
| **TOTAL** | | **7300** | **Complete system** |

---

## 🔗 Cross-References

### By Use Case

**"I want to deploy v2"**
→ [GETTING_STARTED.md](./GETTING_STARTED.md) Phase 1-2

**"I want to understand v2"**
→ [README.md](./README.md) then [ORCHESTRATION_AUDIT.md](../../ORCHESTRATION_AUDIT.md)

**"I want quick commands"**
→ [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)

**"I'm stuck"**
→ [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

**"I have a question"**
→ [FAQ.md](./FAQ.md)

**"I want to extend v2"**
→ [.prompts/orchestration-loop-pattern.md](./.prompts/orchestration-loop-pattern.md) then [routing-registry.md](./routing-registry.md)

**"I want to test"**
→ [test-sample.md](./test-sample.md)

---

## ⚡ Quick Access

### Commands
```bash
# Setup (first time)
source ~/.aios-env.sh

# Deploy
copilot-cli templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md --autopilot

# Monitor
~/monitor-aios.sh

# Troubleshoot
~/diagnose-aios.sh
```

### Documentation
```bash
# View documentation
cat templates-v2/README.md           # Overview
cat templates-v2/GETTING_STARTED.md  # Setup guide
cat templates-v2/QUICK_REFERENCE.md  # Commands
cat templates-v2/FAQ.md              # Questions
```

---

## 📞 Support

**Need help?**

1. Check [FAQ.md](./FAQ.md) - 50+ questions answered
2. Review [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Diagnosis guide
3. Read [GETTING_STARTED.md](./GETTING_STARTED.md) - Step-by-step setup
4. Check [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - Commands

**Still stuck?**
→ Run diagnostic script and review logs

---

## 🎓 Learning Path Recommendation

**For everyone:**
1. Read [README.md](./README.md) (15 min)
2. Skim [GETTING_STARTED.md](./GETTING_STARTED.md) Phase 1 (10 min)

**For operators:**
- Continue with [GETTING_STARTED.md](./GETTING_STARTED.md) Phases 2-3
- Bookmark [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)

**For developers:**
- Read [ORCHESTRATION_AUDIT.md](../../ORCHESTRATION_AUDIT.md)
- Study [.prompts/orchestration-loop-pattern.md](./.prompts/orchestration-loop-pattern.md)

**For architects/leads:**
- Read [README.md](./README.md)
- Deep dive: [ORCHESTRATION_AUDIT.md](../../ORCHESTRATION_AUDIT.md)
- Review: [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)

---

**Version:** 1.0  
**Last Updated:** 2026-07-08  
**Status:** Complete, ready for deployment

**Next Step:** Start with [GETTING_STARTED.md](./GETTING_STARTED.md)
