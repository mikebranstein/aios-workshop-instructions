# Agentic OS Training for GitHub Copilot

This workspace is a hands-on workshop, not a theory guide. You can follow it line by line and build a working multi-agent coding system.

## Repo Topology

This workshop uses a two-repo default model, with an optional third repo.

1. Repo 1: Workshop Instructions Repo
- Purpose: training modules, templates, and workshop guidance.
- In this workspace: this repository.

2. Repo 2: Learner Delivery Repo
- Purpose: real issues, code changes, PRs, and state transitions during the workshop.
- This is where learners run the delivery flow.

3. Repo 3: Framework Repo (optional)
- Purpose: package a reusable Agentic OS framework separate from project delivery code.
- Not required for this workshop path.

## Fast Start

If you want to start immediately, open and follow these in order:

1. docs/README.md
2. docs/00-module-0-shared-app-foundation.md
3. docs/01-module-1-tiny-end-to-end-run.md
4. docs/02-module-2-intake-quality-template.md
5. docs/03-module-3-first-ess.md

Module 0 establishes one fixed starter app baseline so all later modules run on the same project context.

## Full Reading Order

1. docs/README.md
2. docs/00-module-0-shared-app-foundation.md
3. docs/01-module-1-tiny-end-to-end-run.md
4. docs/02-module-2-intake-quality-template.md
5. docs/03-module-3-first-ess.md
6. docs/04-module-4-objective-gates.md
7. docs/05-module-5-loop-safety-and-escalation.md
8. docs/06-module-6-first-intake-skill-contract.md
9. docs/07-module-7-design-build-skill-contracts.md
10. docs/08-module-8-first-agentic-os-run.md
11. docs/09-module-9-github-state-source-of-truth.md (coming soon)
12. docs/10-module-10-add-verification-to-agentic-os.md (coming soon)
13. docs/11-module-11-add-qa-to-agentic-os.md (coming soon)
14. docs/12-module-12-policy-boundaries-and-approvals.md (coming soon)
15. docs/13-module-13-capstone-full-system-run.md (coming soon)

Legacy versions of modules 9–12 are archived in `docs/legacy/` for reference.

## What You Will Build

By the end, you will have a repeatable system that:

- Picks up a GitHub work item
- Creates a design and execution plan
- Implements code in a branch
- Runs verification and QA gates
- Opens a PR with evidence
- Merges and closes the work item with an audit trail

## Important Constraint

This training is intentionally designed for a GitHub Copilot-only setup in VS Code plus normal GitHub features (Issues, PRs, Actions).

The default command examples are now .NET-first. You can adapt later if your stack changes.

## Practical Rule

At each step, you should have either:

- a new file created,
- a command run,
- or an issue/PR field updated.

If a step does not produce one of those, treat it as incomplete.

