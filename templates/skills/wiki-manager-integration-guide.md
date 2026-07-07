# Wiki Manager Integration Guide: Librarian Model

## Overview

The **wiki-manager skill** uses the **librarian model**: simple, explicit storage operations with agents making all business decisions.

**Core Principle:** Agents own logic and decisions. Skill owns storage.

---

## Four Core Actions

### 1. **search** — Find Existing Research

**When to use:**
- Before creating new research (check if it already exists)
- Before writing new findings (avoid duplicates)
- When you need to review existing research

**Agent Responsibility:**
- Decide what to search for
- Evaluate match_score (0.0 = no match, 1.0 = perfect match)
- Decide whether to reuse, link to, or create new research

**Example:**

```bash
# Check if "Field Manager" persona already researched
CALL SKILL: wiki-manager
{
  "action": "search",
  "repo": "owner/repo",
  "query": "Field Manager"
}

RESPONSE:
{
  "total_found": 2,
  "results": [
    {
      "page": "Personas/Field-Manager",
      "match_score": 0.98,
      "snippet": "# Field Manager\n\nManages equipment checkout and field operations..."
    }
  ]
}

# Agent Decision:
IF match_score > 0.95:
  ✅ Use existing research
  → Link from your research issue to Personas/Field-Manager
  → Do NOT create duplicate research
ELSE IF match_score > 0.70:
  ⚠️ Similar research exists (score: 0.72)
  → Review it first
  → Decide: Merge with existing? Or create new focused research?
ELSE:
  ❌ No match found
  → Proceed to create new research
```

---

### 2. **write-page** — Store Findings at Exact Location

**When to use:**
- After research is complete and findings documented
- To create or update any wiki page
- You decide exactly where and what to write

**Agent Responsibility:**
- Write findings in markdown
- Specify exact `page_path` (e.g., "Personas/Field-Manager")
- Include source citations (Issue #, evidence count)
- Format page following templates

**Example:**

```bash
# After 10 Field Manager interviews, write persona to wiki
CALL SKILL: wiki-manager
{
  "action": "write-page",
  "repo": "owner/repo",
  "page_path": "Personas/Field-Manager",
  "content": "# Field Manager\n\n## Primary Job to be Done\nManage daily equipment checkout for field teams.\n\n## Top Frustrations\n1. Manual checkout takes 15 min (60% daily)\n2. No mobile access (40% report as pain)\n3. Equipment location lookup (35% report)\n\n## Evidence\nIssue #1025: 10 interviews conducted\nConfidence: HIGH\n\n**Findings:**\n- All 10 reported manual process friction\n- 8/10 have field teams (mobile use case)\n- Primary industry: Construction"
}

RESPONSE:
{
  "status": "success",
  "page_path": "Personas/Field-Manager",
  "wiki_url": "https://github.com/owner/repo/wiki/Personas/Field-Manager",
  "committed": true,
  "commit_message": "Create Personas/Field-Manager.md"
}
```

**Standard Folders:**
```
Personas/              # User archetypes
Journey-Maps/         # Experience stages
Competitive-Analysis/ # Market comparison
Market-Trends/        # Industry signals
Feature-Research/     # Feature-specific investigations
```

---

### 3. **update-index** — Register in Master Registry

**When to use:**
- After writing a research page (always)
- To mark research as Complete, In Progress, or Deferred
- To track metadata: status, confidence, findings summary

**Agent Responsibility:**
- Call after write-page succeeds
- Provide research status (Complete | In Progress | Deferred)
- Provide confidence level (HIGH | MEDIUM | LOW)
- Write concise findings_summary (one-liner)

**Example:**

```bash
# After Field Manager persona written, register in index
CALL SKILL: wiki-manager
{
  "action": "update-index",
  "repo": "owner/repo",
  "subject": "Field Manager",
  "status": "Complete",
  "wiki_page": "Personas/Field-Manager",
  "github_issue": "#1025",
  "confidence": "HIGH",
  "findings_summary": "10 interviews. Primary JTBD: manage equipment checkout. Top 3 frustrations identified."
}

RESPONSE:
{
  "status": "success",
  "message": "Index entry added: Field Manager",
  "index_entry_added": true
}
```

**This updates Research-to-Decision-Index:**
```markdown
| Field Manager | ✅ Complete | Personas/Field-Manager | 2026-07-08 | #1025 | HIGH | 10 interviews... |
```

---

### 4. **audit-and-organize** — Detect Issues (No Auto-Fix)

**When to use:**
- Weekly/periodic maintenance (optional)
- Detecting duplicates, naming issues, stale content
- For housekeeping reporting (flags issues, doesn't auto-merge)

**Agent Responsibility:**
- Review issues flagged by audit
- Decide on merges/reorganization manually
- NO automatic file moves or consolidations

**Example:**

```bash
# Weekly wiki audit
CALL SKILL: wiki-manager
{
  "action": "audit-and-organize",
  "repo": "owner/repo",
  "dry_run": true  # Set false to apply fixes (if any)
}

RESPONSE:
{
  "status": "success",
  "wiki_state": {
    "total_pages": 12,
    "organized_pages": 10,
    "unorganized_pages": 2
  },
  "issues_detected": [
    {
      "issue_type": "potential_duplicates",
      "severity": "HIGH",
      "pages": ["Personas/Field-Manager", "Personas-Manager-Field"],
      "recommendation": "Manual review - similar names"
    },
    {
      "issue_type": "naming_inconsistency",
      "severity": "LOW",
      "pages": ["Personas/Sarah_Director"],
      "recommendation": "Use Kebab-Case: 'Sarah-Director' not 'Sarah_Director'"
    }
  ]
}

# Agent then:
# - Reviews the flagged duplicates
# - Decides: merge? or keep separate?
# - Handles renames/consolidations manually
```

---

## Agent Workflow Patterns

### Pattern 1: PM Agent (Before Creating Research)

```
Step 1: Search
├─ search("Field Manager")
├─ evaluate match_score
└─ decide: reuse OR create new

Step 2: Create Research Issue (if needed)
└─ gh issue create --label "research" ...

Step 3: Link Results
└─ Post comment with wiki link if found
```

### Pattern 2: Research Agent (Execute Research)

```
Step 0: Pre-Flight Check
└─ search("[Research Topic]")
   → If found and Complete: reuse, don't redo
   → If not found: proceed

Step 1-3: Conduct Research
└─ Interviews, analysis, synthesis

Step 4: Write Findings
├─ write-page("Personas/Field-Manager", markdown_content)
├─ write-page("Journey-Maps/Field-Manager-Checkout", content)
└─ verify: both successful

Step 5: Register in Index
├─ update-index(subject, status, confidence, findings)
└─ verify: index_entry_added = true

Step 6: Close Issue
└─ Close with comment: "Research complete, wiki updated, indexed"
```

### Pattern 3: Orchestrator (Housekeeping)

```
Weekly:
├─ audit-and-organize(dry_run=true)
├─ review flagged issues
└─ post summary to team with links
```

---

## Key Decision Points

### When to Search vs Create?

| Scenario | Action |
|----------|--------|
| "Does Field Manager persona exist?" | search("Field Manager") |
| "I need fresh research on Facility Director" | search + create new |
| "Is checkout flow documented?" | search("checkout flow") |
| "Should I update existing persona or create new?" | search + compare findings + agent decides |

### When to Update Index?

| Scenario | When |
|----------|------|
| After write-page succeeds | Always |
| During research | update-index(..., status="In Progress") |
| When research deferred | update-index(..., status="Deferred") |
| After research complete | update-index(..., status="Complete") |

### When to Call Audit?

| Scenario | Frequency |
|----------|-----------|
| Check for duplicates | Weekly or after major edits |
| Verify index is current | Bi-weekly |
| Detect naming issues | Monthly housekeeping |

---

## Response Code Examples

### Successful Search

```json
{
  "status": "success",
  "query": "Field Manager",
  "total_found": 1,
  "results": [
    {
      "page": "Personas/Field-Manager",
      "match_score": 0.98,
      "snippet": "# Field Manager\n\nManages equipment checkout..."
    }
  ]
}
```

**Agent reads:** `match_score=0.98` → this is a strong match → likely use it

---

### Successful Write

```json
{
  "status": "success",
  "page_path": "Personas/Field-Manager",
  "wiki_url": "https://github.com/owner/repo/wiki/Personas/Field-Manager",
  "committed": true,
  "commit_message": "Create Personas/Field-Manager.md"
}
```

**Agent reads:** `committed=true` → page written and pushed → proceed to update-index

---

### Successful Index Update

```json
{
  "status": "success",
  "message": "Index entry added: Field Manager",
  "index_entry_added": true
}
```

**Agent reads:** `index_entry_added=true` → index updated → can close research issue

---

### Audit Issues Detected

```json
{
  "issues_detected": [
    {
      "issue_type": "potential_duplicates",
      "severity": "HIGH",
      "pages": ["Personas/Field-Manager", "Personas-Manager-Field"],
      "recommendation": "Manual review"
    }
  ]
}
```

**Agent reads:** Flags raised, agent manually reviews and decides

---

## Error Handling

### Search Error

```json
{
  "status": "error",
  "query": "Field Manager",
  "message": "Wiki clone failed: authentication error"
}
```

**Agent Action:** Retry, or escalate if persistent

---

### Write Error

```json
{
  "status": "error",
  "page_path": "Personas/Field-Manager",
  "message": "Failed to push: branch conflict"
}
```

**Agent Action:**
1. Post error comment on issue
2. Close with label `wiki-error`
3. Escalate to orchestrator

---

### Index Update Error

```json
{
  "status": "error",
  "message": "Research-to-Decision-Index not found in wiki"
}
```

**Agent Action:** Create index first, then retry update-index

---

## Example: Full Research-to-Decision Workflow

### Phase 1: PM Agent Checks for Existing Research

```bash
# PM sees pm-idea: "Mobile app for field checkout"

# Step 1: Search
CALL wiki-manager: search("field checkout")

# Response: No match (total_found: 0)

# Step 2: Create Research Issue
gh issue create --label "research" \
  --title "[research]: Field Manager Persona" \
  --body "Conduct interviews..."
```

### Phase 2: Research Agent Executes

```bash
# Research Agent assigned to research issue #1025

# Step 0: Pre-flight check
CALL wiki-manager: search("Field Manager")
# Response: No match → proceed

# Step 1-3: Conduct 10 interviews, synthesize findings

# Step 4: Write to Wiki
CALL wiki-manager: write-page
{
  "page_path": "Personas/Field-Manager",
  "content": "[findings from 10 interviews]"
}
# Response: success, committed=true

# Step 5: Register in Index
CALL wiki-manager: update-index
{
  "subject": "Field Manager",
  "status": "Complete",
  "confidence": "HIGH",
  "findings_summary": "10 interviews, 15-min checkout time = primary pain"
}
# Response: success, index_entry_added=true

# Step 6: Close
gh issue close 1025 -c "Research complete, wiki updated, indexed"
```

### Phase 3: PM Agent Reviews for Decision

```bash
# PM Phase 2 triggered

# Search to retrieve research
CALL wiki-manager: search("Field Manager")
# Response: match_score=0.98, page=Personas/Field-Manager

# Read page directly:
git clone https://github.com/owner/repo.wiki.git
cat Personas/Field-Manager.md

# Review findings, make decision
# Create strategic-opportunity if decision is GO
```

---

## Best Practices

✅ **DO:**
- Search before creating research
- Always call update-index after write-page
- Provide confidence levels (HIGH/MEDIUM/LOW)
- Include evidence counts (N=X)
- Use Kebab-Case for page names (Personas/Field-Manager, not Personas/FieldManager)
- Include source citations (Issue #, interview count)

❌ **DON'T:**
- Auto-merge or consolidate pages (only audit, agent decides)
- Write to wiki without indexing
- Skip search (might duplicate effort)
- Ignore audit findings
- Create pages outside standard folders without reason

---

## Summary: Dumb Skill, Smart Agent

| Responsibility | Action |
|---|---|
| **Skill:** search | Return matches + scores; agent decides |
| **Skill:** write-page | Write at agent-specified location |
| **Skill:** update-index | Add to master registry |
| **Skill:** audit-and-organize | Detect issues; NO auto-fixes |
| **Agent:** Decide when to search | Based on context |
| **Agent:** Evaluate search results | Based on match_score |
| **Agent:** Decide what to write | Based on research findings |
| **Agent:** Decide where to write | Based on content classification |
| **Agent:** Decide metadata | Status, confidence, findings_summary |
| **Agent:** Handle issues | Merge duplicates, rename files |

