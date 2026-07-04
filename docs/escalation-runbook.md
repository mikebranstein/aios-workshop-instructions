# Escalation Runbook (Docs 2)

## Trigger conditions
Escalate when any is true:
- same gate fails 3 retries
- required approval unavailable
- blocker unresolved beyond SLA

## Owner map
- Intake blocker: issue owner
- Design blocker: design owner
- Verification blocker: build owner
- QA blocker: QA owner
- Merge blocker: repository admin or release owner

## Procedure
1. Set State = Blocked
2. Record escalation comment with gate, retries, blocker cause, requested owner, deadline
3. Notify owner
4. Track response and follow up on SLA miss

## SLA guidance
- Standard: 24 hours
- High risk: 8 business hours

## Resolution
1. Record decision and evidence
2. Move item back to prior active state
3. Resume from failed gate
