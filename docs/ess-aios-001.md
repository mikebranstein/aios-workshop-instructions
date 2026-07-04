# ESS - AIOS-001 Sync Project State From PR Events

## 1) Metadata
- Work item ID: AIOS-001
- Title: Sync Project State From PR Events
- Repo: <your-repo>
- Owner: Mike
- Risk level: Medium
- Target milestone: AIOS Bootstrap Sprint

## 2) Objective
- Desired end state: PR lifecycle events automatically keep issue/project state accurate and post evidence summaries.

## 3) Constraints
- Technical constraints: Use GitHub Actions only; no external service required.
- Policy/security constraints: Use least-privilege token permissions.
- Performance constraints: Workflow should complete under 2 minutes on typical events.

## 4) Acceptance Criteria (Pass/Fail)
- AC1: On PR opened with linked issue, workflow posts issue comment "State transition candidate: In Build".
- AC2: On check suite completion success, workflow posts gate summary with PASS/FAIL per check.
- AC3: On PR merge, workflow posts closure summary with links to PR and checks.
- AC4: On failure to update metadata, workflow exits with clear error output.

## 5) Implementation Plan
- Task 1: Add .github/workflows/state-transition.yml with pull_request and check_suite triggers.
- Task 2: Implement linked issue extraction from PR body/title.
- Task 3: Post transition summary comments to linked issue.
- Task 4: Add robust logging and error branches for missing issue links.

## 6) Verification Plan
- Build command: n/a (workflow-level change)
- Test command: Use manual dry-run with test issue + PR flow
- Static checks: Validate workflow syntax in PR checks
- Expected results: Workflow runs on PR opened/check suite/merged and posts expected comments.

## 7) QA Plan
- Scenario 1: PR opened with valid issue link -> summary comment appears.
- Scenario 2: PR opened without issue link -> warning comment appears, no state update attempted.
- Regression scope: Existing CI workflow unaffected.

## 8) Rollback Plan
- Trigger condition: Workflow causes noisy/incorrect issue updates.
- Rollback actions: Revert workflow file commit and disable workflow in GitHub Actions.

## 9) Closure Evidence
- PR link:
- CI/workflow results:
- QA report:
- Issue closure comment link:
