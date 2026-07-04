# 02 - Foundations Workshop (Build First)

This module gives you quick context, then immediate practice.

## Before You Start

Finish docs/00-prerequisites-and-tooling.md and docs/01-overview.md first.

## How to run this module

Use this loop for each section:

1. Read the context block.
2. Complete the build task.
3. Pass the checkpoint.

If checkpoint fails, stop and fix before moving on.

## Module 1 - Create one real work item

Context:
You need one issue to run the workshop against real state.

Build task:

1. Create one feature issue in your target repository.
2. Add it to your GitHub Project.
3. Set these fields:
   - State = Backlog
   - Risk = Medium
   - Next Gate = Design Gate
   - Owner Agent = Intake

Checkpoint:

- One issue card exists with all four fields populated.

## Module 2 - Define your gate language

Context:
Clear pass and fail criteria prevent debate later.

Build task:

1. Open docs/gates.md.
2. Add at least three objective pass criteria for each gate.
3. Add at least one fail signal for each gate.

Checkpoint:

- Another person could evaluate gate status without asking follow-up questions.

## Module 3 - Add retry safety

Context:
Quality loops need hard stop conditions.

Build task:

1. Open docs/state-machine.md.
2. Add a section named Loop Safety Policy.
3. Add these rules:
   - Max retries per gate = 3
   - On third fail, move work to Blocked
   - Record reason and next action in issue comments

Checkpoint:

- Retry policy is documented and easy to find.

## Module 4 - Build one execution spec

Context:
A short executable spec improves implementation quality.

Build task:

1. Copy templates/ess-feature.md to docs/ess-foundations-lab.md.
2. Fill all required sections.
3. Make acceptance criteria binary pass or fail.

Checkpoint:

- Another engineer could implement from your spec without a live meeting.

## Module 5 - Run a mini end-to-end rehearsal

Context:
Practice one full loop before deeper architecture work.

Build task:

1. Add one issue comment with intake decision.
2. Add one issue comment with design decision.
3. Move State from Backlog to Ready if criteria are met.
4. If criteria are not met, move to Blocked and explain why.

Checkpoint:

- Issue timeline shows at least one decision and one state transition.

## Common mistakes and fixes

Mistake: reading ahead instead of executing.
Fix: do one module at a time and require checkpoint pass.

Mistake: vague gates.
Fix: use measurable pass or fail language.

Mistake: no evidence links.
Fix: add explicit links in issue comments at every transition.

## Checkpoint before you leave this file

You should have all of these:

- one issue with state fields set
- objective gate criteria documented
- loop safety policy documented
- one completed ESS draft
- one mini state transition run

## Next step

Continue to docs/03-reference-architecture.md.
