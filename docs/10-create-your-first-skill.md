# 10 - Create Your First Skill (Hands-On)

This module teaches you exactly how to create and use "skills" in your Agentic OS.

## Before You Start

You already used skills as a concept in 01 and as an execution dependency in 05.

Now you write one contract yourself so you can control behavior instead of relying on ad hoc prompts.

In this training, a skill is a reusable agent instruction file with:

- role
- inputs
- output schema
- gate rules
- escalation behavior

You will create one right now.

## Checkpoint before moving on

You should have one tested skill file that returns valid JSON on a real issue.

Apply this same contract style to each additional skill so outputs stay automatable.

If output is prose or schema fields are missing, do not continue.

## Step 0 - What you are building

You are creating an Intake skill that reads a work item and returns:

- READY or BLOCKED
- missing fields
- recommended next state

## Step 1 - Create the folder

In your repo, ensure this folder exists:

- templates/skills

## Step 2 - Create the skill file

Verify or create file:

- templates/skills/intake-agent.md

If the file already exists in your repo, keep it and only update missing sections.

If the file does not exist, create it and paste the content below.

Paste this exact content:

```markdown
# Intake Agent Skill

## Version
- 1.0 (2026-07-04)

## Mission
Validate that a work item is complete enough to begin design.

## Required Inputs
- work_item_id
- problem_statement
- scope
- non_goals
- acceptance_criteria
- test_scenarios
- risk_level

## Output Schema
Return valid JSON only:

{
  "decision": "READY|BLOCKED",
  "missing_fields": ["string"],
  "questions": ["string"],
  "next_state": "Ready|Blocked",
  "summary": "string",
  "confidence": 0.0
}

## Guardrails
- Do not invent missing requirements.
- If required input is missing, decision must be BLOCKED.
- Keep summary under 120 words.

## Escalation Rule
Escalate when risk_level is High and acceptance criteria do not include failure-path handling.

## Gate Rule
Design Gate can only start when decision is READY.
```

## Step 3 - Test the skill manually in Copilot Chat

Open your issue content and run this prompt:

```text
Act as the Intake Agent Skill defined in templates/skills/intake-agent.md.
Use the following work item data:

<PASTE ISSUE BODY HERE>

Return JSON only. Do not include markdown.
```

Expected output shape:

```json
{
  "decision": "READY",
  "missing_fields": [],
  "questions": [],
  "next_state": "Ready",
  "summary": "Work item is complete and can move to design.",
  "confidence": 0.86
}
```

## Step 4 - Wire the skill into your process

Whenever a new issue is created:

1. Run Intake skill prompt.
2. If BLOCKED, post missing fields as issue comment.
3. If READY, move issue state to Ready.
4. Add a Decision Log entry.

Use this Decision Log format:

```text
Decision Log
- YYYY-MM-DD: Intake gate READY by @<name>. Next state Ready.
```

## Step 5 - Create the next two skills

Create these files by copying the Intake style and changing mission/schema:

- templates/skills/design-agent.md
- templates/skills/verification-agent.md

Design skill output schema should include:

- design_summary
- interfaces_changed
- data_model_impact
- risks
- decision

Verification skill output schema should include:

- build_status
- test_status
- lint_status
- failing_checks
- decision

## Challenge

Try building build-agent.md on your own.

Required output schema fields:

- files_changed
- tests_added_or_updated
- known_limitations
- decision

Then validate by running it on one issue.

## If challenge fails

Fallback procedure:

1. Copy templates/agent-contract.md.
2. Fill Mission and Output Schema first.
3. Add Guardrails last.
4. Re-test with one issue prompt.

## Next step

Continue to docs/11-first-7-days-checklist.md.
