# AIOS-001 - Sync Project State From PR Events

## Problem Statement

State tracking is currently manual. Work items can drift between real delivery status and Project board status.

## Scope

Implement a GitHub Action that updates Project State and issue labels when PR events occur.

In scope:

- PR opened -> State = In Build
- Checks pass -> State = In Verification or In QA (based on policy)
- PR merged -> State = Done
- Summary comment posted on issue

## Non-Goals

- Full autonomous merge approval
- Security scanning policy changes
- Multi-repo orchestration

## Acceptance Criteria

- [ ] When a PR linked to an issue is opened, workflow posts issue comment and updates state metadata.
- [ ] When required checks pass, workflow posts gate summary and recommends next gate.
- [ ] When PR is merged, issue receives closure summary and state is moved to Done.
- [ ] Workflow failures are visible in Actions with clear error messaging.

## Technical Notes

- Use actions/github-script or gh api for metadata updates.
- Read policy from docs/policy-risk-and-approvals.md.

## Risks

- GitHub token permissions may block Project field updates.
- Linked issue detection may be inconsistent if PR does not reference issue.

## Test Scenarios

1. Open PR with "Closes #<id>" and verify state/label changes.
2. Complete checks and verify summary comment format.
3. Merge PR and verify closure evidence comment is posted.

## Done Means

- Workflow file merged
- One test issue run end-to-end successfully
- Evidence links posted in closure summary
