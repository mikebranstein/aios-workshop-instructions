# Obsidian State Management - Implementation Guide

**Status:** Phase 1 Implementation Plan  
**Date:** 2026-07-08  
**Focus:** Git-synced Obsidian vault for orchestrator state

---

## Quick Start (30 minutes)

### Step 1: Create Obsidian Vault Repository (5 min)

```bash
# Create new repo for state vault
mkdir ~/aios-state-vault
cd ~/aios-state-vault

# Initialize git
git init
git branch -M main

# Create directory structure
mkdir -p state decisions metrics

# Create .gitignore
cat > .gitignore << 'EOF'
.DS_Store
.obsidian/
*.swp
EOF

# Create README
cat > README.md << 'EOF'
# AIOS State Vault

Git-synced Obsidian vault for agentic orchestration state management.

## Structure

- **state/** - Current issue states (one file per issue)
- **decisions/** - Audit trail of decisions and transitions
- **metrics.md** - Running metrics and statistics

## Setup

1. Open in Obsidian: File → Open Vault → Select this folder
2. Create a new note to verify it syncs to git

## Queries

- All in Design: `state grep "Stage: design"`
- Stuck issues: `state grep "Stage: design" | grep "2026-07-0[0-7]"`
EOF

# Initial commit
git add .
git commit -m "Initial commit: obsidian vault structure"

# Push to GitHub
git remote add origin https://github.com/YOUR-ORG/aios-state-vault
git push -u origin main
```

### Step 2: Install `ObsidianStateManager` Class (5 min)

Create file: `state_manager.py`

```python
from pathlib import Path
from datetime import datetime
import json
import subprocess
import re
from typing import Dict, List, Optional

class ObsidianStateManager:
    """Git-synced Obsidian vault for orchestrator state"""
    
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
    
    def create_initial_state(self, issue_id: int, issue_data: Dict):
        """Create initial state file for new issue"""
        
        now = datetime.now().isoformat() + "Z"
        
        content = f"""# Issue {issue_id}: {issue_data.get('title', 'TBD')}

## Current State
- **Issue Number:** {issue_id}
- **Title:** {issue_data.get('title', 'TBD')}
- **Stage:** intake
- **Stage Entry Time:** {now}
- **Priority Score:** {issue_data.get('priority_score', 'TBD')}
- **Status:** ⏳ In Progress

## Stage History
(No transitions yet)

## Latest Decision
(Pending intake)

## Related Issues
(To be populated)

## Notes
- Created: {now}
"""
        
        state_file = self.state_dir / f"issue-{issue_id}.md"
        state_file.write_text(content)
        
        # Commit
        self._git_commit(
            files=[state_file],
            message=f"Create initial state for issue #{issue_id}"
        )
    
    def transition_state(self, issue_id: int, new_stage: str, decision: dict):
        """Atomically update state and record decision"""
        
        state_file = self.state_dir / f"issue-{issue_id}.md"
        
        # Load existing state
        old_content = state_file.read_text() if state_file.exists() else None
        old_stage = self._extract_field(old_content, 'Stage') if old_content else None
        
        # Generate new state
        new_content = self._render_state_file(
            issue_id=issue_id,
            new_stage=new_stage,
            decision=decision,
            old_stage=old_stage,
            old_content=old_content
        )
        
        # Write state file
        state_file.write_text(new_content)
        
        # Write decision file
        decision_file = self.decisions_dir / f"issue-{issue_id}-{new_stage}-{datetime.now().isoformat()}.md"
        decision_file.write_text(self._render_decision_file(issue_id, new_stage, decision))
        
        # Commit both
        self._git_commit(
            files=[state_file, decision_file],
            message=f"Issue #{issue_id}: {old_stage or 'NEW'} → {new_stage}\n\n{decision.get('reasoning', '')}"
        )
    
    def _render_state_file(self, issue_id: int, new_stage: str, decision: dict, 
                           old_stage: Optional[str], old_content: Optional[str]) -> str:
        """Generate markdown state file"""
        
        now = datetime.now().isoformat() + "Z"
        
        history = []
        if old_content:
            history = self._extract_stage_history(old_content)
        
        if old_stage:
            history.append({
                'stage': old_stage,
                'entered': self._extract_field(old_content, 'Stage Entry Time'),
                'exited': now,
                'status': '✅ Completed'
            })
        
        history_md = ""
        for i, entry in enumerate(history, 1):
            duration = self._calculate_duration(entry.get('entered'), entry.get('exited'))
            history_md += f"{i}. **{entry['stage']}** ({entry.get('entered', '?')} → {entry.get('exited', '?')}) {entry['status']} ({duration})\n"
        
        return f"""# Issue {issue_id}: {self._extract_title(old_content) or 'Feature'}

## Current State
- **Issue Number:** {issue_id}
- **Stage:** {new_stage}
- **Stage Entry Time:** {now}
- **Priority Score:** {decision.get('priority_score', self._extract_field(old_content, 'Priority Score') or 'TBD')}
- **Status:** ⏳ In Progress

## Stage History
{history_md if history_md else '(No transitions yet)'}

## Latest Decision
```json
{json.dumps({
    'stage': new_stage,
    'decision': decision.get('decision'),
    'reasoning': decision.get('reasoning'),
    'timestamp': now,
    'agent': decision.get('agent'),
    'duration_ms': decision.get('duration_ms'),
}, indent=2)}
```

## Related Issues
(To be populated)

## Notes
- Last updated: {now}
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

## Full Details
```json
{json.dumps(decision, indent=2)}
```
"""
    
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
    
    def get_stuck_issues(self, stage: str, hours: int = 2) -> List[Dict]:
        """Query: find issues stuck in a stage for too long"""
        
        now = datetime.now()
        stuck = []
        
        for issue_id in self.get_all_issues_in_stage(stage):
            state = self.load_state(issue_id)
            
            if state and state['stage_entry_time']:
                entry_time = datetime.fromisoformat(state['stage_entry_time'].replace('Z', '+00:00'))
                elapsed = (now - entry_time).total_seconds() / 3600
                
                if elapsed > hours:
                    stuck.append({
                        'issue_id': issue_id,
                        'stage': stage,
                        'hours_stuck': round(elapsed, 1),
                        'entered': state['stage_entry_time'],
                    })
        
        return stuck
    
    def _extract_field(self, content: str, field_name: str) -> Optional[str]:
        """Parse markdown field value"""
        
        if not content:
            return None
        pattern = rf"- \*\*{re.escape(field_name)}:\*\* (.+)"
        match = re.search(pattern, content)
        return match.group(1) if match else None
    
    def _extract_title(self, content: str) -> Optional[str]:
        """Extract issue title from content"""
        
        if not content:
            return None
        match = re.search(r"# Issue \d+: (.+)", content)
        return match.group(1) if match else None
    
    def _extract_json_block(self, content: str, label: str = "Latest Decision") -> Optional[Dict]:
        """Extract JSON from markdown code block"""
        
        if not content:
            return None
        
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
        
        if not content:
            return []
        
        pattern = r"## Stage History\n(.*?)(?=##|$)"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return []
        
        history = []
        lines = match.group(1).strip().split('\n')
        
        for line in lines:
            if line and line[0] in '0123456789':
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
        """Calculate duration between timestamps"""
        
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
        except:
            return "?"
    
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
            print(f"⚠️ Git operation failed: {e}")
```

### Step 3: Update PM Orchestrator to Use State Manager (15 min)

In your `orchestrator.pm.agent.md`:

```python
# BEFORE
# Orchestrator reads labels from GitHub
LABELS=$(gh issue view $ISSUE_NUM --json labels -q '.labels[].name')

# AFTER
# Orchestrator reads state from Obsidian vault
from state_manager import ObsidianStateManager

state_manager = ObsidianStateManager(
    vault_path="~/aios-state-vault",
    repo_path="~/aios-state-vault"
)

# Load current state
state = state_manager.load_state(issue_id)
current_stage = state['current_stage'] if state else 'intake'

# ... run agent ...

# Update state after decision
state_manager.transition_state(
    issue_id=issue_id,
    new_stage='design',  # Next stage
    decision={
        'decision': 'CHAMPION',
        'reasoning': 'Market opportunity validated',
        'agent': 'pm-agent',
        'duration_ms': 45000,
    }
)
```

### Step 4: Test and Verify (5 min)

```python
# Test state manager
from state_manager import ObsidianStateManager

sm = ObsidianStateManager(
    vault_path="~/aios-state-vault",
    repo_path="~/aios-state-vault"
)

# Create initial state for issue 123
sm.create_initial_state(123, {'title': 'Test Feature', 'priority_score': 2.5})

# Verify file created
print(sm.load_state(123))

# Simulate a transition
sm.transition_state(123, 'design', {
    'decision': 'REVISE',
    'reasoning': 'Need scope clarification',
    'agent': 'design-agent',
    'duration_ms': 30000,
})

# Check updated state
print(sm.load_state(123))

# Verify git push worked
# Should see new commits and files in vault repo
```

---

## Phase 1: Full Implementation (1 week)

Once Step-by-Step works, proceed with:

1. **Migrate all three orchestrators** (PM, PO, Dev) to use `ObsidianStateManager`
2. **Replace all label-based routing** with `state_manager.load_state()`
3. **Update decision posting** to use `state_manager.transition_state()`
4. **Test end-to-end** workflow through all three loops
5. **Open vault in Obsidian** and visualize

---

## Obsidian Setup (Optional but Recommended)

### Install Obsidian

1. Download from https://obsidian.md
2. Open vault: File → Open → Select `~/aios-state-vault`

### Create Dashboard Note

Create `index.md`:

```markdown
# AIOS State Dashboard

## Quick Links
- [[state/]] - View all issue states
- [[decisions/]] - View decision history

## Pipeline Health

### Issues by Stage
- **Intake:** [[query:stage-intake]]
- **Design:** [[query:stage-design]]
- **Build:** [[query:stage-build]]
- **QA:** [[query:stage-qa]]
- **Verification:** [[query:stage-verification]]

### Stuck Issues
See [[metrics]] for issues stuck >2 hours

## Recent Decisions
(Auto-updated from decisions/ folder)
```

### Useful Plugins

- **Obsidian Git** — Auto-syncs vault to git repo
- **Dataview** — Query state files across vault
- **Graph View** — Visualize issue relationships (using `[[issue-N]]` links)

---

## Queries You Can Now Run

```bash
# All issues in design stage
grep -r "Stage: design" ~/aios-state-vault/state/

# Issues stuck >2 hours in design
find ~/aios-state-vault/state/ -name "*.md" | xargs grep -l "Stage: design" | while read f; do
  ENTERED=$(grep "Stage Entry Time:" "$f" | cut -d: -f2- | xargs)
  HOURS_AGO=$(echo "($NOW - $(date -d "$ENTERED" +%s)) / 3600" | bc)
  if (( $HOURS_AGO > 2 )); then
    echo "$f stuck for $HOURS_AGO hours"
  fi
done

# Decision history for specific issue
ls ~/aios-state-vault/decisions/issue-123-*

# Pipeline metrics
wc -l ~/aios-state-vault/state/*.md
```

---

## Next: Phase 2 - Routing Registry

Once state management is solid, move to [ORCHESTRATION_AUDIT.md - Phase 2](ORCHESTRATION_AUDIT.md) to extract centralized routing logic.

