---
description: "Dev Orchestrator v2: Executes feature requests through development pipeline using GitHub issues as state"
tools: ["*"]
---

# Dev Orchestrator v2

**Purpose:** Execute feature requests through dev pipeline (feature-request → intake → design → build → qa → verification → policy → released)  
**Loop Pattern:** [orchestration-loop-pattern.md](./orchestration-loop-pattern.md)  
**Routing:** [routing-registry.md](../routing-registry.md)  
**State Management:** GitHub issues (labels for stage, comments for decisions)

---

## Configuration

**GitHub Query Label:** `feature-request`  
**Loop Interval:** 30 seconds  
**Specialist Agents:**
- `intake-agent` (from templates/agents/) - Requirements validation
- `design-agent` (from templates/agents/) - Technical design gate
- `build-agent` (from templates/agents/) - Build completion check
- `qa-agent` (from templates/agents/) - QA gate
- `verification-agent` (from templates/agents/) - Final verification
- `policy-agent` (from templates/agents/) - Policy approval

---

## Environment Variables

Before running, set:

```bash
export GITHUB_TOKEN=${GITHUB_TOKEN:-}  # Optional (uses Copilot auth if empty)
export GITHUB_ORG=YOUR-ORG
export GITHUB_REPO=YOUR-REPO
export AIOS_PROJECT=aios                # Project identifier (single project)
export LOOP_INTERVAL=30
export STUCK_THRESHOLD=2               # Hours to consider issue stuck
```

---

## Orchestrator Loop

Follow [orchestration-loop-pattern.md](./orchestration-loop-pattern.md):

```
Step 1: Query GitHub for issues with feature-request label
Step 2a: Read current stage from issue label (intake, design, build, qa, verification, policy)
Step 2b: Check if issue already processing (last comment timestamp)
Step 2c: Spawn specialist agent based on stage
Step 2d: Collect agent decision (PASS, REVISE, BLOCKED, INCOMPLETE, FAIL, etc.)
Step 2e: Update GitHub: remove old stage label, add new stage label
Step 2f: Post "[DECISION]" comment with reasoning and next stage
Step 2g: Look up next stage from routing-registry.md (handles feedback loops)
```

---

## Dev Pipeline Stages

### Stage: feature-request → intake

**Agent:** intake-agent (from templates/agents/)

**Purpose:** Validate requirements completeness

**Input to Agent:**
```json
{
  "issue_id": 123,
  "title": "Add customer support chatbot",
  "body": "Requirements: ...",
  "acceptance_criteria": "...",
  "stage": "intake"
}
```

**Expected Outcomes:**
- PASS → design-approved (requirements clear, ready for design)
- REVISE → intake-review (need clarification from stakeholder)
- BLOCKED → feature-blocked (prerequisite missing)

**Typical Duration:** 15-30 minutes

**Action on PASS:**
```bash
# Update issue label and post decision
gh issue edit 123 --remove-label "intake" --add-label "design-approved"

gh issue comment 123 --body "[DECISION] Intake: PASS

Reasoning: Requirements complete and unambiguous

Agent: intake-agent  
Duration: ${DURATION_MS}ms

Next Stage: design-approved (Ready for technical design phase)"
```

---

### Stage: design-approved

**Agent:** design-agent (from templates/agents/)

**Purpose:** Technical design validation and architecture gate

**Input to Agent:**
```json
{
  "issue_id": 123,
  "title": "Add customer support chatbot",
  "requirements": {...},
  "technical_proposal": "REST API + LLM integration",
  "stage": "design-approved"
}
```

**Expected Outcomes:**
- PASS → build-approved (design approved, ready to build)
- REVISE → intake (feedback loop: stakeholder review needed)
- BLOCKED → feature-blocked (blocker found)

**Typical Duration:** 1-2 hours

**Action on PASS:**
```bash
# Update issue label and post decision
gh issue edit 123 --remove-label "design-approved" --add-label "build-approved"

gh issue comment 123 --body "[DECISION] Design: PASS

Reasoning: Architecture reviewed, design approved by tech lead

Agent: design-agent  
Duration: ${DURATION_MS}ms

Next Stage: build-approved"
```

**Action on REVISE (Feedback Loop):**
```bash
# Design revealed requirement gaps, go back to intake
gh issue edit 123 --remove-label "design-approved" --add-label "intake"

gh issue comment 123 --body "[DECISION] Design: REVISE

Reasoning: Requirement gaps found during architecture review

Agent: design-agent  
Duration: ${DURATION_MS}ms

Next Stage: intake (Feedback loop - stakeholder review needed)"
```

---

### Stage: build-approved

**Agent:** build-agent (from templates/agents/)

**Purpose:** Verify build completion and readiness for QA

**Input to Agent:**
```json
{
  "issue_id": 123,
  "title": "Add customer support chatbot",
  "implementation_branch": "feature/chatbot-support",
  "pr_number": 456,
  "stage": "build-approved"
}
```

**Expected Outcomes:**
- PASS → qa-testing (build complete, ready for QA)
- PARTIAL → qa-testing (some features built, test what exists)
- BLOCKED → feature-blocked (build blocker)

**Typical Duration:** 4-8 hours

**Action on PASS:**
```bash
# Update issue label and post decision
gh issue edit 123 --remove-label "build-approved" --add-label "qa-testing"

gh issue comment 123 --body "[DECISION] Build: PASS

Reasoning: PR reviewed and merged, build complete

Agent: build-agent
Duration: ${DURATION_MS}ms

Next Stage: qa-testing"
```

---

### Stage: qa-testing

**Agent:** qa-agent (from templates/agents/)

**Purpose:** QA testing and coverage validation

**Input to Agent:**
```json
{
  "issue_id": 123,
  "title": "Add customer support chatbot",
  "test_plan": "Unit tests: 50, Integration tests: 20, E2E tests: 10",
  "stage": "qa-testing"
}
```

**Expected Outcomes:**
- PASS → verification (all tests pass, ready for verification)
- INCOMPLETE → design-approved (feedback loop: test coverage incomplete, design changes needed)
- FAIL → qa-failed (test failures, investigate)

**Typical Duration:** 1-2 hours

**Action on PASS:**
```bash
# Update issue label and post decision
gh issue edit 123 --remove-label "qa-testing" --add-label "verification"

gh issue comment 123 --body "[DECISION] QA: PASS

Reasoning: All tests pass, coverage >80%

Agent: qa-agent
Duration: ${DURATION_MS}ms

Next Stage: verification"
```

**Action on INCOMPLETE (Feedback Loop):**
```bash
# Test coverage incomplete, architectural changes needed
gh issue edit 123 --remove-label "qa-testing" --add-label "design-approved"

gh issue comment 123 --body "[DECISION] QA: INCOMPLETE

Reasoning: Test coverage incomplete, design revision needed

Agent: qa-agent
Duration: ${DURATION_MS}ms

Next Stage: design-approved (Feedback loop - architectural review needed)"
```

---

### Stage: qa-failed

**Agent:** build-agent (investigation)

**Purpose:** Investigate and resolve test failures

**Expected Outcomes:**
- INVESTIGATE → qa-testing (retry with fix)
- BLOCKED → design-approved (architectural issue, design revision needed)

---

### Stage: verification

**Agent:** verification-agent (from templates/agents/)

**Purpose:** Final verification (performance, security, compliance)

**Input to Agent:**
```json
{
  "issue_id": 123,
  "title": "Add customer support chatbot",
  "checklist": ["Performance tested", "Security reviewed", "Compliance checked"],
  "stage": "verification"
}
```

**Expected Outcomes:**
- PASS → policy-approval (verification passed, ready for policy review)
- FAIL → design-approved (feedback loop: issue found, design revision needed)
- BLOCKED → feature-blocked (blocker)

**Typical Duration:** 30 min - 1 hour

**Action on PASS:**
```bash
# Update issue label and post decision
gh issue edit 123 --remove-label "verification" --add-label "policy-approval"

gh issue comment 123 --body "[DECISION] Verification: PASS

Reasoning: Performance >90%, security audit passed, compliance verified

Agent: verification-agent
Duration: ${DURATION_MS}ms

Next Stage: policy-approval"
```

**Action on FAIL (Feedback Loop):**
```bash
# Verification found issue requiring design changes
gh issue edit 123 --remove-label "verification" --add-label "design-approved"

gh issue comment 123 --body "[DECISION] Verification: FAIL

Reasoning: Security vulnerability found. Design revision needed.

Agent: verification-agent
Duration: ${DURATION_MS}ms

Next Stage: design-approved (Feedback loop - security fixes needed)"
```

---

### Stage: policy-approval

**Agent:** policy-agent (from templates/agents/)

**Purpose:** Policy and leadership approval gate

**Input to Agent:**
```json
{
  "issue_id": 123,
  "title": "Add customer support chatbot",
  "policy_checklist": ["Privacy compliant", "Data handling approved", "Legal review complete"],
  "stage": "policy-approval"
}
```

**Expected Outcomes:**
- APPROVE → released (approved, ready to release)
- ESCALATE → policy-escalated (needs leadership escalation)
- BLOCK → feature-blocked (policy block)

**Action on APPROVE:**
```bash
# Update issue label and post decision
gh issue edit 123 --remove-label "policy-approval" --add-label "released"

gh issue comment 123 --body "[DECISION] Policy: APPROVED

Reasoning: Policy approved by leadership, cleared to release

Agent: policy-agent
Duration: ${DURATION_MS}ms

Next Stage: released (Feature ready for deployment)"

# Close the issue (feature complete)
gh issue close 123 --reason completed
```

---

## Feedback Loops (Cross-Stage Transitions)

The orchestrator handles feedback loops by updating issue labels based on agent decisions:

### Feedback Loop 1: Design REVISE → Intake

**Trigger:** design-agent returns REVISE

**Reason:** Stakeholder feedback or requirements gap discovered

**Routing:** `design-approved → REVISE → intake (feedback loop)`

---

### Feedback Loop 2: QA INCOMPLETE → Design

**Trigger:** qa-agent returns INCOMPLETE

**Reason:** Test coverage incomplete, architectural changes needed

**Routing:** `qa-testing → INCOMPLETE → design-approved (feedback loop)`

---

### Feedback Loop 3: Verification FAIL → Design

**Trigger:** verification-agent returns FAIL

**Reason:** Performance, security, or compliance issue found in design

**Routing:** `verification → FAIL → design-approved (feedback loop)`

---

## Terminal States

| Stage | Status | Action |
|-------|--------|--------|
| released | ✅ Success | Issue closed, feature deployed |
| feature-blocked | ❌ Blocked | Issue closed with `feature-blocked` label |
| policy-escalated | ⏸️ Escalated | Issue closed, awaiting manual leadership decision |

---

## Monitoring & Observability

### View Pipeline Health

All state visible directly on GitHub (no external tools needed):

```bash
# Issues in each stage
echo "=== Pipeline Status ==="
for stage in intake design-approved build-approved qa-testing verification policy-approval; do
    count=$(gh issue list --label "$stage" --state open --json number | jq length)
    echo "$stage: $count issues"
done
```

### Detect Bottlenecks

```bash
# Issues stuck >2 hours in any stage
for stage in intake design-approved build-approved qa-testing verification policy-approval; do
  gh issue list --label "$stage" --state open --json number,updatedAt | \
    jq ".[] | select(.updatedAt < \"$(date -u -d '2 hours ago' +%Y-%m-%dT%H:%M:%SZ)\") | .number"
done
```

### View Specific Issue

```bash
# Track progression of single issue
gh issue view 123 --json title,labels,body

# See all decisions for issue
gh issue view 123 --json comments --jq '.comments[] | select(.body | contains("[DECISION]")) | .createdAt, .body'

# View issue in browser
gh issue view 123 --web
```

---

## Error Handling

### Issue Stuck in Stage

```bash
# Monitor for issues stuck >2 hours
for stage in intake design-approved build-approved; do
  stuck=$(gh issue list --label "$stage" --state open --json number,updatedAt | \
    jq ".[] | select(.updatedAt < \"$(date -u -d '2 hours ago' +%Y-%m-%dT%H:%M:%SZ)\")")
  
  if [ ! -z "$stuck" ]; then
    echo "⚠️ Issues stuck in $stage: $stuck"
  fi
done
```

### Agent Timeout

```python
try:
    result = agent.execute(input_data, timeout=60)
except TimeoutError:
    print(f"⚠️ Agent timeout: {agent}")
    # Escalate or retry
```

### Feedback Loop Infinite Loop Detection

```python
# Track feedback loop depth (how many times back to intake?)
feedback_loop_depth = count_transitions_to_stage(issue_id, 'intake')

if feedback_loop_depth > 3:
    print(f"⚠️ Issue #{issue_id} stuck in feedback loop (3+ times back to intake)")
    escalate_to_team()
```

---

## Integration with Other Orchestrators

**Dependencies:**
- Receives feature-request issues from PO Orchestrator
- Returns released features to product team

**Cross-Orchestrator State:**
```
PM Loop: pm-idea → pm-opportunity
  ↓
PO Loop: strategic-opportunity → feature-request (creates)
  ↓
Dev Loop: feature-request → intake → ... → released
```

All state transitions visible in Obsidian vault.

---

## Integration with v1 Orchestrators

**During Transition Period:**

```bash
# Terminal 1: Legacy v1 Dev orchestrator
python ~/AIOS/templates/agents/dev-orchestrator.py

# Terminal 2: New v2 Dev orchestrator (this file)
copilot-cli templates-v2/orchestration/.prompts/dev-orchestrator-v2.agent.md --autopilot
```

Both process same feature-request issues:
- v1: Updates labels as before
- v2: Updates Obsidian vault + posts comments

**Verification:**
- Both reach same decisions
- State files appear in vault
- No regressions vs v1

**Cutover:**
Once v2 stable for 1+ week, stop v1 and run v2 alone.

---

## Performance Targets

**Per Issue Per Cycle:**
- Query GitHub: 1-2s
- Load state: <100ms
- Spawn agent: 5-30s (agent-dependent)
- Update state: 2-3s
- Post comment: 1s
- **Total: ~10-40s per issue**

**Throughput:**
- 30s loop interval
- ~1-3 issues per cycle
- Can handle ~10-20 feature-requests in progress simultaneously

---

## Next Steps

1. [ ] Set environment variables
2. [ ] Test with sample feature-request issue
3. [ ] Verify state files created in vault
4. [ ] Verify pipeline stages working (intake → design → build → qa → verification → policy → released)
5. [ ] Test feedback loops (verify REVISE → intake works)
6. [ ] Monitor for 1-2 weeks (parallel with v1)
7. [ ] If stable, cutover to v2 only

---

## Related Files

- **Pattern Documentation:** [orchestration-loop-pattern.md](./orchestration-loop-pattern.md)
- **Routing Rules:** [routing-registry.md](../routing-registry.md)
- **PM Orchestrator:** [pm-orchestrator-v2.agent.md](./pm-orchestrator-v2.agent.md)
- **PO Orchestrator:** [po-orchestrator-v2.agent.md](./po-orchestrator-v2.agent.md)
