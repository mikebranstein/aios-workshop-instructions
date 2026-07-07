# Audit: Follow-On Research Spawning Process

## Problem Statement

Research issues are closing, but follow-on research items (for CRITICAL next steps) are NOT being created. The orchestrator may not be noticing that follow-on research is needed.

---

## Root Cause Analysis

### **GAP 1: Research Agent Closure Procedure (CRITICAL)**

**Current State:**
- Step 5 shows a template with CRITICAL/HIGH/MEDIUM/LOW next steps
- Template says "Post final research summary comment"
- Template includes full CRITICAL next steps section
- **BUT:** No explicit instruction on HOW to:
  - Close the research: issue AFTER posting comment
  - Use `gh issue close` command
  - Add a label when closing
  - Verify closure

**Result:**
- Research Agent may be posting the comment ✅
- But NOT ACTUALLY CLOSING the issue ❌
- Orchestrator Step 3b waits for issues to be CLOSED
- If not closed, Orchestrator never reaches PM Phase 2

**Evidence:**
Research Agent Step 5 ends with:
```
Close research issue with summary.
```

This is **vague**. No command specified. No timing. No label specified.

---

### **GAP 2: Research Agent - No Explicit Link to Research Issue**

**Current State:**
- Research Agent posts comments on the research: issue
- PM Agent Phase 2 needs to READ those comments
- **BUT:** The research: issue numbers are not explicitly captured

**Problem:**
- When PM Agent Phase 2 runs on pm-idea #123
- How does it know which research: issues to read?
- It needs to query: "What research: items are linked to pm-idea #123?"

**Current attempt (Orchestrator):**
```bash
gh issue view <pm-idea-#N> --json body | grep -o "#\d\+" | while read research_item; do
  status=$(gh issue view $research_item --json state --jq '.state')
done
```

This extracts issue numbers from pm-idea BODY. But:
- Research items might be created AFTER pm-idea is created
- Body text might not have been updated
- **Better way:** Query linked issues via GitHub API

---

### **GAP 3: PM Agent Phase 2 - Step 3 Vague on Reading Comments**

**Current State:**
Step 3 says:
```
Read research comments for severity-rated Next Steps Assessment:
- Are there any CRITICAL follow-on research items identified?
- CRITICAL = must validate before CHAMPION decision can be made
```

**Problem:**
- "Read research comments" is vague
- No explicit instruction on HOW to:
  - Get the list of research: issues
  - Fetch comments from each research: issue
  - Parse for "CRITICAL" section
  - Extract specific next steps
  - Create follow-on research issue

**Result:**
- PM Agent might skip this step or do it incorrectly
- Follow-on research never gets spawned

---

### **GAP 4: Orchestrator - No Explicit Research Issue Linking**

**Current State:**
- Orchestrator Step 3b spawns research agents
- Each research: item is created separately
- **BUT:** No explicit linking between pm-idea and research: items

**Problem:**
- When Step 4 checks if research is complete, it manually extracts issue numbers
- When Step 5 spawns PM Phase 2, it passes only pm-idea #N
- PM Phase 2 has no reliable way to find the associated research: issues

**Better way:**
- When creating research: issue (Phase 1), explicitly link it to pm-idea
- Use GitHub's "links" feature or standardized comment format
- Make it programmatically discoverable

---

## Complete Flow Audit

### **Phase 1: Creating Research Items** ✅

1. PM Agent Phase 1 creates research: issue
2. Body includes: `Linked to pm-idea #[N]` 
3. Research issue created with label: `research:` + `pm-idea-[N]`

**Status:** ✅ Mostly good (though linking could be more explicit)

---

### **Phase 1.5: Research Execution** ⚠️

1. Research Agent reads research: issue
2. Conducts research (methodologies, interviews, etc.)
3. Updates Wiki pages ✅ (now via wiki-manager skill)
4. **CRITICAL STEP:** Posts closure comment with CRITICAL/HIGH/MEDIUM/LOW next steps
5. **CRITICAL STEP:** Closes research: issue

**GAP:** 
- Step 4 happens ✅
- Step 5 is **vague** ❌
  - No explicit `gh issue close` command
  - No label applied
  - No verification that issue is actually closed

**Result:**
- Orchestrator Step 3b: `while true do: check if research: item CLOSED`
- If not closed → waits forever (or times out)

---

### **Phase 2 Setup: Reading Closed Research** ⚠️

1. Orchestrator Step 4: Lists all research: items
2. Verifies ALL are CLOSED

**GAP:**
```bash
gh issue view <pm-idea-#N> --json body | grep -o "#\d\+" | ...
```

This only works if research issue numbers are in pm-idea BODY. But:
- Research items created in Phase 1 by PM Agent
- These are new issues separate from pm-idea
- They might NOT be in the body

**Better way:**
```bash
# Query research: items linked to pm-idea #N
gh issue list --label "pm-idea-[N]" --state closed --search "research:"
```

---

### **Phase 2: Read Research Comments** ❌

**PM Agent Phase 2 Step 3 - Current:**
```
Read research comments for severity-rated Next Steps Assessment
```

**Problem:** NO actual implementation shown. How does PM Agent:
1. Get list of research: issues for this pm-idea?
2. Fetch ALL comments from each research: issue?
3. Find the closure comment (usually last comment)?
4. Parse for "CRITICAL" section?
5. Extract specific next steps?
6. Create follow-on research issue?

**Current implementation:** Unclear. Possibly missing entirely.

---

## Recommended Fixes

### **Fix 1: Research Agent - Explicit Closure Procedure**

**Location:** Research Agent Step 5

**Change:** Replace vague "Close research issue with summary" with explicit steps:

```markdown
**CLOSURE STEPS:**

6. **Close the research: issue:**

   After posting the complete research summary with Next Steps Assessment:
   
   ```bash
   # Get this research issue number (passed as parameter or extract from environment)
   RESEARCH_ISSUE_NUM=$(gh issue view --json number --jq '.number')
   
   # Close with label
   gh issue close $RESEARCH_ISSUE_NUM --reason "not_planned"
   
   # Add label: research-complete
   gh issue edit $RESEARCH_ISSUE_NUM --add-label "research-complete"
   
   # Verify closure
   gh issue view $RESEARCH_ISSUE_NUM --json state --jq '.state'
   # Should return: CLOSED
   ```
   
   **DO NOT proceed until:**
   - ✅ Research summary comment posted
   - ✅ CRITICAL/HIGH/MEDIUM/LOW next steps visible in comment
   - ✅ All wiki pages updated
   - ✅ Research issue is CLOSED (verified)
```

---

### **Fix 2: PM Agent Phase 2 - Explicit Comment Reading Procedure**

**Location:** Product Manager Agent Step 3 ("Evaluate Follow-On Research Needs")

**Add:** Detailed procedure to find and read research comments:

```markdown
3. **Evaluate Follow-On Research Needs (Detailed Procedure):**

   **STEP 3.1: Find research: issues linked to this pm-idea**
   
   Query for all research items tagged with this pm-idea:
   ```bash
   # Get list of research items for this pm-idea (e.g., #123)
   gh issue list \
     --label "pm-idea-[THIS_PM_IDEA_NUMBER]" \
     --state closed \
     --search "research:" \
     --json number,title,state
   ```
   
   Example output:
   ```
   Number: 125, Title: "research: Personas-John", State: CLOSED
   Number: 126, Title: "research: Journey-Maps", State: CLOSED
   ```
   
   **STEP 3.2: Read comments from each closed research: issue**
   
   For each research: issue found above:
   ```bash
   # Get all comments (API returns newest last, so last comment is likely the summary)
   gh issue view #125 --json comments --jq '.comments'
   ```
   
   **STEP 3.3: Parse for CRITICAL next steps**
   
   Loop through comments, find section:
   ```markdown
   **Next Steps Assessment (Severity-Rated for Follow-On Research):**
   
   **CRITICAL - MUST VALIDATE BEFORE CHAMPION DECISION:**
   - [Next step 1]: [Why this is critical]...
   - [Next step 2]: ...
   ```
   
   **STEP 3.4: Make decision**
   
   If ANY "CRITICAL" items found:
   ```
   - Create issue: "research: [Topic] - Follow-On Critical Validation"
   - Label: follow-on-research, pm-idea-[THIS_NUMBER]
   - Body: [Copy CRITICAL next step from research comment]
   - Link: "Related to research issue #125"
   - Post comment: "Spawning follow-on research for CRITICAL validation."
   - Return to Orchestrator (loop back to Step 3b to process this follow-on item)
   ```
   
   If NO CRITICAL items found:
   ```
   - Proceed to Step 4 (final decision)
   - Document HIGH/MEDIUM/LOW items as "Post-Launch Research Recommendations"
   ```
```

---

### **Fix 3: Orchestrator - Explicit Research Issue Discovery**

**Location:** Orchestrator Step 3b & Step 4

**Change:** Use consistent labeling to find research issues:

```markdown
**STEP 3B: Spawn Research Agents (Sequential)**

When PM Agent Phase 1 creates research: items, they must be labeled:
- Label: pm-idea-[THIS_PM_IDEA_NUMBER]
- Label: research:

Example: pm-idea-123 creates research-124 and research-125
Both get labels: `pm-idea-123`, `research:`

**STEP 4: Verify research completion**

```bash
# Find all research items for this pm-idea
RESEARCH_ITEMS=$(gh issue list \
  --label "pm-idea-[THIS_PM_IDEA_NUMBER]" \
  --label "research:" \
  --state all \
  --json number)

# Check if ALL are CLOSED
for issue_num in $RESEARCH_ITEMS; do
  STATE=$(gh issue view #$issue_num --json state --jq '.state')
  if [ "$STATE" != "CLOSED" ]; then
    echo "ERROR: Research item #$issue_num is still $STATE"
    exit 1
  fi
done

echo "✅ All research items complete"
```

**STEP 5: Pass research items to PM Phase 2**

When spawning PM Agent Phase 2, pass:
- pm-idea issue number
- List of research: issue numbers (so PM Phase 2 knows where to read comments)

```bash
task(
  description="Validate pm-idea #N with research from: #124, #125",
  agent_id="product-manager",
  parameters={
    "pm_idea_number": 123,
    "research_issues": [124, 125]
  }
)
```
```

---

## Testing the Flow

### **Manual Test Case**

1. **Create test pm-idea:**
   ```bash
   gh issue create \
     --label pm-idea \
     --title "Test mobile app feature" \
     --body "Customer request from support"
   # Returns: issue #999
   ```

2. **Run Phase 1 (PM Agent):**
   - Should create research issues, labeled: `pm-idea-999`, `research:`
   - Example: #1000, #1001

3. **Verify research issue labels:**
   ```bash
   gh issue view #1000 --json labels
   # Should show: ["pm-idea-999", "research:", ...]
   ```

4. **Run Phase 1.5 (Research Agent):**
   - On #1000: Conduct research
   - Post closure comment with CRITICAL next steps
   - Close issue with: `gh issue close #1000`

5. **Verify closure:**
   ```bash
   gh issue view #1000 --json state
   # Should return: {"state": "CLOSED"}
   ```

6. **Query research comments:**
   ```bash
   gh issue view #1000 --json comments --jq '.comments[-1].body'
   # Should show closure comment with CRITICAL section
   ```

7. **Run Phase 2 (PM Agent):**
   - Should read comments from #1000
   - Find CRITICAL items
   - Create follow-on research issue if needed

---

## Summary of Gaps

| Gap | Location | Problem | Impact |
|-----|----------|---------|--------|
| **Gap 1** | Research Agent Step 5 | No explicit `gh issue close` command | Research issue never closes, orchestrator hangs |
| **Gap 2** | Research Agent | No label applied to research issue | PM Phase 2 can't find research issues |
| **Gap 3** | PM Agent Phase 2 Step 3 | "Read research comments" is vague, no implementation | Follow-on research never gets created |
| **Gap 4** | Orchestrator Step 4 | Research issue discovery relies on pm-idea BODY | Unreliable way to find research items |
| **Gap 5** | Orchestrator Step 5 | Research issue numbers not passed to PM Phase 2 | PM Agent doesn't know where to read comments |

---

## Recommended Action Items

1. ✅ **Update Research Agent Step 5** with explicit closure procedure (with `gh issue close`)
2. ✅ **Add label strategy** to research: issues (pm-idea-[N] label for linking)
3. ✅ **Update PM Agent Phase 2 Step 3** with detailed comment-reading procedure
4. ✅ **Update Orchestrator Steps 3b/4/5** to use consistent labeling for discovery
5. ⏳ **Test the flow end-to-end** with a manual test case
