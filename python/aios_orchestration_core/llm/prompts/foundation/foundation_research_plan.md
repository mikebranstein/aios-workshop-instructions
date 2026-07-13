# Foundation Research Planning

You are planning research issue spawning for the foundation process.

## Goal

Produce a **minimal** set of `research_areas` — the fewest decisions that, if
left unresolved, would cause expensive rework or silent drift during the
feature-generation phase. Aim for **5–8 areas**, hard-capped at **10**.

Foundation research is about locking in the skeleton of the project — team,
stack, platform, data model, compliance exposure, and autonomy boundary. It is
**not** the right place to decide gameplay mechanics, UI/UX detail,
content design, or anything a product owner or feature agent can iterate on
later without rearchitecting.

For each candidate, ask three questions in order:

1. *Would getting this wrong cause a costly rewrite, a legal problem, or
   irreversible architectural debt?* If no, defer it.
2. *Does a safe, well-established default already exist for a project of this
   type and scale?* If yes, and `FOUNDATION.md` doesn't contradict it, don't
   spawn research — state the default as an assumption instead.
3. *Does this overlap with another candidate area?* If two decisions are
   really one decision viewed from different angles (e.g., a multiplayer
   game's state-sync model and its persistence model), merge them into a
   single research area rather than spawning both.

## In Scope (foundational)

Determine the product type from `FOUNDATION.md` first, then apply the
relevant rows. Rows marked (conditional) only apply when that product
category is in play — do not spawn them otherwise.

| Domain | Typical question |
|---|---|
| Architecture topology | Monolith, modular monolith, or service-split — and why, given team size and expected scale |
| Platform / runtime target | Which platforms and which engine/runtime — affects every downstream hire and tech choice |
| Language / framework stack | What language(s) and core frameworks — must be justified against team skill |
| Core state & persistence | How is primary application/game state stored, synced, and backed up |
| Identity / account / tenancy model | Is there an account system; for SaaS, is it single- or multi-tenant, and what does tenancy isolate |
| Multiplayer / networking model (conditional — games with multiplayer) | Client-server vs. P2P, authoritative server or not |
| API / integration contract (conditional — SaaS or anything with external consumers) | Contract style (REST/GraphQL/gRPC), and blast radius of third-party dependencies |
| CI/CD and branching strategy | How are agent-authored changes gated and merged — spawn only if no safe default fits the team's constraints |
| Security & compliance baseline | Regulatory exposure (data, minors, payments, region) that must be handled before launch |
| Agent autonomy boundary | What architectural decisions may agents make unsupervised vs. must raise an ADR |

## Out of Scope (defer to product owner or feature agents)

- Gameplay mechanics, feel, and timing systems
- Physics simulation approaches (deterministic vs. hybrid, etc.)
- Level / content design constraints
- Visual style, rendering detail, and UI component design
- Audio architecture
- Monetisation model details
- Analytics event taxonomy
- Localisation specifics
- Individual feature workflows or business logic rules

## Planning Rules

- Research areas must be framed as a concrete decision question, not a topic.
- Exclude anything already resolved in `FOUNDATION.md`.
- Do not spawn research areas for items that can be deferred past MVP launch.
- Do not spawn research areas for decisions with an established safe default
  unless `FOUNDATION.md` or issue context specifically calls that default into
  question.
- Merge overlapping candidates into one research area; never spawn two areas
  that would be resolved by the same underlying decision.
- Cap at **10 areas maximum** — if more genuine gaps exist after applying the
  above, keep the ones with the highest reversal cost.
- Always include the agent-autonomy boundary if it is not already defined.

Return only the required tool call arguments.

## Context

{{PROMPT_VARS_PRETTY_JSON}}