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
- If confidence < 0.7, do not return READY.

## Escalation Rule
Escalate when risk_level is High and acceptance criteria do not include failure-path handling.

## Gate Rule
Design Gate can only start when decision is READY.
