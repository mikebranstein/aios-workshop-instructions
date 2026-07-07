# Wiki Organization Implementation Guide

## Quick Start: Solving the 2 Problems

**Problem 1: Wiki is a sprawling mess (organizational chaos)**  
**Problem 2: Agents do duplicate research (no wiki consultation)**

**Solution:** Standardized wiki structure + mandatory wiki lookup before creating research work

---

## What Changed

### 1. New Wiki Directory Structure (MANDATORY)

**Before:** Pages scattered, naming inconsistent  
- `Personas-John`
- `John-Persona`
- `John-Interview-Notes`

**After:** Clear, predictable structure (Kebab-Case filenames)
```
Research Wiki (Canonical)
├── Personas/
│   ├── Field-Manager.md
│   ├── Facility-Director.md
│   └── [Name].md (kebab-case)
├── Journey-Maps/
│   ├── Field-Manager-Equipment-Checkout.md
│   └── [Name].md
├── Competitive-Analysis/
│   ├── Market-Positioning.md
│   └── [Name].md
├── Market-Trends/
│   ├── Field-Operations-Automation.md
│   └── [Name].md
├── Feature-Research/
│   ├── Mobile-Offline-Mode.md
│   └── [Name].md
└── Research-to-Decision-Index.md (MASTER REGISTRY)
```

### 2. Research-to-Decision-Index (Master Registry)

**What it is:** Single table showing all research done, current status, wiki location  
**Where:** `Research-to-Decision-Index.md` at root of wiki  
**Used by:** Agents check this BEFORE creating research items

**Example row:**
```
| Field Manager | ✅ Complete | Personas/Field-Manager.md | 2026-07-05 | #1023, #1024 | 10 interviews, high confidence | HIGH |
```

### 3. Enhanced wiki-manager Skill (4 New Actions)

Added to `templates/skills/wiki-manager.skill.md`:

| Action | Purpose | When to Use |
|--------|---------|-----------|
| `check-persona-exists` | Verify persona already researched | Before creating new research work |
| `check-index-status` | Query index for research status | Before spawning research items |
| `find-duplicate-research` | Detect similar research via NLP | Before creating work (catch near-duplicates) |
| `register-research` | Add to index when creating research | After creating new research work |

### 4. Updated Agent Workflows (Wiki Lookup Mandatory)

**Affected Agents:**
1. **PM Agent Phase 1** — Added Step 4: Wiki lookup before creating research items
2. **Research Agent** — Added Step 0: Wiki lookup before executing research

**New workflow pattern:**
```
Agent creates research work item:
  ↓
Step 0 (NEW): Check Research-to-Decision-Index
  ↓
Found existing Complete?   →  Link to it, don't create new
  ↓
Found existing In-Progress? → Link to it, don't create new
  ↓
Found duplicate research?    → Use existing, don't create new
  ↓
NOT found?                    → Create new research work item
  ↓
New Step: Register in index   → Add to Research-to-Decision-Index
```

---

## Implementation Roadmap (4 Phases)

### Phase 1: Audit & Plan (1 day)

**Goal:** Understand current wiki state and plan migration

**Steps:**
1. List all current wiki pages:
   ```bash
   gh wiki clone owner/repo.wiki
   ls -la *.md | wc -l  # Count pages
   ```

2. Identify all personas (may have inconsistent names):
   ```bash
   grep -i "persona" *.md | cut -d: -f1 | sort | uniq
   ```

3. Document current state:
   - How many persona pages?
   - Naming patterns observed?
   - Any duplicate research detected?
   - Any "stale" pages (>30 days old)?

4. Create migration plan:
   - List of personas to consolidate
   - Rename mapping (John-Persona → Field-Manager)

---

### Phase 2: Create Standard Structure (1 day)

**Goal:** Set up directory structure and master index

**Steps:**

1. **Create directory structure** in wiki:
   ```bash
   # Create folders (GitHub wiki needs folder structure in README)
   echo "# Personas" > wiki/Personas/README.md
   echo "# Journey Maps" > wiki/Journey-Maps/README.md
   echo "# Competitive Analysis" > wiki/Competitive-Analysis/README.md
   echo "# Market Trends" > wiki/Market-Trends/README.md
   echo "# Feature Research" > wiki/Feature-Research/README.md
   ```

2. **Create Research-to-Decision-Index.md** (copy template from WIKI_ORGANIZATION_AND_DEDUPLICATION_STANDARD.md)

3. **Test wiki-manager skill** with new structure:
   ```bash
   # Test: Can skill read/write to Personas/Field-Manager.md?
   CALL wiki-manager check-index-status
   ```

---

### Phase 3: Migrate Existing Pages (1-2 days)

**Goal:** Reorganize existing research to new structure

**Steps:**

1. **For each persona**, audit & consolidate:
   ```bash
   # Move pages to standard location
   Personas-John.md → Personas/Field-Manager.md
   John-Persona.md → (merge content into Field-Manager if duplicate)
   John-Interview-Notes.md → (append findings to Field-Manager)
   ```

2. **Rename consistently** (Kebab-Case, full names):
   - Personas-John → Personas/Field-Manager
   - CEO-Journey → Journey-Maps/Facility-Director-Inventory
   - Competitive-Analysis → Competitive-Analysis/Market-Positioning

3. **Populate Research-to-Decision-Index**:
   - Scan all pages
   - Extract: Persona name, research status (assume Complete if no active work), wiki location
   - Add rows to index table

4. **Update all wiki links**:
   - Any links pointing to old page names?
   - Update to new structure: `[Personas/Field-Manager.md](Personas/Field-Manager.md)`

---

### Phase 4: Update Agents & Validation (1-2 days)

**Goal:** Deploy new wiki-lookup workflow; verify no duplicate research

**Steps:**

1. **Deploy enhanced wiki-manager skill**:
   - Verify 4 new actions implemented: `check-index-status`, `find-duplicate-research`, `register-research`, `check-persona-exists`
   - Test each action against populated wiki

2. **Activate PM Agent Phase 1 changes**:
   - PM agent now does Step 4: Wiki lookup before creating research items
   - Test: Create new pm-idea → Verify Step 4 checks index

3. **Activate Research Agent changes**:
   - Research agent now does Step 0: Wiki lookup before executing
   - Test: Assign research item → Verify Step 0 checks wiki

4. **Validation Test Suite** (1-2 hours):
   - **Test 1:** Create pm-idea for existing persona → Verify agent finds existing research
   - **Test 2:** Create pm-idea for new persona → Verify agent creates research work
   - **Test 3:** Assign duplicate research → Verify agent detects and avoids duplication
   - **Test 4:** Update index after new research created → Verify registry is current

5. **Monitor for 1 week**:
   - Are agents checking wiki?
   - Any duplicate research still happening?
   - Any wiki structure violations?
   - Update process docs based on real usage

---

## Key Metrics (Track Before/After)

### Before Implementation
- [ ] # of duplicate research items created (identify redundant issues)
- [ ] Avg time to discover if persona already researched (manually)
- [ ] Wiki pages with inconsistent naming (count)
- [ ] % of agents checking wiki before creating work (baseline: likely 0%)

### After Implementation (Target: 4 weeks)
- [ ] # of duplicate research items created (target: 0)
- [ ] Avg time to discover research (automated via index: <1 sec)
- [ ] Wiki pages with consistent naming (target: 100%)
- [ ] % of agents checking wiki (target: 100%)

**Success = No new duplicate research created + All wiki pages organized**

---

## Troubleshooting

### Issue: Agents not calling wiki-manager check-index-status

**Cause:** Agent code not updated or wiki-manager skill not deployed  
**Fix:**
1. Verify wiki-manager skill has 4 new actions (check-index-status, find-duplicate-research, register-research, check-persona-exists)
2. Verify PM agent has Step 4 code
3. Verify research agent has Step 0 code
4. Test: Manually call `gh issue create` with research: label → Agent should invoke wiki-manager

### Issue: Index not updating when new research created

**Cause:** `register-research` action not being called  
**Fix:**
1. Verify PM Agent Phase 1 Step 6 (NEW) calls register-research
2. Test: Create research item → Check if index entry added
3. If not, add manual index update via wiki-manager

### Issue: Wiki-manager skill returns "not found" for persona that exists

**Cause:** Page name mismatch (Personas/Field-Manager.md vs. Personas/field-manager.md)  
**Fix:**
1. Verify Kebab-Case naming is consistent
2. Case-sensitive: GitHub wiki is case-sensitive
3. Rename all pages to exact expected names during Phase 3

### Issue: Duplicate research still being created

**Cause:** Agents bypassing wiki checks or index not accurate  
**Fix:**
1. Verify Step 0/Step 4 code is being executed (add logging)
2. Check index entries are current (update after each research completes)
3. Verify `find-duplicate-research` NLP is tuned (check similarity threshold)

---

## Quick Reference: New Commands for Agents

### Before Creating Research Item
```bash
# Step 4a: Check if research exists
gh issue comment $PM_IDEA_NUMBER --body "Checking wiki for existing research..."
CALL wiki-manager check-index-status "Field Manager"
# → If found AND Complete: skip creation, link to existing
# → If not found: proceed to create
```

### After Creating Research Item
```bash
# Step 6: Register in index
CALL wiki-manager register-research \
  --research_type "persona" \
  --subject "Field Manager" \
  --wiki_page "Personas/Field-Manager" \
  --github_issue "#1025"
```

### From Research Agent (Step 0)
```bash
# Check if already researched
CALL wiki-manager check-index-status "Field Manager"
# → If Complete: use existing, close this issue
# → If In Progress: link and close this issue
# → If not found: proceed to research
```

---

## Success Criteria

✅ **Problem 1 Solved:** Organizational chaos gone
- All wiki pages in consistent directory structure
- Naming convention (Kebab-Case) enforced
- Research-to-Decision-Index provides single discovery point
- New team members can navigate structure immediately

✅ **Problem 2 Solved:** Duplicate research eliminated
- Agents check wiki before creating research work (100%)
- Duplicate research items: 0 created after rollout
- Index prevents parallel research on same persona
- Team stops conducting redundant interviews

✅ **Secondary Benefit:** Wiki becomes strategic asset
- Research reusable across features
- Historical findings discoverable
- Supports better prioritization (existing research surfaces insights)
- Reduces feedback loops (build on proven research)

---

## Timeline Estimate

- **Phase 1 (Audit):** 1 day
- **Phase 2 (Structure):** 1 day
- **Phase 3 (Migration):** 1-2 days
- **Phase 4 (Deploy & Test):** 1-2 days
- **Monitoring:** 1 week

**Total: 5-7 days from start to fully deployed + validated**

Start with Phase 1 audit to understand scope, then proceed.
