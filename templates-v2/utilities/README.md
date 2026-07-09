# Utilities Folder

**Callable tools and utilities that agents execute.**

Unlike contracts (which are read-only reference documents), utilities are executable tools that agents can call to perform complex operations. Utilities return structured results that agents use to proceed with their logic.

## Current Utilities

### wiki-manager.md
An autonomous expert librarian utility that manages the GitHub wiki repository. Agents call this utility to store and retrieve research artifacts.

### metrics-reporter.md
Metrics utility for agent and orchestrator telemetry. Supports continuous loops (PM/PO/Dev) and bounded runs (Discovery).

Common usage:
```bash
./utilities/metrics-reporter.md report \
	--agent-id "idea-scout" \
	--issue-number "123" \
	--decision "CREATE_PM_IDEA" \
	--confidence "0.87"

./utilities/metrics-reporter.md report-cycle \
	--orchestrator "discovery" \
	--cycle-number "18" \
	--duration-seconds "540" \
	--issues-processed "5" \
	--issues-completed "3" \
	--agents-spawned "1"
```

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
