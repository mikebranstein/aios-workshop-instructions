# GitHub Issue Naming Standard

## Standard Format

```
[type]: Description
```

**Rules:**
- Type is lowercase, in square brackets
- Colon separates type from description
- Single space after colon
- Description is Title Case (capitalize first word and proper nouns)
- Description should be specific and actionable
- No redundant type info in description (don't repeat "[Feature]" in the title text)

---

## Issue Types & Naming Conventions

### Strategic & Planning Issues

| Type | Format | Example | Created By | Label(s) |
|---|---|---|---|---|
| Feature Request | `[feature-request]: Description` | `[feature-request]: Mobile checkout for field teams` | Product Owner | `feature-request` |
| Strategic Opportunity | `[strategic-opportunity]: Description` | `[strategic-opportunity]: Mobile checkout for field teams` | Product Manager | `strategic-opportunity`, `pm-opportunity` |
| PM Idea | `[pm-idea]: Description` | `[pm-idea]: Add mobile checkout capability` | User/PM | `pm-idea` |

### Research & Validation Issues

| Type | Format | Example | Created By | Label(s) |
|---|---|---|---|---|
| Research | `[research]: [Persona/Topic] for [Opportunity]` | `[research]: Field Manager for mobile checkout` | Product Manager | `research:`, `pm-idea-N` |
| Research Follow-On | `[research-follow-on]: [Topic] for #N` | `[research-follow-on]: Safety compliance validation for #42` | Product Manager | `research:`, `pm-idea-N`, `follow-on-research` |

### Development Pipeline Issues

| Type | Format | Example | Created By | Label(s) |
|---|---|---|---|---|
| Escalation (Intake) | `[escalation-intake]: [Reason]` | `[escalation-intake]: Requirements ambiguous - clarity needed` | Intake Agent | `intake-blocked-on-clarity` |
| Escalation (BA) | `[escalation-ba]: [Reason]` | `[escalation-ba]: Acceptance criteria not testable` | BA Agent | `ba-blocked` |
| Escalation (Design) | `[escalation-design]: [Reason]` | `[escalation-design]: Architecture cannot implement design pattern` | Design Agent | `design-blocked` |
| Escalation (Build) | `[escalation-build]: [Reason]` | `[escalation-build]: Cannot implement architectural decision` | Build Agent | `build-blocked` |
| Escalation (Verification) | `[escalation-verification]: [Reason]` | `[escalation-verification]: Code quality failures in critical path` | Verification Agent | `verification-failed` |
| Escalation (QA) | `[escalation-qa]: [Reason]` | `[escalation-qa]: Test coverage incomplete for scenario X` | QA Agent | `test-coverage-incomplete` |
| Escalation (Policy) | `[escalation-policy]: [Reason]` | `[escalation-policy]: Security compliance gate failed - requires leadership decision` | Policy Agent | `policy-escalated` or `policy-blocked` |

### Follow-Up & Remediation Issues

| Type | Format | Example | Created By | Label(s) |
|---|---|---|---|---|
| Mitigation | `[mitigation]: [What] by [Date]` | `[mitigation]: Fix security gap in payment flow by 2026-08-15` | Policy/QA Agent | `mitigation` |
| Dependency Blocker | `[dependency-blocker]: [What blocks what]` | `[dependency-blocker]: Waiting on backend API #89 to deploy` | Development Agent | `blocked-on-dependency` |

---

## Examples by Workflow

### PM-to-PO Workflow

```
1. User creates: [pm-idea]: Add mobile checkout for field teams
2. PM creates: [research]: Field Manager for mobile checkout
3. PM creates: [strategic-opportunity]: Mobile checkout for field teams
4. PO creates: [feature-request]: Mobile checkout for field teams (iOS/Android)
```

### Development Pipeline Workflow

```
1. PO creates: [feature-request]: Mobile checkout for field teams
2. Build flow proceeds normally through Intake, BA, Design, Build...
3. If BA blocks: [escalation-ba]: Acceptance criteria not testable
4. If Design blocks: [escalation-design]: Cannot implement pattern with React constraints
5. If QA finds gaps: [escalation-qa]: Missing test scenarios for offline mode
6. If Policy rejects: [escalation-policy]: Security compliance gap - API token storage
7. If policy-escalated accepted with conditions: [mitigation]: Implement token encryption by sprint N
```

### Manual Unblocking Workflow

```
1. Issue is [escalation-policy]: Security compliance gap
2. Leadership posts: @dev-orchestrator policy-override-approved comment
3. Orchestrator creates (if applicable): [mitigation]: Implement secure token storage by 2026-09-30
```

---

## Implementation Rules

### When Creating Issues in Agents

**All `gh issue create` commands must use standardized format:**

```bash
gh issue create \
  --title "[research]: Field Manager for mobile checkout" \
  --label "research:,pm-idea-123" \
  --body "..."
```

**Not:** `--title "research: Field Manager..."` (lowercase without brackets)  
**Not:** `--title "Research: Field Manager..."` (uppercase without brackets)  
**Not:** `--title "Follow-On Research - Field Manager..."` (hyphens, inconsistent)

### When Documenting Examples

**In all module docs and templates, use standardized format:**

```markdown
Create an issue:
Title: [feature-request]: Mobile checkout for field teams
Body: ...
```

**Not:** `Title: Feature: Mobile checkout...`  
**Not:** `Title: "[Feature Request]" Mobile checkout...`

### When Posting Escalation Comments

**Escalation comments reference the issue type for clarity:**

```
@dev-orchestrator policy-override-approved

This [escalation-policy] is approved for override...
```

---

## Rationale

- **Consistent brackets `[type]`**: Easy for regex/automation to parse
- **Lowercase type**: Matches existing `research:` usage in codebase; easier for machine parsing
- **Colon separator**: Clearly separates type from content
- **No duplication**: Don't repeat the type name in the description
- **Specific, actionable titles**: "What" + optionally "by when"
- **Searchable**: GitHub search `title:[escalation-*]` finds all escalations

---

## Migration Notes

### Existing Instances to Update

1. **Product Manager Agent** (`templates/agents/product-manager.agent.md`):
   - `research: [Persona Name]...` → Already correct, keep as-is (already using `research:` format)
   - `research: Follow-On Critical Validation...` → Change to `[research-follow-on]: ...`

2. **Product Owner Agent** (`templates/agents/product-owner.agent.md`):
   - No issue creation; references only

3. **Development Orchestrator** (`templates/agents/orchestrator.development.agent.md`):
   - Currently creates follow-up issues; should use `[mitigation]: ...` format
   - Escalation references in comments should use standardized format

4. **Documentation** (`docs/` folder):
   - Update all example issues to use standardized format
   - Module 2: `[Feature]: ...` → Keep as `[feature-request]: ...`
   - Module 13: `[PM Idea]: ...` → Keep as `[pm-idea]: ...`
   - Module 13: `[Strategic Opportunity]: ...` → Keep as `[strategic-opportunity]: ...`

5. **Templates** (`templates/` folder):
   - Update all example titles in skill files
   - Update all example titles in agent files

---

## Quick Reference: Type Codes

| Code | Full Type | Usage |
|---|---|---|
| `[feature-request]` | Feature Request | Development backlog items |
| `[strategic-opportunity]` | Strategic Opportunity | PM strategic planning |
| `[pm-idea]` | PM Idea | User/PM input before validation |
| `[research]` | Research | Market/user research work items |
| `[research-follow-on]` | Research Follow-On | Round 2 research (critical validation) |
| `[escalation-*]` | Escalation | Blocked items requiring human decision |
| `[mitigation]` | Mitigation | Risk follow-up work items |
| `[dependency-blocker]` | Dependency Blocker | External blockers |
