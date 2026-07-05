# Module 08 - Building the Local Agentic OS: The Orchestrator Pattern

## Concept: One orchestrator, many specialists

In Modules 6 and 7, you defined three skill contracts�intake, design, and build�as markdown files describing how decisions should be made. They have been documentation. This module makes them executable.

The shift is architectural. Instead of manually invoking a contract, you define it as a **Copilot CLI agent**: a specialized AI with a single role and a clear scope. Then you build an **orchestrator**�a persistent agent that watches GitHub for new work, checks each issue's current state, and dispatches the right specialist.

The result is a local agentic loop:

```
copilot --autopilot (one command, runs until you stop it)
    └─ orchestrator agent (self-directed continuous loop)
            ├─ reads open GitHub issues
            ├─ checks labels to determine pipeline stage
            ├─ spawns specialist agents as needed
            │       ├─ intake agent → posts decision → sets label
            │       ├─ design agent → posts decision → sets label
            │       └─ build agent → posts decision → sets label
            └─ sleeps 90 seconds → starts next cycle
```

You run this on your own machine. Nothing is in the cloud. No GitHub Actions. The orchestrator is a local process that knows how to use GitHub as its state store�reading labels to know where each issue is, writing comments as decision records, updating labels to advance state.

**What makes this an agentic OS:**
- **Labels are the state machine.** An issue with no label is new. `intake-approved` means design can start. `design-approved` means build can start. Any agent anywhere can read this state.
- **The orchestrator drives itself.** It does not wait for an external scheduler. It finishes a cycle, sleeps briefly, and starts the next one. You start it with one command and stop it with Ctrl+C.
- **The orchestrator is stateless.** Each cycle reads GitHub fresh. It does not remember the last run. Restart it any time and it picks up exactly where things are.
- **Specialists are composable.** You add a new stage by writing one agent file and adding one routing rule to the orchestrator. The existing agents do not change.

**How you build it in this module:** Incrementally. You start with an orchestrator that only knows about intake. You run it, watch it process an issue, and verify the result. Then you extend it to know about design. Then build. At each step, you have a working system � not a partial one.—not a partial one.

---

## Time Box

- Target: 65 minutes

## Required tasks

1. Set up GitHub labels for the pipeline state machine.
2. Create the intake, design, and build agent files in `.github/agents/`.
3. Create the orchestrator agent v1 (intake only) and start the loop.
4. Watch intake process a live GitHub issue.
5. Extend the orchestrator to design and verify.
6. Extend the orchestrator to build and run 2 issues through the full pipeline.

## Stretch tasks

- Add a `needs-human` label condition to the orchestrator for issues that stay BLOCKED across two cycles.
- Define a fourth agent (`verification.agent.md`) and extend the orchestrator to route `build-complete` issues to it.

---

## Step 1 (5 minutes): Set up GitHub state labels

Labels are how your orchestrator reads state. Create these in your GitHub repository now so the agents can apply them.

Run these commands from your repo directory:

```bash
gh label create "intake-approved"  --color "0075ca" --description "Intake contract passed"
gh label create "intake-blocked"   --color "e4e669" --description "Intake contract blocked - needs revision"
gh label create "design-approved"  --color "0075ca" --description "Design contract passed"
gh label create "design-blocked"   --color "e4e669" --description "Design contract blocked - needs revision"
gh label create "build-complete"   --color "0e8a16" --description "Build contract complete"
gh label create "build-blocked"    --color "e4e669" --description "Build contract blocked - needs revision"
```

These six labels represent the full pipeline state space. An issue moves through them in order. A blocked label means it needs human attention before the orchestrator will touch it again.

---

## Step 2 (15 minutes): Create the specialist agent files

Copilot CLI loads custom agents from `.github/agents/`. Each file is a markdown document with a YAML frontmatter block. The `description` field tells the orchestrator (and Copilot) what this agent does when it decides to spawn it.

Create the directory:

```bash
mkdir -p .github/agents
```

### Create `.github/agents/intake.agent.md`

This agent wraps your existing intake contract. It reads the issue, applies the contract, posts the decision, and sets the label.

```markdown
---
description: "Evaluates a GitHub issue using the intake contract. Posts the decision as a comment and applies intake-approved or intake-blocked label."
tools: ["*"]
---

You are the intake evaluator for the Team Equipment Checkout Tracker project.

Your contract is in `templates/skills/intake-agent.md`. Apply it strictly.

## Steps

You will be given an issue number. Do the following in order:

1. Read the issue using the GitHub MCP `issue_read` tool.
2. Evaluate the issue body against the contract in `templates/skills/intake-agent.md`.
3. Post the JSON decision output as a comment:
   ```
   gh issue comment <number> --body "## Intake Decision\n\`\`\`json\n<json output>\n\`\`\`"
   ```
4. Apply the label that matches the decision:
   - If READY: `gh issue label <number> --add intake-approved`
   - If BLOCKED: `gh issue label <number> --add intake-blocked`
5. Output a one-line summary: "Issue #<number>: intake <READY|BLOCKED> - <contract summary field>"
```

### Create `.github/agents/design.agent.md`

```markdown
---
description: "Evaluates the design for a GitHub issue using the design contract. Reads the intake decision comment, posts a design decision, and applies design-approved or design-blocked label."
tools: ["*"]
---

You are the design evaluator for the Team Equipment Checkout Tracker project.

Your contract is in `templates/skills/design-agent.md`. Apply it strictly.

## Steps

You will be given an issue number. Do the following in order:

1. Read the issue using the GitHub MCP `issue_read` tool.
2. Read the issue comments to find the intake decision:
   ```
   gh issue view <number> --comments --json comments
   ```
3. Extract the JSON from the Intake Decision comment and use it as context.
4. Evaluate the design using the contract in `templates/skills/design-agent.md`.
5. Post the JSON decision output as a comment:
   ```
   gh issue comment <number> --body "## Design Decision\n\`\`\`json\n<json output>\n\`\`\`"
   ```
6. Apply the label:
   - If PASS: `gh issue label <number> --add design-approved`
   - If BLOCKED: `gh issue label <number> --add design-blocked`
7. Output a one-line summary: "Issue #<number>: design <PASS|BLOCKED> - <contract summary field>"
```

### Create `.github/agents/build.agent.md`

```markdown
---
description: "Evaluates build scope for a GitHub issue using the build contract. Reads the design decision comment, posts a build decision, and applies build-complete or build-blocked label."
tools: ["*"]
---

You are the build evaluator for the Team Equipment Checkout Tracker project.

Your contract is in `templates/skills/build-agent.md`. Apply it strictly.

## Steps

You will be given an issue number. Do the following in order:

1. Read the issue using the GitHub MCP `issue_read` tool.
2. Read the issue comments to find the design decision:
   ```
   gh issue view <number> --comments --json comments
   ```
3. Extract the JSON from the Design Decision comment and use it as context.
4. Evaluate the build scope using the contract in `templates/skills/build-agent.md`.
5. Post the JSON decision output as a comment:
   ```
   gh issue comment <number> --body "## Build Decision\n\`\`\`json\n<json output>\n\`\`\`"
   ```
6. Apply the label:
   - If COMPLETE: `gh issue label <number> --add build-complete`
   - If PARTIAL or BLOCKED: `gh issue label <number> --add build-blocked`
7. Output a one-line summary: "Issue #<number>: build <COMPLETE|BLOCKED> - <contract summary field>"
```

### Create `.github/agents/orchestrator.agent.md` (v1 — intake only)

Start with one stage. You will extend this in Steps 4 and 5.

Notice the structure: this agent runs a continuous loop. It does not call `task_complete`. It checks GitHub, routes issues, then sleeps and checks again. This is the autopilot pattern — one command starts it and it drives itself.

```markdown
---
description: "Agentic OS orchestrator. Continuously monitors GitHub issues and advances each one through the workflow pipeline. Runs in a self-directed loop."
tools: ["*"]
---

You are the agentic OS orchestrator for the Team Equipment Checkout Tracker project.

You run in a continuous self-directed loop. Do not call task_complete. Keep running until the user stops you with Ctrl+C.

## Loop structure

1. Run one cycle (see below)
2. Output a brief cycle summary
3. Wait 90 seconds: run the shell command `sleep 90`
4. Go back to step 1

## Cycle: pipeline routing (v1 — intake only)

For each open GitHub issue:

| Current labels on issue      | Action                                                                 |
|-----------------------------|------------------------------------------------------------------------|
| No pipeline labels          | Spawn intake agent: `task(description="Run intake on issue #<n>", agent_id="intake")` |
| `intake-approved`           | No action. Design routing coming in next version.                     |
| `intake-blocked`            | Skip. Needs human revision before pipeline can continue.              |
| `build-complete`            | Skip. Issue is done.                                                  |

## Cycle steps

1. List all open issues using the `list_issues` GitHub MCP tool.
2. For each issue, read its labels.
3. Route each issue using the table above.
4. Wait for each spawned task to complete before spawning the next.
5. Output a brief cycle summary: issues checked, issues advanced, issues skipped and why.
6. Sleep 90 seconds, then start a new cycle.
```

**Checkpoint:** Before continuing, verify your `.github/agents/` directory has four files: `intake.agent.md`, `design.agent.md`, `build.agent.md`, `orchestrator.agent.md`.

---

## Step 3 (15 minutes): Start the orchestrator loop v1 and watch intake run

### Launch the orchestrator

Open a terminal in your repository root and start the orchestrator with a single command:

```bash
copilot --autopilot --allow-all-tools --enable-all-github-mcp-tools \
  -p "Start the agentic OS orchestrator. Run continuously. Do not stop until I tell you to."
```

- `--autopilot` keeps Copilot running without requiring confirmation between steps
- `--allow-all-tools` lets agents run shell commands and use tools without prompting each time
- `--enable-all-github-mcp-tools` unlocks the full GitHub MCP toolset (label writes, comment writes)
- `-p` passes the initial prompt — it tells the orchestrator to begin its self-directed loop

The orchestrator will start immediately. You will see it list open issues, process any qualifying ones, print a cycle summary, then sleep 90 seconds before starting the next cycle.

**What you just did:** You started a persistent local agent process. It drives itself. You do not issue any more commands. When you want to stop it, press Ctrl+C.

### Create a test issue

In a browser or second terminal, create a GitHub issue using the Module 2 feature request template. Use the full template structure — Problem Statement, Scope, Non-Goals, Acceptance Criteria, Test Scenarios, Risk Level, Dependencies.

Use this example issue for the Team Equipment Checkout Tracker:

```markdown
**Title:** Prevent double checkout of the same item

## Problem Statement
An operations coordinator can check out an item that is already checked out
by someone else. The app does not validate item availability before recording
the checkout.

## Scope
Add availability check to checkout flow. Show validation error when item is
already checked out. Display current holder name in error message.

## Non-Goals
- No notifications to current holder
- No queue or reservation system
- No changes to return flow

## Acceptance Criteria
- [ ] PASS: Checking out an available item succeeds normally
- [ ] FAIL: Checking out an already-checked-out item shows a validation error
- [ ] PASS: Error message names the item and current holder
- [ ] PASS: Existing checkouts are unaffected

## Test Scenarios
- Scenario 1 (happy): Coordinator checks out available laptop — succeeds
- Scenario 2 (failure): Coordinator tries to check out laptop held by someone — error shown

## Risk Level
Low � adds a check to existing flow, no schema changes

## Dependencies
None

## Notes
Coordinators are accidentally creating duplicate checkout records.
```

### Watch the first cycle

Within seconds of creating the issue, the orchestrator's next cycle will pick it up. You should see:
- Copilot reading the open issues via GitHub MCP
- The orchestrator identifying your new issue has no pipeline labels
- A `task` spawned for the intake agent
- The intake agent reading your issue, evaluating against `templates/skills/intake-agent.md`
- A comment posted on your GitHub issue with the intake JSON decision
- The `intake-approved` or `intake-blocked` label applied

**Go look at your GitHub issue.** You should see an Intake Decision comment with the contract's JSON output and a label applied automatically.

**Micro-check:** If the intake returns BLOCKED, read the `missing_fields` in the JSON. Fix the issue body and wait for the next cycle — the orchestrator will retry it once the blocking label is cleared.

---

## Step 4 (10 minutes): Extend the orchestrator to design

The orchestrator reads its instructions from the agent file at the start of each cycle. To add a new stage, edit the file — the change takes effect on the next cycle. No restart required.

### Update `.github/agents/orchestrator.agent.md`

Replace the pipeline routing table with this expanded version:

```markdown
## Cycle: pipeline routing (v2 — intake + design)

For each open GitHub issue:

| Current labels on issue                     | Action                                                                    |
|--------------------------------------------|---------------------------------------------------------------------------|
| No pipeline labels                         | Spawn intake: `task(description="Run intake on issue #<n>", agent_id="intake")` |
| `intake-approved` only                     | Spawn design: `task(description="Run design on issue #<n>", agent_id="design")` |
| `intake-approved` + `design-approved`      | No action. Build routing coming in next version.                         |
| `intake-blocked`                           | Skip. Needs human revision.                                               |
| `design-blocked`                           | Skip. Needs human revision.                                               |
| `build-complete`                           | Skip. Done.                                                               |
```

Keep the loop structure and cycle steps the same. Only the routing table changes.

### Watch the next cycle

On the next 90-second cycle, the orchestrator will:
- See your issue now has `intake-approved`
- Match the second routing row
- Spawn the design agent
- The design agent reads the issue and the intake decision comment
- Posts a Design Decision comment with the design contract's JSON output
- Applies `design-approved` or `design-blocked`

**Check your GitHub issue again.** It should now have both an Intake Decision comment and a Design Decision comment, with two labels.

---

## Step 5 (15 minutes): Extend the orchestrator to build — run two issues through

### Update `.github/agents/orchestrator.agent.md`

Replace the pipeline routing table again with the full three-stage version:

```markdown
## Pipeline routing (v3 — full pipeline)

For each open GitHub issue:

| Current labels on issue                                    | Action                                                                    |
|-----------------------------------------------------------|---------------------------------------------------------------------------|
| No pipeline labels                                        | Spawn intake: `task(description="Run intake on issue #<n>", agent_id="intake")` |
| `intake-approved` only                                    | Spawn design: `task(description="Run design on issue #<n>", agent_id="design")` |
| `intake-approved` + `design-approved`                     | Spawn build: `task(description="Run build on issue #<n>", agent_id="build")` |
| Any `*-blocked` label                                     | Skip. Needs human revision before continuing.                             |
| `build-complete`                                          | Skip. Done.                                                               |
```

### Create a second issue and watch the full pipeline

Create one more GitHub issue using the template. Try a different feature scope:

```markdown
**Title:** Show checkout history for each item

## Problem Statement
There is no way to see the history of who has checked out a specific item.
Operations coordinators cannot audit past usage or investigate disputes.

## Scope
Add a checkout history view for a single item showing past checkouts in
reverse chronological order: date, holder name, return date.

## Non-Goals
- No export or report generation
- No filtering or search within history
- No changes to how checkouts are recorded

## Acceptance Criteria
- [ ] PASS: Selecting an item shows its checkout history
- [ ] PASS: History shows holder name, checkout date, return date
- [ ] PASS: Items with no history show an empty state message
- [ ] PASS: History is in reverse chronological order (newest first)

## Test Scenarios
- Scenario 1 (happy): Item with two prior checkouts — history shows both in order
- Scenario 2 (empty): Item never checked out — "No checkout history" message shown

## Risk Level
Low � read-only view, no changes to data model

## Dependencies
None

## Notes
Coordinators need audit capability for equipment disputes.
```

Now watch the orchestrator run this new issue through all three stages automatically across two or three cycles.

---

## Step 6 (5 minutes): Verify the full system

Go to your GitHub repository and look at the issues list. You should see:

- **Labels** showing exactly where each issue is in the pipeline
- **Comments** on each issue with the JSON decision from each contract
- **Two or three issues** that have moved from no label → intake-approved → design-approved → build-complete without any manual work

This is your agentic OS running. One command started it. The orchestrator reads state, routes work, and writes results. You did not touch it once the loop started.

**What to notice:**
- Each issue's label trail is the pipeline state — readable at a glance
- Each issue's comment trail is the decision record — auditable and traceable
- The orchestrator processed each issue across multiple cycles, not all at once
- Issues that returned BLOCKED were correctly skipped until you intervene

---

## Micro checks

- **Minute 5:** Six pipeline labels created in GitHub.
- **Minute 20:** Four agent files created in `.github/agents/`.
- **Minute 35:** Orchestrator started in autopilot, first issue processed by intake agent on first cycle.
- **Minute 45:** Orchestrator extended to design, second cycle shows intake → design.
- **Minute 60:** Full pipeline running, two issues with `build-complete` label and three decision comments each.

## You should see

- `.github/agents/` contains four agent files: `intake.agent.md`, `design.agent.md`, `build.agent.md`, `orchestrator.agent.md`
- Two or more GitHub issues have all three pipeline labels set
- Each issue has three comments (Intake Decision, Design Decision, Build Decision) with JSON from the contracts
- The Copilot CLI autopilot session is still running in the terminal
- No manual prompting was required after the initial launch command

## What you learned

- **Agents vs skills:** A skill is a prompt module. An agent is a specialized actor with a role, tools, and a scope. The same contract content works in both, but agents can be spawned by an orchestrator.
- **Labels as state machine:** Labels let any agent read current state without memory. The orchestrator does not track history — it reads GitHub.
- **Incremental orchestration:** You built v1 (intake only), verified it, added v2 (design), verified it, added v3 (full). Each version was a working system.
- **The autopilot loop:** Copilot CLI with `--autopilot` is a persistent self-directed agent process. No external scheduler, no GitHub Actions, no cloud services. One command starts it; it drives itself from there.

## If something fails, do this

- **Orchestrator does not find the issue:** Check that the issue is open (not closed) and has no pipeline labels. Verify `gh auth status` is authenticated.
- **Agent file not loading:** Run `/env` in the Copilot CLI session to see which agents are loaded. If your agent does not appear, check that the file is in `.github/agents/` and has valid YAML frontmatter with a `description` field.
- **Contract returns BLOCKED unexpectedly:** Check the `missing_fields` array in the JSON comment. The issue body is likely missing one of the required fields from `templates/skills/intake-agent.md`.
- **Labels not being applied:** Verify `gh auth status` shows the repo is accessible. The agent uses shell commands to apply labels, so `gh` must be authenticated.
- **Orchestrator stops unexpectedly:** Check that the agent file does not call `task_complete`. The loop must not terminate itself. If it stopped, relaunch with the same command.

## Definition of done

- Four agent files exist in `.github/agents/` and load correctly
- Orchestrator has been extended through all three stages (v1 ? v2 ? v3)
- Two or more GitHub issues have traversed intake ? design ? build automatically
- Each issue has a comment trail with JSON contract decisions at each stage
- The pipeline state is readable from GitHub labels alone, without opening any comments
- You understand how to add a fourth stage by editing one file

## Next module

Module 9 extends the orchestrator with **project state tracking** � GitHub Projects fields that let you query "show me all issues currently in design" or "how many issues are blocked this week." The orchestrator you built here is the foundation; the next module makes its state visible at scale.
