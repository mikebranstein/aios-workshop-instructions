# Skill: GitHub Wiki Manager (Librarian Model)

## Philosophy

**Wiki Manager = Dumb Librarian**

Storage, retrieval, and housekeeping. **Agents make decisions.** No auto-classification, no auto-organization, no magic. Agents control content, location, and metadata.

## Purpose

Provide simple, explicit wiki operations for AIOS agents. All decisions about content, classification, and placement rest with agents.

## Prerequisites

- GitHub CLI (`gh`) installed and authenticated
- Git installed
- PowerShell 5.1+
- Wiki enabled on target repo

## Input Parameters

```json
{
  "action": "string (required) - search | write-page | update-index | audit-and-organize",
  "repo": "string (required) - format: 'owner/repo'",
  "query": "string (optional) - search keyword",
  "page_path": "string (optional) - where to write (e.g., 'Personas/Field-Manager')",
  "content": "string (optional) - markdown content to write",
  "subject": "string (optional) - topic for index",
  "status": "string (optional) - Complete|In Progress|Deferred",
  "confidence": "string (optional) - HIGH|MEDIUM|LOW",
  "github_issue": "string (optional) - issue number for tracking"
}
```

## Actions

### **search**

Find pages by keyword. Returns candidates with match scores and snippets. **Agent evaluates results.**

**Input:**
```json
{
  "action": "search",
  "repo": "owner/repo",
  "query": "Field Manager persona"
}
```

**Output:**
```json
{
  "status": "success|error",
  "query": "Field Manager persona",
  "total_found": 2,
  "results": [
    {
      "page": "Personas/Field-Manager",
      "match_score": 0.98,
      "snippet": "# Field Manager\n\nManages equipment checkout and field operations..."
    },
    {
      "page": "Journey-Maps/Field-Manager-Checkout",
      "match_score": 0.72,
      "snippet": "Field Manager's experience during checkout workflow..."
    }
  ]
}
```

---

### **write-page**

Store content at exact location. **Agent decides where and what.**

**Input:**
```json
{
  "action": "write-page",
  "repo": "owner/repo",
  "page_path": "Personas/Field-Manager",
  "content": "# Field Manager\n\n## Demographics\n..."
}
```

**Output:**
```json
{
  "status": "success|error",
  "page_path": "Personas/Field-Manager",
  "wiki_url": "https://github.com/owner/repo/wiki/Personas/Field-Manager",
  "committed": true,
  "commit_message": "Create Personas/Field-Manager.md"
}
```

---

### **update-index**

Register research metadata in master index. **Agent provides all data.**

**Input:**
```json
{
  "action": "update-index",
  "repo": "owner/repo",
  "subject": "Field Manager",
  "status": "Complete",
  "wiki_page": "Personas/Field-Manager",
  "github_issue": "#1025",
  "confidence": "HIGH",
  "findings_summary": "10 interviews completed. Established primary persona for field operations."
}
```

**Output:**
```json
{
  "status": "success|error",
  "message": "Research index updated",
  "index_entry_added": true,
  "index_page": "Research-to-Decision-Index",
  "timestamp": "2026-07-08T14:30:00Z"
}
```

---

### **audit-and-organize**

Detect chaos and flag issues. **No auto-merging.** For housekeeping/reporting.

**Input:**
```json
{
  "action": "audit-and-organize",
  "repo": "owner/repo",
  "dry_run": true
}
```

**Output:**
```json
{
  "status": "success|error",
  "audit_timestamp": "2026-07-08T14:30:00Z",
  "wiki_state": {
    "total_pages": 12,
    "organized_pages": 10,
    "unorganized_pages": 2
  },
  "issues_detected": [
    {
      "issue_type": "duplicate_candidates",
      "severity": "HIGH",
      "description": "Found 2 similar pages that might be duplicates",
      "pages": ["Personas-John", "Personas/John-Doe"],
      "recommendation": "Manual review recommended - are these the same person?"
    },
    {
      "issue_type": "naming_inconsistency",
      "severity": "MEDIUM",
      "pages": ["Personas-Sarah", "Personas/Sarah-Director"],
      "recommendation": "Inconsistent naming convention"
    },
    {
      "issue_type": "uncategorized_page",
      "severity": "LOW",
      "pages": ["Research-Notes"],
      "recommendation": "Page not in standard folder structure"
    }
  ],
  "index_status": {
    "total_entries": 8,
    "index_current": false,
    "last_updated": "2026-07-05",
    "days_stale": 3
  },
  "housekeeping_actions_if_dry_run_false": {
    "pages_reorganized": 0,
    "pages_consolidated": 0,
    "naming_fixed": 0,
    "index_updated": true
  }
}
```

---

## Master Index Format

Research-to-Decision-Index.md maintained in wiki root:

```markdown
# Research-to-Decision-Index

Master registry of all research. Updated explicitly by agents as research progresses.

Last Updated: 2026-07-08 by Research Agent #1025

| Subject | Status | Wiki Page | Last Updated | GitHub Issue | Confidence | Findings |
|---------|--------|-----------|--------------|--------------|------------|----------|
| Field Manager | ✅ Complete | Personas/Field-Manager | 2026-07-08 | #1025 | HIGH | 10 interviews, established persona |
| Equipment Checkout | 🔄 In Progress | Journey-Maps/Field-Manager-Checkout | 2026-07-07 | #1026 | MEDIUM | 5 of 7 interviews complete |
| Competitor Analysis | ⏸️ Deferred | Competitive-Analysis/Market-Position | 2026-07-01 | #1020 | LOW | Scope changed, deferring |
```

---

## Standard Directory Structure

Agents are responsible for organizing content into these folders:

```
Personas/
  └─ Field-Manager.md
  └─ Facility-Director.md

Journey-Maps/
  └─ Field-Manager-Equipment-Checkout.md
  └─ Facility-Director-Inventory.md

Competitive-Analysis/
  └─ Market-Positioning.md
  └─ Feature-Comparison.md

Market-Trends/
  └─ Field-Operations-Automation.md

Feature-Research/
  └─ Bulk-Checkout-Operations.md
  └─ Mobile-Offline-Mode.md

Research-to-Decision-Index.md (root)
```

**Agents decide folder placement.** Wiki-manager doesn't auto-classify.

---

## Implementation

### PowerShell (Librarian Version)

```powershell
# ============================================================================
# GitHub Wiki Manager - Librarian Model (Simple, Explicit)
# ============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$action,
    
    [Parameter(Mandatory=$true)]
    [string]$repo,
    
    [Parameter(Mandatory=$false)]
    [string]$query,
    
    [Parameter(Mandatory=$false)]
    [string]$page_path,
    
    [Parameter(Mandatory=$false)]
    [string]$content,
    
    [Parameter(Mandatory=$false)]
    [string]$subject,
    
    [Parameter(Mandatory=$false)]
    [string]$status,
    
    [Parameter(Mandatory=$false)]
    [string]$confidence,
    
    [Parameter(Mandatory=$false)]
    [string]$github_issue,
    
    [Parameter(Mandatory=$false)]
    [boolean]$dry_run = $true
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$WIKI_BASE = if ($env:AIOS_WIKI_CACHE) { $env:AIOS_WIKI_CACHE } else { "$env:TEMP" }
$WIKI_TEMP_ID = "aios-wiki-$(Get-Random -Minimum 100000 -Maximum 999999)"
$WIKI_TEMP = Join-Path $WIKI_BASE $WIKI_TEMP_ID
$IS_PERSISTENT = [bool]$env:AIOS_WIKI_CACHE

# ============================================================================
# Logging & Helpers
# ============================================================================

function Write-Log {
    param([string]$message, [string]$level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$level] $message"
}

function Get-WikiUrl { param([string]$repo); return "https://github.com/$repo.wiki.git" }

function Initialize-WikiTemp {
    try {
        if (Test-Path $WIKI_TEMP) {
            Remove-Item -Recurse -Force $WIKI_TEMP -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
        }
        New-Item -ItemType Directory -Path $WIKI_TEMP -Force | Out-Null
        return $true
    }
    catch {
        Write-Log "Failed to initialize temp: $_" "ERROR"
        return $false
    }
}

function Clone-Wiki { param([string]$repo)
    try {
        Push-Location $WIKI_TEMP
        & git clone $(Get-WikiUrl $repo) "." 2>&1 | Out-Null
        Pop-Location
        return $true
    }
    catch {
        Write-Log "Failed to clone: $_" "ERROR"
        return $false
    }
}

function Configure-GitUser {
    try {
        Push-Location $WIKI_TEMP
        & git config user.email "aios-automation@github.local" 2>&1 | Out-Null
        & git config user.name "AIOS Agent" 2>&1 | Out-Null
        Pop-Location
        return $true
    }
    catch { return $false }
}

function Push-WikiChanges { param([string]$message)
    try {
        Push-Location $WIKI_TEMP
        & git add "." 2>&1 | Out-Null
        $status = & git status --porcelain 2>&1
        if (-not $status) { Pop-Location; return $true }
        & git commit -m $message 2>&1 | Out-Null
        & git push origin main 2>&1 | Out-Null
        Pop-Location
        return $true
    }
    catch {
        Write-Log "Failed to push: $_" "ERROR"
        return $false
    }
}

function Cleanup-WikiTemp {
    if (-not $IS_PERSISTENT -and (Test-Path $WIKI_TEMP)) {
        Remove-Item -Recurse -Force $WIKI_TEMP -ErrorAction SilentlyContinue
    }
}

# ============================================================================
# Search Implementation
# ============================================================================

function Search-WikiPages {
    param([string]$wikiPath, [string]$query)
    
    $results = @()
    $query_lower = $query.ToLower()
    
    $mdFiles = Get-ChildItem -Path $wikiPath -Recurse -Filter "*.md" -ErrorAction SilentlyContinue |
               Where-Object { $_.Name -ne "Home.md" -and $_.Name -ne "README.md" }
    
    foreach ($file in $mdFiles) {
        $content = Get-Content -Path $file.FullName -Encoding UTF8 -Raw
        $title = ($content -split "`n" | Where-Object { $_ -match '^#\s' } | Select-Object -First 1) -replace '^#\s+', ''
        
        # Simple keyword matching (could be enhanced)
        $query_words = $query_lower -split '\s+'
        $matching_words = @()
        
        foreach ($word in $query_words) {
            $word_count = ([regex]::Matches($content.ToLower(), "\b$word\b")).Count
            if ($word_count -gt 0) {
                $matching_words += @{ word = $word; count = $word_count }
            }
        }
        
        if ($matching_words.Count -gt 0) {
            $match_score = [math]::Min(($matching_words | Measure-Object -Property count -Sum).Sum / ($query_words.Count * 5), 1.0)
            
            # Extract snippet
            $snippet = ($content -split "`n" | Select-Object -First 3) -join "`n"
            if ($snippet.Length -gt 200) { $snippet = $snippet.Substring(0, 200) + "..." }
            
            # Build relative path
            $relativePath = $file.FullName.Substring($wikiPath.Length).TrimStart('\')
            $page = $relativePath -replace '\.md$', '' -replace '\\', '/'
            
            $results += @{
                page = $page
                match_score = [math]::Round($match_score, 2)
                title = $title
                snippet = $snippet
            }
        }
    }
    
    # Sort by score descending
    return $results | Sort-Object -Property match_score -Descending
}

# ============================================================================
# Action Handlers
# ============================================================================

function Handle-Search {
    Write-Log "Executing search for: $query"
    
    $result = @{
        status = "error"
        query = $query
        total_found = 0
        results = @()
    }
    
    if (-not (Initialize-WikiTemp)) { Cleanup-WikiTemp; return $result | ConvertTo-Json -Depth 5 }
    if (-not (Clone-Wiki $repo)) { Cleanup-WikiTemp; return $result | ConvertTo-Json -Depth 5 }
    
    try {
        $results = Search-WikiPages $WIKI_TEMP $query
        
        $result.status = "success"
        $result.total_found = $results.Count
        $result.results = $results | Select-Object page, match_score, snippet
        
        Write-Log "Found $($results.Count) matches"
    }
    catch {
        Write-Log "Search failed: $_" "ERROR"
        $result.status = "error"
    }
    finally {
        Cleanup-WikiTemp
    }
    
    return $result | ConvertTo-Json -Depth 5
}

function Handle-WritePage {
    Write-Log "Executing write-page to: $page_path"
    
    $result = @{
        status = "error"
        page_path = $page_path
        wiki_url = ""
        committed = $false
        commit_message = ""
    }
    
    if (-not $page_path) { $result.status = "error"; return $result | ConvertTo-Json }
    if (-not $content) { $result.status = "error"; return $result | ConvertTo-Json }
    
    if (-not (Initialize-WikiTemp)) { Cleanup-WikiTemp; return $result | ConvertTo-Json }
    if (-not (Clone-Wiki $repo)) { Cleanup-WikiTemp; return $result | ConvertTo-Json }
    if (-not (Configure-GitUser)) { Cleanup-WikiTemp; return $result | ConvertTo-Json }
    
    try {
        # Parse page_path: "Personas/Field-Manager" -> create folders and write file
        $parts = $page_path -split '/' | Where-Object { $_ }
        $fileName = ($parts[-1] -replace '\s+', '-') + ".md"
        
        if ($parts.Count -gt 1) {
            $folderPath = Join-Path $WIKI_TEMP ($parts[0..($parts.Count-2)] -join '\')
            if (-not (Test-Path $folderPath)) {
                New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
            }
            $filePath = Join-Path $folderPath $fileName
        } else {
            $filePath = Join-Path $WIKI_TEMP $fileName
        }
        
        # Write content
        Set-Content -Path $filePath -Value $content -Encoding UTF8
        
        # Push
        if (Push-WikiChanges "Create $page_path") {
            $result.status = "success"
            $result.committed = $true
            $result.wiki_url = "https://github.com/$repo/wiki/$page_path"
            $result.commit_message = "Create $page_path.md"
        }
    }
    catch {
        Write-Log "Write failed: $_" "ERROR"
        $result.status = "error"
    }
    finally {
        Cleanup-WikiTemp
    }
    
    return $result | ConvertTo-Json -Depth 5
}

function Handle-UpdateIndex {
    Write-Log "Executing update-index for: $subject"
    
    $result = @{
        status = "error"
        message = ""
        index_entry_added = $false
    }
    
    if (-not (Initialize-WikiTemp)) { Cleanup-WikiTemp; return $result | ConvertTo-Json }
    if (-not (Clone-Wiki $repo)) { Cleanup-WikiTemp; return $result | ConvertTo-Json }
    if (-not (Configure-GitUser)) { Cleanup-WikiTemp; return $result | ConvertTo-Json }
    
    try {
        $indexPath = Join-Path $WIKI_TEMP "Research-to-Decision-Index.md"
        
        # Create index if not exists
        if (-not (Test-Path $indexPath)) {
            $indexContent = @"
# Research-to-Decision-Index

Master registry of all research. Updated by agents as research progresses.

| Subject | Status | Wiki Page | Last Updated | GitHub Issue | Confidence | Findings |
|---------|--------|-----------|--------------|--------------|------------|----------|
"@
        } else {
            $indexContent = Get-Content -Path $indexPath -Encoding UTF8 -Raw
        }
        
        # Add entry
        $statusEmoji = if ($status -eq "Complete") { "✅" } elseif ($status -eq "In Progress") { "🔄" } else { "⏸️" }
        $newEntry = "| $subject | $statusEmoji $status | $wiki_page | $(Get-Date -Format 'yyyy-MM-dd') | $github_issue | $confidence | $findings_summary |"
        
        $indexContent += "`n$newEntry"
        Set-Content -Path $indexPath -Value $indexContent -Encoding UTF8
        
        if (Push-WikiChanges "Update index: $subject") {
            $result.status = "success"
            $result.message = "Index entry added: $subject"
            $result.index_entry_added = $true
        }
    }
    catch {
        Write-Log "Index update failed: $_" "ERROR"
        $result.status = "error"
    }
    finally {
        Cleanup-WikiTemp
    }
    
    return $result | ConvertTo-Json -Depth 5
}

function Handle-AuditAndOrganize {
    Write-Log "Executing audit-and-organize (dry_run: $dry_run)"
    
    $result = @{
        status = "error"
        audit_timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
        wiki_state = @{}
        issues_detected = @()
        index_status = @{}
    }
    
    if (-not (Initialize-WikiTemp)) { Cleanup-WikiTemp; return $result | ConvertTo-Json -Depth 5 }
    if (-not (Clone-Wiki $repo)) { Cleanup-WikiTemp; return $result | ConvertTo-Json -Depth 5 }
    
    try {
        $mdFiles = Get-ChildItem -Path $WIKI_TEMP -Recurse -Filter "*.md" -ErrorAction SilentlyContinue |
                   Where-Object { $_.Name -ne "Home.md" -and $_.Name -ne "README.md" -and $_.Name -ne "Research-to-Decision-Index.md" }
        
        $total = $mdFiles.Count
        $organized = 0
        $unorganized = 0
        $duplicates = @()
        $naming_issues = @()
        
        foreach ($file in $mdFiles) {
            $relativePath = $file.FullName.Substring($WIKI_TEMP.Length).TrimStart('\')
            $isOrganized = $relativePath -match '^(Personas|Journey-Maps|Competitive-Analysis|Market-Trends|Feature-Research)\\'
            
            if ($isOrganized) { $organized++ } else { $unorganized++ }
            
            # Check naming (should be Kebab-Case)
            if ($file.BaseName -match '[A-Z]' -or $file.BaseName -match '_') {
                $naming_issues += $relativePath
            }
        }
        
        # Look for near-duplicates
        $pageNames = @{}
        foreach ($file in $mdFiles) {
            $baseName = $file.BaseName.ToLower() -replace '[^a-z0-9]', ''
            if ($pageNames.ContainsKey($baseName)) {
                $duplicates += @{
                    similar_to = $pageNames[$baseName]
                    candidate = $file.FullName
                }
            } else {
                $pageNames[$baseName] = $file.FullName
            }
        }
        
        # Check index
        $indexPath = Join-Path $WIKI_TEMP "Research-to-Decision-Index.md"
        $indexExists = Test-Path $indexPath
        $indexAge = if ($indexExists) { ((Get-Date) - (Get-Item $indexPath).LastWriteTime).Days } else { -1 }
        
        # Build results
        $result.status = "success"
        $result.wiki_state = @{
            total_pages = $total
            organized_pages = $organized
            unorganized_pages = $unorganized
        }
        
        if ($unorganized -gt 0) {
            $result.issues_detected += @{
                issue_type = "uncategorized_pages"
                severity = "MEDIUM"
                count = $unorganized
                recommendation = "Move pages to standard folders (Personas/, Journey-Maps/, etc.)"
            }
        }
        
        if ($naming_issues.Count -gt 0) {
            $result.issues_detected += @{
                issue_type = "naming_inconsistency"
                severity = "LOW"
                pages = $naming_issues[0..2]  # Show first 3
                recommendation = "Use Kebab-Case naming: 'Field-Manager' not 'FieldManager' or 'Field_Manager'"
            }
        }
        
        if ($duplicates.Count -gt 0) {
            $result.issues_detected += @{
                issue_type = "potential_duplicates"
                severity = "HIGH"
                count = $duplicates.Count
                recommendation = "Manual review - are these pages about the same topic?"
            }
        }
        
        $result.index_status = @{
            exists = $indexExists
            age_days = $indexAge
            current = $indexAge -le 1
            recommendation = if ($indexAge -gt 3) { "Index is stale - update recommended" } else { "Index is current" }
        }
    }
    catch {
        Write-Log "Audit failed: $_" "ERROR"
        $result.status = "error"
    }
    finally {
        Cleanup-WikiTemp
    }
    
    return $result | ConvertTo-Json -Depth 5
}

# ============================================================================
# Main Execution
# ============================================================================

Write-Log "Wiki Manager (Librarian) - Action: $action"

try {
    switch ($action) {
        "search" { Handle-Search }
        "write-page" { Handle-WritePage }
        "update-index" { Handle-UpdateIndex }
        "audit-and-organize" { Handle-AuditAndOrganize }
        default {
            @{ 
                status = "error"
                message = "Unknown action: $action"
                valid_actions = @("search", "write-page", "update-index", "audit-and-organize")
            } | ConvertTo-Json
        }
    }
}
catch {
    Write-Log "Execution failed: $_" "ERROR"
    @{
        status = "error"
        message = "Execution failed: $_"
        action = $action
    } | ConvertTo-Json
}
```

---

## Agent Integration Patterns

### From PM Agent (Before Creating Research)

```markdown
## Step 1: Search for Existing Research

CALL SKILL: wiki-manager
- action: search
- repo: owner/repo
- query: "Field Manager"

RECEIVE:
- total_found: 2
- results[0]: Personas/Field-Manager (score: 0.98)
- results[1]: Journey-Maps/Field-Manager-Checkout (score: 0.72)

## Step 2: Agent Decides

IF results[0].match_score > 0.95:
  → High confidence match
  → Comment: "Research already exists: Personas/Field-Manager"
  → Close pm-idea: "duplicate_research_exists"
ELSE IF results[0].match_score > 0.70:
  → Moderate confidence
  → Comment: "Found potentially related research, needs review"
  → Create research-issue anyway
ELSE:
  → No relevant results
  → Create research-issue
```

### From Research Agent (Execute Research)

```markdown
## Step 0: Check if Already Done

CALL SKILL: wiki-manager
- action: search
- repo: owner/repo
- query: "Field Manager"

IF search returns complete research:
  → Comment: "Using existing research"
  → Close issue: "already_researched"
  → Exit (no duplicate work!)

## Step N: Research Complete

[Agent has finished research and written findings]

## Step N+1: Write to Wiki

CALL SKILL: wiki-manager
- action: write-page
- repo: owner/repo
- page_path: "Personas/Field-Manager"  ← Agent decides folder
- content: "[Markdown findings]"

RECEIVE:
- success
- wiki_url

## Step N+2: Register in Index

CALL SKILL: wiki-manager
- action: update-index
- repo: owner/repo
- subject: "Field Manager"
- status: "Complete"
- wiki_page: "Personas/Field-Manager"
- github_issue: "#1025"
- confidence: "HIGH"
- findings_summary: "10 interviews completed..."

RECEIVE:
- success
- index_entry_added: true
```

### Periodic Housekeeping (Orchestrator)

```markdown
## Weekly Maintenance

CALL SKILL: wiki-manager
- action: audit-and-organize
- repo: owner/repo
- dry_run: true

RECEIVE:
- issues_detected: [list of problems]
- index_status: stale? current?

IF issues found:
  → Post summary to team
  → Link to specific pages needing attention
  → Do NOT auto-merge (agents handle manually)
```

---

## Benefits of Librarian Model

✅ **Transparent** — Each action explicit, agent controls flow  
✅ **Simple** — 4 actions, no magic or auto-decisions  
✅ **Debuggable** — Failures traceable to agent logic or skill  
✅ **Flexible** — Agents can batch, defer, or override  
✅ **Safe** — No auto-write, no auto-reorganization  
✅ **Testable** — Each action independent  
✅ **Clear Responsibility** — Agent = logic, Skill = storage

---

## Comparison: Smart Skill vs Librarian Model

| Aspect | Smart Skill | Librarian |
|--------|------------|-----------|
| **find-or-create** | 1 action, does everything | Split: search + agent decision |
| **Auto-classification** | Skill classifies content | Agent specifies folder |
| **Auto-organization** | Skill auto-moves files | Audit flags issues, agent reviews |
| **Index updates** | Skill auto-registers | Agent explicitly calls update-index |
| **Actions** | 3 complex | 4 simple |
| **Control** | Skill decides | Agent decides |
| **Traceability** | Implicit (skill logic) | Explicit (agent code) |
| **Error Handling** | Skill catches errors | Agent implements retry logic |
| **Flexibility** | Fixed workflow | Agent-driven workflow |

