"""Parser for templates-v2/orchestration/routing-registry.md.

Extracts every declared (source_stage, decision) → next_stage triplet from
the markdown table format used by the registry.

Table format matched:
    | Decision | Condition | Next Stage |
    |----------|-----------|------------|
    | SOME_DECISION | ... | some-next-stage |
"""
import re
from pathlib import Path
from typing import Dict, List, Tuple


# Matches lines like: | DECISION | any text | next-stage |
_ROW_RE = re.compile(r"^\|\s*([A-Za-z_][A-Za-z0-9_ ]*?)\s*\|\s*[^|]*\|\s*([a-z0-9:_\-]+)\s*\|")
# Matches lines like: ### Stage: some-stage-name
_STAGE_RE = re.compile(r"^#{2,4}\s+Stages?:\s*([a-z0-9,_\- ()]+)", re.IGNORECASE)
# Separator row check (| --- | ... |)
_SEP_RE = re.compile(r"^\|[\s\-|]+\|$")


RegistryEntry = Tuple[str, str, str]  # (source_stage, decision, next_stage)


def parse_routing_registry(path: Path) -> List[RegistryEntry]:
    """Parse *path* and return all routing entries as (source, decision, next) tuples."""
    entries: List[RegistryEntry] = []
    current_stages: List[str] = []

    with path.open(encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.rstrip()

            stage_match = _STAGE_RE.match(line)
            if stage_match:
                # Parse comma-separated stage names; strip parenthetical notes
                raw_stages = stage_match.group(1)
                current_stages = [
                    s.strip().split("(")[0].strip()
                    for s in raw_stages.split(",")
                    if s.strip() and not re.fullmatch(r"[\s\-]+", s.strip())
                ]
                continue

            if _SEP_RE.match(line):
                continue

            row_match = _ROW_RE.match(line)
            if row_match and current_stages:
                decision = row_match.group(1).strip()
                next_stage = row_match.group(2).strip()
                # Skip header row
                if decision.lower() in ("decision", "fitness outcome"):
                    continue
                for stage in current_stages:
                    if stage:
                        entries.append((stage, decision, next_stage))

    return entries


def entries_by_loop(entries: List[RegistryEntry]) -> Dict[str, List[RegistryEntry]]:
    """Group entries by a heuristic loop prefix derived from the stage name."""
    loop_prefixes = {
        "foundation": "foundation",
        "signal": "discovery",
        "pm-idea": "pm",
        "pm-provisional": "pm",
        "pm-finalizing": "pm",
        "pm-opportunity": "pm",
        "pm-blocked": "pm",
        "pm-escalated": "pm",
        "strategic-opportunity": "po",
        "feature-requests-created": "po",
        "po-deferred": "po",
        "po-rejected": "po",
        "feature-request": "dev",
        "intake": "dev",
        "intake-review": "dev",
        "design-approved": "dev",
        "qa-testing": "dev",
        "policy-approval": "dev",
        "released": "dev",
        "feature-blocked": "dev",
        "arch-review": "arch_review",
        "arch-refactor": "arch_review",
        "architecture-debt": "debt",
        "debt-triaged": "debt",
        "debt-scheduled": "debt",
        "debt-resolved": "debt",
        "debt-deferred": "debt",
        "candidate-deferred": "discovery",
        "dropped": "discovery",
        "pm-idea-created": "discovery",
    }

    grouped: Dict[str, List[RegistryEntry]] = {}
    for src, decision, nxt in entries:
        loop = "unknown"
        for prefix, loop_name in loop_prefixes.items():
            if src.startswith(prefix):
                loop = loop_name
                break
        grouped.setdefault(loop, []).append((src, decision, nxt))
    return grouped
