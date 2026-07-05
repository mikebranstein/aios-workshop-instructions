# Module 08 - Building the Local Agentic OS: The Orchestrator Pattern

## Concept: One orchestrator, many specialists

In Modules 6 and 7, you defined three skill contracts - intake, design, and build - as markdown files describing how decisions should be made. They have been documentation. This module makes them executable.

The shift is architectural. Instead of manually invoking a contract, you define it as a Copilot CLI agent: a specialized AI with a single role and a clear scope. Then you build an orchestrator - a persistent agent that watches GitHub for new work, checks each issue's current state, and dispatches the right specialist.

The result is a local agentic loop started with one command:

```
copilot --autopilot -p "Start the orchestrator..."

  orchestrator agent (continuous self-directed loop)
    1. read all open GitHub issues via MCP
    2. check labels on each issue
    3. spawn the right specialist agent:
         - no labels     -> intake agent
         - intake-approved -> design agent
         - design-approved -> build agent
    4. sleep 90 seconds
    5. go back to step 1
```

You run this on your own machine. Nothing is in the cloud. No GitHub Actions. The orchestrator is a local process that uses GitHub as its state store - reading labels to know where each issue is, writing comments as decision records, updating labels to advance state.

**What makes this an agentic OS:**

- **Labels are the state machine.** An issue with no label is new. `intake-approved` means design can start. `design-approved` means build can start. Any agent anywhere can read this state without needing memory or shared context.
- **The orchestrator drives itself.** It does not wait for an external scheduler. It finishes a cycle, sleeps, and starts the next one. You start it with one command and stop it with Ctrl+C.
- **The orchestrator is stateless.** Each cycle reads GitHub fresh. It does not remember the last run. Restart it any time and it picks up exactly where things left off.
- **Specialists are composable.** You add a new stage by writing one agent file and adding one routing rule to the orchestrator. The existing agents do not change.

**How you build it in this module:** Incrementally. You start with an orchestrator that only knows about intake. You run it, watch it process an issue, and verify the result. Then you extend it to design. Then build. At each step you have a working system.

---

## Time Box

- Target: 65 minutes

## Required tasks

1. Set up GitHub labels for the pipeline state machine.
2. Create the intake, design, and build agent files in `.github/agents/`.
3. Create the orchestrator agent (v1 - intake only) and start the loop.
4. Watch intake process a live GitHub issue.
5. Extend the orchestrator to design and verify.
6. Extend the orchestrator to build and run 2 issues through the full pipeline.

---

## Step 1 (5 minutes): Set up GitHub state labels

Labels are how your orchestrator reads state. Create these in your GitHub repository now so agents can apply them.

**Option A - GitHub CLI (faster):**

Run from your repo directory, or use the `-R` flag to specify the repo:

```bash
# Option 1: Run from inside your repo directory
cd /path/to/your/repo
gh label create "intake-approved"  --color "0075ca" --description "Intake contract passed"
gh label create "intake-blocked"   --color "e4e669" --description "Intake contract blocked"
gh label create "design-approved"  --color "0075ca" --description "Design contract passed"
gh label create "design-blocked"   --color "e4e669" --description "Design contract blocked"
gh label create "build-complete"   --color "0e8a16" --description "Build contract complete"
gh label create "build-blocked"    --color "e4e669" --description "Build contract blocked"

# Option 2: Specify the repo explicitly (run from anywhere)
gh label create "intake-approved"  --color "0075ca" --description "Intake contract passed" -R your-org/your-repo
gh label create "intake-blocked"   --color "e4e669" --description "Intake contract blocked" -R your-org/your-repo
gh label create "design-approved"  --color "0075ca" --description "Design contract passed" -R your-org/your-repo
gh label create "design-blocked"   --color "e4e669" --description "Design contract blocked" -R your-org/your-repo
gh label create "build-complete"   --color "0e8a16" --description "Build contract complete" -R your-org/your-repo
gh label create "build-blocked"    --color "e4e669" --description "Build contract blocked" -R your-org/your-repo
```

Replace `your-org/your-repo` with your actual GitHub repository path (e.g., `mike/aios-workshop`).

**Option B - GitHub UI:**

1. Go to your repository on GitHub.
2. Click the **Issues** tab, then click **Labels**.
3. Click **New label** for each of the following:

| Label name        | Color   | Hex code  | Description                   |
|-------------------|---------|-----------|-------------------------------|
| intake-approved   | Blue    | `#0075ca` | Intake contract passed        |
| intake-blocked    | Yellow  | `#e4e669` | Intake contract blocked       |
| design-approved   | Blue    | `#0075ca` | Design contract passed        |
| design-blocked    | Yellow  | `#e4e669` | Design contract blocked       |
| build-complete    | Green   | `#0e8a16` | Build contract complete       |
| build-blocked     | Yellow  | `#e4e669` | Build contract blocked        |

For each label: type the name, paste the hex code into the color field, add the description, then click **Create label**.

These six labels represent the full pipeline state space. An issue moves through them in order. A blocked label means it needs human attention before the orchestrator will touch it again.

---

## Step 2 (15 minutes): Create the specialist agent files and skill contracts

Copilot CLI loads custom agents from `.github/agents/`. Each file is a markdown document with a YAML frontmatter block. The `description` field tells the orchestrator what this agent does when it decides to spawn it.

Each agent wraps a skill contract (intake, design, build). These contracts define the decision rules each agent applies. You need to copy both the agents and the skill templates into your repo so the agents can reference them locally.

Create the directories and copy both agent and skill templates:

```bash
mkdir -p .github/agents
mkdir -p templates/skills

# Copy agent files
cp templates/agents/intake.agent.md .github/agents/
cp templates/agents/design.agent.md .github/agents/
cp templates/agents/build.agent.md .github/agents/
cp templates/agents/orchestrator.v1.agent.md .github/agents/orchestrator.agent.md

# Copy skill contract files (agents reference these)
cp templates/skills/intake-agent.md templates/skills/
cp templates/skills/design-agent.md templates/skills/
cp templates/skills/build-agent.md templates/skills/
```

This creates the directory structure in your repo:

```
.github/agents/
  intake.agent.md
  design.agent.md
  build.agent.md
  orchestrator.agent.md

templates/skills/
  intake-agent.md     (referenced by intake.agent.md)
  design-agent.md     (referenced by design.agent.md)
  build-agent.md      (referenced by build.agent.md)
```

Each agent file is a specialist. The agent reads its corresponding skill contract (e.g., intake.agent.md reads templates/skills/intake-agent.md), applies the contract rules to the issue, and posts a JSON decision comment with the result.

**Checkpoint:** Before continuing, confirm your `.github/agents/` directory has four files:
- `intake.agent.md`
- `design.agent.md`
- `build.agent.md`
- `orchestrator.agent.md`

---

## Step 3 (15 minutes): Launch the orchestrator v1 and watch intake run

### Prerequisites

Confirm these tools are installed and authenticated:

```bash
gh auth status       # GitHub CLI - must be authenticated
copilot login        # Copilot CLI - authenticate if not already done
```

### Launch the orchestrator

Open a terminal in your repository root and run:

```bash
copilot --autopilot --allow-all-tools --enable-all-github-mcp-tools \
  -p "Start the agentic OS orchestrator. Run continuously. Do not stop until I tell you to."
```

Flag meanings:
- `--autopilot` keeps Copilot running without requiring confirmation between steps
- `--allow-all-tools` lets agents run shell commands and use tools without prompting each time
- `--enable-all-github-mcp-tools` unlocks the full GitHub MCP toolset (label writes, comment writes)
- `-p` passes the initial prompt that tells the orchestrator to begin its self-directed loop

The orchestrator will start immediately. You will see it list open issues, process any qualifying ones, print a cycle summary, then sleep 90 seconds before starting the next cycle.

**What you just did:** You started a persistent local agent process. It drives itself. You do not issue any more commands. When you want to stop it, press Ctrl+C.

### Create a test issue

In a browser or second terminal, create a GitHub issue using the `.github/ISSUE_TEMPLATE/feature_request.md` template from Module 2. The intake agent evaluates against the contract in `templates/skills/intake-agent.md`, which requires all template fields to be present.

Use this fully-formed example for the Team Equipment Checkout Tracker:

```markdown
Title: Prevent double checkout of the same item

## Problem Statement
An operations coordinator can check out an item that is already checked out
by someone else. The app does not validate item availability before recording
the checkout, so two people can hold the same device simultaneously.

## Scope
Add an availability check to the checkout flow. Show a clear error when an
item is already checked out. Display current holder name in the error message.

## Non-Goals
- No notifications or emails to the current holder
- No queue or reservation system
- No changes to the return flow

## Acceptance Criteria
- [ ] PASS: Checking out an available item succeeds normally
- [ ] FAIL: Checking out an already-checked-out item shows a validation error
- [ ] PASS: Error message names the item and the current holder
- [ ] PASS: Existing checkouts are unaffected by this change

## Test Scenarios
- Scenario 1 (happy path): Coordinator checks out available laptop - checkout succeeds
- Scenario 2 (failure path): Coordinator tries to check out laptop held by someone - error shown

## Risk Level
Low - adds a check to existing flow, no schema changes, no external dependencies

## Dependencies
None

## Notes
Coordinators are accidentally creating duplicate checkout records for the same device.
```

**Also try this:** Create a second issue that is deliberately incomplete - skip Risk Level and Non-Goals. Watch the intake agent return BLOCKED and list the missing fields. That is the gate working exactly as designed.

### Watch the first cycle

Within 90 seconds, the orchestrator's next cycle will pick up your new issue. You should see:
- Copilot reading open issues via the GitHub MCP `list_issues` tool
- The orchestrator routing your new issue (no labels) to the intake agent
- A `task` spawned with `agent_id="intake"`
- The intake agent reading the issue, evaluating against `templates/skills/intake-agent.md`
- A comment posted on your GitHub issue with the intake JSON decision
- The `intake-approved` or `intake-blocked` label applied automatically

Go look at your GitHub issue. You should see an Intake Decision comment with the contract JSON output and a label applied - with no manual prompting from you.

**Micro-check:** If intake returns BLOCKED, read the `missing_fields` array in the JSON. Fix the issue body and wait for the next cycle. The orchestrator will retry it once the blocking label is cleared.

---

## Step 4 (10 minutes): Extend the orchestrator to design

The orchestrator reads its agent file at the start of each cycle. To add a new stage, update the file. The change takes effect on the next cycle. No restart required.

### Update `.github/agents/orchestrator.agent.md`

Copy the v2 template to replace your v1 orchestrator:

```bash
cp templates/agents/orchestrator.v2.agent.md .github/agents/orchestrator.agent.md
```

This expands the routing table to include design: issues with `intake-approved` (and no design label yet) will now be routed to the design agent on the next cycle.

### Watch the next cycle

On the next 90-second cycle, the orchestrator will:
- See your issue now has `intake-approved`
- Match the second routing row
- Spawn the design agent
- The design agent reads the issue and the intake decision comment
- Posts a Design Decision comment with the design contract JSON output
- Applies `design-approved` or `design-blocked`

Check your GitHub issue again. It should now have both an Intake Decision comment and a Design Decision comment, with two labels applied.

---

## Step 5 (15 minutes): Extend the orchestrator to build - run two issues through

### Update `.github/agents/orchestrator.agent.md`

Copy the v3 template to add the build stage:

```bash
cp templates/agents/orchestrator.v3.agent.md .github/agents/orchestrator.agent.md
```

This adds the final routing rule: issues with both `intake-approved` and `design-approved` will now be routed to the build agent on the next cycle.

### Create a second issue and watch the full pipeline

Create one more issue using the template. Use a different feature scope:

```markdown
Title: Show checkout history for each item

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
- Scenario 1 (happy path): Item with two prior checkouts - history shows both in order
- Scenario 2 (empty state): Item never checked out - "No checkout history" message shown

## Risk Level
Low - read-only view, no changes to data model

## Dependencies
None

## Notes
Coordinators need audit capability for equipment disputes.
```

Now watch the orchestrator run this issue through all three stages automatically across two or three cycles.

---

## Step 6 (5 minutes): Verify the full system

Go to your GitHub repository and look at the issues list. You should see:

- **Labels** showing exactly where each issue is in the pipeline
- **Comments** on each issue with the JSON decision from each contract
- **Two or more issues** that moved from no label through all three stages without any manual work

This is your agentic OS running. One command started it. The orchestrator reads state, routes work, and writes results. You did not touch it once the loop started.

**What to notice:**
- Each issue's label trail is the pipeline state - readable at a glance from the issues list
- Each issue's comment trail is the decision record - auditable and traceable
- The orchestrator processed each issue across multiple cycles, not all at once
- Issues that returned BLOCKED were correctly skipped until you intervene

---

## Micro checks

- Minute 5: Six pipeline labels created in GitHub.
- Minute 20: Four agent files created in `.github/agents/`.
- Minute 35: Orchestrator started, first issue processed by intake agent.
- Minute 45: Orchestrator extended to design, second cycle shows intake then design.
- Minute 60: Full pipeline running, two issues with `build-complete` label and three decision comments each.

## You should see

- `.github/agents/` contains four agent files
- Two or more GitHub issues have all three pipeline labels set
- Each issue has three comments (Intake Decision, Design Decision, Build Decision) with JSON from the contracts
- The Copilot CLI autopilot session is still running in the terminal
- No manual prompting was required after the initial launch command

## What you learned

- **Agents vs skills:** A skill is a prompt module. An agent is a specialized actor with a role, tools, and a scope. The same contract content works in both, but agents can be spawned by an orchestrator using the `task` tool.
- **Labels as state machine:** Labels let any agent read current state without memory. The orchestrator does not track history - it reads GitHub fresh on every cycle.
- **Incremental orchestration:** You built v1 (intake only), verified it, added v2 (design), verified it, added v3 (full pipeline). Each version was a working system.
- **The autopilot loop:** Copilot CLI with `--autopilot` is a persistent self-directed agent process. No external scheduler, no GitHub Actions, no cloud services. One command starts it; the agent drives itself from there.

## If something fails

- **Orchestrator stops unexpectedly:** Check that the agent file does NOT call `task_complete`. The loop must not terminate itself. If it stopped, relaunch with the same command.
- **Agent file not loading:** Run `/env` in the Copilot CLI session to see which agents are loaded. If your agent does not appear, check the file is in `.github/agents/` and has valid YAML frontmatter with a `description` field.
- **Contract returns BLOCKED unexpectedly:** Check the `missing_fields` array in the JSON comment. The issue body is likely missing one of the required fields from `templates/skills/intake-agent.md`.
- **Labels not being applied:** Verify `gh auth status` shows the repo is accessible. The agent uses shell commands to apply labels, so `gh` must be authenticated.

## Definition of done

- Four agent files exist in `.github/agents/` and load correctly
- Orchestrator has been extended through all three stages (v1 to v2 to v3)
- Two or more GitHub issues have traversed intake, design, and build automatically
- Each issue has a comment trail with JSON contract decisions at each stage
- The pipeline state is readable from GitHub labels alone, without opening any comments
- You understand how to add a fourth stage by writing one agent file and updating the routing table

## Next module

Module 9 extends the orchestrator with project state tracking - GitHub Projects fields that let you query "show me all issues currently in design" or "how many issues are blocked this week." The orchestrator you built here is the foundation; the next module makes its state visible at scale.
