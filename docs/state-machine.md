# State Machine (Docs 2)

## Primary states
Backlog -> Ready -> In Build -> In Verification -> In QA -> Ready to Merge -> Done

## Exception state
Any active state -> Blocked

## Loop Safety Policy
- Max retries per gate = 3
- On third fail, set State = Blocked
- Record blocker cause and next action in issue comments
- Escalate according to escalation runbook before resuming

## Transition notes
- Do not skip gates
- Capture evidence at every gate decision
- Resume from failed gate after fix, not from start unless root cause requires it
