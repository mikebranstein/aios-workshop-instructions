# Skill: GitHub Wiki Manager v2 (Smart, Adaptive, Self-Healing)

## Overview

A self-adapting wiki manager that **discovers what exists, measures chaos, auto-organizes, and maintains a master index**. Each call evaluates the current wiki state and reorganizes if chaos exceeds thresholds.

## Core Principle

**Don't enforce structure → Discover it, measure it, fix it.**

The skill:
1. Scans all pages
2. Classifies content by type (Persona, Journey Map, etc.) via content analysis
3. Calculates a "messiness metric" (0-100: 0=perfect, 100=chaos)
4. Auto-reorganizes if messiness > threshold (40+)
5. Maintains Research-to-Decision-Index as source of truth
6. Adapts to whatever state the wiki is in

## Prerequisites

- GitHub CLI (`gh`) installed and authenticated
- Git installed
- PowerShell 5.1+ (Windows) or Bash (Mac/Linux)
- Access to target GitHub repository with wiki enabled

## Input Parameters

```json
{
  "action": "string (required)",
  "repo": "string (required) - format: 'owner/repo'",
  "search_term": "string (optional) - topic to find or create",
  "content": "string (optional) - content for new pages",
  "force_reorganize": "boolean (optional, default: false) - bypass messiness threshold"
}
```

## Actions

### **audit-and-organize**
Comprehensive wiki health check. Discovers all pages, classifies them, measures chaos, auto-reorganizes if needed.

**Input:**
```json
{
  "action": "audit-and-organize",
  "repo": "owner/repo",
  "force_reorganize": false
}
```

**Output:**
```json
{
  "status": "success|error",
  "audit_timestamp": "2026-07-08T10:30:00Z",
  "wiki_state_before": {
    "total_pages": 12,
    "messiness_score": 65,
    "messiness_percentage": "CHAOS - High",
    "issues": [
      "Found 3 persona variants: Personas-John, John-Persona, PersonaJohn",
      "Found 5 pages without category folder",
      "Index is 2 days out of date"
    ]
  },
  "reorganization_performed": true,
  "wiki_state_after": {
    "total_pages": 12,
    "messiness_score": 12,
    "messiness_percentage": "ORGANIZED - Low",
    "pages_consolidated": 3,
    "pages_reorganized": 7,
    "new_structure": {
      "Personas": 3,
      "Journey-Maps": 2,
      "Competitive-Analysis": 2,
      "Market-Trends": 1,
      "Feature-Research": 3,
      "Other": 1
    }
  },
  "index": {
    "total_entries": 8,
    "status": "CURRENT - Updated in this audit",
    "entries_consolidated": 2
  },
  "recommendations": []
}
```

---

### **check-wiki-health**
Quick status check without reorganization. Returns current organization state.

**Input:**
```json
{
  "action": "check-wiki-health",
  "repo": "owner/repo"
}
```

**Output:**
```json
{
  "status": "success|error",
  "wiki_health": {
    "total_pages": 12,
    "messiness_score": 65,
    "messiness_percentage": "CHAOS - High",
    "organization_status": "NEEDS_ATTENTION",
    "last_organized": "2026-07-05T14:00:00Z",
    "days_since_organization": 3
  },
  "category_distribution": {
    "Personas": 2,
    "Journey-Maps": 1,
    "Uncategorized": 5,
    "Duplicates": 3
  },
  "health_indicators": {
    "has_index": true,
    "index_current": false,
    "duplicate_subjects": 3,
    "inconsistent_naming": 4,
    "orphaned_pages": 5
  },
  "action_required": "audit-and-organize should be run - messiness is above 40 threshold"
}
```

---

### **find-or-create**
Search for a topic in the wiki. If found, return existing pages. If not found, create new page in appropriate category based on content analysis.

**Input:**
```json
{
  "action": "find-or-create",
  "repo": "owner/repo",
  "search_term": "Field Manager",
  "content": "# Field Manager\n\n## Demographics\n..."
}
```

**Output:**
```json
{
  "status": "success|error",
  "action_taken": "FOUND|CREATED|CONSOLIDATED",
  "search_term": "Field Manager",
  "result": {
    "page_name": "Field-Manager",
    "location": "Personas/Field-Manager",
    "category": "Persona",
    "category_confidence": 0.95,
    "created": false,
    "consolidated_from": []
  },
  "consolidation_note": null,
  "index_entry": {
    "subject": "Field Manager",
    "status": "In Progress",
    "wiki_page": "Personas/Field-Manager",
    "research_items": []
  }
}
```

---

## Core Functions (Implementation)

### Content Classification

The skill uses a **multi-signal classifier** to categorize pages:

**Signals (by priority):**
1. **Title analysis** — "Persona: John" → Persona; "Journey Map: Checkout" → Journey Map
2. **Keyword detection** — Pages with "interview", "demographics", "goals" → Persona
3. **Structure matching** — Markdown h2/h3 patterns indicate category
4. **Content length** — Short pages (< 500 chars) might be stubs/Other
5. **File name heuristics** — "Personas-*", "*-Journey*" patterns

**Categories detected:**
- **Persona**: Interview notes, demographics, goals, frustrations
- **Journey Map**: Steps, touchpoints, emotions, pain points
- **Competitive Analysis**: Competitor name, features, pricing
- **Market Trends**: Industry trends, market sizing, adoption
- **Feature Research**: Feature ideas, use cases, technical feasibility
- **Other**: Anything else

---

### Messiness Metric (0-100)

Calculated across all pages and overall structure:

| Factor | Points | Example |
|--------|--------|---------|
| **Duplicate subjects** | +20 each | "Personas-John" + "John-Persona" = +20 |
| **Naming inconsistency** | +15 each | "PersonaJohn" vs "Persona-John" = +15 |
| **Uncategorized page** | +10 each | Page not in proper category folder = +10 |
| **Index out of date** | +25 | Index last updated 3+ days ago = +25 |
| **Page without clear category** | +5 each | Can't classify page = +5 |
| **Orphaned page** | +15 | Page exists but not in index = +15 |

**Messiness Percentage:**
- 0-20: ✅ **ORGANIZED** — Well structured
- 21-40: ⚠️ **NEEDS_ATTENTION** — Some issues
- 41-60: 🔴 **CHAOS** — Significant problems (auto-organize recommended)
- 61-100: 🔥 **SEVERE_CHAOS** — Reorganize immediately

**Threshold for auto-reorganize: 40+**

---

### Auto-Organization Engine

When messiness > 40, the skill:

1. **Consolidates duplicates** — "Personas-John" + "John-Persona" merged to "Field-Manager"
2. **Renames pages** — "PersonaJohn" → "Persona-John" (Kebab-Case)
3. **Moves pages to category folders** — "John-Persona" → "Personas/Field-Manager"
4. **Creates missing folders** — Creates Personas/, Journey-Maps/, etc. as needed
5. **Updates all links** — Finds broken links, fixes them
6. **Reconciles index** — Updates or recreates Research-to-Decision-Index

**Consolidation logic:**
- Find pages with similar names (Levenshtein distance < 3)
- Ask: are they duplicates or variants?
- If duplicates: merge content, keep canonical name, redirect old page
- If variants: note relationship in consolidated page

---

### Index Reconciliation

After any reorganization:

1. **Scan all pages** in new structure
2. **Extract metadata** — Subject, category, creation date, size
3. **Reconcile against index** — Match pages to existing index entries
4. **Update index** — Add new pages, mark completions, update timestamps
5. **Validate index** — Ensure index and filesystem are in sync

---

## Implementation Strategy

### Three Simple Actions (replacing 9 old ones)

**Action 1: audit-and-organize**
```powershell
function Handle-AuditAndOrganize {
    $discoveredPages = Discover-WikiState $repo
    $classifications = $discoveredPages | Classify-PageContent
    $messiness = Calculate-MessinessMetric $classifications
    
    if ($messiness.score -gt 40 -or $force_reorganize) {
        Auto-Organize $classifications $messiness
        Reconcile-Index
        return "REORGANIZED" status with before/after
    } else {
        return "ALREADY_ORGANIZED" status
    }
}
```

**Action 2: check-wiki-health**
```powershell
function Handle-CheckWikiHealth {
    $discoveredPages = Discover-WikiState $repo
    $classifications = $discoveredPages | Classify-PageContent
    $messiness = Calculate-MessinessMetric $classifications
    
    return $messiness + distribution + recommendations
}
```

**Action 3: find-or-create**
```powershell
function Handle-FindOrCreate {
    $found = Find-Topic $search_term
    
    if ($found) {
        return $found pages
    } else {
        $category = Classify-Content $content
        Create-InCategory $search_term $content $category
        return created page
    }
}
```

---

## Usage from Agents

### From PM Agent (before creating research)

```markdown
CALL SKILL: wiki-manager

**Parameters:**
- action: find-or-create
- repo: owner/repo
- search_term: "Field Manager"
- content: "[Optional: if you have content describing this topic]"

**Expected Response:**
- If found: Use existing wiki page
- If created: Add to index, proceed with new research item
```

### From Research Agent (at start of work)

```markdown
CALL SKILL: wiki-manager

**Parameters:**
- action: check-wiki-health
- repo: owner/repo

**Decision Logic:**
- If health.messiness_percentage is "CHAOS": 
  - Recommend: Run audit-and-organize first
- If health.total_pages > 20 and not organized recently:
  - Suggest: audit-and-organize before proceeding
```

### Periodic Maintenance (via Orchestrator)

```markdown
WEEKLY TASK:

CALL SKILL: wiki-manager

**Parameters:**
- action: audit-and-organize
- repo: owner/repo
- force_reorganize: false

**Purpose:** Keep wiki healthy, consolidate duplicates, update index
```

---

## Key Differences from v1

| Aspect | v1 (Strict) | v2 (Adaptive) |
|--------|----------|-----------|
| **Structure Assumption** | Requires perfect structure to exist | Discovers actual structure |
| **Organization** | User responsibility | Skill responsibility (auto-organize) |
| **Error Handling** | Fails if structure wrong | Fixes structure automatically |
| **Index** | Must be manually maintained | Auto-updated on every call |
| **Duplicate Detection** | Looks for exact match only | Finds similar pages, consolidates |
| **Actions Count** | 9 (specialized) | 3 (smart generalists) |
| **Complexity** | User navigates / Skill validates | Skill handles everything |
| **Adaptability** | Fixed rules | Learns from state, adapts |

---

## Success Criteria

✅ **Consistency**: All pages organized with predictable structure  
✅ **Master Index**: Single source of truth, always current  
✅ **No Duplicates**: Similar pages consolidated automatically  
✅ **Self-Healing**: Detects chaos, fixes it without user intervention  
✅ **Simplicity**: 3 actions handle all use cases vs 9 specialized ones

---

## Example Workflow

**Day 1: Initial Audit**
```
Wiki has 12 pages scattered with inconsistent names
Action: audit-and-organize
Result:
  - Found: Personas-John, John-Persona, PersonaJohn (duplicates)
  - Consolidated to: Personas/Field-Manager
  - Reorganized: 7 pages moved to appropriate folders
  - Messiness: 65 → 12 (SEVERE_CHAOS → ORGANIZED)
  - Index: Created/Updated with 8 entries
```

**Day 2: PM Creates New Idea**
```
PM Agent runs: find-or-create search_term="Field Manager"
Result: FOUND → Personas/Field-Manager (already researched, 10 interviews)
Action: Use existing, post comment with wiki link, don't create duplicate
```

**Day 5: Check Health**
```
Orchestrator runs: check-wiki-health
Result:
  - messiness_score: 18 (ORGANIZED)
  - Pages organized: 12/12
  - Index current: Yes
  - Recommendation: None (keep running)
```

**Day 10: Periodic Maintenance**
```
Orchestrator runs: audit-and-organize force_reorganize=true
Result:
  - Messiness already low (12)
  - No reorganization needed
  - Index verified and current
  - Status: HEALTHY
```

---

## Benefits

1. **Less brittle code** — Don't assume structure, discover it
2. **Self-healing** — Detects chaos, fixes automatically
3. **Simpler actions** — 3 smart actions vs 9 specialized
4. **Adaptive** — Handles existing messes, learns from them
5. **Measurable** — Messiness score shows progress
6. **Autonomous** — Can run periodically without user guidance
7. **Team-friendly** — New team members inherit organized wiki

