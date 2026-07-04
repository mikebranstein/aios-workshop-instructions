# 19 - Curriculum Map and File Intent

This document explains what every major file is for.

You asked for depth and no hidden gaps. This map prevents ambiguity by showing which files teach concepts, which files execute workflows, and which files are operational templates.

## How to use this map iteratively

This map builds on all prior modules by connecting concept files to execution files and artifact files.

Do not treat this as a static index.

Use it at the start of each session to decide what to learn next, what to execute now, and what artifact to validate before moving on.

## How to read this map

Three file types are used intentionally:

1. Teaching guides
- explain concepts and reasoning

2. Execution runbooks
- provide step-by-step actions and pass gates

3. Operational artifacts
- templates, checklists, and scoring tools used during execution

Short files are acceptable only when they are operational artifacts.

## Teaching guides

- docs/01-overview.md: program orientation, outcomes, how to use the workshop
- docs/02-foundations.md: foundational concepts with labs and practical interpretation
- docs/03-reference-architecture.md: architecture decisions and control model
- docs/04-github-as-state.md: state and memory operating model
- docs/07-ess-guide.md: ESS concept and creation walkthrough
- docs/09-implementation-blueprint.md: phased deployment strategy
- docs/12-dotnet-command-pack.md: .NET verification rationale and command standards
- docs/13-github-projects-click-by-click.md: GitHub Projects as AIOS state system
- docs/14-what-you-are-missing.md: reliability control diagnostics
- docs/15-industry-synthesis-agentic-os.md: frontier guidance translated to your implementation

## Execution runbooks

- docs/05-training-regimen.md: multi-week calendar and progression logic
- docs/06-build-first-vertical-slice.md: exact issue-to-close runbook
- docs/10-create-your-first-skill.md: first skill creation and validation
- docs/16-zero-to-hero-live-workshop.md: primary scripted training path

## Operational artifacts

- docs/11-first-7-days-checklist.md: compressed launch checklist
- docs/18-live-lab-answer-keys.md: quick correctness checks
- docs/17-copy-paste-exercise-pack.md: reusable prompts and templates
- docs/19-capstone-evaluator-rubric.md: objective graduation scoring
- docs/20-lab-file-by-file-solutions.md: exact file solution examples

## Governance and policy artifacts

- docs/gates.md
- docs/state-machine.md
- docs/policy-risk-and-approvals.md
- docs/autonomy-boundaries.md
- docs/evidence-convention.md
- docs/postmortem-template.md
- docs/aios-definition-of-done.md

These are intentionally concise because they are policy controls and should stay precise.

## Work item examples

- docs/work-items/aios-001-project-state-sync.md
- docs/ess-aios-001.md

These are reference implementations for bootstrapping AIOS on itself.

## Recommended reading and doing order

1. Read docs/01-overview.md
2. Read docs/02-foundations.md
3. Read docs/15-industry-synthesis-agentic-os.md
4. Execute docs/16-zero-to-hero-live-workshop.md with docs/17-copy-paste-exercise-pack.md
5. Validate using docs/18-live-lab-answer-keys.md and docs/20-lab-file-by-file-solutions.md
6. Score with docs/19-capstone-evaluator-rubric.md

## Completion confidence test

You can consider the curriculum clear enough when you can answer all without searching externally:

1. What is Agentic OS in this workshop
2. What is your canonical state source
3. Why are retry caps required
4. What evidence is mandatory at closure
5. Which pattern is your default for feature delivery and why

If any answer is unclear, revisit the corresponding teaching guide before continuing execution.

## Next step

After this map check, resume execution in 14 with 16 and validate every gate output in 15.
