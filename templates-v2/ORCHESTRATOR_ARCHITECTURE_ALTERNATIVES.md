# Orchestrator Architecture Analysis - Structural Alternatives

## Current Architecture: Three Separate Orchestrators

```
PM Orchestrator (loop)         PO Orchestrator (loop)         Dev Orchestrator (loop)
├─ Loop every 30s              ├─ Loop every 30s              ├─ Loop every 30s
├─ Find actionable pm-idea     ├─ Find actionable strg-opp    ├─ Find actionable feat-req
├─ Route based on labels       ├─ Route based on labels       ├─ Route based on labels
├─ Spawn agent task            ├─ Spawn agent task            ├─ Spawn agent task
├─ Wait & process output       ├─ Wait & process output       ├─ Wait & process output
└─ Update GitHub               └─ Update GitHub               └─ Update GitHub
(parallel processes)           (parallel processes)           (parallel processes)
```

### Problems with Current Design

**1. Massive Code Duplication**
- Loop logic duplicated 3x
- Label routing logic duplicated 3x
- GitHub state management duplicated 3x
- Error handling duplicated 3x
- ~300 lines per orchestrator × 3 = ~900 lines of nearly identical code

**2. Scattered Feedback Loops**
- PM feedback loops in pm-orchestrator
- PO feedback loops in po-orchestrator
- Dev feedback loops in dev-orchestrator
- Hard to reason about globally; bug fixes needed in 3 places

**3. No Cross-Pipeline Visibility**
- Can't easily ask: "What's the status of all issues across all pipelines?"
- Monitoring requires checking three separate systems
- If one orchestrator crashes, others continue (creating inconsistent state)

**4. Tightly Coupled to Domain**
- Add a new pipeline? Write entire new orchestrator
- Change loop timing? Update 3 files
- Fix state bug? Patch 3 orchestrators

**5. No Priority Coordination**
- If PM generates 10 pm-ideas but only 1 feature-request slots open in Dev, system still processes all 10 PM items
- No way to throttle PM based on Dev capacity
- Resource waste if PM is faster than PO

---

## Alternative 1: Unified Generic Orchestrator + Pipeline Configs

### Architecture

```
Master Orchestrator (single loop)
├─ Every 30s:
│  ├─ Query GitHub for ALL issues across all labels
│  ├─ Build priority queue (PM first, then PO, then Dev)
│  ├─ Find first actionable issue from queue
│  ├─ Dispatch to correct pipeline handler
│  └─ Wait for agent task
│
├─ PM Pipeline Handler (imported config)
│  ├─ Routing rules (Phase 1 gate → Research → Phase 2 gate)
│  ├─ Decision routing
│  └─ Label/state management
│
├─ PO Pipeline Handler (imported config)
│  ├─ Routing rules (Prioritization → Sequencing → Feature-requests)
│  ├─ Decision routing
│  └─ Label/state management
│
└─ Dev Pipeline Handler (imported config)
   ├─ Routing rules (Intake → Design → Build → QA → Policy → Release)
   ├─ Decision routing
   └─ Label/state management
```

### Advantages

✅ **Single loop implementation** (easier to debug, monitor, maintain)
✅ **Pipeline logic in separate configs** (can version, review, change independently)
✅ **No code duplication** (routing logic written once, reused)
✅ **Cross-pipeline visibility** (master can see all pipelines at once)
✅ **Easy to add new pipelines** (just write new config, plug into master)
✅ **Global priority coordination** (master can throttle PM if Dev is backed up)
✅ **Centralized monitoring** (all issues visible from one place)
✅ **Unified error handling** (one place to fix bugs, implement retries, etc.)

### Disadvantages

✗ More complex master orchestrator
✗ Requires significant refactoring
✗ Config format needs careful design

### Config Example (YAML-like)

```yaml
# pipelines/pm-pipeline.yaml
name: "PM Pipeline"
input_label: "pm-idea"
terminal_states: ["pm-opportunity", "pm-blocked", "pm-deferred"]
stages:
  - name: "Phase 1 Gate"
    condition: "has(pm-idea) && !has(pm-provisional-champion)"
    agent: "product-manager"
    task_description: "Run PM Phase 1 gate on issue #%{issue_number}: %{title}"
    outcomes:
      - decision: "PASS"
        actions:
          - label_add: "pm-provisional-champion"
          - route_to: "Research"
      - decision: "BLOCK"
        actions:
          - label_add: "pm-blocked"
          - close_issue: true
          
  - name: "Research"
    condition: "has(pm-provisional-champion) && !has(research-complete)"
    agent: "research-agent"
    task_description: "Run market research on issue..."
    outcomes:
      - decision: "HIGH_PRIORITY"
        actions:
          - label_add: "research-complete"
          - label_add: "research-priority-high"
          - route_to: "Phase 2 Gate"
```

---

## Alternative 2: Microservice Orchestrator Pattern

### Architecture

```
Master Orchestrator (single polling loop)
│
├─ Priority Scheduler
│  ├─ PM pipeline queue (N items)
│  ├─ PO pipeline queue (M items)
│  └─ Dev pipeline queue (K items)
│
├─ Pipeline Router
│  ├─ Route to PM handler if PM priority high
│  ├─ Route to PO handler if PO priority high
│  └─ Route to Dev handler if Dev priority high
│
├─ PM Handler
│  ├─ Route based on pm-idea labels/stage
│  └─ Spawn PM agent
│
├─ PO Handler
│  ├─ Route based on strg-opp labels/stage
│  └─ Spawn PO agent
│
├─ Dev Handler
│  ├─ Route based on feat-req labels/stage
│  └─ Spawn Dev agent
│
└─ Shared State Manager
   ├─ GitHub label operations
   ├─ GitHub comment operations
   ├─ Issue read/query operations
   └─ Error handling & retry logic
```

### Advantages

✅ **Single loop** (simpler than three loops)
✅ **Handler pattern allows reuse** (similar handlers for similar pipelines)
✅ **Centralized state management** (GitHub ops in one place)
✅ **Priority-aware scheduling** (can throttle based on capacity)
✅ **Easier to test** (mock handlers independently)
✅ **Gradual migration** (can refactor orchestrators one at a time)

### Disadvantages

✗ Requires refactoring existing orchestrators into handlers
✗ Moderately complex scheduler logic

---

## Alternative 3: Consolidated Single Orchestrator with Label-Based Routing

### Architecture (Simplest)

```
Single Orchestrator Loop (every 30s)
│
├─ Query GitHub for ALL issues
│  ├─ Labels: pm-idea, strategic-opportunity, feature-request
│  ├─ Plus all active stage labels
│  └─ Build unified action queue
│
├─ Priority Order Processing
│  1. Process any blocked issues (intake-blocked, design-blocked, etc.)
│  2. Process PM pipeline issues (oldest pm-idea first)
│  3. Process PO pipeline issues (oldest strg-opp first)
│  4. Process Dev pipeline issues (oldest feat-req first)
│
└─ Label-Based Routing
   ├─ if [pm-idea, !pm-*]:        PM Phase 1 Gate
   ├─ if [pm-provisional-champion, !research-complete]: Research Phase
   ├─ if [strategic-opportunity, !po-*]: PO Prioritization
   ├─ if [feature-request, !intake-approved]: Dev Intake
   ├─ if [intake-approved, !design-approved]: Dev Design
   └─ ... etc
```

### Code Structure

```python
# Single orchestrator
class AIOSOrchestrator:
    def __init__(self):
        self.pm_router = PMRouter()
        self.po_router = PORouter()
        self.dev_router = DevRouter()
        self.state_manager = GitHubStateManager()
    
    def run_cycle(self):
        issues = self.list_all_actionable_issues()
        for issue in self.priority_sort(issues):
            if self.is_pm_issue(issue):
                self.pm_router.route(issue)
            elif self.is_po_issue(issue):
                self.po_router.route(issue)
            elif self.is_dev_issue(issue):
                self.dev_router.route(issue)
```

### Advantages

✅ **Minimal refactoring** (rename orchestrators to routers)
✅ **Single loop, centralized logic** (easy to debug)
✅ **Unified priority scheduling** (master sees all pipelines)
✅ **No code duplication in loop** (loop written once)
✅ **Clear pipeline separation** (routers are independent)
✅ **Easiest to implement** (least refactoring)

### Disadvantages

✗ Still has three separate routers (some duplication remains)
✗ Label-based routing logic gets complex with many labels

---

## Comparison Matrix

| Factor | Current | Alt 1 (Generic) | Alt 2 (Microservice) | Alt 3 (Consolidated) |
|--------|---------|---|---|---|
| **Code duplication** | High (3x loop code) | None | Low | Low |
| **Maintenance burden** | High (3 places) | Low | Low | Low |
| **Adding new pipeline** | Rewrite orchestrator | Add config file | Add handler class | Add router class |
| **Cross-pipeline visibility** | No | Yes | Yes | Yes |
| **Priority coordination** | No | Yes | Yes | Yes |
| **Refactoring effort** | N/A | High | Medium | Low |
| **Operational complexity** | Medium (3 processes) | Low (1 process) | Low (1 process) | Low (1 process) |
| **Testing difficulty** | Medium | Low | Low | Medium |
| **Performance** | Good | Good | Good | Good |
| **Complexity of implementation** | Low | High | Medium | Low |

---

## My Recommendation: Alternative 3 (Consolidated Single Orchestrator)

### Why?

1. **Minimal refactoring** — Rename existing orchestrators to routers, keep domain logic intact
2. **Immediate benefits** — Single loop eliminates 2/3 of loop code duplication
3. **Scalable** — If we later need generic config approach, it's easier to extract from single orchestrator
4. **Pragmatic** — Don't over-engineer; solve the duplication problem first
5. **Low risk** — If it doesn't work, easy to revert to three orchestrators

### Implementation Path

```
Step 1: Create AIOSOrchestrator class
  └─ Has single 30-second loop
  
Step 2: Refactor existing orchestrators into routers
  PM Orchestrator → pm_router.route(issue)
  PO Orchestrator → po_router.route(issue)
  Dev Orchestrator → dev_router.route(issue)
  
Step 3: Move GitHub state management to shared manager
  All three routers use: self.state_manager.add_label(issue, label)
  
Step 4: Implement unified priority queue
  Queue sorted: [blocked issues] → [PM] → [PO] → [Dev]
  
Step 5: Add global monitoring
  Track pipeline queue depth
  Alert if any pipeline idle >10 cycles
  Monitor feedback loop depth
```

### Pseudocode

```python
class AIOSOrchestrator:
    def __init__(self):
        self.pm_router = PMRouter()
        self.po_router = PORouter()
        self.dev_router = DevRouter()
        self.state = GitHubStateManager()
        
    def run(self):
        """Main orchestration loop"""
        while True:
            self.run_cycle()
            sleep(30)
    
    def run_cycle(self):
        """Single cycle: process one issue across all pipelines"""
        git_checkout_and_pull()
        
        # Build unified queue
        pm_issues = self.query_pm_issues()
        po_issues = self.query_po_issues()
        dev_issues = self.query_dev_issues()
        blocked_issues = self.query_blocked_issues()
        
        # Priority order: blocked → PM → PO → Dev
        action_queue = (blocked_issues + pm_issues + po_issues + dev_issues)
        
        # Find first actionable
        for issue in action_queue:
            if not self.is_actionable(issue):
                continue
                
            if self.is_pm_issue(issue):
                self.pm_router.route(issue, self.state)
                return  # Process one per cycle
            
            elif self.is_po_issue(issue):
                self.po_router.route(issue, self.state)
                return
            
            elif self.is_dev_issue(issue):
                self.dev_router.route(issue, self.state)
                return
        
        # If nothing actionable, log and sleep
        logger.info("No actionable issues in this cycle")
```

---

## Long-Term Evolution

### Phase 1 (Now): Consolidated Single Orchestrator
- Merge three orchestrators into one
- Routers handle domain-specific logic
- Shared state manager handles GitHub

### Phase 2 (Later): Configurable Pipelines
- Extract router logic to YAML configs
- Support custom pipelines without code
- Example: Add "Release" pipeline, add "QA" pipeline, etc.

### Phase 3 (Future): Event-Driven
- Replace polling with GitHub webhooks
- Event triggers routing (instead of polling)
- Reduces latency from 30s to milliseconds

---

## Decision Questions

1. **Preferred refactoring timeline:** How much disruption can the team absorb?
   - Option 3 (Consolidated): ~2 hours
   - Option 2 (Microservice): ~4 hours
   - Option 1 (Generic Config): ~8 hours

2. **Future pipeline frequency:** Will we need many new pipelines soon?
   - If yes: Invest in Option 1 (configurable)
   - If no: Option 3 (consolidated) is sufficient

3. **Operational model:** Single server or distributed?
   - Single server: Option 3 preferred (single process)
   - Distributed: Option 2 or keep current model

4. **Team expertise:** How comfortable with complex refactoring?
   - Comfortable: Option 1 (go big)
   - Pragmatic: Option 3 (incremental)

---

## Conclusion

**Current architecture has significant duplication and scalability issues.**

**Recommendation: Alternative 3 (Consolidated Single Orchestrator)**
- Lowest refactoring effort
- Immediate maintenance benefits
- Enables future evolution to generic config approach
- Single loop simplifies debugging and monitoring
- Clear pathway to more sophisticated orchestration later

**Start there. If we later need more flexibility, Option 1 is available.**
