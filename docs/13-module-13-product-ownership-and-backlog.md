# Module 13 - Product Leadership: Strategy and Execution

## Concept: The product is driven by two complementary leaders

Modules 1-12 focused on **how** to build and release features efficiently: intake → design → build → verification → QA → policy → release. But someone needs to decide **what** to build and **why**—and someone else needs to execute that strategy tactically.

**Module 13 introduces the complete product leadership layer**: the product manager (strategic direction) and the product owner (tactical execution). Together, they ensure every feature shipped is strategically important *and* valuable to the business.

**Key distinctions:**
- **Product Manager (Strategic)**: Sets long-term product vision, discovers market opportunities, understands competition, evaluates trade-offs at the strategic level. Asks: "What market problems should we solve? Where is the product heading?"
- **Product Owner (Tactical)**: Prioritizes the backlog, ensures execution aligns with strategy, works daily with development team. Asks: "Which features should we build next to execute that vision?"

**Why both roles matter:**
- Without a PM, the product becomes reactive (chasing every customer request) instead of strategic (building toward a vision)
- Without a PO, the strategy stays theoretical (never gets executed) instead of practical (features ship regularly)

Together, they form the **two-tier leadership model**: PM sets direction → PO executes it through the backlog → Development pulls from backlog continuously.

## Where product leadership fits in the system

**Two independent, concurrent orchestrator loops:**

```
┌─────────────────────────────────────────────────────────────┐
│ PM-PO Orchestrator Loop (runs continuously, independent)    │
│                                                             │
│ [PM Discovery] → [PM Validation] → [PO Prioritization]    │
│ ├─ Research market opportunities                          │
│ ├─ Validate with customers                                │
│ ├─ Make CHAMPION/DEFER/BLOCK decisions                    │
│ └─ Order backlog by priority score                         │
│                                                             │
│ Output: "Ready for Development" column (pre-prioritized)   │
└─────────────────────────────────────────────────────────────┘
                         ↓ (async pull)
┌─────────────────────────────────────────────────────────────┐
│ Development Orchestrator Loop (runs continuously, pulls)    │
│                                                             │
│ [Intake] → [BA] → [Design] → [Build]                      │
│ → [Verification] → [QA] → [Policy] → [Release]            │
│                                                             │
│ - Never waits for PM-PO                                    │
│ - Pulls next-priority issue from backlog                   │
│ - Executes 8-stage pipeline                                │
│ - Ships to production                                      │
└─────────────────────────────────────────────────────────────┘
```

**Why two independent loops:**
- PM-PO can continuously research, validate, and re-prioritize opportunities without blocking the development pipeline
- Development can keep shipping from the backlog without waiting for product decisions
- When market conditions change, PM can reprioritize without halting mid-development work
- Both teams work autonomously at the speed that suits their work

## Time Box

- Target: 90 minutes (understanding both PM and PO roles, how they collaborate, and running features through both tiers)

## Required Tasks

1. Understand the product manager role and strategic discovery process.
2. Understand the product owner role and tactical prioritization process.
3. Define your product vision and strategic priorities.
4. Review the product manager agent (`templates/agents/product-manager.agent.md`).
5. Review the product owner agent (`templates/agents/product-owner.agent.md`).
6. Research market opportunities and validate with stakeholders or customers.
7. Create backlog items based on validated opportunities.
8. Practice PM ↔ PO collaboration (PM proposes → PO prioritizes).

---

## Step 1 (10 minutes): Understand the Product Manager role

A product manager is responsible for **strategic product direction**. They sit at the intersection of business, market, and technology.

**What PMs do:**
- **Set product vision:** Where is the product headed? What market are we trying to own? What competitive advantage are we building?
- **Discover market opportunities:** Talk to customers, analyze competition, identify problems that need solving. PMs are customer detectives.
- **Validate ideas:** Before building anything, confirm that customers actually want it and it aligns with strategy.
- **Make strategic trade-offs:** When capacity is limited (always), decide what's important and what can wait.
- **Channel opportunities to PO:** Hand off validated ideas to the Product Owner for tactical prioritization.

**What PMs do NOT do:**
- **Create `feature-request` issues** (PO creates these exclusively)
- Define acceptance criteria (BA does this)
- Design architecture (Design does this)
- Prioritize the day-to-day backlog (PO does this)
- Manage sprint execution (PO does this)

**CRITICAL BOUNDARY:** PM creates `strategic-opportunity` issues. PO creates `feature-request` issues. This boundary is non-negotiable.

**Key PM question:** "What market problems should we solve? Is this strategically important?"

---

## Step 2 (10 minutes): Understand the Product Owner role

A product owner is responsible for **tactical execution** of the PM's strategic vision. They work daily with the development team.

**What POs do:**
- **Manage the backlog:** Order features by priority. Quick wins first (high value + low complexity), then strategic bets (high value + high complexity), then maintenance work.
- **Collaborate with BA:** Clarify requirements, ask clarifying questions, work through ambiguities.
- **Create `feature-request` issues:** Turn validated strategic-opportunities into GitHub issues with user story, acceptance criteria, and priority score (PO-only responsibility).
- **Prioritize:** Use a formula to assess (User Value + Business Value) / (Complexity × 1.5). Higher score = higher priority.
- **Escalate to PM:** If a customer request conflicts with strategy or needs strategic context, ask PM for input.

**What POs do NOT do:**
- Set product strategy (PM does this)
- Conduct market research (PM does this)
- Create strategic-opportunity issues (PM does this)
- Define acceptance criteria at the strategic level (PM research informs this)
- Build features (Design and Build do this)

**CRITICAL BOUNDARY:** PO consumes `strategic-opportunity` issues (PM creates those) and creates `feature-request` issues exclusively. PO never creates feature-requests from pm-ideas directly; they must come via PM validation first.

**Key PO question:** "Which features should we build next to execute our strategy? What's the business value vs. effort?"

---

## Step 3 (15 minutes): Three Issue Types in Product Leadership

Product leadership uses three distinct issue types to separate concerns and make hand-offs explicit.

### Creating Custom Labels

First, create the labels that the issue templates will auto-apply.

**Option 1: GitHub Web UI**

1. Go to your repository main page on GitHub
2. Click **Settings** (top right)
3. In the left sidebar, click **Labels**
4. Click **New label** and create these 7 labels:

| Label | Description |
|-------|-------------|
| `pm-idea` | Feature idea submitted for product discovery |
| `pm-opportunity` | Validated market opportunity ready for PO prioritization |
| `pm-deferred` | PM opportunity deferred to next quarter |
| `pm-blocked` | PM opportunity blocked (not strategic fit) |
| `feature-request` | Development-ready feature (labeled by PO) |
| `po-prioritized` | PO has prioritized and positioned in backlog |
| `blocked-on` | Feature blocked by dependency; revisit when blocker clears |

**Option 2: GitHub CLI (faster)**

If you have `gh` (GitHub CLI) installed, run these commands in your terminal:

```bash
gh label create pm-idea --description "Feature idea submitted for product discovery" --color "E8F4F8"
gh label create pm-opportunity --description "Validated market opportunity ready for PO prioritization" --color "D4E8F7"
gh label create pm-deferred --description "PM opportunity deferred to next quarter" --color "F0E5D8"
gh label create pm-blocked --description "PM opportunity blocked (not strategic fit)" --color "E8D5D8"
gh label create feature-request --description "Development-ready feature (labeled by PO)" --color "D4E8E8"
gh label create po-prioritized --description "PO has prioritized and positioned in backlog" --color "D4F0E8"
gh label create blocked-on --description "Feature blocked by dependency; revisit when blocker clears" --color "E8E4D8"
```

Once all 7 labels exist, they'll be available for your issue templates and orchestrator workflows.

---

## Step 3b (5 minutes): Enable GitHub Wiki

The Product Manager agent will create and maintain the Research Wiki on its first run. You just need to enable the feature.

**Enable GitHub Wiki in your repository:**

1. Go to your GitHub repository main page
2. Click **Settings** (top right)
3. Scroll down to **Features** section
4. Check the box next to **Wiki**
5. Click **Save**

That's it. When the PM agent runs for the first time, it will automatically create:
- Research Wiki home page
- Skeleton pages for personas, journey maps, interview data, strategic decisions
- Research-to-Decision Index

**See:** [User Research & Personas Skill](../templates/skills/user-research-and-personas.md) for details on how the research wiki will be structured and updated quarterly.

---

### Issue Type 1: `pm-idea` — User Submission

**Who creates:** Anyone (customer, sales, support, user, PM themselves)  
**What it is:** Lightweight feature idea (1-3 sentences)  
**When it's created:** Anytime someone thinks of a feature worth exploring

**Example:**
```
Title: [pm-idea]: Mobile app for field teams
Labels: pm-idea
Body: 
- 4 support tickets this week about "can't checkout from field"
- 2 enterprise customers mentioned in recent calls
- Competitor X doesn't have mobile; Competitor Y has basic iOS
- Fits Q3 priority "mobile-first experience"
```

**Now create the `pm-idea` template:**

1. Go to your repository main page on GitHub
2. Click **Add file** → **Create new file**
3. In the filename field, type exactly: `.github/ISSUE_TEMPLATE/pm-idea.md`
4. Copy and paste this content into the file:

```markdown
---
name: PM Idea
about: Submit a feature idea for product discovery
title: "[pm-idea]: "
labels: 'pm-idea'
assignees: ''

---

## Feature Idea (1-3 sentences)
[Describe your feature idea here]

## Customer Context (optional)
- Who mentioned this?
- Support tickets or customer calls?

## Competitive Context (optional)
- What do competitors do?
- What's our advantage?
```

5. Click **Commit changes** at the bottom right

---

### Issue Type 2: `strategic-opportunity` — PM's Research & Validation

**Who creates:** Product Manager agent (after autonomous research/validation)  
**What it is:** Market research findings, customer validation evidence, strategic decision  
**When it's created:** After PM completes discovery, validation, and makes CHAMPION/DEFER/BLOCK decision

**Example:**
```
Title: [strategic-opportunity]: Mobile app for field teams

Research Findings:
- 12 support tickets about field checkout over 4 weeks
- 4 customers interviewed; all confirmed critical pain point
- Competitor A has basic mobile; Competitor B doesn't
- Affects ~35% of enterprise customer base

Validation Assessment:
- Strategic alignment: ✅ (aligns with Q3 mobile-first priority)
- Market opportunity: High (multiple enterprise upsell opportunities)
- Competitive advantage: Real-time + FM system integration (competitors lack this combo)
- Effort estimate: 3-4 weeks
- Customer validation: Strong (4/4 customers volunteered to beta-test)

Decision: CHAMPION → Ready for PO prioritization
```

**Now create the `strategic-opportunity` template:**

1. Click **Add file** → **Create new file** again
2. In the filename field, type exactly: `.github/ISSUE_TEMPLATE/strategic-opportunity.md`
3. Copy and paste this content into the file:

```markdown
---
name: Strategic Opportunity
about: PM research, validation, and strategic decision
title: "[strategic-opportunity]: "
labels: 'pm-opportunity'
assignees: ''

---

## Strategic Summary
[Link to source pm-idea or standalone summary]

## Research Findings
- Support tickets: [X mentions]
- Customer validation: [Talked to Y customers; Z confirmed]
- Competitive landscape: [Competitor analysis]
- Market size: [~X% of target customers affected]

## Research Wiki References
**Always link research to persistent sources:**
- **Persona(s):** [Link to wiki persona page(s)]
- **Journey Map Stage:** [Link to journey map + stage affected]
- **Interview Transcripts:** [Link to Interview-Transcripts-Q2-2026 page with specific quotes]
- **Research-to-Decision Index:** [Link confirming pattern identified]

*Example:*
- **Persona:** [Facility Manager Frank](https://github.com/your-org/your-repo/wiki/Personas-Facility-Manager-Frank)
- **Journey Stage:** [Problem Resolution](https://github.com/your-org/your-repo/wiki/Journey-Maps-Facility-Manager)
- **Transcripts:** [Q2 2026 - 8 customers mentioned equipment loss problem](link)
- **Pattern:** [Research-to-Decision Index - Equipment Loss](link)

## Validation Assessment
- Strategic alignment: ✅ or ❌
- Market opportunity: High/Medium/Low
- Competitive advantage: [What makes ours unique?]
- Effort estimate: [X weeks]
- Customer validation strength: Strong/Medium/Weak

## Decision
- **Decision:** CHAMPION / DEFER / BLOCK
- **Rationale:** [Why this decision?]
- **Decision Recorded In:** [Link to Strategic-Decisions-2026 wiki page]
```

4. Click **Commit changes** at the bottom right

---

### Issue Type 3: `feature-request` — PO's Prioritized Task

**Who creates:** Product Owner (after reading strategic-opportunity)  
**What it is:** Ready-to-build development task  
**When it's created:** After PO prioritizes a CHAMPION strategic-opportunity

**The hand-off:** PO creates `feature-request` issues → Development pulls them from "Ready for Development" → Executes the 8-stage pipeline.

You've already created and customized the `feature-request` template in Module 2. Use it as-is, and add a **Strategic Context** line at the top linking back to the source `strategic-opportunity`.

See [Module 2 - Intake Quality Template](02-module-2-intake-quality-template.md) for the template.

**Verify all templates are working:**

Go to your repository, click **New issue**, and you should see **PM Idea**, **Strategic Opportunity**, and **Feature Request** in the template list.

---

## Step 4 (10 minutes): Review the Product Manager agent

The PM agent (`templates/agents/product-manager.agent.md`) walks you through:

1. Strategic discovery: How to find market problems
2. Research methods: User interviews, competitor analysis, support feedback, data trends
3. Validation framework: Does this problem affect many customers? Is it strategically aligned?
4. **Creates `strategic-opportunity` issues** as output (not just making decisions internally)
5. **Autonomy Mode**: Submit a `pm-idea` and have the agent autonomously research, validate, and create `strategic-opportunity` issues

**Key insight:** PM agent reads `pm-idea` issues → researches → creates `strategic-opportunity` issues for PO to consume.

**See also**: [templates/pm-discovery-README.md](../../templates/pm-discovery-README.md) for step-by-step guide on autonomous PM discovery.

---

## Step 5 (10 minutes): Review the Product Owner agent

The PO agent (`templates/agents/product-owner.agent.md`) walks you through:

1. **Consumes:** `strategic-opportunity` issues from PM
2. **Evaluates:** Value, business impact, complexity
3. **Prioritizes:** Calculates priority score and backlog position
4. **Creates:** `feature-request` issues with user stories, acceptance criteria, success metrics
5. **Hands off:** `feature-request` issues ready for development

**Key insight:** PO agent reads `strategic-opportunity` → creates `feature-request` for development to consume.

### Key PO Frameworks and Skill References

The PO agent includes five specialized skill contracts for different aspects of tactical execution:

**[Release Coordination](../templates/skills/release-coordination.md)**
- Multi-team dependencies and staging gates
- Feature flag strategy (1% → 10% → 100% rollout)
- Launch readiness checklists
- Rollback planning and post-launch monitoring
- Use when: Feature involves multiple teams or requires staged deployment

**[Metrics and Experimentation](../templates/skills/metrics-and-experimentation.md)**
- AARRR framework (identify which funnel stage is broken: Acquisition, Activation, Retention, Referral, Revenue?)
- Cohort analysis (are new users better than old?)
- A/B testing for high-risk features
- Post-launch adoption tracking and kill decision frameworks
- Use when: Making data-driven backlog decisions or measuring feature success

**[Stakeholder Alignment - PO](../templates/skills/stakeholder-alignment-po.md)**
- Three frameworks for saying "no" strategically (explicit priority list, impact vs. effort, strategic alignment)
- Stakeholder communication cadences (weekly, monthly, quarterly)
- Trade-off communication templates
- Use when: Managing competing priorities or executive pressure

**[Feedback Loops and Learning](../templates/skills/feedback-loops-and-learning.md)**
- A.C.A.F. framework (Ask → Categorize → Act → Follow-up)
- NPS/CSAT/CES metrics and support ticket categorization
- "5+ customer rule" (when feedback becomes signal vs. edge case)
- Churn analysis and close-the-loop communication
- Use when: Capturing customer feedback signals and converting to backlog priorities

**[Cross-Functional Workflows](../templates/skills/cross-functional-workflows.md)**
- PM ↔ PO workflow (strategic opportunity review)
- PO ↔ BA workflow (acceptance criteria refinement)
- PO ↔ Design, Engineering, QA, Marketing workflows
- Meeting cadences (weekly refinement, daily standups, release planning, post-launch review)
- Use when: Coordinating with any downstream function

---

## Step 6 (20 minutes): Run end-to-end orchestration with one feature

Now create a `pm-idea` issue and invoke the PM-PO Orchestrator to handle the full flow autonomously. Your role is to observe—the agents do the work.

**Workflow:**
1. **You create** a `pm-idea` issue (user input: simple problem statement)
2. **PM-PO Orchestrator runs autonomously:**
   - PM Agent reads pm-idea → researches → creates `strategic-opportunity` issue
   - PO Agent reads strategic-opportunity → prioritizes → creates `feature-request` issue
3. **Development Orchestrator runs** (pulls feature-request, routes through Intake → Design → Build)
4. **You observe** the end-to-end flow and results

**What you're testing:**
- Can the PM agent research a market opportunity autonomously and validate it?
- Can the PO agent prioritize it and hand it off to development?
- Does the development orchestrator pull it and route it correctly?

**Steps:**

1. **Create a `pm-idea` GitHub issue** as your starting input (this is what users or customer success would submit):

   Use this format for a `pm-idea` issue:
   ```
   Title: [1-3 sentence feature idea]
   Label: pm-idea
   Body (optional): Customer trigger, competitive context, strategic rationale, or support ticket references
   ```

   **Example `pm-idea` for this workshop project:**
   
   ```
   Title: [pm-idea]: Mobile checkout for field teams - field teams waste 2-3 hours/day returning to office for equipment checkout
   Label: pm-idea
   Body: 8 support tickets in the last month from our largest customers requesting mobile access. Competitor just launched mobile app. Blocking upsell to field-heavy customers.
   ```

   Create this issue in your GitHub repo. The PM agent will read it from the backlog.

2. **Invoke the PM orchestrator** (Terminal 1):

   Copy the PM orchestrator template to your active agent location:

   ```bash
   cp templates/agents/orchestrator.pm.agent.md .github/agents/orchestrator.agent.md
   ```

   Then run it:

   ```bash
   copilot --autopilot --allow-all-tools --enable-all-github-mcp-tools \
     -p "Start the PM orchestrator. Run continuously in an infinite loop. Check every 30 seconds for new unprocessed pm-idea issues. Do not stop until Ctrl+C."
   ```

   The PM orchestrator will (autonomously, from its contract in orchestrator.pm.agent.md):
   - Find unprocessed `pm-idea` issues
   - Spawn PM agent to research and validate each idea
   - Output `strategic-opportunity` issues with CHAMPION/DEFER/BLOCK decisions
   - Link back to source pm-idea and update Research Wiki
   - Loop back to find the next pm-idea
   - Continue until you press Ctrl+C

3. **In a second terminal, invoke the PO orchestrator** (Terminal 2):

   Copy the PO orchestrator template to your active agent location:

   ```bash
   cp templates/agents/orchestrator.po.agent.md .github/agents/orchestrator.agent.md
   ```

   Then run it (in parallel with the PM orchestrator):

   ```bash
   copilot --autopilot --allow-all-tools --enable-all-github-mcp-tools \
     -p "Start the PO orchestrator. Run continuously in an infinite loop. Check every 30 seconds for new CHAMPION strategic-opportunities without feature-requests. Do not stop until Ctrl+C."
   ```

   The PO orchestrator will (autonomously, from its contract in orchestrator.po.agent.md):
   - Find CHAMPION `strategic-opportunity` issues without corresponding feature-requests
   - Spawn PO agent to evaluate and prioritize each opportunity
   - Create `feature-request` issues with priority scores and acceptance criteria
   - Move feature-requests to "Ready for Development" column
   - Link back to source strategic-opportunity
   - Loop back to find the next unprocessed opportunity
   - Continue until you press Ctrl+C

   **Both orchestrators now run concurrently in separate terminals:**
   - Terminal 1 (PM): Discovering and validating ideas
   - Terminal 2 (PO): Prioritizing validated opportunities
   - Neither waits for the other; both work asynchronously

4. **Observe what both orchestrators produce** (or optionally invoke Development Orchestrator in Terminal 3):

   Watch the PM and PO orchestrators process your pm-idea:
   - Terminal 1 (PM): Creates strategic-opportunity issue with research findings
   - Terminal 2 (PO): Creates feature-request issue with priority score, moves to "Ready for Development"

   **Optional: Route through Development Pipeline**

   If you want to see the feature flow through development (Intake → Design → Build), open a third terminal and start the Development Orchestrator:

   ```bash
   cp templates/agents/orchestrator.development.agent.md .github/agents/orchestrator.agent.md
   copilot --autopilot --allow-all-tools --enable-all-github-mcp-tools \
     -p "Start the Development orchestrator."
   ```

   The Development orchestrator will:
   - Parse priority scores from all issues in "Ready for Development"
   - Pull the highest-priority issue created by PO orchestrator
   - Route it through Intake → Design → Build
   - Create design documentation and architecture decisions
   - Generate build task breakdown and code scaffolding

5. **Review the output and verify full traceability:**

   **From PM Orchestrator (Terminal 1):**
   - `strategic-opportunity` issue with research findings, customer validation, decision label (CHAMPION/DEFER/BLOCK)
   - Research Wiki updates (personas, journey maps, decision reasoning)
   - Links back to source pm-idea

   **From PO Orchestrator (Terminal 2):**
   - `feature-request` issue with user story, acceptance criteria, priority score
   - Positioned in "Ready for Development" column
   - Links back to strategic-opportunity

   **From Development Orchestrator (Terminal 3, if running):**
   - Intake: Issue validated, moved to "In Development"
   - Design: Architecture decision, wireframes, interaction model, risk assessment
   - Build: Code scaffolding, task breakdown, test cases

   **Full traceability chain:** pm-idea → strategic-opportunity → feature-request → intake → design → code

### pm-idea Issue Lifecycle: Two-Phase Validation

When you create a pm-idea issue, the PM orchestrator processes it through **two phases** to ensure decisions are backed by customer research:

#### **PHASE 1: Research Gate (10-15 min)**

When PM orchestrator finds a new `pm-idea`:

1. PM agent does **quick validation**:
   - Does a credible customer signal exist? (support tickets, customer feedback)
   - Does it fit strategic pillars (high-level)?
   - If **NO** → BLOCK or DEFER immediately, close pm-idea → Done

2. If **YES signal** → PM agent identifies research gaps:
   - What personas are affected?
   - What journey stages matter?
   - What research exists in the Wiki already?

3. PM agent creates **research work items** for missing research:
   - Issue title: "[research]: [Persona Name] for [Opportunity]"
   - Label: `research`, `pm-work`
   - Due: 2 weeks
   - Body: Guidance on conducting 5+ interviews and updating Research Wiki

4. PM agent creates **strategic-opportunity issue** with status: "PENDING RESEARCH VALIDATION"
   - Links all research items
   - Marks with `pm-provisional-champion` label (not final yet)
   - **pm-idea stays OPEN** (doesn't close yet)

**Your responsibility in Phase 1:** Research work items are now created. Your PM team must conduct the interviews and update the Research Wiki pages (Personas, Journey Maps) with findings.

#### **PHASE 2: Final Validation (10-15 min) - Triggered when research items close**

When all linked research items are **closed** (research completed and Wiki updated):

1. PM orchestrator detects Phase 1 is complete and triggers Phase 2

2. PM agent re-reads the `pm-idea` and checks the completed Research Wiki:
   - What do the N interviews reveal about personas?
   - What journey map patterns emerged?
   - What competitive positioning data exists?

3. PM agent **validates with full research evidence**:
   - Is this CHAMPION, DEFER, or BLOCK based on research?
   - If CHAMPION confirmed → Continue to step 4
   - If research changed decision → DEFER or BLOCK

4. PM agent **closes the pm-idea** with decision:
   - If **CHAMPION** (validated with research): "Validated with customer research. See strategic-opportunity #X for findings. Closing pm-idea."
   - If **DEFER** (research shows wrong timing): "Research shows market timing wrong. Deferred for Q[X] review. Closing pm-idea."
   - If **BLOCK** (research shows weak fit): "Research revealed weak persona fit. Decision: BLOCK. Closing pm-idea."

**Timeline:**
- Phase 1: 10-15 min (quick validation + research gate setup)
- Research execution: 2 weeks (your team's responsibility)
- Phase 2: 10-15 min (final validation with completed research)
- **Total: ~2 weeks before decision is final**

**Why two phases?**
- Phase 1 gates: Prevents wasting time researching ideas with no signal
- Research work tracking: Research tasks are explicit GitHub issues, not orphaned Wiki pages
- Phase 2 validation: Decisions backed by actual customer interviews (15+ hours of work)
- Quality assurance: Weak ideas are blocked early; strong ideas are thoroughly validated before PO resources them

---

## Step 7 (10 minutes): Review what the orchestration produced

After the end-to-end run, review the artifacts and verify the full flow:

**What happened (the complete flow):**
1. **You created** `pm-idea` issue → User input describing a problem
2. **PM Orchestrator Phase 1 processed it** (Terminal 1):
   - PM agent quick-validated → Created research work items for gaps
   - Created `strategic-opportunity` issue (PENDING RESEARCH VALIDATION)
   - Identified personas/journey maps that need research
3. **Research team executed** (manual, 2 weeks):
   - Conducted 5+ interviews per persona
   - Updated Research Wiki (Personas, Journey Maps, Interview Transcripts)
   - Closed research work items when done
4. **PM Orchestrator Phase 2 processed it** (Terminal 1, after research items closed):
   - PM agent re-validated with complete research
   - Updated `strategic-opportunity` with research findings
   - Final decision: CHAMPION/DEFER/BLOCK
5. **PO Orchestrator processed it autonomously** (Terminal 2, after Phase 2):
   - PO agent read strategic-opportunity → created `feature-request` with priority score → moved to "Ready for Development"
6. **Development Orchestrator pulled it** (Terminal 3, optional):
   - Routed through Intake → Design → Build
   - Created intake, design, and build artifacts

**What you learned:**
- The PM agent autonomously researched a real problem and documented findings credibly (Terminal 1 workflow)
- The PO agent independently prioritized that research into a shippable feature with clear acceptance criteria (Terminal 2 workflow)
- Both PM and PO worked concurrently without blocking each other (separate terminals, parallel execution)
- The Development orchestrator deterministically pulled the highest-priority issue and created intake, design, and build artifacts
- **Full traceability:** pm-idea → strategic-opportunity → feature-request → intake → design → code
- **Three independent loops** (PM, PO, Development) can all run in parallel without coordination overhead

**Verify traceability:**
- Navigate to the `pm-idea` issue you created → see link to `strategic-opportunity` created by PM orchestrator (Terminal 1)
- Navigate to the `strategic-opportunity` issue → see Research Wiki links (personas, journey maps, decision reasoning) and final decision label (CHAMPION)
- Navigate to the `feature-request` issue → see link back to strategic-opportunity, priority score included, acceptance criteria present (created by PO orchestrator, Terminal 2)
- Navigate to the intake/design/build issues (if Development orchestrator ran) → see full pipeline trace back to pm-idea
- All artifacts reference each other in a complete chain; no decision is orphaned

**Identify any gaps:**
- If research was thin, note what was missing (PM agent opportunity for improvement)
- If feature-request wasn't detailed enough, note what BA needed to ask (PO opportunity for improvement)
- If design was incomplete, note what builder needs to clarify (Design opportunity for improvement)
- This is normal—no first pass is perfect. What matters is: **the loop works, and issues flow predictably through the system.**

---

## Definition of Done

✅ You have successfully completed Module 13 when:

1. **Three issue types understood** (Step 3)
   - `pm-idea` (user input): 1-3 sentences, simple problem statement
   - `strategic-opportunity` (PM output): research, validation, decision
   - `feature-request` (PO output): user story, acceptance criteria, priority score

2. **Product Manager role understood** (Step 1)
   - Can explain: strategic discovery, validation, opportunity evaluation, decision-making backed by customer research
   - Understand two-phase PM workflow: 
     - Phase 1 (Research Gate): Quick validation + identify research gaps + create research work items
     - Phase 2 (Final Validation): Research completion triggers final validation + decision + pm-idea closure
   - Understand what PM does (research gate, validate, create strategic-opportunity issues, create research work items) vs. what PO does (create feature-request issues)
   - Understand pm-idea lifecycle: created by user → Phase 1 gate → research execution (manual) → Phase 2 validation → closed with decision

3. **Product Owner role understood** (Step 2)
   - Can explain: consuming `strategic-opportunity` issues, value assessment, priority scoring, creating `feature-request` issues
   - Understand relationship: PM validates market opportunities with research; PO converts them to actionable development tasks
   - Understand: PO only acts AFTER Phase 2 completes (after research is done)

3b. **GitHub Wiki enabled** (Step 3b)
   - GitHub Wiki feature enabled in Repository Settings → Features
   - Understand: PM agent will create Research Wiki skeleton pages on first run
   - Understand: Research work items guide your team in filling Wiki pages with interview data
   - Familiar with [User Research & Personas Skill](../templates/skills/user-research-and-personas.md)

4. **PM and PO agent capabilities reviewed** (Step 5)
   - Can articulate: Phase 1 workflow (quick gate + research item creation)
   - Can articulate: Phase 2 workflow (triggered when research items close; final validation + decision)
   - Can articulate: What PM agent creates (strategic-opportunity, research work items, Wiki links)
   - Can articulate: What PO agent does (read strategy, prioritize, create feature-request)
   - Can articulate: What Development orchestrator does (intake, design, build routing)
   - Understand: PM agent is responsible for both phases; your team is responsible for research execution
   - Understand: Orchestration is autonomous for gates and decisions; manual research work required between phases

5. **PO Skill Files understood** (Step 5)
   - Familiar with [Release Coordination](../templates/skills/release-coordination.md) (multi-team dependencies, feature flags, launch checklists)
   - Familiar with [Metrics and Experimentation](../templates/skills/metrics-and-experimentation.md) (AARRR framework, data-driven decisions, kill frameworks)
   - Familiar with [Stakeholder Alignment](../templates/skills/stakeholder-alignment-po.md) (saying no, communication cadences)
   - Familiar with [Feedback Loops and Learning](../templates/skills/feedback-loops-and-learning.md) (A.C.A.F., NPS/CSAT, 5+ rule)
   - Familiar with [Cross-Functional Workflows](../templates/skills/cross-functional-workflows.md) (PM↔PO, PO↔BA, team coordination)

6. **End-to-end orchestration completed** (Step 6)
   - Created 1 `pm-idea` issue (user input with problem statement)
   - PM orchestrator Phase 1: researched and created 1 `strategic-opportunity` (PENDING RESEARCH) + N research work items
   - Your team: Completed research work items (filled Wiki pages with N interviews)
   - PM orchestrator Phase 2: Re-validated and updated strategic-opportunity with final decision (CHAMPION/DEFER/BLOCK)
   - PO agent created 1 `feature-request` issue with priority score and moved to "Ready for Development"
   - Development orchestrator pulled feature-request (highest priority first) and created Intake/Design/Build artifacts
   - Full traceability: pm-idea → strategic-opportunity → feature-request → intake → design → code

7. **Artifacts reviewed and traceability verified** (Step 7)
   - Research findings in strategic-opportunity are credible and linked to Research Wiki
   - Feature-request has clear user story, acceptance criteria, priority score, and value assessment
   - Intake documentation includes BA validation and clarification questions
   - Design documentation includes architecture decisions, wireframes, risk assessment
   - Build documentation includes task breakdown and acceptance test mapping
   - All artifacts reference each other (pm-idea → strategic-opportunity → feature-request → intake → design)

8. **Orchestration architecture understood** (Step 7)
   - Two independent loops: PM-PO researches continuously; Dev executes continuously
   - PM agent reads `pm-idea` issues and creates `strategic-opportunity` issues
   - PO agent reads `strategic-opportunity` issues and creates `feature-request` issues with priority scores
   - Development orchestrator reads "Ready for Development" column, pulls highest-priority issue first (parsed priority score), routes through intake → design → build
   - Each stage feeds into the next; you invoke orchestrators and respond to questions
   - Orchestrators run concurrently without blocking each other

## Stretch Goals

- Run a 30-minute customer interview (in-person or simulated). Document what problems you discover.
- Create a competitive analysis: What features do 3 competitors have? What don't they have? What's our differentiation?
- Build a product roadmap showing quarterly goals and how backlog items map to them
- Create a market sizing estimate: How many customers face this problem? What's the TAM (Total Addressable Market)?
- Document a strategic trade-off decision: "We're not building X because Y is more strategic."

---

## Reflection

After completing Module 13, reflect on:

- **What makes a good market opportunity?** How do you differentiate between "real market problem" and "nice-to-have feature"?
- **How does strategy guide decisions?** How would you explain your product vision to a new team member?
- **How do PM and PO collaborate?** What questions should PO ask PM? When should PM escalate to leadership?
- **What's the relationship between strategy and execution?** How does PM vision flow into PO prioritization into development pipeline?

Next: **Module 14 — Capstone: Full System End-to-End Run** — You'll run 2-3 features through the complete 10-stage pipeline (PM → PO → Intake → BA → Design → Build → Verification → QA → Policy → Release) with real market opportunities and strategic context. By the end, you'll have a complete, strategic, production-ready product organization.
