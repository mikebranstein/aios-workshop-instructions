# Escalation Runbook

Use this runbook when a gate cannot be resolved inside normal retry limits.

## How this builds on the workshop

Gate loops and blocked-state handling are defined in foundations and state-machine.

This file gives exact who/when/how escalation steps.

## Escalation triggers

Escalate when any is true:

- same gate fails 3 full retries
- design requires breaking API or cross-team dependency
- high-risk change lacks required approver
- blocker remains unresolved for 24 hours
- CI cannot run due to infrastructure or permission issue

## Escalation owner map

- Intake gate blocker: Product owner or issue author
- Design gate blocker: Tech lead or architecture owner
- Verification gate blocker: Build owner and CI maintainer
- QA gate blocker: QA owner
- Merge blocker: Repository admin or release owner

## Escalation procedure

1. Set State = Blocked.
2. Set Owner Agent = Human Review.
3. Add issue comment using template below.
4. Mention responsible owner.
5. Record expected response deadline.

Escalation comment template:

```markdown
## Escalation Notice
- Gate: <Design|Verification|QA|Merge>
- Retry count: 3/3
- Root cause summary:
- Decision required:
- Requested owner: @<name>
- Response deadline: <YYYY-MM-DD HH:mm TZ>
- Interim state: Blocked
```

## SLA and timeout

- Standard SLA: 24 hours
- High-risk SLA: 8 business hours

If SLA is missed:

1. Add follow-up escalation comment.
2. Notify backup owner.
3. Keep item Blocked until decision is recorded.

## Resolution procedure

When escalation is resolved:

1. Add Decision Log comment with final decision.
2. Link evidence or approved exception.
3. Move State back to prior active state.
4. Resume from failed gate only.

## Checkpoint

Every escalation must have:

- trigger condition
- owner mention
- deadline
- explicit resolution comment

## Next step

Return to the relevant runbook step in 05 or 14 and continue execution.