---
description: "Model routing strategy for orchestrated task execution. Maps agent task types to model tiers and guides orchestrators in optimal model selection for cost and latency."
---

# Model Routing Framework

## Overview

This framework optimizes task execution cost and latency by routing work to appropriately-sized models based on task complexity. Every spawned agent task declares its required model tier, and the orchestrator selects the best available model at that tier when launching the task.

**Core principle:** Reserve expensive models for tasks that genuinely need them (architecture, code, debugging). Use small/fast models for deterministic, structured, or simple tasks (classification, formatting, validation).

---

## Model Tiers

### FAST Tier
**Purpose:** Deterministic, structured, low-complexity tasks.
**Characteristics:** Small, cost-effective, optimized for consistency and speed.
**Latency:** 1-2 seconds per task.
**Cost:** Lowest per-token.

**Suitable for:**
- Field validation & structured data parsing
- Classification (PASS/FAIL, HIGH/MEDIUM/LOW, APPROVED/BLOCKED)
- Label selection & application
- Issue comment formatting & markdown generation
- Wiki title/section creation
- Simple decision rules with boolean logic
- Metadata extraction (issue number, title, branch name)
- JSON output generation from fixed templates
- Summarization of structured data (e.g., "Feature adds 3 files, 450 LOC")

**Examples:**
- Intake agent: validating required fields ✅
- Policy agent: applying tiered gating criteria ✅
- BA agent: formatting wiki edits, applying labels ✅
- QA agent: coverage % classification (70%+ PASS, <70% INCOMPLETE) ✅

---

### STANDARD Tier
**Purpose:** Analysis, observation, and moderate complexity.
**Characteristics:** Capable, balanced for reasoning and speed.
**Latency:** 5-10 seconds per task.
**Cost:** Moderate per-token.

**Suitable for:**
- Risk classification (LOW/MEDIUM/HIGH) with multi-factor analysis
- Test scenario documentation & observation recording
- Design decision critique & feedback
- Requirements clarification & ambiguity detection
- Decision rationale writing (post-execution explanation)
- Output quality validation (e.g., is this PR description clear?)
- Pattern recognition in logs/output
- Edge case analysis in defined scope

**Examples:**
- Design agent: evaluating low-risk vs high-risk changes ✅
- QA agent: running scenarios, documenting failures, analyzing timeouts ✅
- Intake agent: detecting subtle requirement ambiguities ✅

---

### EXPENSIVE Tier
**Purpose:** Complex reasoning, code generation, architecture, debugging.
**Characteristics:** Large, capable, optimized for deep analysis and creativity.
**Latency:** 15-30+ seconds per task.
**Cost:** Highest per-token.

**Suitable for:**
- Code implementation & architecture decisions
- Complex debugging (analyzing test failures, error chains)
- Design decisions: breaking changes, schema modifications, multi-team impact
- Novel approach evaluation ("Should we refactor this?")
- Complex failure root cause analysis
- Trade-off analysis & recommendation generation
- Integration with existing systems

**Examples:**
- Build agent: implementing code from design spec ✅
- Design agent: creating new feature architecture ✅
- Verification agent: debugging complex integration issues ✅

---

## Agent Model Tier Mapping

| Agent | Primary Tier | Alternate Tier | Routing Logic |
|-------|--------------|----------------|---------------|
| **Intake** | FAST | STANDARD | FAST for field validation; STANDARD if clarification needed (design feedback) |
| **Design** | EXPENSIVE | STANDARD | EXPENSIVE for new features/breaking changes; STANDARD for bug fixes |
| **Build** | EXPENSIVE | FAST | EXPENSIVE for implementation; FAST for retry after QA failure (already-approved design) |
| **QA** | STANDARD | FAST | STANDARD for scenario execution; FAST for coverage classification-only |
| **Policy** | FAST | STANDARD | FAST for tiered gating rules; STANDARD for edge case escalation |
| **Verification** | EXPENSIVE | STANDARD | EXPENSIVE for complex failures; STANDARD for simple documentation |
| **Research** | STANDARD | FAST | STANDARD for research synthesis; FAST for wiki formatting |
| **Business Analyst** | FAST | STANDARD | FAST for wiki updates/formatting; STANDARD for content synthesis |
| **Product Manager** | STANDARD | EXPENSIVE | STANDARD for Phase 1/2 gate decisions; EXPENSIVE for strategy trade-offs |
| **Product Owner** | STANDARD | FAST | STANDARD for prioritization logic; FAST for sequencing/labeling |

---

## Orchestrator Task Spawning Pattern

When orchestrators spawn agents, they declare the required model tier. The runtime selects the best available model at that tier.

### Pattern 1: Single Tier (Most Common)

```bash
task(
  description="Run intake validation on issue #NUMBER: TITLE",
  agent_id="intake",
  model_tier="FAST"  # Deterministic field validation
)
```

### Pattern 2: Tier with Fallback (Flexible Complexity)

```bash
# Design work - try expensive first, fall back to standard if needed
task(
  description="Create design for issue #NUMBER: TITLE",
  agent_id="design",
  model_tier="EXPENSIVE"
)
```

### Pattern 3: Conditional Tier (Context-Dependent)

```bash
# Intake re-clarification based on design feedback - might need more reasoning
# Use STANDARD tier since it's already partially understood
task(
  description="Re-clarify requirements based on design feedback for issue #NUMBER",
  agent_id="intake",
  model_tier="STANDARD"  # More complex than initial validation
)
```

---

## Orchestrator Updates

### PM Orchestrator

**Phase 1 Gate (Product Manager):**
```bash
task(description="Run PM Phase 1 gate on issue #NUMBER: TITLE", 
     agent_id="product-manager",
     model_tier="STANDARD")  # Gate decision logic
```

**Research Execution (Research Agent):**
```bash
task(description="Run market research on issue #NUMBER: TITLE", 
     agent_id="research-agent",
     model_tier="STANDARD")  # Synthesis of findings
```

**Phase 2 Gate (Product Manager):**
```bash
task(description="Run PM Phase 2 full validation on issue #NUMBER: TITLE", 
     agent_id="product-manager",
     model_tier="STANDARD")  # Strategy & validation
```

### PO Orchestrator

**Prioritization (Product Owner):**
```bash
task(description="Prioritize strategic opportunity #NUMBER", 
     agent_id="product-owner",
     model_tier="STANDARD")  # Priority reasoning
```

**Sequencing & Feature Creation (Product Owner):**
```bash
task(description="Sequence and create feature request for #NUMBER", 
     agent_id="product-owner",
     model_tier="FAST")  # Label application, deterministic sequencing
```

### Dev Orchestrator

**Intake (Intake Agent):**
```bash
task(description="Intake validation on issue #NUMBER: TITLE", 
     agent_id="intake",
     model_tier="FAST")  # Field validation
```

**Intake Re-clarification (after design feedback):**
```bash
task(description="Re-clarify requirements based on design feedback for #NUMBER", 
     agent_id="intake",
     model_tier="STANDARD")  # More complex reasoning
```

**Design (Design Agent):**
```bash
task(description="Design issue #NUMBER: TITLE", 
     agent_id="design",
     model_tier="EXPENSIVE")  # Architecture decisions
```

**Build (Build Agent):**
```bash
task(description="Build issue #NUMBER: TITLE", 
     agent_id="build",
     model_tier="EXPENSIVE")  # Code implementation
```

**Build Fix (after QA failure):**
```bash
task(description="Fix QA test failures on issue #NUMBER", 
     agent_id="build",
     model_tier="FAST")  # Bug fixes in already-designed code
```

**QA (QA Agent):**
```bash
task(description="QA issue #NUMBER: TITLE", 
     agent_id="qa",
     model_tier="STANDARD")  # Scenario execution & observation
```

**Policy (Policy Agent):**
```bash
task(description="Evaluate policy gate for issue #NUMBER", 
     agent_id="policy",
     model_tier="FAST")  # Tiered gating criteria
```

**Verification (Verification Agent):**
```bash
task(description="Verify and release issue #NUMBER", 
     agent_id="verification",
     model_tier="EXPENSIVE")  # Complex integration verification
```

---

## Runtime Model Selection

When an orchestrator spawns a task with `model_tier="FAST"`, the runtime:

1. **Query available models** at that tier
2. **Select the best available:**
   - If multiple FAST models exist, pick one (prioritize lowest cost)
   - If FAST not available, escalate to STANDARD (if acceptable for task type)
   - If neither available, queue task and retry
3. **Inject model selection** into agent environment so agent knows what model it's using
4. **Log model tier + model name** in agent output for transparency

---

## Cost & Latency Impact

### Realistic Scenario: 5 Concurrent Features (Dev Pipeline)

**Naive (all EXPENSIVE models):**
- 5 features × 4 EXPENSIVE tasks (design, build, QA, verification) = 20 expensive tasks
- 20 × 20 seconds average = 400 seconds = 6.7 min
- Cost: High (all premium tokens)

**Optimized (with model routing):**
- 5 Intake (FAST): 5 × 2s = 10s (concurrent)
- 5 Design (EXPENSIVE): 5 × 15s = 75s (limited expensive capacity)
- 5 Build (EXPENSIVE): 5 × 18s = 90s (batched after design)
- 5 QA (STANDARD): 5 × 8s = 40s (concurrent, during build)
- 5 Policy (FAST): 5 × 1s = 5s (concurrent)
- Verification (EXPENSIVE): 1 × 20s = 20s (single path-to-production)
- **Total: ~125 seconds** (dominated by expensive tasks, others overlap)
- **Cost: 60-70% lower** (intake, policy, QA handle bulk of workload on cheap models)

---

## Implementation Checklist

- [ ] Add `model_tier` parameter to all orchestrator `task()` calls
- [ ] Update each agent's YAML frontmatter to declare primary & alternate tiers
- [ ] Update agent "Task Capability Requirements" sections to map to tier definitions
- [ ] Test model tier injection in agent environment
- [ ] Document tier selection strategy in team runbooks
- [ ] Monitor actual latency & cost impact after deployment
