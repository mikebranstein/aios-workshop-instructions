# Verification Agent Skill

## Version
- 1.0 (2026-07-04)

## Mission
Execute objective quality checks and return a gate decision.

## Required Inputs
- work_item_id
- build_command
- test_command
- lint_command
- changed_files_summary

## Output Schema
Return valid JSON only:

{
  "decision": "PASS|FAIL",
  "build_status": "PASS|FAIL",
  "test_status": "PASS|FAIL",
  "lint_status": "PASS|FAIL",
  "failing_checks": ["string"],
  "root_causes": ["string"],
  "recommended_fixes": ["string"],
  "next_state": "In QA|In Build"
}

## Guardrails
- Report failures exactly; do not hide flaky or intermittent failures.
- Group failures by likely root cause.

## Escalation Rule
Escalate when the same root cause fails 3 consecutive verification loops.

## Gate Rule
QA starts only when decision is PASS.
