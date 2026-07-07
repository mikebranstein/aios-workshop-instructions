# Development Orchestrator: State Transitions & Label Management Matrix

## Part 1: Complete State Transition Matrix

### Stage 1: Intake (Requirements Validation)

| Entry State | Labels | Column | Process | Exit State | Labels | Column | Gaps |
|---|---|---|---|---|---|---|---|
| feature-request created | `po-prioritized` | Ready for Dev | Read requirements, validate clarity | ✅ Pass: → BA | `po-prioritized`, `intake-working` | In Development | ❌ **Gap 1**: No removal of `po-prioritized` when exiting Intake |
| feature-request created | `po-prioritized` | Ready for Dev | Requirements unclear/ambiguous | ⚠️ Hold: → BA | `po-prioritized`, `intake-blocked-on-clarity` | In Development | ❌ **Gap 2**: No escalation comment format defined |

### Stage 2: BA (Acceptance Criteria Refinement)

| Entry State | Labels | Column | Process | Exit State | Labels | Column | Gaps |
|---|---|---|---|---|---|---|---|
| Issue from Intake | `intake-working`, `po-prioritized` | In Development | Refine ACs; ensure testable | ✅ Pass: → Design | `ba-working`, `po-prioritized` | In Development | ❌ **Gap 3**: `intake-working` not removed |
| Issue from Intake | `intake-working`, `intake-blocked-on-clarity` | In Development | Ask for clarification; wait | ⏸️ Hold: → Intake | `intake-working` | In Development | ❌ **Gap 4**: No escalation path defined |

### Stage 3: Design (Architecture & Risk Assessment)

| Entry State | Labels | Column | Process | Exit State | Labels | Column | Gaps |
|---|---|---|---|---|---|---|---|
| Issue from BA | `ba-working`, `po-prioritized` | In Development | Design architecture; low-risk | ✅ Pass (Low-Risk): → Build | `design-working`, `po-prioritized` | In Development | ❌ **Gap 5**: `ba-working` not removed |
| Issue from BA | `ba-working`, `po-prioritized` | In Development | Design architecture; high-risk | ✅ Pass (High-Risk): → Policy | `policy-review-required`, `po-prioritized` | Policy Review | ❌ **Gap 5**: `ba-working` not removed; `design-working` not added |
| Issue from BA | `ba-working`, `po-prioritized` | In Development | ACs not testable | 🔄 Fail: → BA | `ba-working`, `po-prioritized`, `test-coverage-incomplete` | In Development | ❌ **Gap 6**: No escalation comment |

### Stage 4: Build (Implementation)

| Entry State | Labels | Column | Process | Exit State | Labels | Column | Gaps |
|---|---|---|---|---|---|---|---|
| Issue from Design | `design-working`, `po-prioritized` | In Development | Implement + write tests | ✅ Pass: → Verification | `build-working`, `po-prioritized` | In Development | ❌ **Gap 7**: `design-working` not removed |
| Issue from Design | `design-working`, `po-prioritized` | In Development | Cannot implement design | 🔄 Fail: → Design | `design-working`, `po-prioritized`, `build-blocked` | In Development | ❌ **Gap 8**: Escalation path unclear |

### Stage 5: Verification (Code Quality Gate)

| Entry State | Labels | Column | Process | Exit State | Labels | Column | Gaps |
|---|---|---|---|---|---|---|---|
| PR from Build | `build-working`, `po-prioritized` | In Development | Tests pass, quality OK | ✅ Pass: → QA | `verification-passed`, `po-prioritized` | In Development | ❌ **Gap 9**: `build-working` not removed; inconsistent label naming |
| PR from Build | `build-working`, `po-prioritized` | In Development | Tests fail or quality issues | 🔄 Fail: → Build | `build-working`, `po-prioritized`, `verification-failed` | In Development | ❌ **Gap 10**: Escalation comment format undefined |

### Stage 6: QA (Test Coverage & Validation)

| Entry State | Labels | Column | Process | Exit State | Labels | Column | Gaps |
|---|---|---|---|---|---|---|---|
| Issue from Verification | `verification-passed`, `po-prioritized` | In Development | All ACs tested + pass | ✅ Pass (Low-Risk): → Release | `qa-passed`, `po-prioritized` | Ready to Release | ❌ **Gap 11**: Routing decision not clear (low-risk vs policy-required) |
| Issue from Verification | `verification-passed`, `po-prioritized`, `policy-review-required` | In Development | All ACs tested + pass | ✅ Pass (High-Risk): → Policy | `qa-passed`, `policy-review-required`, `po-prioritized` | Policy Review | ❌ **Gap 11**: Same label naming |
| Issue from Verification | `verification-passed`, `po-prioritized` | In Development | Test coverage incomplete | 🔄 Fail: → Design | `verification-passed`, `test-coverage-incomplete` | In Development | ❌ **Gap 12**: `design-working` should be added; escalation comment format |
| Issue from Verification | `verification-passed`, `po-prioritized` | In Development | Tests fail or ACs not met | 🔄 Fail: → Build | `verification-passed`, `qa-failed` | In Development | ❌ **Gap 13**: `build-working` should be re-added |

### Stage 7: Policy (Governance Gate - **Manual Intervention Zone**)

| Entry State | Labels | Column | Process | Exit State | Labels | Column | Gaps |
|---|---|---|---|---|---|---|---|
| Issue from QA | `qa-passed`, `policy-review-required` | Policy Review | All 12 APPROVE criteria met | ✅ APPROVED: → Release | `policy-approved`, `po-prioritized` | Ready to Release | ❌ **Gap 14**: `qa-passed` not removed; no escalation comment |
| Issue from QA | `qa-passed`, `policy-review-required` | Policy Review | Some ESCALATE criteria triggered | ⚠️ ESCALATED: Hold | `policy-escalated`, `po-prioritized` | Policy Review (Blocked) | ❌ **Gap 15**: No manual unblock procedure documented |
| Issue from QA | `qa-passed`, `policy-review-required` | Policy Review | BLOCK criteria triggered | 🔴 BLOCKED: → Design | `policy-blocked`, `po-prioritized` | In Development | ❌ **Gap 16**: No manual override/unblock procedure |

### Stage 8: Release (Deployment)

| Entry State | Labels | Column | Process | Exit State | Labels | Column | Gaps |
|---|---|---|---|---|---|---|---|
| Issue from QA (low-risk) | `qa-passed`, `po-prioritized` | Ready to Release | Merge → deploy → verify | ✅ RELEASED | `released`, `po-prioritized` | Released | ❌ **Gap 17**: Issue should be CLOSED; `po-prioritized` kept forever? |
| Issue from Policy | `policy-approved`, `po-prioritized` | Ready to Release | Merge → deploy → verify | ✅ RELEASED | `released`, `po-prioritized` | Released | ❌ **Gap 17**: Same issue |

---

## Part 2: Gap Analysis

### **Gap 1: `po-prioritized` Label Not Removed During Intake**
- **Current:** Label enters with feature-request and stays on all the way through
- **Problem:** Accumulation; unclear which stage issue is in by labels alone
- **Fix:** Remove `po-prioritized` on exit from Intake; re-add only if returning from escalation

### **Gap 2: Escalation Comment Format Undefined (Intake)**
- **Current:** When requirements are ambiguous, no standard comment format
- **Problem:** Unclear what info is needed to resolve; hard to track escalation reason
- **Fix:** Define escalation comment template with required fields (reason, blocker, ask)

### **Gap 3: `intake-working` Label Not Removed on BA Entry**
- **Current:** BA receives issue but old label lingers
- **Problem:** Accumulation; impossible to tell if Intake is still working
- **Fix:** Remove `intake-working` when exiting Intake

### **Gap 4: BA Escalation Path Unclear**
- **Current:** If requirements still ambiguous after BA refinement, unclear what happens
- **Problem:** Issue could loop infinitely between Intake ↔ BA
- **Fix:** Define max escalation attempts; after 2 rounds, escalate to PO

### **Gap 5: `ba-working` Not Removed; `design-working` Inconsistently Added**
- **Current:** BA label persists; Design agent sometimes adds/removes labels inconsistently
- **Problem:** Label churn; stage tracking breaks
- **Fix:** Strict label hygiene: Remove incoming label, add outgoing label as atomic operation

### **Gap 6: Design Escalation Comment Undefined**
- **Current:** When ACs not testable, Design comments but format varies
- **Problem:** BA can't parse escalation reason reliably
- **Fix:** Define escalation template matching Gap 2

### **Gap 7-10: Stage Label Accumulation**
- **Current:** Labels from Build, Verification accumulate; never removed
- **Problem:** Labels don't reflect current stage; impossible to determine position
- **Fix:** Implement atomic label swaps at every stage boundary

### **Gap 11: Routing Decision at QA Unclear**
- **Current:** QA doesn't explicitly check for `policy-review-required`; routing magic
- **Problem:** Inconsistent routing; some features skip policy incorrectly
- **Fix:** Explicit conditional routing in QA agent with logging

### **Gap 12: Incomplete Test Coverage → No Stage Label Management**
- **Current:** When coverage incomplete, issue goes back to Design but labels don't change
- **Problem:** `verification-passed` stays; Design doesn't know it's re-entering from QA
- **Fix:** Add specific label (`qa-coverage-gap`) when returning from QA

### **Gap 13: Failed QA → No Build Label Re-added**
- **Current:** Issue fails QA and goes back to Build, but `build-working` label not restored
- **Problem:** Build doesn't know it's re-entering; unclear stage
- **Fix:** Remove QA labels, add back `build-working` on re-entry

### **Gap 14: `qa-passed` Not Removed at Policy**
- **Current:** QA label stays even after Policy decision
- **Problem:** Accumulation; label doesn't reflect current decision
- **Fix:** Remove `qa-passed` when making APPROVED/ESCALATED/BLOCKED decision

### **Gap 15: ⚠️ POLICY ESCALATION - No Manual Unblock Procedure** 
- **Current:** If ESCALATED (needs leadership decision), issue stays in Policy Review with no clear next step
- **Problem:** No documented procedure for leadership to approve and move forward
- **Fix:** Define explicit HITL unblock procedure:
  - Leadership reviews policy comment with details
  - Leadership posts approval comment: `@dev-orchestrator override-approval: [reason]`
  - Orchestrator detects comment, removes `policy-escalated`, adds `policy-approved-override`
  - Issue continues to Release

### **Gap 16: ⚠️ POLICY BLOCKING - No Manual Override Procedure**
- **Current:** If BLOCKED (critical issues), issue returned to Design with `policy-blocked` label
- **Problem:** No procedure to manually override if policy violation intentional or acceptable
- **Fix:** Define explicit HITL override procedure:
  - Design/leadership reviews why blocked
  - Posts comment: `@policy-agent accept-risk: [reason] [acceptance-criteria]`
  - Policy agent verifies format, removes `policy-blocked`, adds `policy-override-accepted`
  - Issues continues to Build

### **Gap 17: `po-prioritized` Label Never Removed**
- **Current:** Label added by PO, persists through entire pipeline, stays on released issue
- **Problem:** Accumulation; no signal that issue is complete; label becomes meaningless
- **Fix:** Remove `po-prioritized` when issue is CLOSED (Release stage)

---

## Part 3: Manual Intervention Procedures

### **Procedure 1: Policy Escalation → Leadership Override**

**Trigger:** Issue in "Policy Review" with labels `policy-escalated`, `po-prioritized`

**Who:** Engineering Leadership (Director+ level required)

**Steps:**

1. **Review the escalation:**
   - Read the policy comment (posted by Policy Agent) containing escalation reason(s)
   - Review the PR code + architecture notes
   - Assess risk level

2. **Make decision:**
   - **Option A (Approve):** Risk is acceptable; proceed to Release
   - **Option B (Block):** Risk is unacceptable; send to Design for re-work
   - **Option C (Conditional Approve):** Approve with conditions (e.g., "Approved but only for internal testing; needs follow-up")

3. **Post approval comment** (format is REQUIRED for orchestrator to detect):
   ```
   @dev-orchestrator policy-override-approved
   
   Risk Assessment: [Leadership's reasoning]
   Conditions: [Any conditions on this override, e.g., "Monitor for regressions for 1 week"]
   Approved by: [Name + Title]
   Date: [ISO 8601]
   ```

4. **Orchestrator detects comment with `policy-override-approved`:**
   - Removes label: `policy-escalated`
   - Adds label: `policy-approved-override`
   - Removes label: `qa-passed`
   - Adds comment: "Leadership override approved. Proceeding to Release stage."
   - Moves issue to "Ready to Release" column

5. **Release agent** picks up issue and deploys

**Result:** Feature ships with documented override; audit trail is clear.

---

### **Procedure 2: Policy Blocking → Design Accept-Risk Override**

**Trigger:** Issue in "Policy Review" with labels `policy-blocked`, `po-prioritized`

**Who:** Design Lead + Product Manager (joint decision required)

**Steps:**

1. **Review the block:**
   - Read the policy comment (posted by Policy Agent) containing BLOCK reason(s)
   - Understand why it's blocked (security issue? compliance gap? regression risk?)
   - Assess whether override is acceptable

2. **Determine response:**
   - **Option A (Re-work in Design):** Block is legitimate; return to Design to address root cause
   - **Option B (Accept Risk):** Block is known/accepted; override and proceed with documented risk
   - **Option C (Defer):** Defer feature to next quarter; deprioritize

3. **If accepting risk, post acceptance comment** (format is REQUIRED):
   ```
   @dev-orchestrator accept-policy-risk
   
   Policy Issue: [Which BLOCK criterion is being overridden]
   Risk Acceptance: [Why we're accepting this risk]
   Mitigation Plan: [What we'll do to manage risk: monitoring, follow-up work, date]
   Approved by: [Design Lead], [PM]
   Date: [ISO 8601]
   ```

4. **Orchestrator detects comment with `accept-policy-risk`:**
   - Removes label: `policy-blocked`
   - Adds label: `policy-risk-accepted`
   - Removes label: `qa-passed`
   - Adds comment: "Risk override accepted. Proceeding to Release. [Mitigation plan link]"
   - Moves issue to "Ready to Release" column
   - **Creates follow-up issue** (if mitigation plan specifies): `Fix mitigation for [feature] by [date]` linked to released feature

5. **Release agent** picks up issue and deploys

**Result:** Feature ships with documented risk acceptance; follow-up work is tracked.

---

### **Procedure 3: Build Escalation → Design Architectural Re-evaluation**

**Trigger:** Issue returned from Build with label `build-blocked`

**Who:** Build Lead + Design Lead

**Steps:**

1. **Review escalation comment** (posted by Build agent):
   - What's the architectural blocker?
   - Can it be worked around? How?
   - Does design need to change fundamentally?

2. **Design reviews and responds:**
   - Option A: Proposed workaround is acceptable; Build continues
   - Option B: Architecture needs revision; provide new design approach
   - Option C: Scope is too large; deprioritize and revisit

3. **Post response comment:**
   ```
   @build-agent [Option A/B/C]
   
   [If A] Proposed workaround: [Details]
   [If B] New architecture approach: [Details]
   [If C] Defer and revisit: [When, why]
   ```

4. **Orchestrator detects response:**
   - Removes label: `build-blocked`
   - Adds label: `design-working` (if re-design needed) OR
   - Removes label: `build-blocked` (if workaround accepted; Build continues)

---

### **Procedure 4: Test Coverage Gap → Design Coverage Planning**

**Trigger:** Issue returned from QA with label `test-coverage-incomplete`

**Who:** QA Lead + Design Lead

**Steps:**

1. **QA posts comment** (during return from QA):
   ```
   @design-agent test-coverage-gap
   
   Missing Coverage:
   - [AC #1] — No test for scenario X
   - [AC #2] — Edge case Y untested
   
   Recommendation: [Make ACs more specific OR reduce scope]
   ```

2. **Design reviews:**
   - Option A: AC needs to be more specific (testable); route back to BA
   - Option B: AC is vague; Design will clarify in next build
   - Option C: AC is out of scope for this sprint; defer to Phase 2

3. **Post response:**
   ```
   @qa-agent coverage-plan
   
   [Option A/B/C]
   [Details on how to resolve]
   ```

4. **Orchestrator processes:**
   - Removes label: `test-coverage-incomplete`
   - Routes accordingly (BA, continue, or defer)

---

## Part 4: Label Hygiene Rules (Atomic Transitions)

### At Every Stage Boundary, Implement:

```bash
# Example: Exiting Intake → Entering BA
gh issue edit $ISSUE_NUM \
  --remove-label "intake-working" \
  --add-label "ba-working"

# Example: BA Pass → Design (low-risk)
gh issue edit $ISSUE_NUM \
  --remove-label "ba-working" \
  --add-label "design-working"

# Example: Design Pass (high-risk) → Policy
gh issue edit $ISSUE_NUM \
  --remove-label "design-working" \
  --add-label "policy-review-required"

# Example: Policy Override Approved → Release
gh issue edit $ISSUE_NUM \
  --remove-label "policy-escalated" \
  --add-label "policy-approved-override" \
  --remove-label "qa-passed"

# Example: Release Complete → Closed
gh issue edit $ISSUE_NUM \
  --remove-label "po-prioritized" \
  --add-label "released"

gh issue close $ISSUE_NUM
```

---

## Summary: Gaps to Implement

| Priority | Gap # | Title | Stage | Action |
|---|---|---|---|---|
| 🔴 CRITICAL | 15 | Policy Escalation Override Procedure | Policy | Add manual approval procedure + orchestrator detection |
| 🔴 CRITICAL | 16 | Policy Blocking Accept-Risk Procedure | Policy | Add manual override procedure + mitigation tracking |
| 🟠 HIGH | 1,3,5,9,14,17 | Label Accumulation | All | Implement atomic label swaps (remove old, add new) at every boundary |
| 🟠 HIGH | 2,6,10 | Escalation Comment Format | Intake, Design, Verification | Define standard template for escalation reasons |
| 🟠 HIGH | 11 | QA Routing Logic | QA | Explicit conditional check for `policy-review-required` |
| 🟡 MEDIUM | 4 | BA Loop Prevention | BA | Define max 2 escalation attempts → escalate to PO |
| 🟡 MEDIUM | 7,8,12,13 | Stage Label Consistency | Build, QA | Ensure incoming/outgoing labels managed atomically |
