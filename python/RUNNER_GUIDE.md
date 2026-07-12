# Running Orchestrators Against External Repositories

The AIOS orchestration system can be run from this location (`python/`) against any GitHub repository in **two modes**:

## Execution Modes

### 1. **Continuous Mode** (Default)
Continuously processes all matching issues until the queue is empty.

```powershell
python pm_runner.py owner/my-repo --continuous
python po_runner.py owner/my-repo --continuous
python dev_runner.py owner/my-repo --continuous
```

**PM Continuous** finds all `pm:queued` issues and processes them one by one until none remain.
**PO Continuous** finds all `po:queued` issues and processes them through prioritization.
**Dev Continuous** finds all `dev:intake` issues and processes them through the full development pipeline.

### 2. **Single-Issue Mode**
Process one specific issue through its orchestrator loop.

```powershell
python pm_runner.py owner/my-repo 42
python po_runner.py owner/my-repo 42
python dev_runner.py owner/my-repo 42
```

---

## Architecture

### Why Two Modes?

Per the Module 13 design, orchestrators run **continuously** until no more work exists:

- **PM Orchestrator (continuous)**: Finds all `pm:queued` strategic opportunities, validates them, conducts research, makes CHAMPION/DEFER/BLOCK decisions, then moves to next opportunity
- **PO Orchestrator (continuous)**: Finds all `po:queued` opportunities, prioritizes them, creates feature-request issues for development
- **Dev Orchestrator (continuous)**: Finds all `dev:intake` feature requests, executes the full 8-stage pipeline, ships to production
- **Exceptions**: Foundation and Discovery orchestrators run once (single-issue only) per design

### Continuous Execution Flow

```
PM Continuous Loop
├─ Find pm:queued issues
├─ Process issue #1 → #2 → #3 → ... (sequential FIFO)
└─ Exit when no pm:queued remain

        ↓ (async handoff)

PO Continuous Loop  
├─ Find po:queued issues
├─ Process issue #1 → #2 → #3 → ... (sequential FIFO)
└─ Exit when no po:queued remain

        ↓ (async handoff)

Dev Continuous Loop
├─ Find dev:intake issues
├─ Process issue #1 → #2 → #3 → ... (sequential FIFO)
└─ Exit when no dev:intake remain
```

## Quick Start

### Prerequisites

1. **GitHub CLI** (`gh`) installed and authenticated:
   ```powershell
   gh auth login
   ```

2. **Python 3.9+** with orchestrator code available (this directory)

### Continuous Mode (Recommended)

Process **all** pm:queued issues until the queue is empty:

```powershell
# PM orchestrator - process all strategic opportunities
python pm_runner.py owner/my-repo --continuous

# After PM completes, PO processes all opportunities
python po_runner.py owner/my-repo --continuous

# After PO completes, Dev processes all features
python dev_runner.py owner/my-repo --continuous
```

### Single-Issue Mode

Process **one specific** issue:

```powershell
python pm_runner.py owner/my-repo 42
python po_runner.py owner/my-repo 42
python dev_runner.py owner/my-repo 42
```

### Environment Variables

```powershell
$env:AIOS_TARGET_REPO = "owner/my-repo"

# Now you can omit the repo:
python pm_runner.py --continuous
python pm_runner.py 42
```

## Architecture

### Repository Context Detection

The `RepoContext` class automatically detects the target repository type:

```python
from aios_orchestration_core.repo_context import RepoContext

# GitHub: detected by "owner/repo" format
context = RepoContext.from_string("owner/my-repo")
context.is_github  # True

# Local: detected by path format (coming soon)
context = RepoContext.from_string("./local/repo")
context.is_github  # False
```

### Gateway Factory

Once context is established, create the appropriate gateway:

```python
context = RepoContext.from_env(default="owner/my-repo")
gateway = context.create_pm_gateway()
# Now returns GitHubApiPMGateway (uses gh CLI for real GitHub interaction)
```

### Continuous Orchestrator Architecture

Each continuous orchestrator (`PMContinuousOrchestrator`, `POContinuousOrchestrator`, `DevContinuousOrchestrator`) wraps the single-issue orchestrator in a loop:

```python
while True:
    # Find next matching issue (pm:queued, po:queued, or dev:intake)
    issues = gateway.list_open_issues_with_any_label([matching_label])
    
    if not issues:
        break  # Exit loop when no more work
    
    # Process first issue (FIFO)
    issue = issues[0]
    orchestrator = RunOnceOrchestrator(...)
    result = orchestrator.run_once(issue.number)
    
    # Log result and continue to next issue
```

**Key properties:**
- **FIFO ordering**: Issues processed in order (by number)
- **Fault tolerance**: Errors in one issue don't stop the loop (logged and skipped)
- **Atomic transitions**: Each issue completes fully before moving to next
- **Separate runlogs**: Each continuous run gets its own SQLite database (`pm_continuous.sqlite`, etc.)

## Examples

### Example 1: Continuous PM Validation Loop

Process all strategic opportunities in order:

```powershell
python pm_runner.py acme-corp/product-ideas --continuous
```

Output:
```
Running PM orchestrator in CONTINUOUS mode...
  Processing all pm:queued issues until none remain
2026-07-13 14:22:15 [INFO] Processing pm:queued issue #15: "Implement dark mode"
✓ Issue #15 completed with state: PM_OUTPUT_PUBLISHED
2026-07-13 14:22:45 [INFO] Processing pm:queued issue #23: "Add API rate limiting"
✓ Issue #23 completed with state: PM_OUTPUT_PUBLISHED
2026-07-13 14:23:00 [INFO] No more pm:queued issues. Continuous loop complete.

============================================================
Continuous run complete:
  Issues processed: 2
  Runlog: ./pm_runs/pm_continuous.sqlite
============================================================
```

### Example 2: Process Entire PM-PO-Dev Pipeline

```powershell
# Phase 1: PM validates all strategic opportunities
python pm_runner.py acme-corp/repo --continuous

# Phase 2: PO prioritizes all validated opportunities
python po_runner.py acme-corp/repo --continuous

# Phase 3: Dev builds all prioritized features
python dev_runner.py acme-corp/repo --continuous
```

Each phase processes all matching issues until completion, then hands off to the next phase.

### Example 3: Single-Issue for Testing

Process one specific issue to validate behavior:

```powershell
python pm_runner.py acme-corp/product-ideas 123
```

Executes the PM loop on issue #123 only. After completion:
- Issue labels updated with PM state
- Comments posted with decisions
- Runlog saved to `./pm_runs/pm_issue_123.sqlite`

### Example 4: Dry-Run to Preview

```powershell
# Continuous mode
python pm_runner.py acme-corp/repo --continuous --dry-run

# Output:
# [DRY RUN] Would run PM orchestrator:
#   Repo: GitHub: acme-corp/repo
#   Mode: continuous
#   Log directory: ./pm_runs

# Single issue
python pm_runner.py acme-corp/repo 42 --dry-run

# Output:
# [DRY RUN] Would run PM orchestrator:
#   Repo: GitHub: acme-corp/repo
#   Mode: single
#   Issue: 42
#   Log directory: ./pm_runs
```

### Example 5: Custom LLM and Retry Settings

```powershell
python pm_runner.py acme-corp/repo --continuous \
  --model gpt-4-turbo \
  --max-retries 5 \
  --log-dir ./production_logs
```

## Adapters & LLM Integration

The `pm_runner.py` script uses `StubLLMAdapter` by default, which returns hardcoded responses without invoking a real LLM. This is suitable for:

- **Testing** — Validate orchestration logic without LLM calls
- **Dry runs** — Understand orchestrator behavior
- **Debugging** — Trace execution without API costs

### Replace with Real Adapter

Use the factory helper so the runtime can fail closed when SDK setup is missing:

```python
from aios_orchestration_core.llm.adapter_factory import create_adapter

adapter = create_adapter(model=args.model, use_stub=False)
```

If you need stub behavior for local-only testing, enable it explicitly:

```python
adapter = create_adapter(model=args.model, use_stub=True, stub_class=StubLLMAdapter)
```

### Live Tool-Call Conformance Check

Validate schema-conformant tool payloads across all task types with the real Copilot SDK path:

```powershell
cd python
$env:PYTHONPATH='.'
python scripts/copilot_task_conformance.py --trials 1
```

Target a single task during triage:

```powershell
python scripts/copilot_task_conformance.py --trials 3 --task pm_phase1
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AIOS_TARGET_REPO` | (required) | Target GitHub repo in `owner/repo` format |
| `AIOS_PM_LOG_DIR` | `./pm_runs` | Directory for runlog SQLite databases |
| `AIOS_LLM_MODEL` | `gpt-4` | LLM model hint passed to adapters |

## Troubleshooting

### "gh" command not found

Install GitHub CLI: https://cli.github.com/

### "Repository not found" or authentication error

Verify:
1. You're authenticated: `gh auth status`
2. Repo exists: `gh repo view owner/repo`
3. You have access to the repo

### Issue not found

```powershell
# List open issues in target repo
gh -R owner/repo issue list --state open
```

### Permission denied when writing labels/comments

Ensure your GitHub token has `issues:write` and `pull_requests:write` scopes:

```powershell
gh auth refresh --scopes issues:write,pull_requests:write,repo
```

## Future: Local Repository Support

Currently, only GitHub repositories are supported. Future enhancements will add:

- **Local git repos** — Run against locally cloned repos without GitHub interaction
- **Gitea/Forgejo** — Support for self-hosted Git platforms
- **GitLab** — GitLab issue integration

These will follow the same pattern:

```python
# Coming soon:
context = RepoContext.from_string("./path/to/local/repo")
gateway = context.create_pm_gateway()  # LocalFileGateway or similar
```

## Testing

### Run All Tests

```powershell
cd python
python -m pytest tests/ -q
```

### Run Integration Tests Against Real GitHub

```powershell
$env:RUN_GITHUB_DISPOSABLE_TESTS = 1
python -m pytest tests/pm/test_github_api_gateway_disposable.py -v
```

## Architecture Decision: Why This Approach?

1. **Centralized code** — Single source of truth for orchestrator logic
2. **No duplication** — Don't copy/paste code into target repos
3. **Protocol-based gateways** — Gateway interface is identical whether in-memory or GitHub-backed
4. **Reproducibility** — Run same logic against different repos to validate behavior
5. **Audit trail** — Runlog stored locally, separate from GitHub history
