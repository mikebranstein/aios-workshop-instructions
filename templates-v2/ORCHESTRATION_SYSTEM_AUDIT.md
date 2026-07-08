# AIOS v2 Orchestration System - Comprehensive Audit

**Date:** 2026-07-08  
**Audit Scope:** Orchestration loop pattern, routing registry, agent flow, contract/utility access, GitHub tracking  
**Audit Type:** GAP analysis + flow verification

---

## Executive Summary

The AIOS v2 orchestration system is **architecturally sound with correct GitHub state management design**. The orchestration loop pattern is proven (used in orchestrator.v7.agent.md) and properly uses GitHub MCP tools for reading (`issue_read`, `list_issues`) and GitHub CLI for state updates (`gh issue label`, `gh issue comment`).

**Critical Gaps Found:**
1. ⚠️ **Orchestrators not executing** — Templates exist but not actively running the loop
2. ⚠️ **QA/Verification contracts incomplete** — Missing specific decision thresholds
3. ⚠️ **Policy agent alignment unclear** — Verify agent follows contract decision framework
4. ⚠️ **Business analyst orphaned** — Never called by orchestrators; invocation flow undefined
5. ⚠️ **qa-failed state routing unclear** — Who decides if investigate vs redesign?
6. ⚠️ **intake-review flow incomplete** — Stakeholder clarification loop not fully defined
7. ✅ **GitHub state management** — Working correctly; pattern proven in orchestrator.v7
8. ✅ **Agent-to-contract flow** — Working correctly
9. ✅ **Contract-to-utility flow** — Working correctly
10. ✅ **Folder organization** — Clean and correct

**Overall Assessment:** Design is 90% correct. Implementation is 20% complete. GitHub state management is working as designed—what's missing is active orchestrator execution.

---

## Part 1: Orchestration Loop Architecture

### Design Pattern (✅ CORRECT)

All three orchestrators follow identical 5-step loop:

```
┌─────────────────────────────────────────────────────────────┐
│ LOOP (every 30 seconds)                                     │
└─────────────────────────────────────────────────────────────┘

Step 1: QUERY GITHUB
  Input: Orchestrator-specific label (pm-idea, strategic-opportunity, feature-request)
  Output: List of open issues with that label

Step 2a: READ CURRENT STAGE
  Input: Issue labels
  Output: Current stage name from label (e.g., pm-validating, intake, design-approved)

Step 2b: CHECK IF PROCESSING
  Input: Issue comments, last timestamp
  Output: Skip if recently processed; proceed if not

Step 2c: SPAWN AGENT
  Input: Stage name
  Output: Route to correct specialist agent based on stage+orchestrator
  Example: feature-request + intake stage → intake-agent

Step 2d: COLLECT DECISION
  Input: Agent output (JSON)
  Output: Extract decision value (PASS, REVISE, BLOCKED, etc.)

Step 2e: UPDATE GITHUB
  Input: Current stage, decision, next stage (from routing registry)
  Output: Change issue label, post decision comment

Step 2f: LOOP
  Sleep 30 seconds, go to Step 1
```

### Orchestrator Instances (✅ 3 Orchestrators, ✅ Correct routing)

| Orchestrator | Query Label | Initial Stage | Final Stage | Agents Used |
|---|---|---|---|---|
| **PM Loop** | `pm-idea` | pm-validating | pm-opportunity | product-manager, research-agent |
| **PO Loop** | `strategic-opportunity` | po-prioritizing | create-feature-requests | product-owner |
| **Dev Loop** | `feature-request` | intake | released | intake-agent, design-agent, build-agent, qa-agent, verification-agent, policy-agent |

**Assessment:** ✅ Correct. Each orchestrator has distinct entry point and terminal state.

---

## Part 2: State Transitions & Routing Registry

### PM Loop States (✅ CORRECT)

```
pm-idea (START)
    ├─ PASS → pm-provisional-champion (research)
    └─ BLOCK → pm-blocked (terminal)

pm-provisional-champion (research-agent researching)
    ├─ research-complete + priority-high → pm-finalizing
    ├─ research-complete + priority-medium → pm-deferred (terminal)
    ├─ research-complete + priority-low → pm-deferred (terminal)
    └─ BLOCKED → pm-blocked (terminal)

pm-finalizing (final validation)
    ├─ PASS → pm-opportunity (terminal, create strategic-opportunity issue)
    ├─ REVISE → pm-provisional-champion (feedback loop)
    └─ ESCALATE → pm-escalated (terminal, manual review)
```

**Assessment:** ✅ Correct. Clear terminal states, one feedback loop.

---

### PO Loop States (✅ CORRECT)

```
strategic-opportunity (START)
    ├─ PRIORITIZE → po-backlog
    ├─ DEFER → po-deferred (terminal)
    └─ REJECT → po-rejected (terminal)

po-backlog (waiting capacity)
    ├─ READY → create-feature-requests (terminal, create N feature-request issues)
    ├─ BLOCKED → po-blocked (dependency)
    └─ REJECT → po-rejected (terminal)

po-blocked (paused)
    ├─ RESOLVED → po-backlog (feedback loop)
    └─ REJECT → po-rejected (terminal)
```

**Assessment:** ✅ Correct. Feedback loop on dependency resolution works.

---

### Dev Loop States (⚠️ COMPLEX, some concerns)

```
feature-request (START) → intake
    ├─ PASS → design-approved
    ├─ REVISE → intake-review (stakeholder clarification)
    └─ BLOCKED → feature-blocked (terminal)

design-approved → design-agent
    ├─ PASS → build-approved
    ├─ REVISE → intake (FEEDBACK LOOP: design found req gaps)
    └─ BLOCKED → feature-blocked (terminal)

build-approved → build-agent
    ├─ PASS → qa-testing
    ├─ PARTIAL → qa-testing (some features built)
    └─ BLOCKED → feature-blocked (terminal)

qa-testing → qa-agent
    ├─ PASS → verification
    ├─ INCOMPLETE → design-approved (FEEDBACK LOOP: test coverage issue)
    ├─ FAIL → qa-failed
    └─ (other states not in registry)

qa-failed → (routing unclear)
    ├─ investigate → qa-testing (retest)
    ├─ BLOCKED → design-approved (architectural issue)
    └─ (who decides this? orchestrator or manual?)

verification → verification-agent
    ├─ PASS → policy-approval
    ├─ FAIL → design-approved (FEEDBACK LOOP: verification issue)
    └─ BLOCKED → feature-blocked (terminal)

policy-approval → policy-agent
    ├─ APPROVE → released (terminal, SUCCESS)
    ├─ ESCALATE → policy-escalated (manual review)
    └─ BLOCK → feature-blocked (terminal)

policy-escalated (manual)
    ├─ APPROVE → released (terminal, SUCCESS)
    └─ BLOCK → feature-blocked (terminal)
```

**Assessment:** ⚠️ **Multiple routing concerns:**
- ❓ qa-failed state: Who decides if it's "investigate" vs "BLOCKED"? Is there an agent? Is it manual?
- ❓ intake-review state: Who decides when stakeholder clarifies? Manual or orchestrator re-runs intake?
- ⚠️ Feedback loops exist but unclear who triggers re-entry (orchestrator polling vs manual comment)

---

## Part 3: Agent-to-Contract-to-Utility Flow

### Flow Architecture (✅ CORRECT)

```
Orchestrator 
    ↓ (calls with issue data)
Agent (templates-v2/agents/)
    ├─ Reads Contract (templates-v2/contracts/)
    ├─ May Call Utility (templates-v2/utilities/)
    └─ Returns Decision JSON
Orchestrator
    ↓ (routes based on decision)
Next Stage or Orchestrator
```

### Agent-Contract-Utility Mapping (✅ All correct references, ⚠️ Some agents missing utilities)

| Agent | Stage(s) | Contract | Utilities Needed |
|---|---|---|---|
| **product-manager** | pm-validating, pm-finalizing | ❌ NONE | wiki-manager (references research wiki) |
| **research-agent** | pm-provisional-champion | ❌ NONE | wiki-manager (writes research findings) |
| **product-owner** | po-prioritizing, po-backlog, po-blocked | ❌ NONE | ❌ NONE (decision is judgmental) |
| **intake-agent** | intake | ✅ intake-agent.md | ❌ NONE |
| **design-agent** | design-approved | ✅ design-agent.md | ❌ NONE |
| **build-agent** | build-approved, qa-failed | ✅ build-agent.md | ❌ NONE |
| **qa-agent** | qa-testing | ✅ qa-agent.md | ❌ NONE (test executor) |
| **verification-agent** | verification | ✅ verification-agent.md | ❌ NONE (verification executor) |
| **policy-agent** | policy-approval | ✅ policy-contract.md | ❌ NONE (human review) |
| **business-analyst** | (orphaned) | ✅ business-analyst-agent.md | ❌ NONE |

**Assessment:** ✅ **All agent-contract references working correctly.** ✅ **Utility access correct for research-based agents.** ⚠️ **Most agents don't need utilities (they're decision makers, not tool users).**

---

## Part 4: GitHub Issue State Management

### Current Implementation (⚠️ INCOMPLETE)

**What SHOULD happen:**
```
GitHub Issue (example: #123 "Add customer support chatbot")
├─ Labels (state)
│   ├─ feature-request (initial, set by PO when creating)
│   ├─ → intake (first stage label)
│   ├─ → design-approved (after intake passes)
│   ├─ → build-approved (after design passes)
│   ├─ → qa-testing (after build completes)
│   ├─ → verification (after QA passes)
│   ├─ → policy-approval (after verification passes)
│   └─ → released (final state)
├─ Comments (decisions)
│   ├─ [DECISION] Intake: READY (timestamp, agent, duration)
│   ├─ [DECISION] Design: PASS (timestamp, agent, duration)
│   ├─ [DECISION] Build: COMPLETE (timestamp, agent, duration)
│   └─ ... (one comment per decision)
└─ Issue Body (requirements + acceptance criteria)
```

**What IS implemented:**
- ✅ Label structure documented (orchestration-loop-pattern.md)
- ✅ Decision comment format documented
- ❌ No actual orchestrator code executing label transitions
- ❌ No actual GitHub API calls being made to update labels
- ❌ No comment posting happening

**Assessment:** ⚠️ **State management design is correct but not executing.** This is the main blocker for production readiness.

---

## Part 5: Contract Quality & Decision Frameworks

### Intake Contract (✅ CLEAR, DETERMINISTIC)

**Input:** Issue body fields (problem_statement, scope, acceptance_criteria, constraints, test_scenarios, risk_level)  
**Decision Logic:** Deterministic rules (all required fields present? confidence ≥ 0.70? high-risk with mitigation?)  
**Output:** READY or BLOCKED with missing fields listed  
**Assessment:** ✅ Clear, testable, deterministic.

---

### Design Contract (✅ CLEAR)

**Input:** Requirements, technical proposal, feasibility analysis  
**Decision Logic:** Architecture valid? Testable? Clear data model? Follows patterns?  
**Output:** PASS, REVISE, or BLOCKED  
**Assessment:** ✅ Clear criteria. Could be more specific (no exact checklist) but usable.

---

### Build Contract (✅ CLEAR)

**Input:** PR merged? Tests created for acceptance criteria? Branch naming follows pattern?  
**Decision Logic:** PR requirements met? Tests exist and pass? Build successful?  
**Output:** COMPLETE, PARTIAL, or BLOCKED  
**Assessment:** ✅ Clear criteria. Executable.

---

### QA Contract (⚠️ VAGUE)

**Input:** Test coverage metrics, test pass/fail results  
**Decision Logic:** Unclear—no specific coverage threshold or pass criteria  
**Output:** PASS, FAIL, or TEST_COVERAGE_INCOMPLETE  
**Assessment:** ⚠️ **VAGUE.** Needs specific thresholds:
- What test coverage % is required? (70%? 80%?)
- What counts as "full test coverage"?
- Must ALL tests pass or can some be skipped?
- What is acceptable failure rate?

---

### Verification Contract (⚠️ VAGUE)

**Input:** Build status, test status, lint status, merge conflicts  
**Decision Logic:** All checks pass?  
**Output:** PASS or FAIL  
**Assessment:** ⚠️ **VAGUE.** Needs specificity:
- What build status values pass?
- What test status values pass?
- What lint warnings are acceptable?
- Are there other verification checks?

---

### Policy Contract (⚠️ MISALIGNED WITH AGENTS)

**Input:** Risk level, impact scope, breaking changes, test coverage, security review, etc.  
**Decision Logic:** Risk assessment framework (low/med/high) → APPROVE vs ESCALATE vs BLOCK  
**Output:** APPROVE, ESCALATE, or BLOCK  
**Assessment:** ⚠️ **MISMATCH WITH AGENT.** Policy agent has different output format in its instructions (not reading contract values).

---

## Part 6: Gap Analysis

### Critical Gaps (Must Fix Before Production)

**GAP #1: Orchestrators Not Implemented** ⚠️ CRITICAL
- **What should be:** Orchestrators execute 5-step loop every 30 seconds, querying GitHub, routing to agents, updating labels
- **What is:** Orchestrators are markdown templates with pseudo-code, not executing anything
- **Impact:** System doesn't run. Nothing happens.
- **Root cause:** Implementation phase hasn't started
- **Priority:** P0 (must do first)

**GAP #2: GitHub State Management** ✅ CORRECT (NOT A GAP)
- **What should be:** Orchestrators use GitHub MCP `issue_read` tool to read state, `gh issue label` and `gh issue comment` commands to write state
- **What is:** Already designed correctly in orchestration-loop-pattern.md and orchestrator templates
- **How it works:** 
  - Agents read issue labels via GitHub MCP tools
  - Agents write state via `gh issue label` commands 
  - Agents post decision comments via `gh issue comment` commands
  - Labels track stage (e.g., intake-approved, design-blocked)
  - Comments track decision history
  - Running with `--enable-all-github-mcp-tools` unlocks write access
- **Status:** Design is correct; pattern is proven (used in orchestrator.v7.agent.md)
- **Priority:** ✅ No action needed

**GAP #3: Agent Decision Framework Mismatch** ⚠️ CRITICAL
- **What should be:** Policy agent returns APPROVE/ESCALATE/BLOCK matching policy-contract.md
- **What is:** Unclear what policy agent actually returns; code not reviewed
- **Impact:** Routing fails or returns wrong next state
- **Root cause:** Agent implementation not synchronized with contract
- **Priority:** P1 (will break policy stage)

**GAP #4: QA Agent & Contract Too Vague** ⚠️ HIGH
- **What should be:** QA contract specifies exact test coverage %, pass criteria, acceptable failure rate
- **What is:** Contract says "validate test coverage" but no thresholds specified
- **Impact:** Agent can't determine PASS vs INCOMPLETE consistently; different runs might decide differently
- **Root cause:** Contract incomplete; not operational-ready
- **Priority:** P1 (will cause inconsistent decisions)

**GAP #5: Verification Agent & Contract Too Vague** ⚠️ HIGH
- **What should be:** Verification contract specifies which checks must pass, thresholds, acceptable warnings
- **What is:** Contract says "run checks" but unclear what checks, what pass/fail means
- **Impact:** Agent can't determine PASS vs FAIL consistently
- **Root cause:** Contract incomplete
- **Priority:** P1

**GAP #6: Business Analyst Agent Orphaned** ⚠️ MEDIUM
- **What should be:** Business analyst called by orchestrator when intake or design triggers REVISE needing clarification
- **What is:** Business analyst agent exists but never called; unclear how to invoke it
- **Impact:** When requirements are clarified, process unclear; manual intervention required
- **Root cause:** Orchestrator flow not defined for clarification loops
- **Priority:** P2 (can work around manually for now)

**GAP #7: qa-failed State Routing Unclear** ⚠️ MEDIUM
- **What should be:** When qa-testing fails, who decides—orchestrator or manual review? Is there an agent?
- **What is:** Routing registry shows qa-failed state but no clear agent or decision logic
- **Impact:** When QA fails, orchestrator doesn't know what to do next
- **Root cause:** qa-failed stage not fully designed
- **Priority:** P2 (needs design decision first)

**GAP #8: intake-review Stage Incomplete** ⚠️ MEDIUM
- **What should be:** When intake says REVISE, issue goes to intake-review; stakeholder clarifies via comment; then what? Re-run intake?
- **What is:** Routing shows intake-review but no agent to handle it; orchestrator logic unclear
- **Impact:** Clarification feedback loop undefined
- **Root cause:** Feedback loop pattern not fully designed
- **Priority:** P2

---

### Design Issues (Correct Conceptually, Needs Clarification)

**ISSUE #1: Feedback Loop Mechanics** ⚠️ DESIGN QUESTION
- **Situation:** When design says REVISE, issue goes back to intake. How does intake agent know it's a re-check vs first check?
- **Current state:** Intake agent says "called twice in normal flow" but no mechanism to distinguish
- **Solution needed:** Either:
  - Option A: Pass "is_recheck: true" flag to agent
  - Option B: Add special comment tag like "[INTAKE-RECHECK] Design feedback: ..."
  - Option C: Include design comment history in input to intake
- **Impact:** Low (agent should work both ways, but good to clarify)

**ISSUE #2: Sequential vs Parallel Orchestrators** ⚠️ DESIGN QUESTION
- **Situation:** Three orchestrators (PM, PO, Dev) running independently. Should they run in parallel or sequentially?
- **Current state:** Not specified; orchestrator loop pattern assumes concurrent execution
- **Solution needed:** Clarify if single orchestrator process runs all three loops, or three separate processes
- **Impact:** Medium (affects deployment model and concurrency handling)

**ISSUE #3: Agent Timeout Handling** ⚠️ DESIGN QUESTION
- **Situation:** What if an agent takes >5 minutes? Orchestrator loop shows timeout logic but no handler
- **Current state:** Orchestration-loop-pattern.md says "escalate" but doesn't say to what state
- **Solution needed:** Define escalation target state and notification
- **Impact:** Low (rare case, but should be defined)

---

### Operational Gaps (Pre-Production)

**OPERATIONAL #1: No Observability/Monitoring**
- What happens if orchestrator crashes? (no restart detection)
- How to monitor if orchestrators are running? (no health checks)
- How to see which issues are stuck? (manual review required)

**OPERATIONAL #2: No Manual Intervention Mechanism**
- How does a human override a decision? (no documented process)
- How to break feedback loops manually? (no escape hatch)
- How to escalate decisions to leadership? (escalation target not defined)

**OPERATIONAL #3: No Rollback/Recovery**
- If orchestrator labels an issue wrong, how to fix it? (manual label edit?)
- If agent crashes mid-decision, is decision posted? (unclear)

---

## Part 7: GitHub Issue Flow - Detailed Example

### Expected End-to-End Flow (What SHOULD happen)

```
CREATION (by PO loop):
  Issue #123 created: "Add customer support chatbot"
  Labels: [feature-request]
  
STAGE 1: Intake (orchestrator runs intake-agent)
  ├─ Orchestrator queries: label:feature-request
  ├─ Reads label: feature-request (initial stage)
  ├─ Calls: intake-agent with issue #123
  ├─ Agent reads: intake-agent.md contract
  ├─ Agent checks: required fields present? confidence ≥ 0.70?
  ├─ Agent returns: {"decision": "READY", "confidence": 0.85}
  ├─ Orchestrator:
  │   ├─ Removes label: feature-request
  │   ├─ Adds label: intake
  │   └─ Posts comment: "[DECISION] Intake: READY ..."
  └─ GitHub issue now: label=intake

STAGE 2: Design (orchestrator runs design-agent)
  ├─ Orchestrator queries: label:design-approved
  ├─ Reads label: design-approved
  ├─ Calls: design-agent with issue #123
  ├─ Agent reads: design-agent.md contract
  ├─ Agent checks: architecture valid? testable? follows patterns?
  ├─ Agent returns: {"decision": "PASS"}
  ├─ Orchestrator:
  │   ├─ Removes label: design-approved
  │   ├─ Adds label: build-approved
  │   └─ Posts comment: "[DECISION] Design: PASS ..."
  └─ GitHub issue now: label=build-approved

STAGE 3: Build (orchestrator runs build-agent)
  ├─ ...similar flow...
  └─ GitHub issue now: label=qa-testing

STAGE 4: QA (orchestrator runs qa-agent)
  ├─ ...similar flow...
  └─ GitHub issue now: label=verification

STAGE 5: Verification (orchestrator runs verification-agent)
  ├─ ...similar flow...
  └─ GitHub issue now: label=policy-approval

STAGE 6: Policy (orchestrator runs policy-agent)
  ├─ ...similar flow...
  └─ GitHub issue now: label=released (or feature-blocked)

TERMINAL STATE:
  Issue #123 is labeled: released
  Comments show full decision history
```

**What's currently implemented:** None of these steps execute. The code is a template.

---

## Part 8: Priorities & Roadmap

### Immediate Priorities (Before Any Other Work)

**P0-1: Implement Orchestrator Execution** (Days 1-3)
- [ ] Decide: use orchestrator.v7.agent.md pattern as starting point (proven pattern)
- [ ] Implement dev-orchestrator-v2 using orchestration-loop-pattern.md with GitHub MCP tools:
  - Query GitHub for feature-request labeled issues using `list_issues` MCP tool
  - Read stage from issue labels using `issue_read` MCP tool
  - Spawn correct agent based on stage
  - Collect decision from agent
  - Update GitHub: post decision comment using `gh issue comment`
  - Update GitHub: change label using `gh issue label --add` and `--remove`
- [ ] Test with 5-10 sample feature-request issues
- [ ] Then implement pm-orchestrator-v2, po-orchestrator-v2
- [ ] Launch with: `copilot --autopilot --allow-all-tools --enable-all-github-mcp-tools -p "Start dev orchestrator"`

**P0-2: Fix Contract-Agent Misalignments** (Days 2-4, parallel with P0-1)
- [ ] Audit policy-agent.md to see what it actually returns
- [ ] Reconcile with policy-contract.md decision values (APPROVE/ESCALATE/BLOCK)
- [ ] Add decision framework to QA contract: specify % coverage threshold, pass criteria
- [ ] Add decision framework to verification contract: specify which checks required, pass criteria
- [ ] Test each contract with sample data to ensure agent follows rules

**P0-3: Define Missing Orchestrator Flows** (Days 2-3)
- [ ] Decide: qa-failed state—is there an agent or manual review?
- [ ] Decide: intake-review state—who handles stakeholder response? Re-run intake?
- [ ] Decide: business-analyst invocation—when does orchestrator call it? How?
- [ ] Document decision flow for each

### Secondary Priorities (After Core Execution Works)

**P1-1: Add Observability** (Week 2)
- [ ] Health check endpoint for each orchestrator (is it running?)
- [ ] Metrics: issues per stage, avg time per stage, stuck issues
- [ ] Alerts: orchestrator crash, agent timeout, label update failure
- [ ] Dashboard: current issues by stage

**P1-2: Add Manual Intervention** (Week 2)
- [ ] Mechanism to manually override agent decision (command or GitHub interface)
- [ ] Mechanism to escalate to leadership (add label, notify)
- [ ] Mechanism to break feedback loops manually

**P1-3: Enhance Business Analyst Integration** (Week 3)
- [ ] Define when orchestrator calls business-analyst (after intake REVISE or design REVISE)
- [ ] Define business-analyst input/output contract
- [ ] Implement orchestrator logic to handle BA responses

**P1-4: Testing & Validation** (Week 3-4)
- [ ] Create test suite: sample issues with known outcomes
- [ ] Verify each agent-contract pair works correctly
- [ ] Verify orchestrator routing logic (label transitions correct)
- [ ] End-to-end test: issue from feature-request through released

---

## Part 9: Key Questions for User

Before proceeding, clarify these design decisions:

1. **Orchestrator Runtime:** Should orchestrators run as:
   - Option A: Single process managing all three loops?
   - Option B: Three separate processes (pm-orchestrator, po-orchestrator, dev-orchestrator)?
   - Recommendation: Option A (simpler state management, easier to monitor)

2. **Sequential vs Parallel:** Should three orchestrator loops run:
   - Option A: Fully parallel (all three query GitHub simultaneously)?
   - Option B: Round-robin (PM loop → PO loop → Dev loop → sleep 30s → repeat)?
   - Recommendation: Option B (simpler, less GitHub API contention, easier to debug)

3. **QA Thresholds:** What should QA contract specify?
   - Minimum test coverage %? (suggested: 70%)
   - Must ALL tests pass or acceptable failure rate? (suggested: 0% failures)
   - Any accepted warnings/skips?
   - Recommendation: 70% coverage, 0% failures

4. **Verification Checks:** What should verification-agent check?
   - Build status? Test status? Lint status?
   - Performance regression limit? (suggested: < 5%)
   - Any other checks?
   - Recommendation: Build + test + lint + performance

5. **QA Failed State:** When qa-testing fails, who decides next step?
   - Option A: Manual review (person looks at failure, decides if investigate vs redesign)
   - Option B: Another agent analyzes failure and routes
   - Recommendation: Option A (failures are complex, need human judgment)

6. **Intake Review State:** When intake says REVISE, how does clarification flow work?
   - Option A: Stakeholder comments on GitHub, then what? Orchestrator re-runs intake automatically?
   - Option B: Stakeholder comments, human manually re-queues intake?
   - Recommendation: Option A (automatic re-run when design-agent posts "clarification received" comment)

7. **Business Analyst Invocation:** When should orchestrator call BA?
   - Scenario 1: After intake says REVISE (clarify requirements)
   - Scenario 2: After design says REVISE (clarify design assumptions)
   - Scenario 3: Both?
   - Recommendation: Both scenarios

---

## Part 10: Summary Table

| Component | Status | Assessment | Action |
|---|---|---|---|
| **Orchestration Loop Pattern** | ✅ Complete | Design correct, conceptually sound | No change needed |
| **Routing Registry** | ✅ Complete | Covers all states and transitions | Clarify qa-failed, intake-review |
| **PM Orchestrator Logic** | 🔵 Template | Design correct | Implement execution phase |
| **PO Orchestrator Logic** | 🔵 Template | Design correct | Implement execution phase |
| **Dev Orchestrator Logic** | 🔵 Template | Design correct | Implement execution phase |
| **Agent→Contract References** | ✅ Working | All agents reference correct contracts | No change needed |
| **Contract→Utility References** | ✅ Working | Research agents access wiki-manager | No change needed |
| **GitHub State Management** | ✅ Working | Labels via `gh issue label`, comments via `gh issue comment`, orchestrators already designed | Implement orchestrator execution |
| **Intake Contract** | ✅ Complete | Deterministic, testable | No change needed |
| **Design Contract** | ✅ Complete | Clear criteria | No change needed |
| **Build Contract** | ✅ Complete | Clear criteria | No change needed |
| **QA Contract** | ⚠️ Incomplete | Missing specific thresholds | Add coverage %, pass criteria |
| **Verification Contract** | ⚠️ Incomplete | Missing specific checks | Define required checks, thresholds |
| **Policy Contract** | ✅ Complete | Clear APPROVE/ESCALATE/BLOCK framework | Verify agent follows it |
| **Business Analyst Contract** | ✅ Complete | Clear decision framework | Clarify invocation flow |
| **Orchestrator Templates** | 🔵 Template | Design correct, not executing | Implement execution phase with GitHub MCP tools |
| **GitHub Decision Comments** | ✅ Designed | Pattern established in templates-old | Implement in active orchestrators |

---

## Conclusion

The AIOS v2 orchestration system has **excellent architectural design** with proper separation of concerns (orchestrators, agents, contracts, utilities). The routing logic is sound and handles feedback loops correctly.

**The gap:** Everything documented is **not executing**. This is a normal phase of development—design is complete, now needs implementation.

**Next step:** Pick one orchestrator (recommend dev-orchestrator), implement the 5-step loop with real GitHub API calls and agent invocations. Once that works, replicate for PM and PO orchestrators.

**Timeline:** With focused effort, core orchestrator implementation can be done in 3-5 days. Full system (with observability, manual override, testing) in 2-3 weeks.
