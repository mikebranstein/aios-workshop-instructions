# Gates (Docs 2)

## Design Gate
- Required inputs: issue, ESS draft
- Pass criteria: ESS complete, binary ACs, risk mitigations defined
- Fail signals: missing scope, ambiguous ACs, no rollback
- Evidence: ESS link, design decision comment

## Verification Gate
- Required inputs: code changes, test updates
- Pass criteria: restore/build/test pass, no blocking diagnostics
- Fail signals: failed commands, missing evidence, unstable output
- Evidence: command outputs, CI or local verification summary

## QA Gate
- Required inputs: verification pass, QA scenarios
- Pass criteria: scenarios executed, no blocking defects
- Fail signals: critical defects, untested scenarios
- Evidence: QA report link, scenario results

## Merge Gate
- Required inputs: QA pass, policy compliance
- Pass criteria: required approvals and checks complete
- Fail signals: missing approver, missing checks
- Evidence: PR review history, checks summary, closure-ready note
