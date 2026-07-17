# Foundation Research Planning

You are planning research issue spawning for the foundation process.

## Goal

Produce a `research_areas` list that covers **every decision-pack section that is
marked `<!-- TODO: needs research -->`** in `docs/foundation-decision-pack.md`.

The decision pack has up to 13 sections that require research (2.1–2.8 and 3.1–3.5).
You must spawn a research area for each TODO section, even if the answer seems obvious.
The purpose is to populate every section with a sourced decision — not just to flag
ambiguous items.

Each research area becomes one GitHub sub-issue and one research worker task.
**Cap at 15 areas maximum** (the hard limit is enforced downstream but keep it lean).
Merge areas only when they genuinely resolve the same underlying decision.

## In Scope — Decision Pack Sections

For each row below, spawn a research area if and only if that section is marked TODO
in `foundation_decision_pack`. The "Decision question" column is a starting template —
adapt it to reflect the specific constraints in `FOUNDATION.md`.

| Decision-pack section | Domain | Decision question |
|---|---|---|
| 2.1 Architecture Topology | Architecture topology | Monolith, modular monolith, or service-split — given the team size and expected scale? |
| 2.2 Platform / Runtime | Platform / runtime target | Which platforms and runtime — affects every downstream tech choice? |
| 2.3 Language & Framework Stack | Language / framework | Which language(s) and core frameworks — justified against team skill and constraints? |
| 2.4 State & Persistence | Persistence | How is primary state stored, synced, and backed up? |
| 2.5 Identity / Account / Tenancy | Identity | Is there an account system; for SaaS, single- or multi-tenant? |
| 2.6 API / Integration Contract | API contract | REST/GraphQL/gRPC and blast radius of third-party dependencies? |
| 2.7 CI/CD & Branching Strategy | CI/CD | How are agent-authored changes gated and merged? |
| 2.8 Security & Compliance Baseline | Security & compliance | Regulatory exposure (data, minors, payments, region) that must be handled before launch? |
| 3.1 Agent Autonomy Boundary | Agent autonomy | What architectural decisions may agents make unsupervised vs. must raise an ADR? |
| 3.2 Forbidden Patterns | Forbidden patterns | Which code, dependency, or architecture patterns must agents never introduce? |
| 3.3 Required Conventions | Conventions | Which naming, testing, and documentation conventions must agents follow? |
| 3.4 Dependency Policy | Dependency policy | Which registries are allowed, and what licence constraints apply? |
| 3.5 Migration Policy | Migration policy | How are breaking schema and API changes handled — compatibility windows and process? |

Sections 2.5 and 2.6 may be skipped only when they are explicitly N/A in the decision
pack (e.g. a command-line tool with no API surface has no API contract to define).

## Conditional research areas (spawn only if relevant)

Some areas only apply to specific product types. Check `FOUNDATION.md` and skip if
not applicable:

| Domain | When to spawn |
|---|---|
| Multiplayer / networking model | Games or apps with explicit real-time multi-user features |

## Planning Rules

- **Always spawn for every TODO section** — even when a safe default exists, the research
  worker must document the rationale so the decision pack is fully sourced.
- Adapt the decision question to the project context. Include relevant constraints from
  `FOUNDATION.md` (team size, timeline, platform, budget) in the question.
- Exclude sections that are already locked (non-TODO) in the decision pack.
- Merge two areas into one only when they would be answered by the exact same research
  (e.g., for small projects 2.3 and 2.4 may merge into "stack + persistence stack").
- Research area strings must be concrete decision questions — not topic names.
  - ✅ "Which persistence engine — embedded SQLite vs. PostgreSQL — best fits a 3-person
    team shipping a desktop app in 6 months?"
  - ❌ "Persistence" or "Data storage" (topic only, no question)

## Inputs

You receive these variables in the Context block below:

- `foundation_markdown` — FOUNDATION.md (project type, constraints, locked decisions).
- `foundation_decision_pack` — current content of `docs/foundation-decision-pack.md`
  (read which sections are TODO vs. already locked).
- `issue_number`, `title`, `body` — the foundation tracking issue.

## Output

Call `submit_foundation_research_plan` with:

- `research_areas` (required) — an array of 1–15 strings, each a concrete decision
  **question** tailored to this project. One entry per TODO decision-pack section
  (merged where justified). Strings are deduplicated and capped at 15 downstream.
- `reason` (optional) — a one-line note on why these areas and not others
  (e.g. which sections were already locked and skipped).

Return only the required tool call. Do not output the plan as chat text.

## Context

{{PROMPT_VARS_PRETTY_JSON}}