# Evidence Convention

This convention standardizes where proof is stored for each work item.

## Verification Evidence

Store in issue comment under heading:

- Verification Summary

Must include:

- command set used
- PASS/FAIL per command
- key failure notes if any

## QA Evidence

Store in file:

- docs/qa-report-issue-<id>.md

Must include:

- scenario checklist
- defects found
- final QA PASS/FAIL

## Release Evidence

Store in PR description.

Must include:

- what changed
- why changed
- risks and rollback

## Closure Evidence

Store in final issue closure comment.

Must include links to:

- ESS file
- PR
- verification summary
- QA report

## Rule

If one link is missing, issue cannot be marked Done.
