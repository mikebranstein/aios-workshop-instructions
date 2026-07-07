# Wiki Manager Integration Guide: Expert Librarian Model

## Overview

The **wiki-manager skill** is an **expert librarian**: autonomous, intelligent, and self-optimizing.

**Core Principle:** 
- **Agents own semantics** — what to store (content_type, subject, content)
- **Skill owns everything else** — organization, placement, reorganization, index accuracy

**Key Feature:** The skill is *constantly evaluating* wiki organization quality. Before writing new content, it assesses "messiness" (orphaned pages, scattered structure, redundancy, duplicates) and **reorganizes autonomously if needed**. This is internal—agents never direct it.

**What this means:**
- Agents call write-content, and the skill may reorganize behind the scenes
- write-content response indicates if reorganization occurred
- Index is always accurate and complete
- Structure evolves intelligently based on actual content patterns

---

## Two Core Agent Actions

Agents use only two actions. Everything else is internal skill operation.

### 1. **search** — Find Existing Content

**When to use:**
- Before creating new research
- To check if topic already researched
- To prevent duplicate work

**Agent Responsibility:**
- Decide what to search for
- Evaluate match_score (0.0 = no match, 1.0 = perfect match)
- Decide: reuse existing or create new

**Example:**

```bash
CALL SKILL: wiki-manager
{
  "action": "search",
  "repo": "owner/repo",
  "query": "[search term]"
}

RESPONSE:
{
  "total_found": 1,
  "results": [
    {
      "page": "[type]/[subject]",
      "match_score": 0.98,
      "snippet": "[first few lines]"
    }
  ]
}

# Agent Decision:
IF match_score > 0.95: ✅ Use existing
ELSE: Create new research
```

---

### 2. **write-content** — Autonomous Organization & Write

Agent specifies WHAT to store. Skill autonomously evaluates wiki health, may reorganize, then writes content.

**What happens:**
1. Skill evaluates current wiki organization quality (messiness metric)
2. **If messiness exceeds threshold:** Reorganizes wiki internally
   - Consolidates redundant structure
   - Moves orphaned or scattered pages
   - Audits all pages are accounted for
   - Gap analysis (identifies missing index entries)
   - Updates Content-Index to fill gaps
3. Writes new content to the (possibly reorganized) structure
4. Returns response indicating what occurred

**Input:**
```bash
CALL SKILL: wiki-manager
{
  "action": "write-content",
  "repo": "owner/repo",
  "content_type": "[type]",
  "subject": "[subject]",
  "content": "[markdown content]"
}
```

**Output (No reorganization needed):**
```json
{
  "status": "success",
  "committed": true,
  "reorganized": false
}
```

**Output (Reorganization occurred):**
```json
{
  "status": "success",
  "committed": true,
  "reorganized": true,
  "reorganization_summary": {
    "changes_made": ["consolidated_folders", "moved_orphaned_pages", ...],
    "audit_result": "all_pages_accounted_for",
    "gap_analysis": {
      "missing_from_index": 0,
      "orphaned_content": 0,
      "fixed": true
    },
    "index_updated": true
  }
}
```

**Key Point:** 
- You never know if reorganization happened unless you check response
- Structure is always optimized and indexed
- Index is always trustworthy after write-content completes

---

## Internal Operations (Skill Only)

Agents do not call these. The skill executes them autonomously:

- **update-index** — Executed automatically after write-content. Maintains Content-Index with all metadata. Also run post-reorganization to fill any gaps.
- **discover-structure** — Executed internally before write-content (to evaluate messiness) and post-reorganization (to audit pages and find missing index entries).
- **reorganize** — Triggered autonomously by skill when messiness exceeds threshold. Consolidates duplicates, moves orphaned content, updates index post-reorganization.

**Agents interface through search() and write-content() only.** Everything else is skill responsibility.

---

## Benefits of Expert Librarian Architecture

| Aspect | Benefit |
|--------|---------|
| **Agents focus on content** | Don't think about wiki organization or reorganization |
| **Skill owns all structure** | Can reorganize transparently without breaking agents |
| **Autonomous optimization** | Evaluates and fixes organization proactively |
| **Index always accurate** | Post-reorganization audit ensures complete, gap-free index |
| **Emergent organization** | Structure evolves from content patterns, not rigid schema |
| **Adaptive placement** | Placement decisions based on domain expertise |
| **Generic** | Works with any content types agents define |
| **Simple agent code** | Call write-content; let skill handle rest |
| **Reorganization hidden** | Agents don't manage or direct restructuring |

---

## What Agents Should Expect

### From write-content

**Standard case (most common):**
- Call write-content with your content AND metadata (status, confidence, findings_summary, etc.)
- Skill writes content to optimized location
- Skill updates index automatically
- You get response: `reorganized: false, committed: true`

**Reorganization case (less common):**
- Call write-content with your content AND metadata
- Skill detects wiki messiness exceeds threshold
- Skill reorganizes wiki internally (you don't manage this)
- After reorg: Skill audits, does gap analysis, updates index automatically
- Then writes your content
- You get response: `reorganized: true` + summary of changes + `committed: true`
- Content is in newly organized structure; index is already updated

**Either way:**
- Your content will be found via search() reliably
- Index accurately reflects all content AND your metadata
- No separate index update call needed

### You Don't Need To:
- ✅ Worry about folder structure or naming
- ✅ Check if reorganization happened (unless you want to know)
- ✅ Manually move or consolidate content
- ✅ Audit the wiki for gaps
- ✅ Manually update index entries (skill does this automatically)

### You Still Must:
- ✅ Call write-content with all relevant metadata (status, confidence, findings_summary, github_issue)
- ✅ Verify content was written via search() if unsure
- ✅ Provide accurate metadata

---

## Agent Workflow Patterns

### Pattern 1: Discovery Agent (Before Creating Work)

```
Step 1: Search
├─ search("[subject]")
├─ evaluate match_score
└─ decide: reuse existing OR create new work item

Step 2: Create Work Issue (if needed)
└─ gh issue create --label "[content_type]" ...

Step 3: Link Results
└─ Post comment with wiki link if found
```

### Pattern 2: Research/Analysis Agent (Execute Work)

```
Step 0: Pre-Flight Check
└─ search("[subject]")
   → If found and Complete: reuse, don't redo
   → If not found: proceed

Step 1-3: Conduct Research/Analysis
└─ Interviews, analysis, synthesis, experimentation

Step 4: Write Findings (includes all metadata)
├─ write-content(
│    content_type="[type]",
│    subject="[subject]",
│    content="[markdown]",
│    status="Complete",
│    confidence="HIGH",
│    findings_summary="[summary]",
│    github_issue="#[issue]"
│  )
├─ check response: committed=true
└─ note: reorganized true/false (informational)

Step 5: Close Issue
└─ Close with comment: "Research complete, wiki updated and indexed"
```

### Pattern 3: Infrastructure (Optional)

```
Weekly (optional):
├─ discover-structure()
├─ review organization
└─ post summary if changes needed
```

## Key Decision Points

### When to Search?

| Scenario | Action |
|----------|--------|
| "Does this research already exist?" | search("[subject]") |
| "Should I start new work or reuse?" | search + evaluate match_score |
| "What existing content is related?" | search + review results |

### When to Write?

| Scenario | When |
|----------|------|
| Research/analysis complete | After steps 1-3 conducted |
| Have documented findings | Ready to persist to wiki |
| Multiple pages needed | Call write-content multiple times |
| Ready to register metadata | Include status, confidence, findings_summary in write-content call |

**Note:** write-content handles both content storage AND index registration (metadata included as optional parameters).

## Response Examples

### Successful Search

```json
{
  "status": "success",
  "query": "[search term]",
  "total_found": 1,
  "results": [
    {
      "page": "[type]/[subject]",
      "match_score": 0.98,
      "snippet": "# [Subject]\n\n[first few lines]"
    }
  ]
}
```

**Agent reads:** `match_score=0.98` → strong match → likely reuse

---

### Successful Write (No Reorganization)

```json
{
  "status": "success",
  "committed": true,
  "reorganized": false
}
```

**Agent reads:** `committed=true` and `reorganized: false` → Content written. Structure was already optimized. Index automatically updated with your metadata.

---

### Successful Write (With Reorganization)

```json
{
  "status": "success",
  "committed": true,
  "reorganized": true,
  "reorganization_summary": {
    "trigger": "messiness_exceeded_threshold (orphaned_pages_detected)",
    "changes_made": [
      "consolidated_duplicate_folders",
      "moved_orphaned_research_pages_to_main_structure",
      "removed_empty_intermediate_folders"
    ],
    "pages_touched": 7,
    "audit_result": "all_pages_accounted_for",
    "gap_analysis": {
      "missing_from_index_before": 2,
      "orphaned_content_before": 3,
      "fixed": true,
      "new_index_entries": 5
    },
    "index_updated": true
  }
}
```

**Agent reads:** `reorganized: true` → Skill optimized wiki structure, audited everything, updated index automatically. Your content is in the cleaned-up structure. Index is already accurate with your metadata.

---

## Error Handling

### Search Error

```json
{
  "status": "error",
  "query": "[search term]",
  "message": "Wiki clone failed: authentication error"
}
```

**Agent Action:** Retry, or escalate if persistent

---

### Write Error

```json
{
  "status": "error",
  "content_type": "[type]",
  "subject": "[subject]",
  "message": "Failed to push: branch conflict"
}
```

**Agent Action:**
1. Post error comment on issue
2. Close with label `wiki-error`
3. Escalate to orchestrator

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

## Example: Full Content Creation Workflow

### Phase 1: Discovery Agent Checks for Existing Content

```bash
# Discovery sees opportunity: "Need analysis on [subject]"

# Step 1: Search
CALL wiki-manager: search("[subject]")

# Response: No match (total_found: 0)

# Step 2: Create Work Issue
gh issue create --label "[content_type]" \
  --title "[content_type]: [subject]" \
  --body "Conduct [analysis/research]..."
```

### Phase 2: Execution Agent Produces Content

```bash
# Execution Agent assigned to work issue #1025

# Step 0: Pre-flight check
CALL wiki-manager: search("[subject]")
# Response: No match → proceed

# Step 1-3: Conduct work (interviews, analysis, testing, etc.)

# Step 4: Write to Wiki
CALL wiki-manager: write-content
{
  "action": "write-content",
  "repo": "owner/repo",
  "content_type": "[type]",
  "subject": "[subject]",
  "content": "[findings markdown]",
  "status": "Complete",
  "confidence": "HIGH|MEDIUM|LOW",
  "findings_summary": "[one-line summary]",
  "github_issue": "#1025"
}
# Response: success, committed=true, reorganized: true|false

# Step 5: Close
gh issue close 1025 -c "Work complete, wiki updated and indexed"
```

### Phase 3: Decision Agent Reviews for Action

```bash
# Discovery Phase 2 triggered

# Search to retrieve content
CALL wiki-manager: search("[subject]")
# Response: match_score=0.98, page=[type]/[subject]

# Read page directly:
git clone https://github.com/owner/repo.wiki.git
cat [type]/[subject].md

# Review findings, make decision
# Create work item if decision is GO
```

---

## Best Practices

✅ **DO:**
- Search before creating new work
- Always call update-index after write-content
- Provide confidence levels (HIGH/MEDIUM/LOW)
- Include evidence counts (N=X interviews, N=X tests, etc.)
- Use Kebab-Case for page names ([type]/[subject], not [type]/[subject with spaces])
- Include source citations (Issue #, evidence count)
- Let skill decide where content goes (agent specifies type, not path)

❌ **DON'T:**
- Specify page_path in write-content (agent specifies content_type, skill decides path)
- Write to wiki without indexing
- Skip search (might duplicate work)
- Create pages outside of skill-managed folders
- Assume specific content types exist (let agent define type)

---

## Summary: Structure-Agnostic Architecture

| Who | Responsibility |
|---|---|
| **Skill: search** | Return matches + scores; agent evaluates |
| **Skill: write-content** | Discover structure, auto-place content based on content_type |
| **Skill: update-index** | Add to master index |
| **Skill: discover-structure** | Inspect organization, report findings |
| **Agent: Decide when to search** | Based on context and need |
| **Agent: Evaluate search results** | Based on match_score and relevance |
| **Agent: Decide what to write** | Based on findings and research |
| **Agent: Specify content_type** | What category does this content belong in? |
| **Agent: Decide metadata** | Status, confidence, findings_summary |
| **Agent: Decide on merges** | Manual review of duplicates/conflicts |

