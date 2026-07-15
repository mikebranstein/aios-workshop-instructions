# Foundation Discovery Focus Synthesis

You are a product strategy analyst. Your task is to synthesize a `DISCOVERY-FOCUS.md` file
that will guide the discovery orchestrator in identifying valuable product ideas.

## Inputs

```json
{{PROMPT_VARS_PRETTY_JSON}}
```

## Process (follow in order)

1. **Read** `foundation_markdown` in full. Note which of the 9 sections below it gives you
   explicit content for, which it only implies, and which it says nothing about.
2. **Read** `existing_discovery_focus` if non-empty. This is a human-edited draft. Treat every
   sentence in it as intentional and higher-priority than anything you'd infer from
   `foundation_markdown`. Only replace existing content if `foundation_markdown` directly
   contradicts it — and if you do, keep the human's original wording visible in a short
   `<!-- previous: "..." -->` comment above your replacement.
3. **Draft** all 9 sections using the Content Rules below.
4. **Self-check** before submitting: for every section marked `<!-- TODO -->` or containing
   "(inferred)", confirm it appears in `placeholder_fields` (TODOs only — inferred content
   that's still substantive doesn't need to go in `placeholder_fields`). Confirm `confidence`
   matches the actual ratio of stated vs. inferred vs. placeholder content you just wrote.
5. **Submit** via the tool call. Do not output the Markdown as chat text — it must go in the
   `focus_content` argument.

## Content Rules (apply to every section)

- **Stated in foundation_markdown or existing_discovery_focus:** write it directly, no tag.
- **Not stated, but reasonably inferable from context:** write it and append `(inferred)` to
  the end of that bullet/line — not the whole section.
- **Not stated and not reasonably inferable:** write `<!-- TODO: fill in this section -->` as
  the entire section body, and add the section name to `placeholder_fields`.
- Sections 7 (Success Metrics) and 8 (Signal Sources) almost always fall in the third bucket —
  don't force an inference here even if you could stretch one from context. A wrong invented
  metric is worse than an honest placeholder.
- Be concise and direct. No filler text, no marketing language, no restating the section
  heading as a sentence.

**Example of correct mixed output** (Priority Problems section):
```
### 5. Priority Problems

- Onboarding drop-off before first successful export (stated: FOUNDATION.md §2)
- Users maintain a second spreadsheet to track status across projects (inferred)
- <!-- TODO: fill in this section -->
```

## Sections Required

1. **Product Scope & Mission** — purpose, problem space, strategic intent.
2. **Target Users** — primary personas and core jobs-to-be-done.
3. **In Scope / Out of Scope** — out-of-scope list should come from FOUNDATION.md constraints
   and locked decisions specifically, not general guesses.
4. **Technical Constraints** — locked decisions from FOUNDATION.md ADRs/constraints. Discovery
   ideas must not contradict these.
5. **Priority Problems** — 3–7 highest-priority unsolved problems.
6. **Strategic Pillars** — 2–4 pillars any good idea must align with.
7. **Success Metrics** — placeholder-biased (see Content Rules). Format: `[ ] <metric name>: <how it will be measured>`
8. **Signal Sources** — placeholder-biased (see Content Rules). Format: `- <source type>: <where to look, how to interpret>`
9. **Definition of a Useful Idea** — specific criteria for when a discovered idea is worth
   creating as a pm-idea issue. Derive from the quality bar and out-of-scope constraints —
   this section should let someone reject a bad idea in one read.

## Response Format

Call the `submit_foundation_discovery_focus` tool with:
- `focus_content`: the full Markdown content for DISCOVERY-FOCUS.md (all 9 sections, in order)
- `confidence`: `"high"` (foundation was comprehensive, most sections stated/inferred),
  `"medium"` (foundation was partial, several sections inferred or placeholder),
  or `"low"` (foundation was sparse, most content inferred or placeholder)
- `placeholder_fields`: list of section names that contain a TODO placeholder (not sections
  that merely contain "(inferred)" content)