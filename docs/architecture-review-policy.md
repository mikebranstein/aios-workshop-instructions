# Architecture Review Policy

## Purpose
Define cadence, capacity, and decision boundaries for architecture review and refactor planning.

## Trigger Policy
1. Scheduled review every 24 hours.
2. Event trigger every 3 merged feature requests.
3. Manual trigger allowed for incident-driven checks.

## Capacity Policy
- Reserve 20% default delivery capacity for architecture debt and refactor requests.
- Critical debt can exceed budget only with explicit escalation note.

## Decision Policy
- NO_ACTION: Architecture health stable and fitness functions within tolerance.
- CREATE_REFACTOR_PLAN: Structural improvements needed with bounded execution.
- ESCALATE: Critical uncertainty, cross-team risk, or safety/compliance concern.

## Refactor Scope Rules
- Prefer small independent work items.
- Use branch-by-abstraction for high-impact structural changes.
- Include rollback notes for medium/high-risk refactors.

## Review Output Requirements
- Architecture health summary
- Fitness findings
- Debt ticket updates
- Refactor request links (if any)

## Governance
- Record all major architecture decisions in ADRs under docs/adr.
- Link debt and refactor requests to relevant ADRs when applicable.
