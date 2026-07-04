# Quality Gates

## Design Gate
- Required inputs: Completed issue template, ESS draft sections 1-7, risk level assigned.
- Pass criteria: Design is feasible, scope bounded, risks documented with mitigations.
- Evidence: Link to ESS and design approval comment.
- Owner: Design Agent + Human approver.

## Verification Gate
- Required inputs: Code changes and test updates.
- Pass criteria: Build, tests, and lint all pass.
- Evidence: CI/check logs and verification summary comment.
- Owner: Verification Agent.

## QA Gate
- Required inputs: Verified build and completed QA checklist.
- Pass criteria: Acceptance scenarios pass; no unresolved blocking defects.
- Evidence: QA report document and defect list.
- Owner: QA Agent.

## Merge Gate
- Required inputs: Design/Verification/QA gates passed.
- Pass criteria: Required reviewers approved; rollback plan present.
- Evidence: PR review approvals and release summary.
- Owner: Release Agent + Human approver.
