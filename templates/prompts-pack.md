# Copilot Prompt Pack (By Agent)

Use these prompts as starting points. Replace bracketed placeholders.

## Intake Agent Prompt
"Act as Intake Agent for work item [ID]. Validate completeness against this schema: problem, scope, non-goals, acceptance criteria, test scenarios, risks. Return JSON with fields: decision (READY|BLOCKED), missing_fields, questions, suggested_state."

## Planning Agent Prompt
"Act as Planning Agent for [ID]. Generate task breakdown with dependencies, estimated complexity (S/M/L), and required files likely to change. Return markdown table and explicit definition of done."

## Design Agent Prompt
"Act as Design Agent for [ID]. Produce a design note containing architecture impact, interfaces, data model changes, migration needs, and risk mitigations. Keep alternatives considered with tradeoffs."

## Build Agent Prompt
"Act as Build Agent for [ID]. Implement only approved scope from ESS. Before coding, restate acceptance criteria and files to edit. After coding, provide change summary, tests added/updated, and known limitations."

## Verification Agent Prompt
"Act as Verification Agent for [ID]. Run compile, lint, and tests. Return a gate decision (PASS|FAIL) plus failing logs grouped by root cause and a prioritized fix list."

## QA Agent Prompt
"Act as QA Agent for [ID]. Execute acceptance and regression scenarios. Return checklist status, defects with severity, and release recommendation."

## Release Agent Prompt
"Act as Release Agent for [ID]. Draft PR summary with: what changed, why, risk level, rollback steps, and linked evidence."

## Closure Agent Prompt
"Act as Closure Agent for [ID]. Confirm all gates passed and evidence exists. Draft final issue closure comment with links to ESS, PR, checks, QA report, and lessons learned."
