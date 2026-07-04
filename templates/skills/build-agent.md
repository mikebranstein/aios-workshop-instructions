# Build Agent Skill

## Version
- 1.0 (2026-07-04)

## Mission
Implement approved scope from ESS and acceptance criteria with traceable changes.

## Required Inputs
- work_item_id
- ess_reference
- acceptance_criteria
- scope
- non_goals
- target_branch

## Output Schema
Return valid JSON only:

{
  "decision": "COMPLETE|PARTIAL|BLOCKED",
  "changes_summary": "string",
  "files_changed": ["string"],
  "tests_updated": ["string"],
  "risks": ["string"],
  "next_state": "In Verification|Blocked"
}

## Guardrails
- Implement only approved scope.
- Do not expand scope without explicit decision log update.
- Keep changes traceable to acceptance criteria.

## Escalation Rule
Escalate when required implementation conflicts with non-goals or branch policy.

## Gate Rule
Verification starts only when decision is COMPLETE.
