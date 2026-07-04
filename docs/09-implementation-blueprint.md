# 09 - Implementation Blueprint (From Workshop To Real System)

This file tells you how to convert training artifacts into an operational AIOS.

It is intentionally practical: each step has prerequisites, execution steps, failure signals, and exit gates.

## Before You Start

The workshop proves you can run one issue correctly.

This blueprint shows how to scale that behavior safely across weeks without losing control quality.

## How to apply this file

Pick your current operating position first, then execute only the matching step checklist.

Do not start Step 2 until Step 1 exit conditions are true on real issues.

## Checkpoint before step changes

Before moving to the next step, verify current step exit criteria on real issue evidence, not estimates.

## Why step-by-step implementation matters

Most teams fail by automating too early.

When you automate an unstable process, you do not get scale. You get fast failure.

This blueprint enforces a stable progression:

- first prove correctness manually
- then automate repetitive mechanics
- then introduce policy-aware autonomy

## Step 1 - Manual orchestration first

Duration target: Week 1 to Week 2

Primary objective:

- prove your process is correct before introducing automation

Prerequisites:

- issue template is active
- skill files exist
- ESS and QA templates exist
- project fields are configured

Execution pattern:

1. run one issue end-to-end manually
2. update state fields by hand at each gate
3. record Decision Log entries at every gate decision
4. enforce retry cap on failed gates

What success looks like:

- two completed issues
- no skipped gate
- complete closure evidence on both

Failure signals:

- frequent state drift between issue and project
- unclear gate pass criteria
- closure without full evidence links

If failure signals appear, stop and fix process docs before Step 2.

## Step 2 - Lightweight automation

Duration target: Week 3 to Week 4

Primary objective:

- remove repetitive coordination work while preserving control

Automate these first:

1. issue template enforcement
2. PR event based state suggestions
3. check summary comments posted to issue

Keep manual for now:

- medium and high risk approvals
- policy exception handling

What success looks like:

- at least 80 percent of expected state updates and comments are auto-generated correctly

Failure signals:

- incorrect transitions triggered by missing context
- noisy duplicate comments
- automation bypasses policy boundaries

If automation quality is low, simplify transition rules before adding new rules.

## Step 3 - Policy-driven orchestration

Duration target: Week 5 to Week 6

Primary objective:

- enforce risk-aware decision logic and improve consistency across issues

Add policy enforcement for:

- required gates by risk level
- required reviewers by risk level
- explicit escalation on repeated gate failure

What success looks like:

- three consecutive completed issues
- repeatable cycle time
- visible reduction in manual interventions

Failure signals:

- policy exceptions become common
- many blocked items with no postmortem follow-up
- cycle time variance increases with no clear root cause

If these appear, improve observability before increasing autonomy.

## Capability progression map

Use this map to understand which capabilities must be stable before moving on.

Step 1 capabilities:

- deterministic state transitions
- objective gate definitions
- complete evidence convention

Step 2 capabilities:

- reliable CI checks
- automated lifecycle summaries
- project state sync from PR events

Step 3 capabilities:

- risk-policy enforcement
- selective autonomous transitions
- controlled escalation and recovery loops

Do not move to the next step until the current step is stable for at least two real issues.

## Recommended metrics and interpretation

Lead time from Ready to Done:

- measures flow efficiency

Gate failure rate:

- measures process and quality stability

Rework rate from QA defects:

- measures design and build quality upstream

Manual touch count:

- measures orchestration maturity

Mean time to recovery after gate fail:

- measures operational resilience

Metric guidance:

- optimize for lower variance before lower average

Stable systems are easier to improve than noisy systems.

## Risk policy baseline

Low risk:

- automate transitions after checks pass

Medium risk:

- require design approval and one reviewer

High risk:

- require design approval, two reviewers, and rollback rehearsal evidence

When risk is uncertain, default to the higher level.

## Operational rhythm

Daily operations:

- inspect active items by State, Next Gate, and Owner Agent

Weekly operations:

- review failed gates and adjust contracts or prompts

Biweekly operations:

- reduce overlap between agent responsibilities
- remove low-value automation rules

Monthly operations:

- run one full process audit on a recently closed issue

## Blueprint execution checklist

Before declaring your AIOS operational, confirm all are true:

1. branch protection and required checks are active
2. two manual issues completed with full evidence
3. transition automation works for PR open, check complete, and merge
4. retry and escalation policy is enforced
5. closure gate rejects missing evidence links

If one item is false, you are still in implementation mode, not operational mode.

## Next step

Continue to docs/10-create-your-first-skill.md.
