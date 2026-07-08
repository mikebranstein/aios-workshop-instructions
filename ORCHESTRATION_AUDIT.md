# Comprehensive Agentic Orchestration Audit
**Date:** 2026-07-08  
**Scope:** Complete workflow analysis of PM/PO/Development orchestrators and specialist agents  
**Focus:** State management, handoff efficiency, modularity, and frontier pattern alignment  

---

## Executive Summary

Your agentic OS implements a **three-loop independent orchestration model** that is conceptually elegant and scales well. However, there are significant opportunities to:

1. **Consolidate handoff logic** currently scattered across orchestrator files
2. **Eliminate redundant state management** (labels + comments contain overlapping information)
3. **Adopt centralized state machines** instead of label-driven ad-hoc routing
4. **Modularize decision routing** into reusable components
5. **Implement proper async patterns** (currently manual polling vs event-driven)

### Current Strengths
✅ **Three independent loops** (PM, PO, Dev) allow parallel execution  
✅ **Deterministic skill contracts** ensure consistent decisions  
✅ **GitHub issues as audit trail** provides full observability  
✅ **Feedback loops exist** (Design REVISE → Intake, QA incomplete → Design)  
✅ **Depth-first processing** prevents starvation  

### Critical Gaps vs Frontier Patterns
❌ **Manual polling orchestration** (30-60s cycle loops with sleep) vs event-driven (webhooks)  
❌ **Scattered routing logic** across 3 orchestrator files + multiple agent files  
❌ **Overlapping state representations** (labels serve multiple purposes)  
❌ **No centralized state registry** (hard to audit global system state)  
❌ **Limited error recovery** (stuck agents detected by timeout, no auto-retry logic)  
❌ **No transaction safety** (race conditions possible between parallel orchestrators)  
❌ **Skill contracts lack versioning** (contracts change, but agents don't know which version they're executing)  

---

## Part 1: Current Architecture Deep Dive

### 1.1 Three-Loop Orchestration Model

```
┌─────────────────────────────────────────────────────────────┐
│                   GitHub Issue Stream                        │
│  (pm-idea submissions + strategic-opportunities + backlog)   │
└────┬───────────────────────────┬──────────────────────┬─────┘
     │                           │                      │
     ▼                           ▼                      ▼
┌─────────────┐           ┌────────────┐        ┌──────────────┐
│ PM Loop     │           │ PO Loop    │        │ Dev Loop     │
│ Terminal 1  │           │ Terminal 2 │        │ Terminal 3   │
└─────────────┘           └────────────┘        └──────────────┘
     │                           │                      │
     ├─ Find pm-idea            ├─ Find strategic-op   ├─ Find feature-req
     ├─ Phase 1: Quick gate      ├─ Prioritize         ├─ Intake validation
     ├─ Spawn Research Agent     ├─ Create feature-req ├─ Design
     ├─ Phase 2: Full validation ├─ Close strategic-op ├─ Build
     └─ Create strategic-op      └─ Move to backlog    ├─ QA
                                                       ├─ Verification
                                                       ├─ Policy
                                                       └─ Release
```

**Key Characteristic:** Independent state machines. Each loop reads GitHub fresh each cycle, makes local decisions, posts results. No direct agent-to-agent communication.

### 1.2 Current State Representation

#### PM Loop State (pm-idea issue)
```
pm-idea (NEW)
  ├─ pm-validating (transient, Phase 1 in progress)
  ├─ pm-provisional-champion (OPEN, research executing)
  ├─ pm-finalizing (transient, Phase 2 in progress)
  ├─ pm-opportunity (CLOSED, CHAMPION outcome)
  ├─ pm-deferred (CLOSED, DEFER outcome)
  └─ pm-blocked (CLOSED, BLOCK outcome)

research: issues (created by PM Phase 1)
  ├─ research: (permanent identifier)
  ├─ pm-idea-[N] (links to parent)
  ├─ research-complete (when CLOSED)
  └─ wiki-error (if wiki operations failed)
```

**Problem:** Labels are transient state markers. Multiple labels may be active simultaneously, creating ambiguity (e.g., both `pm-provisional-champion` and `pm-finalizing` can be present, but orchestrator must distinguish between "research complete, Phase 2 waiting" and "Phase 2 in progress").

#### Development Pipeline State (feature-request issue)
```
feature-request (NEW)
  ├─ [none] (awaiting Intake)
  ├─ intake-approved
  ├─ design-approved
  ├─ build-complete
  ├─ qa-passed
  ├─ verification-passed
  ├─ policy-approved
  ├─ release-ready
  └─ released (CLOSED)

Also may have:
  ├─ blocked-on (dependency blocker)
  ├─ policy-escalated (needs leadership approval)
  └─ policy-blocked (critical risk, needs PM+Design acceptance)
```

**Problem:** Labels don't capture the full state machine. An issue can have multiple "stage" labels simultaneously (e.g., `intake-approved` + `design-approved` if design runs twice). No clear single source of truth for current stage.

### 1.3 Handoff Mechanisms

#### Pattern A: Orchestrator → Specialist Agent (Pull-Based)
```
Orchestrator reads GitHub issue
  ↓
Detects label state (e.g., no labels = needs intake)
  ↓
Spawns specialist agent (e.g., intake.agent.md)
  ↓
Agent runs autonomously:
  - Reads issue + comments
  - Evaluates skill contract rules
  - Posts JSON decision as comment
  ↓
Orchestrator re-reads issue
  ↓
Parses decision JSON from comment
  ↓
Applies new labels + routes to next stage
```

**Issue:** Manual parsing of JSON from comments (string regex matching, error-prone). No strong type safety.

#### Pattern B: Research Agent → Wiki Manager (Skill Invocation)
```
Research Agent executes
  ↓
Calls wiki-manager skill with:
  { "action": "write-page", "page": "Personas-X", "content": "..." }
  ↓
wiki-manager.skill.md centrally handles all wiki operations
  ↓
Research Agent receives success/error response
  ↓
Closes research: issue with wiki-error label if failed
```

**Strength:** Centralized wiki operations prevent conflicts. Clear interface.
**Weakness:** One skill, one issue. Doesn't scale to N concurrent agents needing wiki access.

#### Pattern C: Feedback Loop (Design REVISE → Intake)
```
Design Agent posts decision:
  { "decision": "REVISE", "clarifications_needed": [...] }
  ↓
Orchestrator reads decision
  ↓
Orchestrator removes design-approved label
  ↓
Orchestrator adds intake-blocked label
  ↓
Next cycle: Orchestrator routes back to Intake
  ↓
Intake Agent reads design decision comment
  ↓
Clarifies based on design feedback
  ↓
Re-routes to Design
```

**Problem:** Orchestrator must know about feedback loop logic. If you add a new feedback loop (e.g., from Policy → Build), you must modify orchestrator code. Not modular.

### 1.4 Current Agent Ecosystem

#### Specialist Agents (Spawned by Orchestrators)
| Agent | Spawned By | Input | Output Decision |
|-------|-----------|-------|-----------------|
| intake.agent.md | dev-orch | feature-request issue | READY \| BLOCKED |
| design.agent.md | dev-orch | feature-request + intake-approved | PASS \| REVISE \| BLOCKED |
| business-analyst.agent.md | dev-orch | feature-request + intake-blocked | CLARIFY \| AUTHOR \| ESCALATE |
| build.agent.md | dev-orch (in skills/) | feature-request + design-approved | COMPLETE \| PARTIAL \| BLOCKED |
| qa.agent.md | dev-orch | feature-request + build-complete | PASS \| FAIL \| TEST_COVERAGE_INCOMPLETE |
| verification.agent.md | dev-orch | feature-request + qa-passed | PASS \| FAIL |
| policy.agent.md | dev-orch | feature-request + verification-passed | APPROVE \| ESCALATE \| BLOCK |
| product-manager.agent.md | pm-orch | pm-idea + research results | CHAMPION \| DEFER \| BLOCK |
| product-owner.agent.md | po-orch | strategic-opportunity | [creates feature-request] |
| research-agent.md | pm-orch | research: items | [updates wiki, closes items] |

**Problem:** Each orchestrator spawns agents independently. No registry of "who can do what". Adding a new stage requires modifying orchestrator routing logic.

---

## Part 2: Frontier Pattern Comparison

### 2.1 CrewAI Pattern (Production Framework)

**Core Concept:** Crews (agent teams) + Flows (event-driven orchestration)

```python
# Crews: Autonomous agent teams with structured outputs
crew = Crew(
  agents=[intake_agent, design_agent, qa_agent],
  tasks=[intake_task, design_task, qa_task],
  output_format=PydanticModel(decision: str, reasoning: str, next_state: str)
)

# Flows: Event-driven state machines with persistence
flow = Flow(
  name="FeatureFlow",
  state=FlowState(issue_id, current_stage, history),
  
  # Declarative transitions
  transitions=[
    ("INTAKE", "intake_complete", "DESIGN"),
    ("DESIGN", "needs_clarification", "INTAKE"),
    ("DESIGN", "approved", "BUILD"),
  ],
  
  @flow.start()
  def start(state):
    state.current_stage = "INTAKE"
    
  @flow.listen_to("intake_complete")  # Event-driven, not polling
  def route_to_design(state):
    state.current_stage = "DESIGN"
    
  @flow.persist()  # Auto-checkpoint to DB
  def checkpoint(state):
    db.save(state)
)

flow.run()  # Continuous, event-driven
```

**Key Patterns:**
- **Explicit state machines** (not label-driven)
- **Event-driven** (webhook triggers, not polling)
- **Declarative transitions** (define how, not code it)
- **Persistence** (auto-checkpoint, resume from failure)
- **Type safety** (Pydantic models, not JSON string parsing)

### 2.2 LangGraph Pattern (Maximum Control)

**Core Concept:** Explicit DAG topology with checkpointing

```python
# Define nodes (agents/functions)
def intake_node(state):
    decision = intake_agent.decide(state.issue)
    return {"intake_decision": decision}

def design_node(state):
    if state.intake_decision == "BLOCKED":
        return {"stage": "escalation"}
    design_output = design_agent.decide(state.issue)
    return {"design_decision": design_output}

# Define routing (conditional edges)
def route_after_intake(state):
    if state.intake_decision.decision == "BLOCKED":
        return "escalation"
    return "design"

# Build graph
workflow = StateGraph(FeatureState)
workflow.add_node("intake", intake_node)
workflow.add_node("design", design_node)
workflow.add_node("escalation", escalation_node)

workflow.add_edge("intake", route_after_intake)  # Conditional
workflow.add_edge("design", "qa")                 # Direct

# Compile with checkpointing
graph = workflow.compile(checkpointer=PostgresCheckpointer())
graph.invoke({"issue_id": 123})
```

**Key Patterns:**
- **Explicit node topology** (vs implicit label-driven routing)
- **Conditional edges** (code the routing logic once)
- **Checkpointing** (resume from any node on failure)
- **State graph** (full system state in one place)
- **Debugging** (LangSmith provides full trace)

### 2.3 Microsoft Agent Framework (Enterprise)

**Core Concept:** Multi-provider agents with cross-runtime interoperability

```python
# Agents are first-class, versioned
agent_registry = AgentRegistry()
agent_registry.register(
    IntakeAgent(version="2.0", 
    required_inputs=["issue_id", "team_context"],
    output_schema=IntakeDecision
))

# Orchestrators reference agents by name + version
orchestrator = Orchestrator(
    agents=["intake:2.0", "design:1.5", "qa:2.1"],
    routing_rules=RouterConfig(
        default_route="intake:2.0",
        conditional_routes={
            "intake:blocked": "escalation:1.0",
            "design:revise": "intake:2.0",
        }
    )
)

# Auto-handles provider switching (Claude → GPT-4 → Llama)
for issue in issues:
    result = orchestrator.process(issue)  # Provider chosen automatically
```

**Key Patterns:**
- **Agent versioning** (contracts + implementations versioned together)
- **Agent registry** (central repository of "who can do what")
- **Provider abstraction** (switch models without changing orchestrator)
- **Explicit routing rules** (separate from orchestrator loop logic)

### 2.4 Key Gap: Your System vs Frontier

| Dimension | Your System | Frontier Pattern | Impact |
|-----------|-------------|------------------|--------|
| **Orchestration** | Manual polling (sleep loops) | Event-driven (webhooks) | Latency: 30-60s vs <1s |
| **State Management** | Label-driven, ad-hoc | Explicit state machine | Ambiguity vs clarity |
| **Routing Logic** | Scattered in orchestrator code | Declarative routing config | Hard to modify vs easy |
| **Handoff Type** | Async via comments + labels | Typed state transitions | String parsing vs type safety |
| **Error Recovery** | Timeout detection + retry | Built-in checkpointing | Manual vs automatic |
| **Agent Discovery** | Implicit (orchestrator knows agents) | Registry + versioning | Coupling vs modularity |
| **Feedback Loops** | Hard-coded per loop | Declarative edges | Custom code vs config |
| **Observability** | GitHub issue timeline | Centralized trace DB | Issues vs structured logs |

---

## Part 3: Detailed Gap Analysis

### 3.1 State Management Issues

#### Issue 1: Label Ambiguity
**Current:**
```
Feature-request has labels: [design-approved, qa-passed]
Orchestrator must determine: Is this in QA stage or completed QA?
```

**Why problematic:** 
- If both labels exist, did the issue skip Build? Or is it in two stages?
- Logic to detect invalid states is complex
- No single source of truth for "current stage"

**Frontier approach:**
```json
{
  "issue_id": 123,
  "current_stage": "qa",  // Single authoritative state
  "stage_history": ["intake", "design", "build"],
  "metadata": { "started_at": "...", "stage_entry_time": "..." }
}
```

#### Issue 2: Transient vs Terminal Labels
**Current:**
```
pm-validating (transient, Phase 1 in progress)
pm-provisional-champion (semi-persistent, research executing)
pm-opportunity (terminal, Phase 2 complete)
```

**Why problematic:**
- Orchestrator must know which labels are transient
- If orchestrator crashes, transient labels can be left on issues (orphaned state)
- Cleanup logic required

**Frontier approach:**
```python
class PMIdeaState(Enum):
    NEW = "new"
    PHASE_1_IN_PROGRESS = "phase_1_in_progress"
    RESEARCH_IN_PROGRESS = "research_in_progress"
    PHASE_2_IN_PROGRESS = "phase_2_in_progress"
    CHAMPION_COMPLETE = "champion_complete"
    DEFERRED = "deferred"
    BLOCKED = "blocked"
```

#### Issue 3: Dual State Representation (Labels + Comments)
**Current:**
```
Issue has label: design-approved
Issue has comment JSON: { "decision": "REVISE", "clarifications": [...] }
```

**Problem:**
- Label says "approved" but comment says "revise"
- Which is source of truth?
- Possible races: label updated but comment parsing fails

**Frontier approach:**
- State is in ONE place (database state machine)
- Comments are audit trail only, not source of truth

### 3.2 Handoff Inefficiencies

#### Issue 1: Manual JSON Parsing from Comments
**Current:**
```bash
# Orchestrator code
DECISION=$(gh issue view $ISSUE --json comments | grep -A 5 "INTAKE_DECISION" | jq '.decision')
```

**Problem:**
- String parsing is error-prone
- No schema validation
- Changes to JSON format break parsing

**Frontier approach:**
```python
# Typed decision object
@dataclass
class IntakeDecision:
    decision: str  # READY | BLOCKED
    missing_fields: List[str]
    confidence: float
    
decision = IntakeDecision(**parsed_json)  # Type-safe
```

#### Issue 2: Polling vs Event-Driven
**Current:**
```
Orchestrator loop:
  1. Sleep 30s
  2. Query GitHub for new issues
  3. Check label state
  4. Spawn agent if needed
  5. Go to 1
```

**Problems:**
- 30-60s latency before detection
- Wasted API calls (most cycles find no new work)
- Difficult to handle urgent issues

**Frontier approach:**
```
GitHub Webhook (real-time event)
  ├─ Issue created
  ├─ Trigger CrewAI Flow immediately
  └─ No polling needed
```

#### Issue 3: Comment-Based State Transitions
**Current:**
```
Agent posts decision as comment JSON
Orchestrator polls issue comments
Parses comment
Applies labels
Routes to next stage
```

**Problems:**
- Each handoff requires GitHub API call + regex parsing + label application
- If comment parsing fails, orchestrator doesn't know
- Audit trail is implicit in comments, not explicit

**Frontier approach:**
```
Agent returns typed decision
Orchestrator applies decision directly to state
State machine handles routing
State automatically persisted to DB
Audit trail is separate (immutable log)
```

### 3.3 Modularity Issues

#### Issue 1: Routing Logic Scattered
**Current:**
- orchestrator.pm.agent.md: lines 60-120 (PM routing logic)
- orchestrator.po.agent.md: lines 40-80 (PO routing logic)
- orchestrator.development.agent.md: lines 100-200 (Dev routing logic)
- Plus: Each agent has feedback loop logic hardcoded

**Problem:**
- To add a new stage, modify 3+ files
- To add a feedback loop, modify orchestrator + agent
- Hard to test routing logic independently

**Frontier approach:**
```python
# Single routing config
routing_config = {
    "intake": {"success": "design", "blocked": "escalation"},
    "design": {"approved": "build", "revise": "intake"},
    "build": {"complete": "qa", "blocked": "escalation"},
    "qa": {"incomplete": "design", "passed": "verification"},
    # ... etc
}

# Orchestrator applies config declaratively
orchestrator = StateMachineOrchestrator(routing_config)
```

#### Issue 2: Three Separate Orchestrators
**Current:**
```
pm-orch (Terminal 1)
po-orch (Terminal 2)
dev-orch (Terminal 3)
```

**Problem:**
- Difficult to see global system state
- No single place to monitor all three loops
- Cross-orchestrator debugging is manual

**Frontier approach:**
```python
# Single orchestration runtime
orchestration = Orchestration(
    flows=[
        Flow(name="PM Discovery", config=pm_config),
        Flow(name="PO Prioritization", config=po_config),
        Flow(name="Dev Pipeline", config=dev_config),
    ]
)

# All three run in one place (or one per machine, but unified)
orchestration.run()  # Single entry point
```

#### Issue 3: Agent Implementation Scattered
**Current:**
- intake.agent.md (agent)
- intake-agent.md (skill contract)
- Orchestrator spawning logic (references both)

**Problem:**
- Easy to accidentally use wrong version
- No versioning of contracts vs implementations
- No registry of agent capabilities

**Frontier approach:**
```python
# Agent with versioned contract
@agent(version="2.0")
class IntakeAgent:
    skill_contract = IntakeSkill(version="2.0")
    
    def execute(self, issue) -> IntakeDecision:
        # Implementation
        
# Registry
registry = AgentRegistry()
registry.register(IntakeAgent)

# Orchestrator discovers and uses
agent = registry.get("intake", version="2.0")
```

### 3.4 Error Handling Gaps

#### Issue 1: Stuck Agent Detection
**Current:**
```
pm-validating label exists for > 1 hour
→ Orchestrator assumes agent crashed
→ Orchestrator removes label and retries
```

**Problem:**
- Timeout is arbitrary (could be 1h, 2h, etc.)
- No clear error signal from agent
- Retry logic is manual

**Frontier approach:**
```python
@flow.on_error(max_retries=3, backoff=exponential)
def intake_node(state):
    return intake_agent.decide(state)  # Auto-retry on error
```

#### Issue 2: Partial Failures
**Current:**
```
Research agent updates wiki, but wiki_manager fails on last write
Research agent catches error, posts wiki-error label
Orchestrator skips this research: item
But PM Phase 2 may not know to wait
```

**Problem:**
- Error propagation is implicit
- Manual reconciliation required

**Frontier approach:**
```
Flow checkpointing ensures all-or-nothing
If any step fails, entire flow rolls back
Automatically resumes from checkpoint
No partial state
```

#### Issue 3: No Centralized Error Log
**Current:**
- Errors are in GitHub comments
- No structured error tracking
- Difficult to aggregate and alert on

**Frontier approach:**
```python
# Structured error logging
error_logger = ErrorRegistry()

for flow_result in flows:
    if flow_result.error:
        error_logger.log(
            flow_id=flow_result.flow_id,
            stage=flow_result.current_stage,
            error=flow_result.error,
            retry_count=flow_result.retries
        )

# Alert if error rate > threshold
if error_logger.error_rate() > 0.1:
    alert("High error rate in dev pipeline")
```

---

## Part 4: Recommendations for Modularization & Optimization

### 4.1 Consolidate State Management with Obsidian

**Recommendation 1: Obsidian Vault for State Management (Git-Synced)**

Instead of scattering state across GitHub labels, use an Obsidian vault (markdown files) as your source of truth:

```
aios-state-vault/ (Git repository)
  ├── state/
  │   ├── issue-123.md (current state for feature request #123)
  │   ├── issue-124.md
  │   └── index.md (index of all issues)
  ├── decisions/
  │   ├── issue-123-intake-decision.md
  │   ├── issue-123-design-decision.md
  │   └── issue-123-build-decision.md
  └── metrics.md (running pipeline metrics)
```

**Example State File (`state/issue-123.md`):**

```markdown
# Issue 123: Equipment Checkout Feature

## Current State
- **Issue Number:** 123
- **Title:** Equipment Checkout Feature
- **Stage:** Design
- **Stage Entry Time:** 2026-07-08T10:30:00Z
- **Priority Score:** 2.5
- **Status:** ⏳ In Progress

## Stage History
1. **Intake** (2026-07-08T09:00:00Z → 2026-07-08T09:15:00Z) ✅ READY
2. **Design** (2026-07-08T09:15:00Z → current) ⏳ In Progress

## Latest Decision
```json
{
  "stage": "design",
  "decision": "REVISE",
  "design_summary": "Scope needs clarification",
  "clarifications_needed": ["Field mapping not specified", "Edge cases unclear"],
  "agent": "design.agent",
  "timestamp": "2026-07-08T09:20:00Z",
  "duration_ms": 45000
}
```

## Related Issues
- **Parent:** [[strategic-opportunity-45]]
- **Blocked By:** [[issue-119]]
- **Related:** [[issue-120]]

## Notes
- Design review showed scope ambiguity
- Awaiting clarification from BA
- No blockers currently
```

**Implementation:**

```python
from pathlib import Path
from datetime import datetime
import json
import subprocess
from typing import Dict, List, Optional

class ObsidianStateManager:
    """Markdown-based state management with git sync"""
    
    def __init__(self, vault_path: str, repo_path: str):
        self.vault_path = Path(vault_path)
        self.repo_path = repo_path
        self.state_dir = self.vault_path / "state"
        self.decisions_dir = self.vault_path / "decisions"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.decisions_dir.mkdir(parents=True, exist_ok=True)
    
    def load_state(self, issue_id: int) -> Optional[Dict]:
        """Load current state from markdown file"""
        
        state_file = self.state_dir / f"issue-{issue_id}.md"
        
        if not state_file.exists():
            return None
        
        content = state_file.read_text()
        
        # Parse markdown to extract state
        state = {
            'issue_id': issue_id,
            'current_stage': self._extract_field(content, 'Stage'),
            'stage_entry_time': self._extract_field(content, 'Stage Entry Time'),
            'priority_score': float(self._extract_field(content, 'Priority Score') or 0),
            'status': self._extract_field(content, 'Status'),
            'latest_decision': self._extract_json_block(content, 'Latest Decision'),
            'stage_history': self._extract_stage_history(content),
        }
        
        return state
    
    def transition_state(self, issue_id: int, new_stage: str, decision: dict):
        """Update state file and commit to git"""
        
        state_file = self.state_dir / f"issue-{issue_id}.md"
        
        # Load existing state (if any)
        old_content = state_file.read_text() if state_file.exists() else None
        old_stage = self._extract_field(old_content, 'Stage') if old_content else None
        
        # Generate new state file
        new_content = self._render_state_file(
            issue_id=issue_id,
            new_stage=new_stage,
            decision=decision,
            old_stage=old_stage,
            old_content=old_content
        )
        
        # Write atomically
        state_file.write_text(new_content)
        
        # Record decision in decisions/ directory
        decision_file = self.decisions_dir / f"issue-{issue_id}-{new_stage}-decision-{datetime.now().isoformat()}.md"
        decision_file.write_text(self._render_decision_file(issue_id, new_stage, decision))
        
        # Commit to git
        self._git_commit(
            files=[state_file, decision_file],
            message=f"Issue #{issue_id}: {old_stage or 'NEW'} → {new_stage}\n\n{decision.get('reasoning', '')}"
        )
    
    def _render_state_file(self, issue_id: int, new_stage: str, decision: dict, 
                           old_stage: Optional[str], old_content: Optional[str]) -> str:
        """Generate markdown state file"""
        
        now = datetime.now().isoformat() + "Z"
        
        # Parse existing history
        history = []
        if old_content:
            history = self._extract_stage_history(old_content)
        
        # Add old stage to history
        if old_stage:
            history.append({
                'stage': old_stage,
                'entered': self._extract_field(old_content, 'Stage Entry Time'),
                'exited': now,
                'status': '✅ Completed'
            })
        
        # Render history
        history_md = ""
        for i, entry in enumerate(history, 1):
            duration = self._calculate_duration(entry.get('entered'), entry.get('exited'))
            history_md += f"{i}. **{entry['stage']}** ({entry.get('entered', '?')} → {entry.get('exited', '?')}) {entry['status']} ({duration})\n"
        
        # Build markdown
        return f"""# Issue {issue_id}: Equipment Checkout Feature

## Current State
- **Issue Number:** {issue_id}
- **Stage:** {new_stage}
- **Stage Entry Time:** {now}
- **Priority Score:** {decision.get('priority_score', 'TBD')}
- **Status:** ⏳ In Progress

## Stage History
{history_md}

## Latest Decision
```json
{json.dumps({
    **decision,
    'timestamp': now,
    'stage': new_stage,
}, indent=2)}
```

## Related Issues
- **Parent:** [[strategic-opportunity-45]]

## Notes
- Last updated: {now}
- Decision: {decision.get('decision', 'TBD')}
"""
    
    def _render_decision_file(self, issue_id: int, stage: str, decision: dict) -> str:
        """Generate decision audit file"""
        
        now = datetime.now().isoformat() + "Z"
        
        return f"""# Decision: Issue {issue_id} → {stage}

**Timestamp:** {now}  
**Agent:** {decision.get('agent', 'unknown')}  
**Duration:** {decision.get('duration_ms', '?')}ms

## Decision
- **Outcome:** {decision.get('decision', '?')}
- **Reasoning:** {decision.get('reasoning', 'N/A')}

## Details
```json
{json.dumps(decision, indent=2)}
```

## Next Stage
- {decision.get('next_stage', 'unknown')}
"""
    
    def _git_commit(self, files: List[Path], message: str):
        """Commit changes to git"""
        
        try:
            for f in files:
                subprocess.run(
                    ["git", "add", str(f)],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True
                )
            
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
        
        except subprocess.CalledProcessError as e:
            print(f"Git operation failed: {e}")
    
    def get_all_issues_in_stage(self, stage: str) -> List[int]:
        """Query: find all issues in a given stage"""
        
        issues = []
        
        for state_file in self.state_dir.glob("issue-*.md"):
            content = state_file.read_text()
            current_stage = self._extract_field(content, 'Stage')
            
            if current_stage == stage:
                issue_id = int(state_file.stem.split('-')[1])
                issues.append(issue_id)
        
        return issues
    
    def _extract_field(self, content: str, field_name: str) -> Optional[str]:
        """Parse markdown field value"""
        
        import re
        if not content:
            return None
        pattern = rf"- \*\*{re.escape(field_name)}:\*\* (.+)"
        match = re.search(pattern, content)
        return match.group(1) if match else None
    
    def _extract_json_block(self, content: str, label: str = "Latest Decision") -> Optional[Dict]:
        """Extract JSON from markdown code block"""
        
        import re
        if not content:
            return None
        
        # Find code block after label
        pattern = rf"## {re.escape(label)}\n```json\n(.*?)\n```"
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
        
        return None
    
    def _extract_stage_history(self, content: str) -> List[Dict]:
        """Extract stage history from markdown"""
        
        import re
        if not content:
            return []
        
        # Find history section
        pattern = r"## Stage History\n(.*?)(?=##|$)"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return []
        
        history = []
        lines = match.group(1).strip().split('\n')
        
        for line in lines:
            if line.startswith(tuple('0123456789')):
                # Parse: "1. **Intake** (2026-07-08T09:00:00Z → 2026-07-08T09:15:00Z) ✅ Completed"
                pattern = r"^\d+\. \*\*(.+?)\*\* \((.+?) → (.+?)\) (.+)$"
                m = re.search(pattern, line)
                if m:
                    history.append({
                        'stage': m.group(1),
                        'entered': m.group(2),
                        'exited': m.group(3),
                        'status': m.group(4)
                    })
        
        return history
    
    def _calculate_duration(self, start: Optional[str], end: Optional[str]) -> str:
        """Calculate duration between two timestamps"""
        
        if not start or not end:
            return "?"
        
        try:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            duration = end_dt - start_dt
            
            minutes = int(duration.total_seconds() / 60)
            if minutes < 60:
                return f"{minutes}m"
            else:
                hours = minutes / 60
                return f"{hours:.1f}h"
        
        except (ValueError, AttributeError):
            return "?"
```

**Benefits:**
- ✅ **Version-controlled** — Full history in git, reviewable in PRs
- ✅ **Human-readable** — Can read state directly in Obsidian/text editor
- ✅ **Single source of truth** — One markdown file per issue
- ✅ **No infrastructure** — Just files + git
- ✅ **Audit trail** — Decision history preserved in decisions/ directory
- ✅ **Portable** — Works offline, exportable
- ✅ **Team visibility** — State visible in vault before commit

### 4.2 Centralize Routing Logic

**Recommendation 2: Create Routing Registry**

```python
# routing.py
class RoutingRegistry:
    """Define all stage transitions in one place"""
    
    ROUTES = {
        IssueStage.INTAKE: {
            "ready": IssueStage.DESIGN,
            "blocked": IssueStage.ESCALATION,
        },
        IssueStage.DESIGN: {
            "approved": IssueStage.BUILD,
            "revise": IssueStage.INTAKE,  # Feedback loop declared once
            "blocked": IssueStage.ESCALATION,
        },
        IssueStage.BUILD: {
            "complete": IssueStage.QA,
            "partial": IssueStage.BUILD,  # Re-run build
            "blocked": IssueStage.ESCALATION,
        },
        # ... all transitions declared here
    }
    
    @staticmethod
    def get_next_stage(current_stage: IssueStage, decision: str) -> IssueStage:
        return RoutingRegistry.ROUTES[current_stage].get(decision)
    
    @staticmethod
    def is_feedback_loop(from_stage: IssueStage, to_stage: IssueStage) -> bool:
        return from_stage > to_stage  # If going backwards, it's a feedback loop
```

**Benefits:**
- All routing logic in one place
- Easy to visualize full workflow
- Adding new stage is just adding entries to dict
- Feedback loops explicitly marked

### 4.3 Modularize Orchestration Loop

**Recommendation 3: Extract Orchestration Core**

```python
# orchestrator_core.py
class OrchestrationLoop:
    """Reusable orchestration core"""
    
    def __init__(
        self, 
        state_manager: IssueStateManager,
        agent_registry: AgentRegistry,
        routing_registry: RoutingRegistry,
        name: str
    ):
        self.state_manager = state_manager
        self.agent_registry = agent_registry
        self.routing_registry = routing_registry
        self.name = name
    
    def run_one_cycle(self, query: str) -> int:
        """Single orchestration cycle. Returns # issues processed."""
        
        # Step 1: Find issues matching criteria (query)
        issues = self.find_issues(query)
        
        if not issues:
            return 0
        
        # Step 2: For each issue, determine current stage
        for issue in issues:
            state = self.state_manager.load(issue.id)
            current_stage = state.current_stage
            
            # Step 3: Spawn appropriate agent for this stage
            agent = self.agent_registry.get(current_stage)
            
            # Step 4: Execute agent
            result = agent.execute(issue)
            
            # Step 5: Determine next stage using routing registry
            next_stage = self.routing_registry.get_next_stage(
                current_stage, 
                result.decision
            )
            
            # Step 6: Update state
            self.state_manager.transition(issue.id, next_stage, result)
        
        return len(issues)
    
    def run_continuous(self, poll_interval_seconds: int = 30):
        """Continuous orchestration loop"""
        
        while True:
            try:
                processed = self.run_one_cycle()
                if processed > 0:
                    print(f"{self.name}: Processed {processed} issues")
            except Exception as e:
                print(f"{self.name}: Error in cycle: {e}")
            
            time.sleep(poll_interval_seconds)

# Now use it
pm_orchestrator = OrchestrationLoop(
    state_manager=state_manager,
    agent_registry=registry,
    routing_registry=RoutingRegistry,
    name="PM Discovery"
)

po_orchestrator = OrchestrationLoop(
    state_manager=state_manager,
    agent_registry=registry,
    routing_registry=RoutingRegistry,
    name="PO Prioritization"
)

dev_orchestrator = OrchestrationLoop(
    state_manager=state_manager,
    agent_registry=registry,
    routing_registry=RoutingRegistry,
    name="Development Pipeline"
)

# Run all three in parallel
threads = [
    threading.Thread(target=pm_orchestrator.run_continuous),
    threading.Thread(target=po_orchestrator.run_continuous),
    threading.Thread(target=dev_orchestrator.run_continuous),
]

for t in threads:
    t.start()
```

**Benefits:**
- Three orchestrators use same core logic
- No duplication
- Easy to add 4th orchestrator (just call `OrchestrationLoop` again)
- Testable core

### 4.4 Upgrade to Event-Driven (Optional)

**Recommendation 4: Add Webhook-Based Triggering**

```python
# Instead of polling, use GitHub webhooks
@app.route('/webhook/issue-event', methods=['POST'])
def handle_issue_event():
    event = request.json
    
    if event['action'] == 'opened':
        issue_id = event['issue']['number']
        
        # Immediately trigger orchestrator for this issue
        state_manager.create_initial_state(issue_id)
        
        # Determine which orchestrator should handle
        if has_label(event['issue'], 'pm-idea'):
            pm_orchestrator.process_issue(issue_id)
        elif has_label(event['issue'], 'feature-request'):
            dev_orchestrator.process_issue(issue_id)
    
    elif event['action'] == 'labeled':
        # Issue was labeled (e.g., agent posted decision and new label applied)
        issue_id = event['issue']['number']
        
        # Trigger immediate re-evaluation
        dev_orchestrator.process_issue(issue_id)
    
    return {'status': 'ok'}
```

**Benefits:**
- <1s latency vs 30-60s polling
- No wasted API calls
- Scales better

### 4.5 Decouple Agents from Orchestrators

**Recommendation 5: Create Agent Interface**

```python
# agent_interface.py
@dataclass
class AgentInput:
    issue_id: int
    issue_data: Dict[str, Any]
    previous_decision: Optional[Dict] = None  # If this is feedback loop
    agent_config: Optional[Dict] = None

@dataclass
class AgentOutput:
    decision: str  # READY, BLOCKED, PASS, REVISE, etc.
    reasoning: str
    next_stage: Optional[str] = None  # Agent can suggest next stage
    metadata: Optional[Dict] = None

class AgentInterface(ABC):
    @abstractmethod
    def execute(self, input: AgentInput) -> AgentOutput:
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        pass

# Concrete implementation
class IntakeAgent(AgentInterface):
    @property
    def version(self) -> str:
        return "2.0"
    
    def execute(self, input: AgentInput) -> AgentOutput:
        # Implementation using skill contract
        decision = self.evaluate_intake(input.issue_data)
        return AgentOutput(
            decision=decision.get('decision'),
            reasoning=decision.get('summary'),
            metadata=decision
        )
```

**Benefits:**
- Agents are interchangeable
- Easy to swap implementations (LLM-based vs rule-based)
- Version management built-in

### 4.6 Add Observability

**Recommendation 6: Centralized Metrics & Tracing**

```python
# observability.py
class OrchestrationObserver:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def record_stage_entry(self, issue_id: int, stage: IssueStage, timestamp: float):
        self.db.log({
            'event': 'stage_entry',
            'issue_id': issue_id,
            'stage': stage.value,
            'timestamp': timestamp
        })
    
    def record_agent_execution(self, issue_id: int, agent_name: str, result: AgentOutput, duration_ms: float):
        self.db.log({
            'event': 'agent_execution',
            'issue_id': issue_id,
            'agent': agent_name,
            'decision': result.decision,
            'duration_ms': duration_ms,
            'timestamp': time.time()
        })
    
    def record_error(self, issue_id: int, stage: IssueStage, error: Exception, retry_count: int):
        self.db.log({
            'event': 'error',
            'issue_id': issue_id,
            'stage': stage.value,
            'error_type': type(error).__name__,
            'error_msg': str(error),
            'retry_count': retry_count,
            'timestamp': time.time()
        })
    
    def get_pipeline_metrics(self, hours: int = 24) -> Dict:
        """Get system-wide metrics"""
        return {
            'avg_stage_duration': self.db.query("SELECT stage, AVG(duration) FROM events"),
            'error_rate': self.db.query("SELECT COUNT(*) FROM events WHERE event='error'") / 
                          self.db.query("SELECT COUNT(*) FROM events WHERE event='stage_entry'"),
            'bottleneck_stages': self.db.query("SELECT stage FROM events ORDER BY duration DESC LIMIT 3"),
        }
```

**Benefits:**
- See full workflow metrics
- Identify bottlenecks
- Debug failures easily

---

## Part 5: Implementation Roadmap (Non-Breaking v2 Approach)

### Architecture: Parallel Implementation in `templates-v2/`

**Key Constraint:** All new work goes into `templates-v2/` folder. Legacy `templates/agents/` and `templates/skills/` remain untouched. This allows side-by-side testing and gradual migration.

```
aios-workshop-instructions/
├── templates/ (LEGACY - UNTOUCHED)
│   ├── agents/ (all existing .agent.md files)
│   ├── skills/ (all skill contracts)
│   └── ...
│
├── templates-v2/ (NEW - ALL REFACTORING GOES HERE)
│   ├── orchestration/
│   │   ├── .prompts/
│   │   │   ├── orchestration-loop-pattern.md (reusable pattern)
│   │   │   ├── pm-orchestrator-v2.agent.md
│   │   │   ├── po-orchestrator-v2.agent.md
│   │   │   └── dev-orchestrator-v2.agent.md
│   │   ├── routing-registry.md (reference copy)
│   │   └── README.md (setup guide)
│   │
│   └── state-manager/
│       ├── state_manager.py (ObsidianStateManager class)
│       └── README.md (usage guide)
│
├── ORCHESTRATION_AUDIT.md (this file)
└── OBSIDIAN_STATE_MANAGEMENT.md (state vault setup guide)

aios-state-vault/ (SEPARATE REPO)
├── state/
├── decisions/
├── routing-registry.md (authoritative)
└── metrics.md
```

### Phase 1: Foundation - Obsidian State Management + Templates-v2 Setup (1 week)

#### 1.1 Create aios-state-vault Repository (External)
- [ ] Create new GitHub repo: `aios-state-vault/`
- [ ] Initialize folder structure: `state/`, `decisions/`, `metrics/`
- [ ] Create `.gitignore`, `README.md`
- [ ] Initial commit and push

#### 1.2 Create templates-v2 Folder Structure (In Workshop Repo)
- [ ] Create `templates-v2/orchestration/.prompts/` folder
- [ ] Create `templates-v2/state-manager/` folder
- [ ] Create `templates-v2/README.md` explaining v2 approach

#### 1.3 Copy Supporting Files to templates-v2
- [ ] Copy `ObsidianStateManager` class to `templates-v2/state-manager/state_manager.py`
- [ ] Create `templates-v2/state-manager/README.md` (usage guide)
- [ ] Create `templates-v2/orchestration/.prompts/orchestration-loop-pattern.md` (reusable pattern)

#### 1.4 Create PM Orchestrator v2
- [ ] Create `templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md`
- [ ] Uses orchestration-loop-pattern.md
- [ ] Integrates ObsidianStateManager
- [ ] Posts "[STATE UPDATE]" comments to GitHub

#### 1.5 Test PM Orchestrator v2
- [ ] Run PM orchestrator against sample issue
- [ ] Verify `state/issue-N.md` files created in vault
- [ ] Verify git commits working
- [ ] Verify GitHub comments posted
- [ ] **Result:** PM v2 operational, state vault syncing

### Phase 2: Routing Registry + Modular Orchestration (1 week)

#### 2.1 Create Routing Registry Template
- [ ] Define `templates-v2/orchestration/routing-registry.md`
- [ ] Document all stage transitions (PM, PO, Dev)
- [ ] Document all feedback loops (Design REVISE → Intake, etc.)
- [ ] Mirror content syncs with vault

#### 2.2 Create PO Orchestrator v2
- [ ] Create `templates-v2/orchestration/.prompts/po-orchestrator-v2.agent.md`
- [ ] Uses orchestration-loop-pattern.md
- [ ] References routing-registry.md for transitions
- [ ] Integrates ObsidianStateManager

#### 2.3 Create Dev Orchestrator v2
- [ ] Create `templates-v2/orchestration/.prompts/dev-orchestrator-v2.agent.md`
- [ ] Uses orchestration-loop-pattern.md
- [ ] References routing-registry.md for transitions
- [ ] Integrates ObsidianStateManager

#### 2.4 Test All Three v2 Orchestrators
- [ ] Run all three orchestrators in parallel
- [ ] Verify state updates coordinated correctly
- [ ] Verify feedback loops working
- [ ] **Result:** Full v2 orchestration operational, ready for cutover

### Phase 3: Observability & Metrics (1 week)

#### 3.1 Add Metrics to ObsidianStateManager
- [ ] Add methods: `get_metrics()`, `get_stuck_issues()`, `get_stage_durations()`
- [ ] Auto-generate `metrics.md` in state vault

#### 3.2 Create Metrics Dashboard
- [ ] Create `templates-v2/orchestration/metrics-dashboard.md` template
- [ ] Orchestrators query and display metrics each cycle

#### 3.3 Implement Stuck Issue Detection
- [ ] Issues stuck >2 hours in any stage trigger alerts
- [ ] Alerts posted to GitHub + recorded in vault

### Phase 4: Cutover & Cleanup (Optional)
- [ ] Run v2 orchestrators for 1 week (parallel with v1)
- [ ] Verify all issues processed correctly
- [ ] Archive legacy v1 orchestrators
- [ ] Full migration complete

---

## Part 6: Quick Wins - Templates-v2 Implementation (Can Start Immediately)

### Within 1-2 Hours: File Structure
1. **Create folders** (5 min)
   - `templates-v2/orchestration/.prompts/`
   - `templates-v2/state-manager/`

2. **Copy state manager** (10 min)
   - Copy `state_manager.py` from OBSIDIAN_STATE_MANAGEMENT.md to `templates-v2/state-manager/`
   - Create README explaining usage

3. **Create pattern documentation** (30 min)
   - Create `templates-v2/orchestration/.prompts/orchestration-loop-pattern.md`
   - Document the 5-step loop all orchestrators follow

### Within 3-4 Hours: PM Orchestrator v2
4. **Create PM orchestrator v2** (2 hours)
   - Create `templates-v2/orchestration/.prompts/pm-orchestrator-v2.agent.md`
   - Follows orchestration-loop-pattern.md
   - Integrates ObsidianStateManager

5. **Test PM orchestrator** (1 hour)
   - Run against sample issue
   - Verify state files created
   - Verify GitHub comments posted

**Total Quick Wins: ~5-6 hours for Phase 1 foundation**

---

## Conclusion: Non-Breaking Modernization via templates-v2

Your agentic OS orchestration is solid. The improvements recommended—specifically **Obsidian-based state management via templates-v2**—are:

### Why templates-v2 (Not Rewriting Existing)

**Benefits of parallel implementation:**

| Concern | templates-v2 Approach | Direct Rewrite |
|---------|----------------------|-----------------|
| **Risk** | ✅ None (legacy untouched) | ❌ High (breaks existing) |
| **Testing** | ✅ Side-by-side comparison | ⚠️ Must validate everything |
| **Rollback** | ✅ Trivial (keep v1) | ❌ Difficult if issues found |
| **Learning** | ✅ Compare v1 vs v2 behavior | ⚠️ Binary (works or doesn't) |
| **Team Buy-In** | ✅ Opt-in migration | ❌ Forced cutover |
| **Documentation** | ✅ Both versions documented | ⚠️ Only v2 matters |

**Key Decision:** Build v2 as clean new implementation, test thoroughly side-by-side with v1, then cutover when confident.

### Implementation Priorities

**Phase 1 (This Week):** Foundation
1. Create `templates-v2/` folder structure
2. Implement PM orchestrator v2 with Obsidian state
3. Verify state file generation + GitHub comments

**Phase 2 (Next Week):** Full Orchestration
1. Create routing registry
2. Implement PO and Dev orchestrators v2
3. Test all three working together

**Phase 3 (Optional):** Polish
1. Add observability metrics
2. Implement stuck issue detection

### What This Solves

**Before (Current v1):**
- State scattered across labels + comments
- Routing logic duplicated in 3 files
- Hard to audit global system state
- No metrics/observability

**After (With v2 in templates-v2/):**
- ✅ Single source of truth per issue (state/issue-N.md)
- ✅ Centralized routing (routing-registry.md)
- ✅ Clear audit trail (decision files + git history)
- ✅ Easy observability (metrics.md auto-generated)
- ✅ **Legacy untouched** (v1 still works, safe to migrate gradually)

### Architecture Summary

```
Run Both Versions in Parallel (During Transition)
│
├─ templates/agents/ (v1 orchestrators)
│  └─ Process issues, update GitHub labels/comments
│
└─ templates-v2/orchestration/ (v2 orchestrators)
   └─ Process same issues, update Obsidian vault + GitHub comments
   
Both update same GitHub issues → v2 state is visible + auditable
Once v2 proven stable → cutover, archive v1
```

---

## Next Steps

1. **Create `aios-state-vault/` repository** (git-synced Obsidian vault)
2. **Implement `ObsidianStateManager`** (code provided above, ~100 lines)
3. **Migrate PM orchestrator** to use state manager (replace label parsing)
4. **Test** state file generation and git sync
5. **Open vault in Obsidian** and visualize state graph
6. **Proceed to Phase 2:** Extract `RoutingRegistry` and centralize routing logic

**Estimated time to Phase 1 completion: 1 week**

This audit is now tailored to Obsidian approach. All recommendations integrate seamlessly with git-synced markdown state management.

