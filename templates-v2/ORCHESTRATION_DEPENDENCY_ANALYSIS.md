# Orchestration Dependency Analysis - Design Issue #2

## Executive Summary

Three orchestrators (PM, PO, Dev) create a **linear data pipeline** where each feeds into the next. The question is whether they should run:
- **Parallel** (all three concurrently)
- **Sequential** (one waits for previous to complete)
- **Hybrid** (concurrent but with blocking points)

**Analysis conclusion:** Hybrid is optimal—all three run concurrently, but with natural blocking points where dependency chains exist.

---

## Part 1: Data Flow & Dependencies

### Linear Dependency Chain

```
PM Loop                    PO Loop                  Dev Loop
========                   ========                 ========

pm-idea                    strategic-opportunity   feature-request
   ↓                            ↓                         ↓
Phase 1 gate              Prioritization           Intake
   ↓                            ↓                         ↓
Research            Backlog sequencing           Design
   ↓                            ↓                         ↓
Phase 2 gate         Create feature-requests     Build
   ↓                            ↓                         ↓
pm-opportunity ─────→ strategic-opportunity ─────→ Released
(output)             (input/output)              (output)
```

### What Each Loop Depends On

**PM Loop:**
- Input: `pm-idea` issues (created by product/stakeholders)
- Dependencies: None on other orchestrators
- Output: `pm-opportunity` issues
- Blocking points: None (PM is independent)

**PO Loop:**
- Input: `strategic-opportunity` issues (created by PM loop)
- Dependencies: **Must wait for PM to create strategic-opportunity**
- Output: `feature-request` issues
- Blocking points: Cannot start if no strategic-opportunities available

**Dev Loop:**
- Input: `feature-request` issues (created by PO loop)
- Dependencies: **Must wait for PO to create feature-request**
- Output: `released` issues, PR merges
- Blocking points: Cannot start if no feature-requests available

---

## Part 2: Orchestrator Execution Model

### Current Design (Implicit)

Each orchestrator runs in a **continuous loop**:

```
PM Orchestrator:
Loop every 30s:
  1. git checkout main; git pull
  2. Find first actionable pm-idea (depth-first)
  3. Process it fully (Phase 1 → Research → Phase 2)
  4. Close/label it
  5. Sleep 30s
  6. Repeat

PO Orchestrator:
Loop every 30s:
  1. git checkout main; git pull
  2. Find first actionable strategic-opportunity (depth-first)
  3. Process it fully (Prioritization → Sequencing → Create feature-requests)
  4. Close/label it
  5. Sleep 30s
  6. Repeat

Dev Orchestrator:
Loop every 30s:
  1. git checkout main; git pull
  2. Find first actionable feature-request (depth-first)
  3. Process it through pipeline (Intake → Design → Build → QA → Policy → Released)
  4. Close/label it
  5. Sleep 30s
  6. Repeat
```

### Execution Timeline Scenarios

#### Scenario A: All Three Running in Parallel

```
Time    PM Loop                      PO Loop                      Dev Loop
────────────────────────────────────────────────────────────────────────
t=0     Processing pm-idea #1       Processing strg-opp #1       Processing feat-req #1
t=30s   Processing pm-idea #2       Processing strg-opp #2       Processing feat-req #2
t=60s   Processing pm-idea #3       Processing strg-opp #3       Processing feat-req #3
...
```

**Characteristics:**
- All three run concurrently
- Each processes one item per 30-second cycle
- No artificial waiting
- Maximum throughput

**Risks:**
- No guarantees about ordering (PO might process strg-opp #5 before PM has created strg-opp #3)
- Dev loop might run out of feature-requests to process (all are stuck in feedback loops)
- PM might generate strategic-opportunities faster than PO can consume them

#### Scenario B: Sequential (Only One Loop Active at a Time)

```
Time    Loop Active                 Action
────────────────────────────────────────────
t=0     PM Loop                     Process pm-idea #1 fully
t=T1    PO Loop                     Process strg-opp #1 fully
t=T2    Dev Loop                    Process feat-req #1 fully
t=T3    PM Loop                     Process pm-idea #2 fully
t=T4    PO Loop                     Process strg-opp #2 fully
...
```

**Characteristics:**
- Clear ordering (pm-idea → strg-opp → feat-req guaranteed sequence)
- High latency (cycle time = PM time + PO time + Dev time)
- No parallelism benefits

**Risks:**
- Very slow throughput
- If PM takes 5 min and PO takes 5 min and Dev takes 30 min, one full cycle takes 40+ minutes
- Resource underutilization (only one agent working at a time)

#### Scenario C: Parallel with Blocking Points (Recommended)

```
Time    PM Loop                      PO Loop                      Dev Loop
────────────────────────────────────────────────────────────────────────
t=0     Processing pm-idea #1       Waiting (no strg-opp yet)    Waiting (no feat-req yet)
t=30s   → creates strg-opp #1
        Processing pm-idea #2       ✓ Now processing strg-opp #1 Waiting (no feat-req yet)
t=60s   → creates strg-opp #2
        Processing pm-idea #3       ✓ Now processing strg-opp #2 Waiting (no feat-req yet)
t=90s   → creates strg-opp #3
                                                                   (PO eventually creates feat-req)
                                    ✓ Now processing strg-opp #3 ✓ Now processing feat-req #1
        Processing pm-idea #4       Processing strg-opp #4       Processing feat-req #2
```

**Characteristics:**
- All three run concurrently
- Natural blocking points (PO waits for strg-opp, Dev waits for feat-req)
- Maximum parallelism within constraints
- Self-regulating (faster loops don't starve slower ones)

---

## Part 3: Blocking Points Analysis

### When Does PO Loop Block?

**Block condition:** No actionable `strategic-opportunity` issues available

This happens when:
- PM hasn't created any yet (new project)
- PM is processing all remaining pm-ideas
- All existing strategic-opportunities are in terminal states (completed, rejected, deferred)

**Recovery:** PO loop sleeps for 30s and retries

### When Does Dev Loop Block?

**Block condition:** No actionable `feature-request` issues available

This happens when:
- PO hasn't created any yet
- All existing feature-requests are in terminal states (released, blocked)
- All existing feature-requests are in active feedback loops (intake-blocked waiting for BA, design-blocked waiting for clarification, etc.)

**Recovery:** Dev loop sleeps for 30s and retries

### Feedback Loops Create Secondary Blocking

Within the Dev loop, many issues get stuck in feedback loops:

```
Intake blocked → BA clarifies → Intake re-evaluates → (blocks again?)
Design blocked → Intake re-evaluates → Design re-evaluates → (blocks again?)
QA incomplete → Design clarifies → Build adds tests → QA re-runs → (blocks again?)
```

These feedback loops can starve the Dev loop of actionable items.

---

## Part 4: Recommended Analysis Framework

To decide between Parallel vs Sequential, analyze these dimensions:

### Dimension 1: Throughput Requirements

**Question:** How many features per day/week do we need to deliver?

- If high throughput needed: **Parallel is better** (can handle multiple features concurrently)
- If low throughput: **Sequential is simpler** (easier to reason about)

### Dimension 2: Latency Requirements

**Question:** How fast should a pm-idea become a released feature?

- If fast latency critical: **Parallel is better** (features don't wait for PM loop to finish)
- If latency flexible: **Sequential is fine** (simpler model)

### Dimension 3: Resource Constraints

**Question:** Can we afford to run three orchestrators simultaneously?

- If yes: **Parallel** (maximize resource utilization)
- If no (single server, limited API quota): **Sequential** (share resources)

### Dimension 4: Complexity Tolerance

**Question:** Can the team handle concurrent state management?

- If yes: **Parallel** (handles concurrent modifications to GitHub)
- If no: **Sequential** (simpler mental model)

### Dimension 5: Feedback Loop Frequency

**Question:** How often do features get stuck in feedback loops (intake-blocked, design-blocked, qa-failed)?

- If rare: **Parallel is fine** (Dev loop has continuous work)
- If frequent: **Parallel might starve** (Dev loop runs out of actionable items)

---

## Part 5: Detailed Comparison Matrix

| Factor | Sequential | Parallel | Hybrid (Recommended) |
|--------|-----------|----------|------------------|
| **Throughput** | 1 item per full cycle | N items across loops | N items across loops |
| **Latency per item** | Very high | Low | Low |
| **Code complexity** | Simple | Complex (concurrency) | Moderate |
| **GitHub API load** | Low (serialized) | High (concurrent) | Moderate |
| **Max concurrent features** | 1 | 3+ (one per loop) | 3+ with natural limits |
| **Feedback loop handling** | Pauses all loops | Pauses only stuck loop | Pauses only stuck loop |
| **State collision risk** | None | Medium | Low |
| **Resource utilization** | Poor | Excellent | Excellent |
| **Mental model** | Trivial | Complex | Intuitive |

---

## Part 6: Specific Blocking Point Analysis

### Blocking Point 1: PO Waiting for Strategic-Opportunities

```
PO Loop Step 2: "Find the FIRST issue not in terminal state"
├─ Looks for: strategic-opportunity issues
├─ Skips: po-deferred, po-rejected, feature-requests-created
└─ If no actionable: Sleep 30s, retry

Time Cost:
- If strategic-opportunities available: 0s (process immediately)
- If none available: 30s wait, then retry
- Worst case: PM hasn't created any yet → waits until PM completes first pm-idea
```

### Blocking Point 2: Dev Waiting for Feature-Requests

```
Dev Loop Step 2: "Find the FIRST issue not in terminal/waiting state"
├─ Looks for: feature-request issues
├─ Skips: released, feature-blocked, policy-escalated, intake-blocked (non-requirement)
└─ If no actionable: Sleep 30s, retry

Time Cost:
- If feature-requests available: 0s (process immediately)
- If none available: 30s wait, then retry
- Worst case: Nested feedback loops (intake-blocked → design-blocked → qa-incomplete)
  → All feature-requests stuck → Dev loop idles
```

### Blocking Point 3: PM Loop (No Blocking)

PM loop has no dependencies on other loops. It can always process.

```
If all pm-ideas processed:
├─ No more actionable pm-ideas
├─ Dev loop might be processing final features
├─ PO loop might be creating final feature-requests
└─ PM loop enters idle state (sleeps 30s, retries)
```

---

## Part 7: Feedback Loop Starvation Risk

### Scenario: Feedback Loop Explosion in Dev

```
Cycle 1: Dev processes feat-req #1
         → Intake approves
         → Design approves
         → Build completes
         → QA fails (TEST_COVERAGE_INCOMPLETE)
         → Routes to Design for clarification

Cycle 2: Dev processes feat-req #1 again (still in design)
         → Design clarifies
         → Routes to Build with design-clarified label
         → Build adds tests
         → Routes back to QA

Cycle 3: Dev processes feat-req #1 again (QA re-running)
         → QA passes
         → Routes to Policy

Cycle 4-5: Dev processing feat-req #1 through policy stages

Meanwhile: feat-req #2, #3, #4 are waiting for Dev loop to become available
           After 20 cycles, feat-req #1 is still cycling
           Dev loop is consumed by one feature
           PO is creating feat-req #5, #6, #7 (no Dev capacity)
```

**Risk:** Feedback loops can consume the entire Dev orchestrator, starving other features.

**Mitigation:** 
- Process multiple features concurrently (not just one per cycle)
- Have a queue depth limit (block PO from creating more features if Dev has >5 queued)
- Separate orchestrator for feedback loops

---

## Part 8: Recommendation: Hybrid Parallel with Blocking

**Decision:** Implement **parallel orchestrators with natural blocking points**.

**Reasoning:**
1. All three loops run concurrently (maximum resource utilization)
2. Blocking points are natural (PO waits for strg-opp, Dev waits for feat-req)
3. No artificial sequential delays
4. Self-regulating (fast PM loop won't starve PO if PO backs up)
5. Handles feedback loops gracefully (stuck features don't block creation of new ones)

**Implementation:**
- Deploy three orchestrators as separate processes
- Each runs its own 30-second loop continuously
- Each independently queries GitHub for actionable issues
- Natural blocking: Loop sleeps if no actionable items

**GitHub API Considerations:**
- Peak QPS: ~3 orchestrators × 2-3 API calls per cycle = 6-9 API calls per 30 seconds
- Rate limit: GitHub allows 5,000 API calls/hour (83/second)
- **No issue:** 6-9 per 30s = 0.2-0.3/second (well below limit)

**Monitoring Points:**
- Track how often PO loop finds no actionable strategic-opportunities
- Track how often Dev loop finds no actionable feature-requests
- Track feedback loop depth (how many cycles one feature spends in loop)
- Alert if Dev loop idle for >10 consecutive cycles (potential deadlock)

---

## Part 9: Alternative Considerations

### Option A: Batch Processing (Multiple Items Per Cycle)

Instead of depth-first (one item per cycle), process multiple items:

```
PM Loop (current):  Process 1 pm-idea per cycle
PM Loop (batch):    Process all available pm-ideas in one cycle

Advantage: Faster feature generation
Disadvantage: More complex orchestrator logic, harder to debug feedback
```

### Option B: Priority-Based Processing

Instead of oldest-first (creation order), process by priority:

```
Dev Loop (current):  Process oldest feature-request first
Dev Loop (priority): Process highest-priority feature-request first

Advantage: Important features get processed faster
Disadvantage: Risk of starvation (low-priority features never processed)
```

### Option C: Adaptive Cycle Time

Instead of fixed 30-second cycles:

```
Orchestrator sleeps 30s if active work done
Orchestrator sleeps 0s if no work found (immediately retry)

Advantage: Responsive (don't wait 30s if nothing to do)
Disadvantage: Higher CPU/API usage during idle scanning
```

---

## Questions for Decision

1. **Throughput:** How many features/month do we need to process?
2. **Latency:** How long should a pm-idea take to become released?
3. **Feedback Loop Frequency:** What % of features need multiple QA/Design cycles?
4. **API Quota:** Any concerns about GitHub API rate limits?
5. **Deployment:** Will orchestrators run on same server or separate servers?
6. **Error Handling:** What happens if one orchestrator crashes?

---

## Conclusion

**Recommended model: Hybrid Parallel**

- All three orchestrators run concurrently
- Each processes one item per 30-second cycle (depth-first)
- Natural blocking points prevent starvation
- Self-regulating (no artificial waits)
- Maximum throughput within current architecture
- Low complexity (no complex coordination needed)

**Next steps to confirm:**
1. Run load test: Simulate 100 pm-ideas, measure throughput
2. Monitor feedback loops: Track cycle depth for features
3. Validate GitHub API impact: Measure actual QPS usage
4. Plan for scaling: What if we need 2x throughput?
