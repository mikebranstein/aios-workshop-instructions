# 11 - GitHub Projects Setup (Click-by-Click, With Context)

This guide is written for developers who are comfortable with Git and pull requests but new to GitHub Projects as an operations layer.

Goal:

- create a board that behaves like a state database for your AIOS

If this is your first time with GitHub Projects, run docs/00-prerequisites-and-tooling.md first.

By the end of this setup, you should be able to answer this at any moment:

- what state is each work item in
- who owns the next action
- what gate must pass next

## How this builds on earlier modules

In 02 you defined architecture and in 03 you defined canonical state.

This file is where that design becomes a working board your team can actually operate.

## Apply this as you read

After each part, verify one real issue card reflects the field updates you just configured.

If setup is done but cards are missing data, treat that as incomplete.

## Checkpoint before workshop execution

Before continuing, confirm at least one issue has complete State, Risk, Next Gate, and Owner Agent values on the board.

## Why Projects is central to this workshop

Your AIOS requires durable state.

If state is only in chat history, the process cannot be audited or resumed reliably.

GitHub Project fields give you durable, queryable state with low overhead.

## Part A - Create the project shell

1. Open GitHub in your browser.
2. Go to your organization or personal account home.
3. Click Projects.
4. Click New project.
5. Choose Board layout.
6. Name it AIOS Delivery Board.
7. Click Create.

Expected result:

- a new board exists with editable fields and workflow options

## Part B - Create required state fields

In your project, add these fields in this order.

Field 1: State (single select)

Options:

- Backlog
- Ready
- In Design
- In Build
- In Verification
- In QA
- Ready to Merge
- Done
- Blocked

Field 2: Risk (single select)

Options:

- Low
- Medium
- High

Field 3: Next Gate (single select)

Options:

- Design Gate
- Verification Gate
- QA Gate
- Merge Gate

Field 4: Owner Agent (text)

Why this field set:

- State tracks lifecycle
- Risk controls approvals
- Next Gate drives immediate objective
- Owner Agent clarifies responsibility

## Part C - Configure board columns for visibility

1. In board view, create a column for each State value.
2. Map each column to the matching State field value.
3. Keep Blocked visible as a dedicated high-priority column.

Expected result:

- cards visually represent true state with no manual interpretation

## Part D - Add first real work item

1. Open repository issues.
2. Create an issue with your feature template.
3. Add issue to AIOS Delivery Board from the issue sidebar.
4. Set field values:
   - State = Backlog
   - Risk = Medium for your first training issue
   - Next Gate = Design Gate
   - Owner Agent = Intake

Expected result:

- one issue card appears with complete operational fields

## Part E - Enable low-risk built-in workflows

Before custom Actions, enable built-in board workflows:

1. Open project Workflows tab.
2. Enable auto-add from your repository issues.
3. Set default State to Backlog when item is added.
4. Set State to Done when linked issue closes.

Expected result:

- baseline lifecycle automation is active without custom code

## Part F - Daily operating procedure

For each active item, perform this cycle:

1. verify current State reflects real work
2. run the skill corresponding to current state
3. decide gate PASS or FAIL
4. update Next Gate and Owner Agent
5. append Decision Log comment to issue

If this cycle is skipped, your board data degrades and orchestration quality falls.

## Part G - Common problems and exact fixes

Issue does not appear on board:

- confirm repository is connected in project settings
- ensure issue is in correct org or account scope

Fields not visible on cards:

- open card settings and pin fields for display

State mismatch between issue label and project field:

- treat project State as canonical and sync labels to it

Too many blocked items:

- inspect Next Gate and Owner Agent quality
- unclear ownership is usually the root cause

## Completion gate for setup

Setup is complete only when all are true:

1. at least one real issue appears on board
2. all required fields are populated
3. you can move Backlog to Ready with a Decision Log entry
4. auto-add and close-to-done workflows are enabled

Once these are true, proceed to live workshop execution.

## Next step

Continue to 14 live workshop and use this board as your single operational state surface.
