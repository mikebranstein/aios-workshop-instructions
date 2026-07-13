# Running All Orchestrators Against a Real GitHub Repository

This is the current operational guide for running every orchestrator from `python/`:

- `pm_runner.py`
- `po_runner.py`
- `dev_runner.py`
- `foundation_runner.py`
- `discovery_runner.py`
- `arch_review_runner.py`

---

## Prerequisites

1. GitHub CLI authenticated:

```powershell
gh auth status
```

2. Run from `python/`:

```powershell
cd python
$env:PYTHONPATH = (Get-Location).Path
```

3. Use a target repo in `owner/repo` format.

Optional convenience variable:

```powershell
$env:AIOS_TARGET_REPO = "owner/my-repo"
```

---

## Modes by Orchestrator

| Loop | Runner | Modes |
|---|---|---|
| PM | `pm_runner.py` | Continuous + single-issue |
| PO | `po_runner.py` | Continuous + single-issue |
| Dev | `dev_runner.py` | Continuous + single-issue |
| Foundation | `foundation_runner.py` | Run-once (resume/create) |
| Discovery | `discovery_runner.py` | Run-once generator |
| ArchReview | `arch_review_runner.py` | Run-once (resume/create) |

Continuous loops include startup adapter preflight and fail early if adapter initialization fails.

---

## Command Reference

### PM

```powershell
# Continuous (default when no issue number supplied)
python pm_runner.py owner/my-repo --continuous

# Single issue
python pm_runner.py owner/my-repo 42

# Single issue with repo from env var
python pm_runner.py 42
```

Queue label for continuous mode: `pm:queued`

PM-specific tuning flags:

```powershell
--max-retries <int>
--min-research <int>
--min-synthesis-conf <float>
```

### PO

```powershell
# Continuous (default when no issue number supplied)
python po_runner.py owner/my-repo --continuous

# Single issue
python po_runner.py owner/my-repo 42

# Single issue with repo from env var
python po_runner.py 42
```

Queue label for continuous mode: `po:queued`

### Dev

```powershell
# Continuous (default when no issue number supplied)
python dev_runner.py owner/my-repo --continuous

# Single issue
python dev_runner.py owner/my-repo 42

# Single issue with repo from env var
python dev_runner.py 42
```

Queue label for continuous mode: `dev:intake`

### Foundation

```powershell
# Process all actionable foundation issues (or create one if none exist)
python foundation_runner.py owner/my-repo

# Force creation of a fresh foundation issue in this run
python foundation_runner.py owner/my-repo --force
```

Resume label set:

- `foundation:needed`
- `foundation:in-progress`
- `foundation:review`
- `foundation:needs-human`

Processing priority: `foundation:review` → `foundation:in-progress` → `foundation:needs-human` → `foundation:needed`.

Approval gate requires both:
- LLM gate decision (`APPROVE_FOUNDATION`)
- objective evidence checks:
  - all linked foundation research issues are closed
  - issue body/comments contain wiki or ADR links
  - at least one ADR link exists

If no progress is detected for 3 consecutive cycles, the issue is moved to `foundation:needs-human` with explicit unblock steps.

### Discovery

```powershell
# Run discovery generator
python discovery_runner.py owner/my-repo

# Force rerun
python discovery_runner.py owner/my-repo --force
```

Discovery reads repository context from:

- foundation gate status (`foundation:approved` present)
- `docs/discovery-focus.md` (exists and populated)

When candidates are approved, discovery creates `pm-idea` issues.

### ArchReview

```powershell
# Resume open architecture-review issue, or create a new one if none exist
python arch_review_runner.py owner/my-repo

# Force fresh run
python arch_review_runner.py owner/my-repo --force
```

Resume label set:

- `arch:review-pending`
- `arch:review-in-progress`
- `arch:refactor-planned`

If nothing resumable exists, runner creates a new issue labeled `arch:review-pending`.

---

## Common Flags

All runners support:

```powershell
--model <model_name>   # default: auto
--stub                 # use stub adapter explicitly
--dry-run              # preview only, no execution
--log-dir <path>       # per-runner default directory
```

Default log directories:

- PM: `<temp>/aios-orchestrator-runlogs/pm`
- PO: `<temp>/aios-orchestrator-runlogs/po`
- Dev: `<temp>/aios-orchestrator-runlogs/dev`
- Foundation: `<temp>/aios-orchestrator-runlogs/foundation`
- Discovery: `<temp>/aios-orchestrator-runlogs/discovery`
- ArchReview: `<temp>/aios-orchestrator-runlogs/arch-review`

---

## Dry-Run Examples

```powershell
python pm_runner.py owner/my-repo --continuous --dry-run
python po_runner.py owner/my-repo 42 --dry-run
python dev_runner.py owner/my-repo --continuous --dry-run
python foundation_runner.py owner/my-repo --dry-run
python discovery_runner.py owner/my-repo --dry-run
python arch_review_runner.py owner/my-repo --dry-run
```

---

## Suggested Rollout Order (Live Testing)

1. Foundation
2. Discovery
3. PM
4. PO
5. Dev
6. ArchReview

For each loop:

1. `--dry-run`
2. `--stub` in non-critical repo
3. real adapter mode in staging repo
4. production repo rollout

---

## First Live Foundation Run Checklist

Use this before running Foundation against a real repository:

1. **Confirm auth and repo access**
   ```powershell
   gh auth status
   gh repo view owner/my-repo
   ```
2. **Preview execution**
   ```powershell
   python foundation_runner.py owner/my-repo --dry-run
   ```
3. **Optional stub safety pass**
   ```powershell
   python foundation_runner.py owner/my-repo --stub
   ```
4. **Run with real adapter**
   ```powershell
   python foundation_runner.py owner/my-repo
   ```
5. **Verify expected effects in GitHub**
   - a foundation issue is resumed or created
   - labels move through foundation states
   - comments are posted with transition details
6. **Verify local runlog artifact**
   - default: `<temp>/aios-orchestrator-runlogs/foundation/foundation_run.runlog.md`
7. **Recovery check**
   - rerun command once and confirm it resumes correctly (or cleanly finishes)

---

## Troubleshooting

### Repo/auth failures

```powershell
gh auth status
gh repo view owner/my-repo
```

### Continuous loops pick up no work

```powershell
gh -R owner/my-repo issue list --state open --label pm:queued
gh -R owner/my-repo issue list --state open --label po:queued
gh -R owner/my-repo issue list --state open --label dev:intake
```

### Discovery halts immediately

Verify both:

- at least one issue labeled `foundation:approved`
- `docs/discovery-focus.md` exists and is non-empty

### Exit codes

All runners use:

- `0` success
- `1` argument/config error
- `2` gateway/repo/auth setup error
- `3` orchestration runtime failure
