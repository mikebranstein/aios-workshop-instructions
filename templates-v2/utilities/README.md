# Utilities Folder

**Callable tools and utilities that agents execute.**

Unlike contracts (which are read-only reference documents), utilities are executable tools that agents can call to perform complex operations. Utilities return structured results that agents use to proceed with their logic.

## Current Utilities

### wiki-manager.md
An autonomous expert librarian utility that manages the GitHub wiki repository. Agents call this utility to store and retrieve research artifacts.

### fitness-evaluator.md
Deterministic architecture fitness-function utility. Evaluates predefined checks and emits structured findings (`PASS|WARN|FAIL_CRITICAL`) for architecture-review processing.

### architecture-debt-manager.md
Deterministic debt upsert utility. Creates or updates architecture-debt issues from fitness and architecture review findings using dedupe fingerprints.

**How agents use utilities:**
```bash
Agent calls: Call the utility with specific action and parameters
Utility executes: Performs the operation (clone, commit, push, reorganize)
Utility returns: Structured result with status and outcome
Agent uses: The returned result to continue processing
```

**Key difference from contracts:**
- Contracts: Agents read them (reference documents)
- Utilities: Agents call them (executable tools)

**Organization principle:**
Utilities are separated from contracts because they have executable side effects (git operations, file I/O, API calls) and return structured results that agents depend on.
