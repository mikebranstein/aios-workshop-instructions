# User Research & Personas: Documentation and Persistence

This reference defines how to systematically document, store, and access user research artifacts—personas, journey maps, and research findings—so they persist across quarters and inform ongoing strategic decisions.

---

## Research Artifact Storage Structure

### GitHub Wiki as Your Research Hub (Recommended)

Create a dedicated **Research Wiki directly in your GitHub repository** using GitHub's built-in Wiki feature.

Use this folder structure:

```
Research Hub
├── Personas (Updated Quarterly)
│   ├── Facility Manager Frank
│   ├── CFO Caroline
│   └── Technician Tyler
│
├── Journey Maps (Segment-Based)
│   ├── Facility Manager Journey
│   ├── CFO Journey
│   └── Technician Journey
│
├── Interview Transcripts & Findings
│   ├── Q2 2026 Research Cycle
│   ├── Q3 2026 Research Cycle
│   └── Q1 2025 Research Cycle
│
├── Research-to-Decision Index
│   └── Which customer problems fuel which opportunities?
│
└── Quarterly Research Summary
    ├── Q2 2026 Summary
    └── Q3 2026 Summary
```

---

## Persona Template

Use this template for every persona. Update quarterly as interview data changes.

```markdown
# Persona: [Name]
**Archetype:** [One-line description]
**Last Updated:** Q3 2026 (12 new interviews, total N=27)

## Primary Job to Be Done
"I want to [action] so that [outcome], because [constraint]."

## Goals & Success Metrics
- Goal 1: [What are they trying to achieve?]
- Goal 2:

## Frustrations & Pain Points
- Friction 1: [What makes their job harder?]
- Friction 2:
- Churn Signal: [What made past users leave?]

## Key Quotes from Interviews
- "[Quote]" — [Customer Name, Interview Date]

## Interview Sources
- Q2 2026: 8 interviews
- Q3 2026: 5 interviews
- Cumulative: 27 interviews

## Connected Strategic Opportunities
- [Equipment Loss Prevention](issue-link)
- [Real-Time GPS Integration](issue-link)
```

---

## Quarterly Update Process

**Every quarter, follow this 5-step cycle:**

1. **Conduct 15-20 New Interviews** — 1 per week
2. **Synthesize Findings** — Create Quarterly Summary page
3. **Update Personas** — Incorporate new interview data
4. **Revise Journey Maps** — Update friction points, metrics, opportunities
5. **Update Research-to-Decision Index** — Link opportunities to research

---

## Continuous Wiki Maintenance

**After Every Interview (Same Day):**
- Add entry to Interview Transcripts page
- Extract 1-2 quotes to relevant persona
- Update journey map if new friction discovered

**Weekly (After 3-4 Interviews):**
- Scan for emerging patterns (3+ mentions = signal)
- Increment persona interview counts
- Update journey map friction points

**Quarterly (Full Synthesis):**
- Execute full 5-step update process
- Synthesize all quarterly interviews into themes
- Promote patterns with 5+ mentions to "STRONG_SIGNAL"

---

## Linking Research to Strategic Decisions

Every strategic opportunity must reference its research basis:

```markdown
## Research Basis
- **Persona(s):** Facility Manager Frank
- **Journey Stage:** Problem Resolution
- **Interview Count:** 8/12 interviews
- **Key Quote:** "[Quote]"
- **Link to Research:** [Wiki: Facility Manager Journey]
- **Churn Signal?** Yes — 15% field teams churned
```

---

## Tool Recommendations

### Primary: GitHub Wiki ✅

**Why GitHub Wiki?**
- Integrated with your GitHub repository
- Version-controlled (audit trail)
- Free for all teams
- Markdown-based
- Teams already familiar with GitHub
- Links directly from issues to research

**Setup:**
1. Go to your GitHub repository
2. Settings → Features → Check **Wiki**
3. Click **Wiki** tab → Create pages

---

## Implementation Checklist

- [ ] Create GitHub Wiki for research hub
- [ ] Build persona templates (minimum 3 personas)
- [ ] Conduct initial 15+ customer interviews
- [ ] Update personas with interview data
- [ ] Create journey maps for each segment
- [ ] Build Research-to-Decision Index
- [ ] Link first strategic-opportunity GitHub issue to research
- [ ] Schedule weekly wiki maintenance
- [ ] Quarterly: Full synthesis sprint (5-step process)
- [ ] Document evolution of personas over time
