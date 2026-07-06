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
    4. go back to step 1
```

You run this on your own machine. Nothing is in the cloud. No GitHub Actions. The orchestrator is a local process that uses GitHub as its state store - reading labels to know where each issue is, writing comments as decision records, updating labels to advance state.

**What makes this an agentic OS:**

- **Depth-first routing:** Unlike batch systems that process all issues through intake, then all through design, then all through build, this orchestrator takes a **depth-first approach**. On each cycle:

1. Find the FIRST issue that hasn't been completed or blocked
2. Advance it ONE step through the pipeline (intake → design → build)
3. On the next cycle, find the next issue needing work
4. Repeat

This means Feature 1 flows through intake, then design, then build before Feature 2 even starts intake. Each feature gets a complete workflow before the next one begins. This creates a focused, sequential delivery model rather than spread-out batch processing.
**Depth-first workflow:** Each issue is advanced one stage per cycle, then the next issue is checked. This ensures Feature 1 completes intake → design → build before Feature 2 starts, creating a focused sequential delivery model.
- **The orchestrator drives itself.** It does not wait for an external scheduler. It finishes a cycle and starts the next one immediately. You start it with one command and stop it with Ctrl+C.
- **The orchestrator is stateless.** Each cycle reads GitHub fresh. It does not remember the last run. Restart it any time and it picks up exactly where things left off.
- **Specialists are composable.** You add a new stage by writing one agent file and adding one routing rule to the orchestrator. The existing agents do not change.

**How you build it in this module:** Incrementally. You start with an orchestrator that only knows about intake. You run it, watch it process an issue, and verify the result. Then you extend it to design. Then build. At each step you have a working system.

---

## Time Box

- Target: 90 minutes

## Required tasks

1. Set up GitHub labels for the pipeline state machine.
2. Create the intake, design, and build agent files in `.github/agents/`.
3. Create the orchestrator agent (v1 - intake only) and start the loop.
4. Watch Feature 1 process through intake (v1).
5. Extend to v2, watch Feature 1 advance through design.
6. Extend to v3, watch Feature 1 complete through build (creates PR).
7. Add Feature 2 and Feature 3 to run through v3 pipeline.
8. Verify all three features in the pipeline with appropriate labels, comments, and PRs.

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

These six labels represent the full pipeline state space. An issue moves through them in order.

**When design says "REVISE"** (not "PASS" or escalation required), it applies `design-blocked` but includes clarifications in the decision comment. The orchestrator recognizes this and **automatically re-routes the issue back to intake** so intake can clarify requirements based on design feedback. Then design runs again. This creates a feedback loop: design feedback → intake clarification → re-design.

**When design says "BLOCKED"** (escalation required), it also applies `design-blocked` but indicates a problem that needs human decision. The orchestrator skips this issue until human intervention.

**When intake says "BLOCKED"** (acceptance criteria unclear), or **build says "BLOCKED"** (scope creep detected), the orchestrator also skips and waits for human review.

Summary: `design-blocked` is actionable (if REVISE) or blocked (if BLOCKED). Other `-blocked` labels always need human attention.

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

# Copy skill contract files (agents reference these to apply decision rules)
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
  orchestrator.agent.md           (v1 - intake only routing)

templates/skills/
  intake-agent.md     (evaluated by intake.agent.md)
  design-agent.md     (evaluated by design.agent.md)
  build-agent.md      (evaluated by build.agent.md)
```

**How they work together:** Each agent file is an executable specialist. When the orchestrator spawns the intake agent on an issue, that agent:
1. Reads the GitHub issue
2. Loads the rules from `templates/skills/intake-agent.md`
3. Applies the contract rules
4. Posts a readable decision comment with collapsible JSON details
5. Applies the appropriate label (`intake-approved` or `intake-blocked`)

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

The orchestrator will start immediately. You will see it list open issues, process any qualifying ones, then print a cycle summary and begin the next cycle.

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

**Important for v1:** The v1 orchestrator only routes issues with NO pipeline labels to intake. Issues that already have `intake-approved` label will be ignored in v1 - they're waiting for the design routing that comes in Step 4 (v2). This is intentional. You'll see something like:

```
Checking issue #1: Prevent double checkout of the same item
  -> Action: Skip (has intake-approved label - design routing not yet available in v1)
```

### Watch the first cycle

Within 10-20 seconds, the orchestrator's next cycle will pick up your new issue. You should see:

**In the terminal (CLI output):**
```
Checking issue #1: Prevent double checkout of the same item
  -> Action: Routing to intake agent

--- Orchestrator Cycle Summary ---
Issues checked: 1
Issues advanced to intake: 1
Issues blocked or complete: 0
```

Each issue check and routing decision appears on its own line for readability.

**On your GitHub issue (comment section):**
You should see two new comments:

1. **Orchestrator Routing Decision** comment:
   - Shows a readable summary: "Routing to intake"
   - Lists current labels and reasoning
   - Collapsible JSON details for future agent parsing

2. **Intake Decision** comment (posted after intake agent completes):
   - Shows a readable summary: "READY" or "BLOCKED"
   - Shows confidence level
   - Collapsible JSON with full decision details

The `intake-approved` or `intake-blocked` label is also applied automatically to your issue.

**Micro-check:** If intake returns BLOCKED, click "Evaluation Details (JSON)" to expand and read the `missing_fields` array. Fix the issue body, delete the `intake-blocked` label, and wait for the next cycle. The orchestrator will retry it.

---

## Step 4 (10 minutes): Extend the orchestrator to design

The orchestrator reads its agent file at the start of each cycle. To add a new stage, update the file. The change takes effect on the next cycle. No restart required.

### Update `.github/agents/orchestrator.agent.md`

Copy the v2 template to replace your v1 orchestrator:

```bash
cp templates/agents/orchestrator.v2.agent.md .github/agents/orchestrator.agent.md
```

This expands the routing table to include design: issues with `intake-approved` (and no design label yet) will now be routed to the design agent on the next cycle.

**What design can decide:** Design evaluates the intake decision and may return one of three decisions:
- **PASS:** Design is sound, ready for build. Applies `design-approved` label. Orchestrator routes to build on next cycle.
- **REVISE:** Design needs clarification or scope narrowing, but not escalation. Applies `design-blocked` label with clarifications in the JSON. **The orchestrator recognizes REVISE, re-routes back to intake**, and intake clarifies based on design feedback. Then design runs again. This creates a feedback loop.
- **BLOCKED:** Design is blocked and requires escalation (breaking API changes, cross-team dependencies, etc.). Applies `design-blocked` label. Orchestrator skips and waits for human decision.

### Watch the next cycle

On the next cycle, the orchestrator will:
- See your issue now has `intake-approved`
- Match the design routing rule
- Spawn the design agent
- The design agent reads the issue and the intake decision comment
- Posts a Design Decision comment with the design contract JSON output
- Applies `design-approved` (if PASS), `design-blocked` (if REVISE or BLOCKED)

Check your GitHub issue again. It should now have both an Intake Decision comment and a Design Decision comment.

**If design returns REVISE:** You'll see the issue's labels change. The orchestrator will remove `design-blocked` and `design-approved`, keep `intake-approved`, and re-spawn the intake agent to clarify based on the design feedback. The issue will then flow back through design with the updated requirements.

**If design returns PASS:** The issue will have `design-approved` label, and the orchestrator will route it to build on the next cycle.

---

## Step 5 (15 minutes): Extend the orchestrator to build

### Update `.github/agents/orchestrator.agent.md`

Copy the v3 template to add the build stage:

```bash
cp templates/agents/orchestrator.v3.agent.md .github/agents/orchestrator.agent.md
```

This adds the final routing rule: issues with both `intake-approved` and `design-approved` will now be routed to the build agent on the next cycle.

### Watch Feature 1 complete the full pipeline

Watch the next 2-3 cycles as Feature 1 ("Prevent double checkout") completes the build stage:

1. The orchestrator sees your issue has both `intake-approved` and `design-approved`
2. Spawns the build agent
3. The build agent creates a branch, implements code, commits, pushes, and opens a PR
4. Posts Build Decision comment with PR link and `build-complete` label

**On your GitHub issue,** you should now see:
- **Three labels:** `intake-approved`, `design-approved`, `build-complete`
- **Three comments:** Intake Decision, Design Decision, Build Decision (each with JSON)
- **One PR:** Linked from the Build Decision comment

**In the terminal,** you should see output like:
```
Checking issue #1: Prevent double checkout of the same item
  -> Action: Routing to build agent (creates PR)

--- Orchestrator Cycle Summary ---
Issues checked: 1
Issues advanced to build: 1
Issues complete: 0
```

---

## Step 6 (20 minutes): Add two more features and run through V3 orchestrator

Now that V3 is running continuously, create two additional features. They will both run through the full intake → design → build pipeline automatically while the orchestrator continues.

### Feature 2: Show checkout history for each item

Create a new issue using the template:

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

### Feature 3: Flag overdue checkout items

Create a third new issue:

```markdown
Title: Flag overdue checkout items in the list

## Problem Statement
Coordinators cannot see at a glance which items have been checked out past
their expected return date. Equipment disappears, disputes arise, and no one
knows who to follow up with.

## Scope
Add a visual indicator (badge or icon) to items in the checkout list that
show which items are currently overdue for return. Show the holder name and
days overdue in a tooltip.

## Non-Goals
- No automatic notifications or reminders sent
- No enforcement or lockout mechanism
- No changes to the checkout/return flow
- No email or SMS alerts

## Acceptance Criteria
- [ ] PASS: Items checked out past return date show an overdue badge
- [ ] PASS: Badge includes holder name and days overdue
- [ ] PASS: Items returned on time do not show a badge
- [ ] PASS: Overdue badge is clearly visible in the item list

## Test Scenarios
- Scenario 1 (overdue item): Item checked out 2 days past return date - badge shows "John D. - 2 days overdue"
- Scenario 2 (on-time item): Item due back tomorrow - no badge shown
- Scenario 3 (empty state): No items checked out - list shows normally

## Risk Level
Low - display-only feature, no changes to checkout logic or data model

## Dependencies
None

## Notes
This helps coordinators prioritize follow-up on missing equipment.
```

### Watch both features run through the full pipeline

As you create each issue, the orchestrator will pick them up on the next cycle and route them through intake → design → build automatically.

On the GitHub issues list, you should see:
- **Feature 1:** Three labels, three comments, PR created (build-complete)
- **Feature 2:** Starting at intake, advancing through design, eventually reaching build
- **Feature 3:** Starting at intake, advancing through design, eventually reaching build

The orchestrator continues running, reading fresh state on each 90-second cycle. No manual intervention needed.

---

## Step 7 (5 minutes): Verify the full system

Go to your GitHub repository and look at the issues list. You should see:

- **Labels** showing exactly where each issue is in the pipeline
- **Comments** on each issue with the JSON decision from each contract
- **Three issues** that have moved through the pipeline: Feature 1 complete (build-complete), Features 2 & 3 in progress

This is your agentic OS running. One command started it. The orchestrator reads state, routes work, and writes results. You did not touch it once the loop started.

**What to notice:**
- Feature 1 shows the full journey: intake-approved → design-approved → build-complete with PR
- Features 2 & 3 are progressing through the same stages automatically
- Each issue's label trail is the pipeline state - readable at a glance from the issues list
- Each issue's comment trail is the decision record - auditable and traceable
- The orchestrator processed all three issues across multiple cycles, not all at once
- Issues that returned BLOCKED were correctly skipped until you intervene

---

## Micro checks

- Minute 5: Six pipeline labels created in GitHub.
- Minute 20: Four agent files created in `.github/agents/`.
- Minute 35: Orchestrator V1 started, Feature 1 processed by intake agent (depth-first: Feature 1 intake only).
- Minute 45: Orchestrator V2 deployed, Feature 1 advances to design (Feature 2 hasn't started yet).
- Minute 60: Orchestrator V3 deployed, Feature 1 completes build stage with PR (Features 2 & 3 not yet started).
- Minute 80: Feature 2 enters intake while Feature 1 is complete.
- Minute 100: Feature 2 in design, Feature 3 starting intake (depth-first: sequential progression).

## You should see

- `.github/agents/` contains four agent files
- **Feature 1 (Prevent double checkout):** Complete with three labels, three comments, and a PR
- **Feature 2 (Show checkout history):** Behind Feature 1 (just starting or in middle stages)
- **Feature 3 (Flag overdue items):** Further behind, waiting its turn (depth-first queueing)
- Each issue flows through all stages sequentially, not in parallel
- Copilot CLI autopilot session running continuously in the terminal

## What you learned

- **V1 → V2 → V3 progression:** Each version is a working system. You add one new routing rule at a time.
- **Feature 1 as the pilot:** Running one issue through V1, then V2, then V3 validates the entire pipeline before adding new work.
- **Depth-first orchestration:** The orchestrator focuses on one issue at a time, taking it through all available stages before moving to the next issue. This creates sequential, focused delivery instead of scattered batch processing.
- **Continuous orchestration:** V3 running continuously picks up new features and queues them in order, processing them depth-first as capacity allows.
- **Build agent creates PRs:** The build stage is fully autonomous—it creates branches, implements code, commits, and opens PRs without human intervention.
- **Design can request clarification:** When design says REVISE, the orchestrator recognizes this as actionable feedback (not a blocker), and re-routes the issue back to intake. Intake clarifies requirements based on design feedback, then design runs again. This creates a feedback loop.
- **Agents vs skills:** Skills are contract documents. Agents are executable actors that apply those contracts. The orchestrator spawns agents as tasks.
- **Labels as state:** The full pipeline is driven by label state, readable at a glance, and auditable in comments.

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
