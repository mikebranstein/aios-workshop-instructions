# State Machine

## States

- Backlog
- Ready
- In Design
- In Build
- In Verification
- In QA
- Ready to Merge
- Done
- Blocked

## Allowed Transitions

- Backlog -> Ready
- Ready -> In Design
- In Design -> In Build
- In Build -> In Verification
- In Verification -> In QA
- In QA -> Ready to Merge
- Ready to Merge -> Done

## Failure/Exception Transitions

- Any active state -> Blocked
- In Verification -> In Build (if checks fail)
- In QA -> In Build (if defects found)
- Blocked -> prior active state (once resolved)

## Retry Semantics

- Max retries per gate = 3.
- One retry means one full gate attempt, not one command.
- Example: Verification retry = restore + build + test + format run as one attempt.
- Retry counter resets only when root cause class changes.
- On retry 3/3 failure: set State = Blocked and Owner Agent = Human Review.

## Gate Ownership

- Ready -> In Design: Intake Agent
- In Design -> In Build: Design + Human approval
- In Build -> In Verification: Build Agent
- In Verification -> In QA: Verification Agent
- In QA -> Ready to Merge: QA Agent
- Ready to Merge -> Done: Release/Closure + Human approval
