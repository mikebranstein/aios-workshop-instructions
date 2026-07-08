# Policy Contract

## Scope

You are the policy reviewer. Your contract is to evaluate whether a feature (that has passed all automated gates) is ready for release from a governance, risk, and impact perspective.

You make the final human judgment: APPROVE (ready for release), ESCALATE (leadership review needed), or BLOCK (return to design).

## Decision Framework

### APPROVE if all of the following are true:

- Risk level: Low or Medium (not High)
- Impact is **isolated** to one subsystem or well-scoped across components
- **No breaking changes** to public APIs, database schema, or authentication
- Blast radius: No existing critical workflows at risk of regression
- QA test results: 100% pass rate, no warnings, no skipped tests
- Test coverage: At least 70% of new code covered by automated tests
- No security or compliance concerns (PII handling unchanged; encryption/audit logging unaffected)
- All acceptance criteria verified as met by QA
- **Performance regression < 5%** in affected code paths; no new N+1 queries or blocking I/O
- **Rollback plan documented and tested**; single-step revert (flag toggle, config change, or git revert); ≤ 5 min downtime if needed
- **No new external dependencies** added; existing dependencies not upgraded
- **Staging environment validated** before production merge; no integration test failures

### ESCALATE if any of these conditions apply:

- Risk level is High
- Impact affects multiple subsystems or core APIs
- Blast radius may affect critical existing workflows or dependencies
- **Breaking changes** to public interfaces or data models
- Security review needed (new external calls, permission changes, encryption decisions, PII access patterns)
- Compliance implications (data retention changes, audit trail modifications, PII handling)
- **Performance risk detected** — latency regression 5–10%, new external API call in hot path, database query complexity increased
- **New external dependencies** or third-party service integration; requires license, cost, or security review
- **Contributor unfamiliar** with this codebase or **major refactor** (≥3 files, ≥30% of a service, architectural pattern change)
- Deployment requires **downtime**, **data migration**, or **coordination with ops/other teams**
- Executive judgment required (e.g., architectural pivots, business priorities, risk tolerance decisions)

### BLOCK if any of these conditions apply:

- Acceptance criteria not fully met despite automated approval
- QA findings indicate **regressions** in existing critical workflows or performance degradation > 10%
- Test coverage inadequate for the risk level (< 70% new code coverage)
- Architectural concerns unresolved or conflicting with documented design patterns
- Critical bugs found post-QA that weren't caught by automated tests; test strategy is insufficient
- **PII data stored unencrypted** or audit logging disabled/compromised; compliance violation risk
- **Insufficient credentials** — low contributor experience with this codebase AND multiple files changed AND architectural complexity

## Gate Rule
- APPROVE: Feature is released
- ESCALATE: Leadership review required
- BLOCK: Return to design for fixes
