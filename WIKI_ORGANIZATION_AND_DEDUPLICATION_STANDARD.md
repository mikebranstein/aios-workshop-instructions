# Wiki Organization Standard & Deduplication Framework

## Problem Summary

**Issue 1 - Structural Chaos:**
- Personas scattered across wiki with inconsistent naming (Personas-John, John Persona, Persona-John-Smith)
- No clear directory hierarchy
- Difficult to discover existing research
- Sprawling mess without clear organization

**Issue 2 - Duplicate Research:**
- Agents create research work items without checking if persona already researched
- Same persona interviewed multiple times by different research items
- Existing wiki pages ignored; work duplicated
- Waste of time + damages customer relationships (repeated interviews)

---

## Solution: Wiki Directory Standard + Research Registry

### Part 1: Standardized Wiki Directory Structure

**Single source of truth:** All wiki pages organized by type, then by subject.

```
Research Wiki Structure (Canonical)
├── Personas/
│   ├── Field-Manager.md
│   ├── Facility-Director.md
│   ├── Field-Sales-Rep.md
│   └── [Persona-Name].md (kebab-case, no spaces)
│
├── Journey-Maps/
│   ├── Field-Manager-Equipment-Checkout.md (or just Field-Manager.md with journey embedded)
│   ├── Facility-Director-Inventory.md
│   └── [Persona-Name]-[Context].md
│
├── Competitive-Analysis/
│   ├── Competitor-A-Analysis.md
│   ├── Competitor-B-Analysis.md
│   └── Market-Positioning.md
│
├── Market-Trends/
│   ├── Field-Operations-Automation.md
│   ├── Equipment-Tracking-Market.md
│   └── [Trend-Name].md
│
├── Feature-Research/
│   ├── Mobile-Offline-Mode.md (research specific to feature)
│   ├── Bulk-Operations.md
│   └── [Feature-Name].md
│
├── Accessibility/
│   ├── WCAG-Compliance-Notes.md
│   └── [Category].md
│
└── Research-to-Decision-Index.md (MASTER REGISTRY - see Part 2)
```

**Naming Rules:**
- Use KEBAB-CASE (Field-Manager, not Field Manager or field_manager)
- Full name in filename: Field-Manager.md (not F.M.md or FM.md)
- One persona per file (no "Personas-And-Coordinators.md")
- Consistent prefix by category: `Personas/`, `Journey-Maps/`, etc.
- Use title case for filenames: `Field-Manager.md` (not field-manager.md)

---

### Part 2: Research-to-Decision Index (Master Registry)

**Purpose:** Single registry showing what research exists, who it's for, and current status. Agents consult this FIRST before creating any new research work.

**Location:** `Research-to-Decision-Index.md` (root of wiki)

**Format:**

```markdown
# Research-to-Decision Index

**Last Updated:** 2026-07-08 | **Maintained By:** Research Orchestrator

## Persona Research Inventory

| Persona | Research Status | Wiki Page | Last Updated | Research Item(s) | Findings Summary | Confidence |
|---------|-----------------|-----------|--------------|------------------|------------------|------------|
| Field Manager | ✅ Complete | [Personas/Field-Manager.md](Personas/Field-Manager.md) | 2026-07-05 | #1023, #1024 | Primary job: Equipment access. Pain: Lost time to office roundtrip. 10 interviews | HIGH |
| Facility Director | 🔄 In Progress | [Personas/Facility-Director.md](Personas/Facility-Director.md) | 2026-07-07 | #1025 | Job scoping ongoing | MEDIUM |
| Field Sales Rep | ⏸️ Deferred | [Personas/Field-Sales-Rep.md](Personas/Field-Sales-Rep.md) | 2026-06-30 | #1020 | Low priority; defer to Q4 | LOW |

## Journey Map Inventory

| Persona | Journey Stage | Wiki Page | Research Status | Last Updated |
|---------|---------------|-----------|-----------------|--------------|
| Field Manager | Equipment Checkout | [Journey-Maps/Field-Manager-Equipment-Checkout.md](Journey-Maps/Field-Manager-Equipment-Checkout.md) | ✅ Complete | 2026-07-05 |
| Facility Director | Inventory Planning | [Journey-Maps/Facility-Director-Inventory.md](Journey-Maps/Facility-Director-Inventory.md) | 🔄 In Progress | 2026-07-07 |

## Competitive Analysis Inventory

| Topic | Wiki Page | Last Updated | Key Findings |
|-------|-----------|--------------|--------------|
| Market Positioning | [Competitive-Analysis/Market-Positioning.md](Competitive-Analysis/Market-Positioning.md) | 2026-07-01 | Competitor A has mobile; we don't. 6-month gap = opportunity |

## Market Trends Inventory

| Trend | Wiki Page | Last Updated | Evidence |
|-------|-----------|--------------|----------|
| Field Operations Automation | [Market-Trends/Field-Operations-Automation.md](Market-Trends/Field-Operations-Automation.md) | 2026-07-04 | 3 analyst reports (Gartner, IDC, Forrester); 45% YoY growth |

## Feature-Specific Research

| Feature | Topic | Wiki Page | Status | Last Updated |
|---------|-------|-----------|--------|--------------|
| Mobile Checkout | Offline Capability Requirements | [Feature-Research/Mobile-Offline-Mode.md](Feature-Research/Mobile-Offline-Mode.md) | ✅ Complete | 2026-07-05 |
| Bulk Operations | Batch Workflow Preferences | [Feature-Research/Bulk-Operations.md](Feature-Research/Bulk-Operations.md) | 🔄 In Progress | 2026-07-07 |

## Legend

- ✅ Complete = Research finished, findings documented, ready to use
- 🔄 In Progress = Active research underway
- ⏸️ Deferred = Valid but lower priority; revisit later
- ⚠️ Stale (>30 days without update) = Needs refresh
```

**How Agents Use the Index:**
1. **Before creating research work item:** Query index for persona
2. **Found "Complete"?** → Use existing page; don't create new work
3. **Found "In Progress"?** → Link to it; don't duplicate
4. **Not found?** → Create new research item + add to index
5. **Found "Stale"?** → Update it; don't create new

---

### Part 3: Enhanced Wiki-Manager Skill Actions

Add 4 new mandatory lookup actions to wiki-manager.skill.md:

#### **Action: check-persona-exists**
Before creating research for a persona, check if it's already in wiki.

```json
{
  "action": "check-persona-exists",
  "repo": "owner/repo",
  "persona_name": "Field Manager"
}
```

**Output:**
```json
{
  "status": "success",
  "exists": true,
  "wiki_page": "Personas/Field-Manager",
  "last_updated": "2026-07-05",
  "interview_count": 10,
  "summary": "Researched extensively. High confidence."
}
```

#### **Action: check-index-status**
Query the Research-to-Decision-Index for a topic.

```json
{
  "action": "check-index-status",
  "repo": "owner/repo",
  "search_type": "persona", // or "journey", "competitive", "trend", "feature"
  "search_term": "Field Manager"
}
```

**Output:**
```json
{
  "status": "success",
  "found": true,
  "index_entry": {
    "persona": "Field Manager",
    "research_status": "Complete",
    "wiki_page": "Personas/Field-Manager",
    "last_updated": "2026-07-05",
    "research_items": ["#1023", "#1024"],
    "confidence": "HIGH"
  },
  "action": "USE_EXISTING" // Signal: don't create new work
}
```

#### **Action: find-duplicate-research**
Scan wiki for similar persona/topic research (NLP-like matching).

```json
{
  "action": "find-duplicate-research",
  "repo": "owner/repo",
  "topic": "equipment checkout workflow",
  "persona": "Field Manager"
}
```

**Output:**
```json
{
  "status": "success",
  "duplicates_found": 2,
  "matches": [
    {
      "wiki_page": "Personas/Field-Manager",
      "similarity_score": 0.95,
      "reason": "Exact persona match"
    },
    {
      "wiki_page": "Journey-Maps/Field-Manager-Equipment-Checkout",
      "similarity_score": 0.88,
      "reason": "Overlapping topic"
    }
  ],
  "recommendation": "UPDATE_EXISTING_NOT_CREATE_NEW"
}
```

#### **Action: register-research**
When creating NEW research work, automatically add to index.

```json
{
  "action": "register-research",
  "repo": "owner/repo",
  "research_type": "persona", // or journey, competitive, trend, feature
  "subject": "Field Manager",
  "wiki_page": "Personas/Field-Manager",
  "github_issue": "#1025",
  "status": "In Progress",
  "notes": "Conducting 5+ interviews"
}
```

**Output:**
```json
{
  "status": "success",
  "message": "Research registered in index",
  "index_updated": true,
  "timestamp": "2026-07-08T10:30:00Z"
}
```

---

### Part 4: Agent Workflow Updates

**All agents that create research work must now:**

#### Step 0 (NEW - Before anything else): Consult Research Index

```bash
# Before: Research agent creates research work without checking
# After: ALWAYS do this first:

CALL SKILL: wiki-manager
{
  "action": "check-index-status",
  "repo": "owner/repo",
  "search_type": "persona",
  "search_term": "Field Manager"
}

# If response.action == "USE_EXISTING":
#   → Link to existing wiki page; don't create new research work
#   → Exit research item creation
#
# If response.found == false OR response.research_status == "Deferred":
#   → Proceed to create new research work item
```

#### Step 0b (NEW): Check for duplicate research via NLP

```bash
CALL SKILL: wiki-manager
{
  "action": "find-duplicate-research",
  "repo": "owner/repo",
  "topic": "[from PM phase 1]",
  "persona": "[specific persona]"
}

# If duplicates_found > 0:
#   → Review matches
#   → If HIGH similarity (>0.9): UPDATE existing + link
#   → If LOW similarity (<0.7): Proceed with new research
```

#### Step 1 (EXISTING): Create research work item (only if not found in index)

```bash
# Create research: issue with standard format
gh issue create \
  --title "[research]: [Persona] for [Opportunity]" \
  --label "research:,pm-idea-$PM_IDEA_NUMBER" \
  --body "..."
```

#### Step 2 (NEW): Register in Index

```bash
CALL SKILL: wiki-manager
{
  "action": "register-research",
  "repo": "owner/repo",
  "research_type": "persona",
  "subject": "Field Manager",
  "wiki_page": "Personas/Field-Manager",
  "github_issue": "#$RESEARCH_ISSUE_NUMBER",
  "status": "In Progress"
}
```

**Agents Affected:**
1. **Research Agent** — Add Step 0 + Step 0b + Step 2
2. **PM Agent (Phase 1)** — Add Step 0 before creating research: items
3. **Orchestrator PM** — Add Step 0 validation before spawning Phase 1

---

### Part 5: Migration Plan (Existing Wiki → Structured)

#### Step 1: Audit current wiki
```bash
gh wiki clone owner/repo.wiki
find . -name "*.md" | grep -i persona | sort
# Output: Shows all persona pages with inconsistent naming
```

#### Step 2: Create standard directory structure
- Create `Personas/` directory
- Create `Journey-Maps/` directory
- Create `Competitive-Analysis/` directory
- Create `Market-Trends/` directory
- Create `Feature-Research/` directory

#### Step 3: Rename & reorganize pages
- Personas-John.md → Personas/Field-Manager.md
- John-Persona.md → Personas/Field-Manager.md (merge if duplicate)
- Move all journey maps to Journey-Maps/

#### Step 4: Create Research-to-Decision-Index.md
- Scan all wiki pages
- Populate index table with entries
- Link all pages from index

#### Step 5: Update all agent documentation
- Add Step 0 to research creation workflow
- Update wiki-manager skill with new actions
- Document index lookup in all agents

---

## Implementation Checklist

- [ ] **Phase 1: Create Wiki Directory Structure** (1 day)
  - [ ] Rename personas to Kebab-Case, move to Personas/
  - [ ] Migrate journey maps to Journey-Maps/
  - [ ] Organize competitive analysis
  - [ ] Create index markdown file

- [ ] **Phase 2: Enhance wiki-manager Skill** (1-2 days)
  - [ ] Add check-persona-exists action
  - [ ] Add check-index-status action
  - [ ] Add find-duplicate-research action
  - [ ] Add register-research action
  - [ ] Add tests for each action

- [ ] **Phase 3: Update Agents** (1-2 days)
  - [ ] Research agent: Add wiki lookup Step 0
  - [ ] PM agent Phase 1: Add wiki lookup before research spawning
  - [ ] Orchestrator PM: Add validation
  - [ ] Update documentation

- [ ] **Phase 4: Verification & Rollout** (0.5 day)
  - [ ] Test: Research agent avoids duplicate work
  - [ ] Test: Index updates on new research
  - [ ] Train team on new structure
  - [ ] Monitor for 1 week (catch edge cases)

---

## Expected Benefits

✅ **Problem 1 (Organizational Chaos) Solved:**
- Clear, predictable structure for all wiki pages
- Consistent naming (Kebab-Case)
- Directory hierarchy by research type
- Single index for discovery

✅ **Problem 2 (Duplicate Research) Solved:**
- Agents check index BEFORE creating work
- NLP matching catches near-duplicates
- Registry tracks what's complete/in-progress/deferred
- No redundant interviews or wasted research effort

✅ **Secondary Benefits:**
- New team members understand structure immediately
- Onboarding faster (clear directory to explore)
- Research reusable across features/opportunities
- Historical artifacts preserved and discoverable
- Audit trail: index shows what research was done when

