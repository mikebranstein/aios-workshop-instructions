# Autonomy Boundaries

Use this file to prevent unsafe automation.

## Auto-Allowed Actions

- Read issue and project metadata
- Generate ESS draft and design notes
- Propose code changes in a feature branch
- Run build/test/verification commands
- Post verification and QA summaries
- Suggest state transition

## Human-Required Actions

- Approve medium/high-risk design gate
- Approve high-risk merge gate
- Merge high-risk PR
- Close high-risk issue
- Accept security-risk exceptions

## Never Auto-Allowed

- Direct push to protected main branch
- Disable required checks
- Close issue with missing evidence links
