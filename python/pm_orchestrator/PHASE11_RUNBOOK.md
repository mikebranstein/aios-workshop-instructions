# PM Pilot Dress Rehearsal and Rollback Pack

## Objective
Run a local dress rehearsal of PM pilot phases with mocked GitHub and mocked Copilot SDK outputs.

## Dress Rehearsal Checklist
1. Run phase test suite with `PYTHONPATH=python`.
2. Run smoke harness `python -c "from pm_orchestrator.smoke import run_pm_phase_smoke; print(run_pm_phase_smoke())"`.
3. Confirm migration scanner flags legacy label queries.
4. Confirm transition log entries are persisted to sqlite.

## Pilot Go-Live Checks
1. Forced tool capability probe passes in runtime startup.
2. PM labels are normalized correctly from live issue labels.
3. No conflict labels are present in PM run_once scans.
4. Circuit breaker routes repeated failures to `PM_NEEDS_HUMAN` with blocked stage metadata.

## Rollback Procedure
1. Disable Python PM runtime invocation.
2. Re-enable existing PM prompt orchestrator workflow.
3. Keep sqlite transition logs and issue comments for audit continuity.
4. Do not delete canonical labels already added; they remain valid history.
5. Log rollback reason in issue comments and local operator notes.
