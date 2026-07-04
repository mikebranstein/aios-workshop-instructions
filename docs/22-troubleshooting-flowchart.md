# Troubleshooting Flowchart (Workshop Recovery)

Use this file when a step fails and you are unsure what to do next.

## Before You Start

14 gives the execution path. This file gives recovery routing when a gate fails.

## Decision tree

```mermaid
flowchart TD
    A[Issue is stuck] --> B{Current state?}
    B -->|Backlog or Ready| C[Intake problem]
    B -->|In Design| D[Design problem]
    B -->|In Build or In Verification| E[Build or verification problem]
    B -->|In QA| F[QA problem]
    B -->|Ready to Merge| G[Merge policy problem]
    B -->|Blocked| H[Escalation needed]

    C --> C1[Re-run intake prompt with JSON-only instruction]
    C1 --> C2[Fix missing fields in issue]
    C2 --> Z[Update state and decision log]

    D --> D1[Revise ESS using 00d examples]
    D1 --> D2[Request human design approval]
    D2 --> Z

    E --> E1[Run scripts/verify-windows.ps1]
    E1 --> E2{All commands pass?}
    E2 -->|No| E3[Fix first root cause only]
    E3 --> E1
    E2 -->|Yes| Z

    F --> F1[Fill qa-checklist template fully]
    F1 --> F2{Blocking defect open?}
    F2 -->|Yes| E3
    F2 -->|No| Z

    G --> G1[Check branch protection and required checks]
    G1 --> G2[Ensure PR has ESS, verification, QA links]
    G2 --> Z

    H --> H1[Use escalation-runbook]
    H1 --> Z
```

## Fast recovery commands

Verification reset:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-windows.ps1
```

Check git branch and status:

```powershell
git branch --show-current
git status
```

## Copilot output recovery

If Copilot returns markdown instead of JSON, retry with:

```text
Return raw JSON only. No markdown. Follow schema exactly.
```

If response is still invalid after two retries:

- set State = Blocked
- escalate using escalation-runbook

## Next step

After recovery, resume exactly from the failed gate in 14. Do not skip forward.