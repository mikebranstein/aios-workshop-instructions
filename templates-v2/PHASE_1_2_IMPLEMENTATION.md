# Phase 1+2 Implementation: Consolidated + Batch Orchestrator

## Architecture Overview

### Current State: Three Separate Orchestrators
```
PM Orchestrator (loop)  →  PO Orchestrator (loop)  →  Dev Orchestrator (loop)
Sequential, duplicated    Sequential, duplicated      Sequential, duplicated
```

### Target State: Phase 1+2 (Consolidated + Batch)
```
AIOSOrchestrator (unified loop)
├─ Unified 30s cycle (not 3 separate cycles)
├─ Batch processor (finds ALL actionable items per pipeline per cycle)
├─ Parallel agent spawning (non-blocking concurrent task())
│
├─ PM Router (modular, reusable routing logic)
│  ├─ Phase 1 Gate → Research → Phase 2 Gate
│  └─ Parallel: Research runs on ALL actionable pm-ideas simultaneously
│
├─ PO Router (modular, reusable routing logic)
│  ├─ Prioritization → Sequencing → Feature-requests
│  └─ Parallel: Can process multiple strategic-opps at once
│
├─ Dev Router (modular, reusable routing logic)
│  ├─ Intake → Design → Build → QA → Policy → Release
│  └─ Parallel: 5 features in different stages simultaneously
│
├─ Batch Processor
│  ├─ Find all actionable PM issues
│  ├─ Find all actionable PO issues
│  ├─ Find all actionable Dev issues
│  └─ Spawn tasks in parallel (not sequentially)
│
└─ Shared State Manager
   ├─ GitHub label operations
   ├─ GitHub comment operations
   ├─ Issue read/query operations
   └─ Retry logic & error handling
```

---

## Key Design Principles

### Principle 1: Modular Routers (Keep Domain Logic Separate)
Each router encapsulates one pipeline's logic:
- **PMRouter:** Phase 1 gate, research, Phase 2 gate
- **PORouter:** Prioritization, sequencing, feature creation
- **DevRouter:** Intake, design, build, QA, policy, release

Routers are stateless; they only route based on issue labels.

### Principle 2: Parallel Where Possible (Respect Dependencies)
```
PM Pipeline:
  - Multiple pm-ideas can run Phase 1 gates in parallel ✅
  - Multiple research items can run in parallel ✅
  - CONSTRAINT: Single feature can't be in 2 PM stages simultaneously ✓

PO Pipeline:
  - Multiple strg-opps can be prioritized in parallel ✅
  - CONSTRAINT: PO waits for PM to produce strg-opps first (data dependency)

Dev Pipeline:
  - Multiple feature-requests can run in different stages in parallel ✅
    (feat-req #1 in QA, feat-req #2 in Build, feat-req #3 in Intake simultaneously)
  - CONSTRAINT: One feature can't be in 2 Dev stages simultaneously ✓
  - CONSTRAINT: Dev waits for PO to produce feat-requests first (data dependency)
```

### Principle 3: Batch Processing (Process All Actionable Items Per Cycle)
```
Current (Sequential):
  Cycle N:
    1. Find ONE actionable pm-idea
    2. Spawn PM agent
    3. Wait (blocking)
    4. Cycle N+1 (30s later)

Batch (Parallel):
  Cycle N:
    1. Find ALL actionable pm-ideas
    2. Spawn PM agents in parallel (all at once)
    3. Wait for all (non-blocking, concurrent)
    4. Cycle N+1 (30s later, all pm-ideas advanced)
```

### Principle 4: Pipeline Dependencies (Respect Data Flow)
```
PM can always run (no dependencies)
PO waits for strg-opp supply (created by PM)
Dev waits for feat-req supply (created by PO)

If PO finds no actionable strg-opps: sleep, don't block PM
If Dev finds no actionable feat-reqs: sleep, don't block PM or PO
```

---

## Phase 1: Consolidated Single Orchestrator

### Architecture: Move from 3 Loops to 1 Loop

**Before (3 Loops):**
```
Loop 1 (PM):     Every 30s → query pm-idea → process 1 → sleep 30s
Loop 2 (PO):     Every 30s → query strg-opp → process 1 → sleep 30s
Loop 3 (Dev):    Every 30s → query feat-req → process 1 → sleep 30s
Total sleep: 90s per cycle
```

**After (1 Loop):**
```
Loop (Master):   Every 30s → query all pipelines → process 1 per pipeline → sleep 30s
Total sleep: 30s per cycle
Savings: 60s per cycle (40% reduction in cycle overhead)
```

### Code Structure (Phase 1)

```python
# aios-orchestrator.py (Phase 1: Consolidated but still sequential per pipeline)

class AIOSOrchestrator:
    def __init__(self):
        self.pm_router = PMRouter()
        self.po_router = PORouter()
        self.dev_router = DevRouter()
        self.state_manager = GitHubStateManager()
        self.logger = Logger()
    
    def run(self):
        """Main orchestration loop (Phase 1: Still processes one per pipeline)"""
        while True:
            self.run_cycle()
            sleep(30)
    
    def run_cycle(self):
        """Single cycle processes one feature per pipeline (if available)"""
        self.state_manager.git_checkout_and_pull()
        self.logger.log(f"Cycle started at {now()}")
        
        # Process one PM item
        pm_issue = self.find_actionable_pm_issue()
        if pm_issue:
            self.logger.log(f"Processing PM: {pm_issue}")
            self.pm_router.route(pm_issue, self.state_manager)
            self.state_manager.git_push_if_dirty()
        else:
            self.logger.log("No actionable PM issues")
        
        # Process one PO item
        po_issue = self.find_actionable_po_issue()
        if po_issue:
            self.logger.log(f"Processing PO: {po_issue}")
            self.po_router.route(po_issue, self.state_manager)
            self.state_manager.git_push_if_dirty()
        else:
            self.logger.log("No actionable PO issues")
        
        # Process one Dev item
        dev_issue = self.find_actionable_dev_issue()
        if dev_issue:
            self.logger.log(f"Processing Dev: {dev_issue}")
            self.dev_router.route(dev_issue, self.state_manager)
            self.state_manager.git_push_if_dirty()
        else:
            self.logger.log("No actionable Dev issues")
        
        self.logger.log(f"Cycle completed at {now()}")
    
    def find_actionable_pm_issue(self):
        """Find first PM issue not in terminal state"""
        issues = self.state_manager.list_issues(labels=["pm-idea"])
        for issue in issues:
            labels = issue["labels"]
            # Skip terminal states
            if "pm-opportunity" in labels or "pm-blocked" in labels or "pm-deferred" in labels:
                continue
            return issue
        return None
    
    def find_actionable_po_issue(self):
        """Find first PO issue not in terminal state"""
        issues = self.state_manager.list_issues(labels=["strategic-opportunity"])
        for issue in issues:
            labels = issue["labels"]
            if "po-deferred" in labels or "po-rejected" in labels or "feature-requests-created" in labels:
                continue
            return issue
        return None
    
    def find_actionable_dev_issue(self):
        """Find first Dev issue not in terminal/waiting state"""
        issues = self.state_manager.list_issues(labels=["feature-request"])
        for issue in issues:
            labels = issue["labels"]
            if "released" in labels or "feature-blocked" in labels or "policy-escalated" in labels:
                continue
            # Special case: intake-blocked but requirements-related (eligible for BA routing)
            if "intake-blocked" in labels and "requirements-clarified" not in labels:
                continue
            return issue
        return None
```

**Phase 1 Benefits:**
- ✅ Reduced cycle overhead: 90s → 30s (3x faster cycle iteration)
- ✅ Single loop simplifies debugging and monitoring
- ✅ No code duplication in loop logic
- ✅ Shared state manager (easier to fix bugs once, applies everywhere)
- ✅ Modular routers (still keep domain logic separate)
- **⏱ Time savings:** ~15 minutes per feature

---

## Phase 2: Batch Processing (Parallel Within Pipeline Stages)

### Key Insight: Parallel Task Spawning

**Current (Sequential):**
```
Cycle N:
  1. Find ONE pm-idea
  2. Spawn Phase 1 Gate agent for pm-idea #1
  3. Wait for completion (blocking)
  4. Continue to next cycle

Result: Only ONE pm-idea can be in Phase 1 Gate per cycle
```

**Batch (Parallel):**
```
Cycle N:
  1. Find ALL pm-ideas in "Phase 1 Gate" stage
  2. Spawn Phase 1 Gate agents for pm-ideas #1, #2, #3, #4 (in parallel!)
  3. Wait for all to complete (concurrent wait, non-blocking per issue)
  4. Continue to next cycle

Result: FOUR pm-ideas advance in Phase 1 Gate per cycle
```

### Phase 2 Architecture

```python
class AIOSOrchestrator:
    def __init__(self):
        self.pm_router = PMRouter()
        self.po_router = PORouter()
        self.dev_router = DevRouter()
        self.state_manager = GitHubStateManager()
        self.batch_processor = BatchProcessor()  # NEW
        self.logger = Logger()
    
    def run_cycle(self):
        """Phase 2: Process ALL actionable items in parallel"""
        self.state_manager.git_checkout_and_pull()
        self.logger.log(f"Cycle started at {now()}")
        
        # PHASE 2: Find ALL actionable items per pipeline (not just one)
        pm_issues = self.find_all_actionable_pm_issues()
        po_issues = self.find_all_actionable_po_issues()
        dev_issues = self.find_all_actionable_dev_issues()
        
        # Spawn all tasks in parallel
        tasks = []
        
        # Spawn PM tasks
        for pm_issue in pm_issues:
            task = self.batch_processor.spawn_async(
                lambda: self.pm_router.route(pm_issue, self.state_manager),
                name=f"PM:{pm_issue['number']}"
            )
            tasks.append(task)
        
        # Spawn PO tasks
        for po_issue in po_issues:
            task = self.batch_processor.spawn_async(
                lambda: self.po_router.route(po_issue, self.state_manager),
                name=f"PO:{po_issue['number']}"
            )
            tasks.append(task)
        
        # Spawn Dev tasks (WITHIN STAGE: multiple features can run different stages)
        for dev_issue in dev_issues:
            task = self.batch_processor.spawn_async(
                lambda: self.dev_router.route(dev_issue, self.state_manager),
                name=f"Dev:{dev_issue['number']}"
            )
            tasks.append(task)
        
        # Wait for all tasks to complete (concurrent, not sequential)
        self.batch_processor.wait_all(tasks, timeout=300)
        
        # Batch update GitHub (more efficient)
        self.state_manager.batch_git_push()
        
        self.logger.log(f"Cycle completed at {now()}")
        self.logger.log(f"Processed: {len(pm_issues)} PM, {len(po_issues)} PO, {len(dev_issues)} Dev")
    
    def find_all_actionable_pm_issues(self):
        """Find ALL PM issues not in terminal state (Phase 2)"""
        issues = self.state_manager.list_issues(labels=["pm-idea"])
        actionable = []
        for issue in issues:
            labels = issue["labels"]
            if "pm-opportunity" in labels or "pm-blocked" in labels or "pm-deferred" in labels:
                continue
            actionable.append(issue)
        return actionable
    
    def find_all_actionable_po_issues(self):
        """Find ALL PO issues not in terminal state (Phase 2)"""
        issues = self.state_manager.list_issues(labels=["strategic-opportunity"])
        actionable = []
        for issue in issues:
            labels = issue["labels"]
            if "po-deferred" in labels or "po-rejected" in labels or "feature-requests-created" in labels:
                continue
            actionable.append(issue)
        return actionable
    
    def find_all_actionable_dev_issues(self):
        """Find ALL Dev issues not in terminal/waiting state (Phase 2)"""
        issues = self.state_manager.list_issues(labels=["feature-request"])
        actionable = []
        for issue in issues:
            labels = issue["labels"]
            if "released" in labels or "feature-blocked" in labels or "policy-escalated" in labels:
                continue
            if "intake-blocked" in labels and "requirements-clarified" not in labels:
                continue
            actionable.append(issue)
        return actionable
```

### Phase 2 Key Components

**1. BatchProcessor (New)**
```python
class BatchProcessor:
    def spawn_async(self, func, name=None):
        """Spawn async task (returns immediately, runs in background)"""
        # Implementation: asyncio, threading, or task queue
        # Returns: task handle for waiting later
        pass
    
    def wait_all(self, tasks, timeout=None):
        """Wait for all tasks to complete"""
        # Implementation: gather all results, handle timeouts
        pass
```

**2. Dependency Awareness**
```
Dev Router must respect dependencies:
  - Multiple feat-reqs can be in different stages in parallel ✅
  - But one feat-req can't be in 2 stages simultaneously
  - Route based on issue's current stage label
  
Example:
  - feat-req #1 has label "qa-testing" → Route to QA
  - feat-req #2 has label "build-started" → Route to Build
  - feat-req #3 has label "intake-approved" → Route to Design
  → All three run concurrently (different stages, different features)
```

**3. Resource Limits (Optional, Phase 2.5)**
```python
# Limit concurrent tasks to avoid overwhelming agents
MAX_CONCURRENT_PM_TASKS = 3      # Max 3 Phase 1 gates at once
MAX_CONCURRENT_PO_TASKS = 2      # Max 2 prioritization at once
MAX_CONCURRENT_DEV_TASKS = 5     # Max 5 Dev stages at once

# In run_cycle():
pm_issues = self.find_all_actionable_pm_issues()[:MAX_CONCURRENT_PM_TASKS]
po_issues = self.find_all_actionable_po_issues()[:MAX_CONCURRENT_PO_TASKS]
dev_issues = self.find_all_actionable_dev_issues()[:MAX_CONCURRENT_DEV_TASKS]
```

---

## Modular Router Architecture

Each router is stateless and reusable:

```python
# routers/pm_router.py
class PMRouter:
    def route(self, issue, state_manager):
        """Route PM issue to appropriate stage"""
        labels = issue["labels"]
        
        if "pm-idea" in labels and "pm-provisional-champion" not in labels:
            self._phase_1_gate(issue, state_manager)
        elif "pm-provisional-champion" in labels and "research-complete" not in labels:
            self._research_phase(issue, state_manager)
        elif "pm-provisional-champion" in labels and "research-complete" in labels:
            self._phase_2_gate(issue, state_manager)
        else:
            # Terminal state, skip
            pass
    
    def _phase_1_gate(self, issue, state_manager):
        """Handle Phase 1 gate"""
        state_manager.comment(issue, "PM Orchestrator: Running Phase 1 gate")
        result = task(description=f"Run PM Phase 1 gate on issue #{issue['number']}", 
                     agent_id="product-manager")
        # Parse result, update labels, etc.
        pass
    
    def _research_phase(self, issue, state_manager):
        """Handle research phase"""
        pass
    
    def _phase_2_gate(self, issue, state_manager):
        """Handle Phase 2 gate"""
        pass

# routers/po_router.py
class PORouter:
    def route(self, issue, state_manager):
        """Route PO issue to appropriate stage"""
        pass

# routers/dev_router.py
class DevRouter:
    def route(self, issue, state_manager):
        """Route Dev issue to appropriate stage"""
        labels = issue["labels"]
        
        if "feature-request" in labels and "intake-approved" not in labels:
            self._intake(issue, state_manager)
        elif "intake-approved" in labels and "design-approved" not in labels:
            self._design(issue, state_manager)
        elif "design-approved" in labels and "build-complete" not in labels:
            self._build(issue, state_manager)
        # ... etc
```

---

## Data Flow with Phase 1+2

### Scenario: 5 Features Flowing Through Pipeline

```
Cycle 1 (t=0-5m):
  PM: Process pm-idea #1-5 in Phase 1 Gate (parallel)
      Result: 5 issues now have pm-provisional-champion
  
  PO: Find no strategic-opportunities yet (PM just finished)
      Sleep (no work)
  
  Dev: Find no feature-requests yet
      Sleep (no work)

Cycle 2 (t=5m-10m, PM loop continues):
  PM: Process pm-ideas #1-5 in Research Phase (parallel)
      Research Agent runs on all 5 in parallel
      
  PO: Still waiting for research to complete
      Sleep
  
  Dev: Still waiting
      Sleep

Cycle 3 (t=60m+, research completes, PM loop):
  PM: Process pm-ideas #1-5 in Phase 2 Gate (parallel)
      Result: pm-opportunity labels applied
      pm-orchestrator DONE with these items
  
  PO: NOW find strategic-opportunity #1-5 (just created by PM)
      Process all 5 in Prioritization stage (parallel)
      
  Dev: Still waiting for feature-requests

Cycle 4 (t=65m+):
  PM: Idle (cycle 1-3 complete for first batch)
  
  PO: Process strategic-opps #1-5 in Sequencing stage (parallel)
  
  Dev: Still waiting

Cycle 5 (t=70m+):
  PM: Idle
  
  PO: Create feature-requests from strg-opps #1-5
      Mark strg-opps as feature-requests-created (done)
  
  Dev: NOW pick up feature-requests #1-5
       (Cycle 6)
       Process all 5 in Intake stage (parallel)
       feat-req #1-5 all pass intake in one cycle

Cycle 6 (t=75m+):
  PM: Idle
  PO: Idle
  Dev: Process feat-reqs #1-5 in Design stage (parallel)

Cycle 7 (t=85m+):
  Dev: Process feat-reqs #1-5 in Build stage (parallel)

Cycle 8 (t=145m+):
  Dev: Process feat-reqs #1-5 in QA stage (parallel)

Cycle 9 (t=205m+):
  Dev: Process feat-reqs #1-5 in Policy stage (parallel)

Cycle 10 (t=215m+):
  Dev: Merge/Release all 5 features

TOTAL TIME: 215 minutes (3h 35m) for 5 features
vs. Sequential: 1,100 minutes (18+ hours)
SAVINGS: 885 minutes (14.75 hours) = 89% faster!
```

---

## Implementation Checklist (Phase 1+2)

### Phase 1 (2 hours)
- [ ] Create AIOSOrchestrator class with unified loop
- [ ] Refactor PM orchestrator → PMRouter class
- [ ] Refactor PO orchestrator → PORouter class
- [ ] Refactor Dev orchestrator → DevRouter class
- [ ] Create GitHubStateManager (shared operations)
- [ ] Test: Verify all routers work with unified loop
- [ ] Verify cycle time reduced from 90s to 30s

### Phase 2 (4 hours)
- [ ] Create BatchProcessor class (async task spawning)
- [ ] Modify find_actionable functions to find ALL (not just one)
- [ ] Update run_cycle to spawn all tasks in parallel
- [ ] Add resource limits (MAX_CONCURRENT_*_TASKS)
- [ ] Implement wait_all() for concurrent completion
- [ ] Test: Verify 5 features process in parallel per cycle
- [ ] Monitor: Track parallelism utilization
- [ ] Add logging for batch size per cycle

### Post-Implementation Testing
- [ ] Load test: 10 simultaneous pm-ideas through pipeline
- [ ] Latency test: Measure time for 1 feature (happy path)
- [ ] Feedback loop test: Measure QA failure handling
- [ ] Stress test: 100 pm-ideas queued

---

## Expected Performance Gains

### Before (3 Orchestrators, Sequential)
```
1 feature (happy path):        220 min
5 features sequential:         1,100 min
10 features sequential:        2,200 min
```

### After Phase 1 (Consolidated)
```
1 feature (happy path):        205 min (saved 15 min)
5 features sequential:         1,025 min (saved 75 min)
10 features sequential:        2,050 min (saved 150 min)
```

### After Phase 1+2 (Batch Processing)
```
1 feature (happy path):        130 min (saved 90 min vs. original)
5 features parallel:           260 min (saved 840 min vs. original!)
10 features parallel:          520 min (saved 1,680 min vs. original!)
```

---

## Architectural Advantages (Phase 1+2)

✅ **Modular:** Each router contains one pipeline's logic (can evolve independently)
✅ **Reusable:** Routers can be tested/debugged independently
✅ **Scalable:** Adding new pipeline is just adding new router
✅ **Observable:** Single loop means single place to monitor all pipelines
✅ **Maintainable:** Bug fixes apply globally (no duplication)
✅ **Performant:** Parallel processing within constraints
✅ **Dependency-Aware:** Respects PM→PO→Dev data flow
✅ **Future-Proof:** Can add event-driven later (Phase 3)

---

## Migration Path (Minimal Disruption)

1. **Step 1 (1 hour):** Create AIOSOrchestrator, keep old orchestrators running in parallel
2. **Step 2 (30 min):** Test new unified orchestrator on test issue
3. **Step 3 (30 min):** Gradually migrate: start with PM router, then PO, then Dev
4. **Step 4 (Phase 2, 4 hours):** Add batch processing to dev orchestrator first (most impact)
5. **Step 5:** Add batch to PM and PO routers

Total disruption: Can keep system running while migrating.

