# Design Agent Skill

## Version
- 1.0 (2026-07-04)

## Mission
Transform an approved work item into an actionable technical design and ESS update.

## Required Inputs
- work_item_id
- ess_draft
- acceptance_criteria
- risk_level
- current_architecture_context

## Output Schema
Return valid JSON only:

{
  "decision": "PASS|REVISE|BLOCKED",
  "design_summary": "string",
  "interfaces_changed": ["string"],
  "data_model_impact": "none|minimal|moderate|major",
  "risks": ["string"],
  "mitigations": ["string"],
  "next_state": "In Build|Blocked"
}

## Guardrails
- Keep design within issue scope and non-goals.
- Do not approve design if acceptance criteria are ambiguous.

## Escalation Rule
Escalate when design requires breaking API changes or cross-team dependencies.

## Gate Rule
Build starts only when decision is PASS.
