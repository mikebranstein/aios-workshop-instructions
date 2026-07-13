#!/usr/bin/env python3
"""
Foundation Orchestrator Runner — Initialize project foundational norms & standards.

Reads FOUNDATION.md from repo root to understand project context, then establishes
foundational decisions through a state machine. Supports recovery from interrupted runs.

Usage:
    # Start or resume foundation establishment
    python foundation_runner.py owner/my-repo
    
    # Force restart (ignore any open foundation issues)
    python foundation_runner.py owner/my-repo --force
    
    # Preview without executing
    python foundation_runner.py owner/my-repo --dry-run

    # Confirm "nothing to do" with more (or fewer) verification passes
    python foundation_runner.py owner/my-repo --verify-passes 3

Behavior:
    The runner processes issues in repeated full passes. It re-pulls issues fresh
    each pass and keeps going while any pass changes foundation state. Once a pass
    makes no changes, it runs --verify-passes additional confirming passes (default
    2) before concluding there is nothing to do, guarding against races where
    research issues close or new work appears between passes.

Environment Variables:
    AIOS_TARGET_REPO      Target GitHub repo (owner/repo format)

Exit Codes:
    0   Success
    1   Invalid arguments or FOUNDATION.md not found
    2   GitHub authentication failed
    3   Orchestration failed
"""

import argparse
import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.llm.adapter_factory import create_adapter
from aios_orchestration_core.github.comment_formatter import build_comment_formatter
from aios_orchestration_core.labels.foundation_labels import (
    FOUNDATION_CANONICAL_LABEL_BY_STATE,
    FOUNDATION_CANONICAL_STATE_LABELS,
    normalize_foundation_state_from_labels,
)
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.repo_context import RepoContext
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.runlog.paths import default_runlog_dir
from aios_orchestration_core.states.foundation import FoundationState
from aios_orchestration_core.wiki.llm_wiki_manager import LLMWikiManager, WikiManagerPolicy, slugify
from foundation_orchestrator.evidence import EvidenceSnapshot, classify_adr_links, classify_wiki_links, extract_links
from foundation_orchestrator.run_once import FoundationRunOnceOrchestrator, FoundationRunRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_LOG_DIR = default_runlog_dir("foundation")


class StubLLMAdapter(JudgmentLLMAdapter):
    """Stub adapter for demonstration."""

    def __init__(self, model: str = "auto"):
        self.model = model

    def invoke_json(self, task_type: str, prompt_vars: dict, model_hint: str = ""):
        stubs = {
            "foundation_research_plan": {
                "research_areas": [
                    "Runtime and Language",
                    "Framework or Engine",
                    "Architecture Style",
                ],
                "reason": "stub planning from FOUNDATION.md",
            },
            "foundation_research": {"decision": "RECOMMEND", "reason": "stub research"},
            "foundation_gate": {"decision": "REVISE_FOUNDATION", "reason": "stub gate review"},
            "foundation_research_worker": {
                "decision": "COMPLETE",
                "summary": "stub linked research complete",
                "wiki_page_title": "Foundation Research Stub",
                "wiki_summary": "Captured alternatives and recommendation.",
                "adr_title": "Use selected architecture baseline",
                "adr_summary": "Documented decision and trade-offs.",
                "next_actions": ["Link outputs to primary foundation issue"],
            },
            "wiki_manager": {
                "decision": "CREATE_PAGE",
                "page_path": "foundation/foundation-research-stub.md",
                "page_content": "# Foundation Research Stub\n\nCaptured alternatives and recommendation.",
                "content_index_summary": "Baseline foundation recommendation captured.",
                "page_moves": [],
                "reason": "stub wiki manager path selection",
            },
        }
        return type("Result", (), {"payload": stubs.get(task_type, {}), "model": self.model})()


class ProgressTracker:
    def __init__(self, path: Path):
        self.path = path
        self.data = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def get(self, issue_number: int) -> dict:
        return self.data.get(str(issue_number), {})

    def set(self, issue_number: int, payload: dict) -> None:
        self.data[str(issue_number)] = payload


def _snapshot_issue(gateway, issue_number: int) -> EvidenceSnapshot:
    issue = gateway.get_issue(issue_number)
    normalized = normalize_foundation_state_from_labels(issue.labels)
    state_label = normalized.state.value if normalized.state else FoundationState.FOUNDATION_NEEDED.value
    comments = gateway.get_issue_comments(issue_number)
    links = extract_links([issue.body, *comments])
    wiki_links = classify_wiki_links(links)
    adr_links = classify_adr_links(links)
    return EvidenceSnapshot(
        state_label=state_label,
        closed_research_count=gateway.count_closed_linked_research_issues(issue_number),
        relevant_links=frozenset(links),
        adr_links=frozenset(adr_links),
        wiki_links=frozenset(wiki_links),
    )


def _snapshot_to_dict(snapshot: EvidenceSnapshot) -> dict:
    return {
        "state_label": snapshot.state_label,
        "closed_research_count": snapshot.closed_research_count,
        "relevant_links": sorted(snapshot.relevant_links),
        "adr_links": sorted(snapshot.adr_links),
        "wiki_links": sorted(snapshot.wiki_links),
    }


def _dict_to_snapshot(payload: dict) -> EvidenceSnapshot:
    return EvidenceSnapshot(
        state_label=payload.get("state_label", FoundationState.FOUNDATION_NEEDED.value),
        closed_research_count=int(payload.get("closed_research_count", 0)),
        relevant_links=frozenset(payload.get("relevant_links", [])),
        adr_links=frozenset(payload.get("adr_links", [])),
        wiki_links=frozenset(payload.get("wiki_links", [])),
    )


def _has_progress(previous: EvidenceSnapshot, current: EvidenceSnapshot) -> bool:
    if previous.state_label != current.state_label:
        return True
    if current.closed_research_count > previous.closed_research_count:
        return True
    if current.relevant_links != previous.relevant_links:
        return True
    return False


def _priority(state: FoundationState | None) -> int:
    if state == FoundationState.FOUNDATION_REVIEW:
        return 0
    if state == FoundationState.FOUNDATION_IN_PROGRESS:
        return 1
    if state == FoundationState.FOUNDATION_NEEDS_HUMAN:
        return 2
    if state == FoundationState.FOUNDATION_NEEDED:
        return 3
    return 9


def _build_unblock_message(gateway, issue_number: int, snapshot: EvidenceSnapshot) -> str:
    open_research = gateway.count_open_linked_research_issues(issue_number)
    missing = []
    if open_research > 0:
        missing.append(f"close {open_research} remaining linked foundation research issue(s)")
    if not snapshot.adr_links:
        missing.append("add at least one ADR link to issue body/comments")
    if not snapshot.wiki_links and not snapshot.adr_links:
        missing.append("add wiki and/or ADR outcome links to issue body/comments")
    if not missing:
        missing.append("add new evidence or comments clarifying unresolved foundational decisions")
    return "Needs-human unblock requirements:\n- " + "\n- ".join(missing)


def _approval_blockers(snapshot: EvidenceSnapshot, open_research: int) -> list[str]:
    blockers = []
    if snapshot.closed_research_count == 0:
        blockers.append("no linked foundation research issues are closed")
    if open_research > 0:
        blockers.append(f"{open_research} linked foundation research issue(s) remain open")
    if not snapshot.adr_links:
        blockers.append("at least one ADR link is required")
    if not snapshot.wiki_links and not snapshot.adr_links:
        blockers.append("wiki/ADR outcome links are missing")
    return blockers


def _next_actions_for_state(state: FoundationState | None, blockers: list[str], open_research: int) -> list[str]:
    if state == FoundationState.FOUNDATION_NEEDED:
        return ["initialize foundation research backlog"]
    if state == FoundationState.FOUNDATION_IN_PROGRESS:
        if open_research > 0:
            return ["complete and close all linked foundation research issues"]
        return ["close at least one linked research issue with concrete evidence links"]
    if state == FoundationState.FOUNDATION_REVIEW:
        if blockers:
            return ["address approval blockers listed below, then rerun gate review"]
        return ["run architecture gate decision (approve/revise/block)"]
    if state == FoundationState.FOUNDATION_NEEDS_HUMAN:
        return ["satisfy unblock requirements and add fresh evidence links before rerun"]
    if state == FoundationState.FOUNDATION_BLOCKED:
        return ["resolve contradictions, then move issue back to foundation:in-progress"]
    if state == FoundationState.FOUNDATION_APPROVED:
        return ["foundation complete; use ADR/wiki outputs as downstream design contract"]
    return ["review issue state and add clarifying context"]


def _post_issue_run_summary(gateway, issue_number: int) -> None:
    issue = gateway.get_issue(issue_number)
    normalized = normalize_foundation_state_from_labels(issue.labels)
    state = normalized.state
    state_label = FOUNDATION_CANONICAL_LABEL_BY_STATE.get(state, "foundation:needed")
    snapshot = _snapshot_issue(gateway, issue_number)
    open_research = gateway.count_open_linked_research_issues(issue_number)
    blockers = _approval_blockers(snapshot, open_research)
    next_actions = _next_actions_for_state(state, blockers, open_research)

    lines = [
        "Foundation run summary:",
        f"- State: {state_label}",
        f"- Linked research: open={open_research}, closed={snapshot.closed_research_count}",
        (
            f"- Evidence links: total={len(snapshot.relevant_links)}, "
            f"wiki={len(snapshot.wiki_links)}, adr={len(snapshot.adr_links)}"
        ),
    ]
    if blockers:
        lines.append("- Blocking items:")
        lines.extend([f"  - {item}" for item in blockers])
    else:
        lines.append("- Blocking items: none")
    lines.append("- Next actions:")
    lines.extend([f"  - {item}" for item in next_actions])
    gateway.post_comment(issue_number, "\n".join(lines))


def _slugify(value: str) -> str:
    return slugify(value, fallback="foundation-research")


def _apply_wiki_manager_plan(
    gateway,
    adapter: JudgmentLLMAdapter,
    foundation_issue_number: int,
    research_issue_number: int,
    research_issue_title: str,
    summary: str,
    wiki_title: str,
    wiki_summary: str,
    adr_link: str,
) -> str:
    desired_slug = _slugify(wiki_title or research_issue_title)
    desired_path = f"foundation/{desired_slug}.md"
    manager = LLMWikiManager(
        WikiManagerPolicy(
            target_root="foundation/",
            required_sections=(
                "Summary",
                "Decision",
                "Alternatives Considered",
                "Evidence",
                "Risks and Mitigations",
                "Traceability",
            ),
        )
    )
    return manager.apply_llm_plan(
        gateway=gateway,
        adapter=adapter,
        task_type="wiki_manager",
        prompt_vars={
            "foundation_issue_number": foundation_issue_number,
            "research_issue_number": research_issue_number,
            "research_issue_title": research_issue_title,
            "research_summary": summary,
            "wiki_title": wiki_title,
            "wiki_summary": wiki_summary,
            "adr_link": adr_link,
        },
        default_page_path=desired_path,
        fallback_page_content=(
            f"# {wiki_title or research_issue_title}\n\n"
            f"{wiki_summary or summary}\n\n"
            f"Source issue: #{research_issue_number}\n"
            f"Related ADR: {adr_link or 'N/A'}\n"
        ),
        index_issue_number=research_issue_number,
        default_index_summary=summary,
        commit_message=f"foundation: update wiki for issue #{research_issue_number}",
    )


def _process_research_issue(
    gateway,
    adapter: JudgmentLLMAdapter,
    foundation_issue_number: int,
    foundation_markdown: str,
    linked_issue,
) -> dict:
    """Process a single research issue and return stats + results for posting."""
    issue = gateway.get_issue(linked_issue.number)
    comments = gateway.get_issue_comments(linked_issue.number)

    # Skip issues that already have a worker decision this pass to avoid
    # posting duplicate NEEDS_MORE_RESEARCH comments on every loop.
    worker_decision_marker = "Foundation research worker decision:"
    if any(worker_decision_marker in c for c in comments):
        return {
            "issue_number": linked_issue.number,
            "decision": "ALREADY_PROCESSED",
            "summary": "Skipped — worker decision already recorded.",
            "worker_comment": None,
            "primary_comment": None,
            "blocked": False,
            "completed": False,
        }

    result = adapter.invoke_json(
        "foundation_research_worker",
        {
            "foundation_issue_number": foundation_issue_number,
            "research_issue_number": linked_issue.number,
            "research_issue_title": issue.title,
            "research_issue_body": issue.body,
            "research_issue_comments": comments,
            "foundation_markdown": foundation_markdown,
        },
    )
    payload = result.payload or {}
    decision = payload.get("decision", "NEEDS_MORE_RESEARCH")
    summary = payload.get("summary", "No summary provided")
    wiki_title = payload.get("wiki_page_title", "").strip()
    wiki_summary = payload.get("wiki_summary", "").strip()
    adr_title = payload.get("adr_title", "").strip()
    adr_summary = payload.get("adr_summary", "").strip()
    next_actions = payload.get("next_actions") or []
    next_actions_text = "\n".join([f"- {item}" for item in next_actions if isinstance(item, str) and item.strip()])
    adr_link = f"docs/adr/{_slugify(adr_title)}.md" if adr_title else ""
    wiki_page_path = ""

    worker_comment_lines = [
        f"Foundation research worker decision: {decision}",
        "",
        f"Summary: {summary}",
    ]
    if wiki_title:
        worker_comment_lines.extend(
            [
                "",
                f"Wiki output: {wiki_title}",
                f"Proposed wiki link: wiki/foundation/{_slugify(wiki_title)}.md",
                f"Wiki summary: {wiki_summary or 'No wiki summary provided.'}",
            ]
        )
    if adr_title:
        worker_comment_lines.extend(
            [
                "",
                f"ADR draft: {adr_title}",
                f"ADR link: {adr_link}",
                f"ADR summary: {adr_summary or 'No ADR summary provided.'}",
            ]
        )
    if next_actions_text:
        worker_comment_lines.extend(["", "Next actions:", next_actions_text])

    if decision == "COMPLETE":
        if wiki_title or wiki_summary:
            wiki_page_path = _apply_wiki_manager_plan(
                gateway=gateway,
                adapter=adapter,
                foundation_issue_number=foundation_issue_number,
                research_issue_number=linked_issue.number,
                research_issue_title=issue.title,
                summary=summary,
                wiki_title=wiki_title,
                wiki_summary=wiki_summary,
                adr_link=adr_link,
            )
        gateway.close_issue(linked_issue.number, "completed")
        primary_lines = [
            f"Linked foundation research #{linked_issue.number} completed.",
            f"Summary: {summary}",
        ]
        if wiki_page_path:
            primary_lines.append(f"Research wiki reference: wiki/{wiki_page_path}")
        if adr_link:
            primary_lines.append(f"Research ADR reference: {adr_link}")
        return {
            "issue_number": linked_issue.number,
            "decision": decision,
            "summary": summary,
            "worker_comment": "\n".join(worker_comment_lines),
            "primary_comment": "\n".join(primary_lines),
            "blocked": False,
            "completed": True,
        }
    elif decision == "BLOCKED":
        return {
            "issue_number": linked_issue.number,
            "decision": decision,
            "summary": summary,
            "worker_comment": "\n".join(worker_comment_lines),
            "primary_comment": f"Linked foundation research #{linked_issue.number} is blocked. Summary: {summary}",
            "blocked": True,
            "completed": False,
        }
    else:
        return {
            "issue_number": linked_issue.number,
            "decision": decision,
            "summary": summary,
            "worker_comment": "\n".join(worker_comment_lines),
            "primary_comment": None,
            "blocked": False,
            "completed": False,
        }


def _run_linked_research_workers(
    gateway,
    adapter: JudgmentLLMAdapter,
    foundation_issue_number: int,
    foundation_markdown: str,
    max_workers: int = 3,
) -> dict:
    """Run research workers on linked research issues in parallel.
    
    Args:
        gateway: GitHub gateway
        adapter: LLM adapter
        foundation_issue_number: The foundation issue number
        foundation_markdown: Foundation markdown context
        max_workers: Number of parallel worker threads (default 3)
    
    Returns:
        Dict with 'completed', 'touched', 'blocked' counts
    """
    completed = 0
    touched = 0
    blocked = 0
    linked_issues = [linked for linked in gateway.list_linked_research_issues(foundation_issue_number) if linked.open]

    if not linked_issues:
        return {"completed": completed, "touched": touched, "blocked": blocked}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _process_research_issue,
                gateway,
                adapter,
                foundation_issue_number,
                foundation_markdown,
                linked_issue,
            ): linked_issue
            for linked_issue in linked_issues
        }

        for future in as_completed(futures):
            try:
                result = future.result()
                issue_number = result["issue_number"]

                # worker_comment is None when the issue was already processed this pass
                if result["worker_comment"] is not None:
                    gateway.post_comment(issue_number, result["worker_comment"])
                touched += 1

                if result["completed"]:
                    completed += 1
                    gateway.post_comment(foundation_issue_number, result["primary_comment"])
                elif result["blocked"]:
                    blocked += 1
                    gateway.post_comment(foundation_issue_number, result["primary_comment"])
            except Exception as e:
                linked = futures[future]
                logger.error(f"Error processing research issue #{linked.number}: {e}", exc_info=True)
                touched += 1

    return {"completed": completed, "touched": touched, "blocked": blocked}


def _ensure_supporting_research_issue(gateway, foundation_issue_number: int) -> None:
    linked = gateway.list_linked_research_issues(foundation_issue_number)
    if linked:
        return
    gateway.ensure_research_issue(
        foundation_issue_number=foundation_issue_number,
        title=f"[foundation-research] Evidence collection for #{foundation_issue_number}",
        body=(
            "Collect and publish foundational research outcomes.\n\n"
            "Required outcomes:\n"
            "- linked wiki evidence references\n"
            "- linked ADR references\n"
            "- recommendation for foundation gate"
        ),
        labels=[],
    )


def _is_supporting_research_issue(issue) -> bool:
    labels = getattr(issue, "labels", set()) or set()
    return "foundation:research" in labels


def _plan_research_areas(adapter: JudgmentLLMAdapter, issue, foundation_markdown: str) -> list[str]:
    result = adapter.invoke_json(
        "foundation_research_plan",
        {
            "issue_number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "foundation_markdown": foundation_markdown,
        },
    )
    raw = result.payload.get("research_areas")
    if not isinstance(raw, list):
        raise ValueError("foundation_research_plan must return research_areas as an array")
    areas = []
    for item in raw:
        if isinstance(item, str):
            trimmed = item.strip()
            if trimmed:
                areas.append(trimmed)
    deduped = list(dict.fromkeys(areas))
    if not deduped:
        raise ValueError("foundation_research_plan returned no valid research areas")
    return deduped


def _sync_foundation_research_backlog(
    gateway,
    foundation_issue_number: int,
    research_areas: list[str],
) -> None:
    existing = gateway.list_linked_research_issues(foundation_issue_number)
    existing_titles = {item.title for item in existing}
    for area in research_areas:
        title = f"[foundation-research] {area} for #{foundation_issue_number}"
        if title in existing_titles:
            continue
        gateway.ensure_research_issue(
            foundation_issue_number=foundation_issue_number,
            title=title,
            body=(
                f"Research decision area: {area}\n\n"
                "Before researching, read the following files from the repository to inform your work:\n"
                "- `FOUNDATION.md` — project context, constraints, and locked decisions\n"
                "- `docs/foundation-decision-pack.md` — decisions already made in other areas\n"
                "- `docs/adr/` — existing ADRs; do not re-open settled decisions\n"
                "- `docs/discovery-focus.md` — target audience and priority problems (if present)\n\n"
                "Required outputs:\n"
                "- Decision recommendation with rationale and alternatives considered\n"
                "- Risks and mitigations\n"
                "- Links to supporting evidence (wiki pages, references)\n"
                "- ADR link(s) for accepted major decisions\n"
            ),
            labels=[],
        )


def _set_primary_foundation_state(gateway, issue_number: int, next_state: FoundationState, reason: str) -> None:
    gateway.set_state_labels(
        issue_number,
        list(FOUNDATION_CANONICAL_STATE_LABELS),
        [FOUNDATION_CANONICAL_LABEL_BY_STATE[next_state]],
    )
    gateway.post_comment(
        issue_number,
        f"Foundation orchestrator transition: {next_state.value} — {reason}",
    )


def _cleanup_supporting_issue_state_labels(gateway, foundation_issue_number: int) -> None:
    for linked in gateway.list_linked_research_issues(foundation_issue_number):
        issue = gateway.get_issue(linked.number)
        removable = [label for label in issue.labels if label in FOUNDATION_CANONICAL_STATE_LABELS]
        if removable:
            gateway.remove_labels(linked.number, removable)


# Labels that mark an issue as part of the foundation workflow. Used to build a
# fingerprint of the foundation "world" so verification passes can tell whether a
# fresh pass actually changed anything.
_SIGNATURE_LABELS = [
    "foundation:needed",
    "foundation:in-progress",
    "foundation:review",
    "foundation:needs-human",
    "foundation:research",
]

# Primary foundation labels used when pulling actionable issues for a pass.
_ACTIONABLE_LABELS = [
    "foundation:needed",
    "foundation:in-progress",
    "foundation:review",
    "foundation:needs-human",
]


def _world_signature(gateway) -> tuple:
    """Fingerprint the current foundation state.

    Captures every open foundation-related issue, its foundation state/research
    labels, and its linked-research open/closed counts. Two identical signatures
    across passes mean nothing actionable changed, so the run can be considered
    settled. Any difference means a pass made progress.
    """
    issues = gateway.list_open_issues_with_any_label(_SIGNATURE_LABELS)
    entries = []
    for issue in sorted(issues, key=lambda item: item.number):
        state_labels = tuple(
            sorted(
                label
                for label in (issue.labels or set())
                if label in FOUNDATION_CANONICAL_STATE_LABELS or label == "foundation:research"
            )
        )
        open_research = gateway.count_open_linked_research_issues(issue.number)
        closed_research = gateway.count_closed_linked_research_issues(issue.number)
        entries.append((issue.number, state_labels, open_research, closed_research))
    return tuple(entries)


def _process_foundation_pass(
    gateway,
    adapter,
    orchestrator,
    foundation_markdown: str,
    progress_tracker: "ProgressTracker",
    max_research_workers: int = 3,
) -> tuple[list, list]:
    """Run one full foundation pass.

    Re-pulls open foundation issues fresh, processes each actionable issue, and
    persists progress. Returns ``(actionable, failed_issues)`` where
    ``failed_issues`` is a list of ``(issue_number, reason)`` tuples.
    
    Args:
        max_research_workers: Number of parallel workers for research issue processing
    """
    open_foundation_issues = gateway.list_open_issues_with_any_label(_ACTIONABLE_LABELS)

    actionable = []
    for issue in open_foundation_issues:
        if _is_supporting_research_issue(issue):
            continue
        normalized = normalize_foundation_state_from_labels(issue.labels)
        actionable.append((issue, normalized.state))
    actionable.sort(key=lambda item: (_priority(item[1]), item[0].number))

    failed_issues = []
    for issue, current_state in actionable:
        issue_number = issue.number
        logger.info(f"Processing foundation issue #{issue_number} ({current_state})")
        before = _snapshot_issue(gateway, issue_number)
        open_research_before = gateway.count_open_linked_research_issues(issue_number)
        try:
            # needs-human is resumable if evidence changed since last run.
            if current_state == FoundationState.FOUNDATION_NEEDS_HUMAN:
                previous_payload = progress_tracker.get(issue_number).get("snapshot")
                if previous_payload:
                    previous = _dict_to_snapshot(previous_payload)
                    if _has_progress(previous, before):
                        gateway.post_comment(
                            issue_number,
                            "Resuming from foundation:needs-human because new evidence was detected.",
                        )
                        gateway.set_state_labels(
                            issue_number,
                            ["foundation:needs-human"],
                            ["foundation:in-progress"],
                        )
                    else:
                        gateway.post_comment(
                            issue_number,
                            "Still waiting on needs-human unblock requirements. "
                            + _build_unblock_message(gateway, issue_number, before),
                        )
                        progress_tracker.set(
                            issue_number,
                            {
                                "no_progress_count": progress_tracker.get(issue_number).get("no_progress_count", 0),
                                "snapshot": _snapshot_to_dict(before),
                            },
                        )
                        continue
                else:
                    gateway.post_comment(
                        issue_number,
                        "Resuming from foundation:needs-human to re-evaluate current evidence.",
                    )
                    gateway.set_state_labels(
                        issue_number,
                        ["foundation:needs-human"],
                        ["foundation:in-progress"],
                    )

            planning_issue = gateway.get_issue(issue_number)
            # Only plan research areas when the issue is first picked up (NEEDED or
            # resuming from NEEDS_HUMAN). Once IN_PROGRESS the backlog is fixed —
            # re-planning every pass causes the LLM to generate slightly different
            # titles each time, bypassing deduplication and creating duplicate issues.
            if current_state in (FoundationState.FOUNDATION_NEEDED, FoundationState.FOUNDATION_NEEDS_HUMAN):
                planned_areas = _plan_research_areas(adapter, planning_issue, foundation_markdown)
                _sync_foundation_research_backlog(gateway, issue_number, planned_areas)
            _cleanup_supporting_issue_state_labels(gateway, issue_number)

            normalized_current = normalize_foundation_state_from_labels(gateway.get_issue(issue_number).labels)
            active_state = normalized_current.state or FoundationState.FOUNDATION_NEEDED

            if active_state == FoundationState.FOUNDATION_NEEDED:
                _set_primary_foundation_state(
                    gateway,
                    issue_number,
                    FoundationState.FOUNDATION_IN_PROGRESS,
                    "Initialized foundation workflow and created scoped research backlog.",
                )
                progress_tracker.set(
                    issue_number,
                    {
                        "no_progress_count": 0,
                        "snapshot": _snapshot_to_dict(_snapshot_issue(gateway, issue_number)),
                    },
                )
                continue

            if active_state == FoundationState.FOUNDATION_IN_PROGRESS:
                worker_stats = _run_linked_research_workers(
                    gateway=gateway,
                    adapter=adapter,
                    foundation_issue_number=issue_number,
                    foundation_markdown=foundation_markdown,
                    max_workers=max_research_workers,
                )
                open_research = gateway.count_open_linked_research_issues(issue_number)
                closed_research = gateway.count_closed_linked_research_issues(issue_number)
                if open_research > 0:
                    gateway.post_comment(
                        issue_number,
                        f"Foundation research in progress: waiting on {open_research} linked research issue(s) to close.",
                    )
                    progress_tracker.set(
                        issue_number,
                        {
                            "no_progress_count": (
                                0 if worker_stats["completed"] > 0 else progress_tracker.get(issue_number).get("no_progress_count", 0) + 1
                            ),
                            "snapshot": _snapshot_to_dict(_snapshot_issue(gateway, issue_number)),
                        },
                    )
                    if progress_tracker.get(issue_number).get("no_progress_count", 0) >= 3:
                        gateway.set_state_labels(
                            issue_number,
                            ["foundation:in-progress", "foundation:review", "foundation:needed"],
                            ["foundation:needs-human"],
                        )
                        gateway.post_comment(issue_number, _build_unblock_message(gateway, issue_number, _snapshot_issue(gateway, issue_number)))
                    continue
                if closed_research > 0:
                    _set_primary_foundation_state(
                        gateway,
                        issue_number,
                        FoundationState.FOUNDATION_REVIEW,
                        "All linked research issues are closed. Advancing to architecture review.",
                    )
                    progress_tracker.set(
                        issue_number,
                        {
                            "no_progress_count": 0,
                            "snapshot": _snapshot_to_dict(_snapshot_issue(gateway, issue_number)),
                        },
                    )
                    continue
                gateway.post_comment(
                    issue_number,
                    "No linked research is complete yet; remaining in foundation:in-progress.",
                )
                progress_tracker.set(
                    issue_number,
                    {
                        "no_progress_count": 0,
                        "snapshot": _snapshot_to_dict(_snapshot_issue(gateway, issue_number)),
                    },
                )
                continue

            try:
                orchestrator.run_once(issue_number)
            except Exception as ex:
                failed_issues.append((issue_number, str(ex)))
                gateway.post_comment(issue_number, f"Foundation run failed for this cycle: {ex}")
                continue

            after = _snapshot_issue(gateway, issue_number)
            no_progress = (
                before.state_label == after.state_label
                and after.closed_research_count <= before.closed_research_count
                and after.relevant_links == before.relevant_links
            )
            if open_research_before > 0 and gateway.count_open_linked_research_issues(issue_number) > 0:
                no_progress = False
            prior = progress_tracker.get(issue_number).get("no_progress_count", 0)
            no_progress_count = prior + 1 if no_progress else 0

            normalized_after = normalize_foundation_state_from_labels(gateway.get_issue(issue_number).labels)
            if (
                no_progress_count >= 3
                and normalized_after.state in {FoundationState.FOUNDATION_IN_PROGRESS, FoundationState.FOUNDATION_REVIEW}
            ):
                gateway.set_state_labels(
                    issue_number,
                    ["foundation:in-progress", "foundation:review", "foundation:needed"],
                    ["foundation:needs-human"],
                )
                gateway.post_comment(issue_number, _build_unblock_message(gateway, issue_number, after))
                no_progress_count = 0

            progress_tracker.set(
                issue_number,
                {
                    "no_progress_count": no_progress_count,
                    "snapshot": _snapshot_to_dict(after),
                },
            )
        finally:
            _post_issue_run_summary(gateway, issue_number)

    progress_tracker.save()
    return actionable, failed_issues


def main():
    parser = argparse.ArgumentParser(
        description="Initialize project foundational norms & standards",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "repo",
        nargs="?",
        help="GitHub repo (owner/repo format) or use AIOS_TARGET_REPO env var",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force restart (ignore any open foundation issues and restart from scratch)",
    )
    parser.add_argument(
        "--log-dir",
        default=str(DEFAULT_LOG_DIR),
        help="Directory for runlog output",
    )
    parser.add_argument(
        "--model",
        default="auto",
        help="LLM model hint",
    )
    parser.add_argument(
        "--stub",
        action="store_true",
        help="Use stub adapter instead of GitHub Copilot",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without executing",
    )
    parser.add_argument(
        "--verify-passes",
        type=int,
        default=2,
        help=(
            "Number of consecutive fresh passes that must find nothing to do before "
            "the run is considered settled (re-pulls issues each pass). Default: 2"
        ),
    )
    parser.add_argument(
        "--max-passes",
        type=int,
        default=25,
        help="Safety cap on total verification passes to avoid looping forever. Default: 25",
    )
    parser.add_argument(
        "--research-workers",
        type=int,
        default=3,
        help="Number of parallel research worker threads. Default: 3",
    )

    args = parser.parse_args()

    # Parse target repo
    target_repo = args.repo or os.environ.get("AIOS_TARGET_REPO")
    if not target_repo:
        print(
            "Error: Must provide 'owner/repo' or set AIOS_TARGET_REPO environment variable",
            file=sys.stderr,
        )
        return 1

    try:
        context = RepoContext.from_string(target_repo)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[DRY RUN] Foundation Orchestrator:")
        print(f"  Repo: {context}")
        print(f"  Mode: {'restart (--force)' if args.force else 'resume or start'}")
        print(f"  Log directory: {args.log_dir}")
        return 0

    Path(args.log_dir).mkdir(parents=True, exist_ok=True)
    progress_tracker = ProgressTracker(Path(args.log_dir) / "foundation_progress.json")

    try:
        gateway = context.create_foundation_gateway()
    except Exception as e:
        print(f"Error creating gateway: {e}", file=sys.stderr)
        return 2

    try:
        logger.info(f"Foundation Orchestrator: {context}")

        # Check for FOUNDATION.md first
        logger.info("Checking for FOUNDATION.md at repo root...")
        if not gateway.foundation_markdown_exists():
            print(
                "Error: FOUNDATION.md not found at repository root. "
                "Create FOUNDATION.md before running the foundation orchestrator.",
                file=sys.stderr,
            )
            return 1
        foundation_markdown = gateway.read_foundation_markdown()

        # Bootstrap wiki if needed (ensures backing repo exists before any wiki operations)
        logger.info("Ensuring wiki is ready...")
        try:
            gateway._ensure_wiki_exists()
        except Exception as e:
            print(f"Error: Failed to bootstrap wiki: {e}", file=sys.stderr)
            return 2

        run_registry = FoundationRunRegistry()

        # Create orchestrator
        log_db = f"{args.log_dir}/foundation_run.runlog.md"
        adapter = create_adapter(model=args.model, use_stub=args.stub, stub_class=StubLLMAdapter)
        gateway.comment_formatter = build_comment_formatter(adapter)
        orchestrator = FoundationRunOnceOrchestrator(
            gateway=gateway,
            log_store=TransitionLogStore(log_db),
            run_registry=run_registry,
            research_adapter=adapter,
            gate_adapter=adapter,
            retry_policy=RetryPolicy(max_attempts=3),
        )

        # One-time bootstrap: make sure there is at least one foundation issue to
        # work on. Creation only happens here (never inside a verification pass),
        # so repeated passes re-pull issues without spawning duplicates.
        open_foundation_issues = gateway.list_open_issues_with_any_label(_ACTIONABLE_LABELS)
        if args.force:
            logger.info("--force specified. Creating a fresh foundation issue for this run.")
            created_issue = gateway.create_foundation_issue(
                title="Foundation Setup",
                body="Establish foundational norms and standards for this repository.",
            )
            logger.info(f"Created new foundation issue #{created_issue}")
        elif not open_foundation_issues:
            logger.info("No open foundation issues. Creating a new foundation issue.")
            created_issue = gateway.create_foundation_issue(
                title="Foundation Setup",
                body="Establish foundational norms and standards for this repository.",
            )
            logger.info(f"Created new foundation issue #{created_issue}")

        # Verification loop: keep running full, fresh passes (re-pulling issues each
        # time) as long as any pass changes foundation state. Once a pass makes no
        # changes, run a few more confirming passes before concluding there is
        # genuinely nothing to do. This guards against races where research issues
        # close (or new work appears) between passes.
        verify_passes = max(1, args.verify_passes)
        max_passes = max(verify_passes, args.max_passes)
        failed_by_issue: dict = {}
        pass_index = 0
        consecutive_idle = 0
        last_actionable_count = 0

        while True:
            pass_index += 1
            logger.info(f"Foundation pass {pass_index} (re-pulling issues fresh)...")
            before_signature = _world_signature(gateway)
            actionable, failed_issues = _process_foundation_pass(
                gateway=gateway,
                adapter=adapter,
                orchestrator=orchestrator,
                foundation_markdown=foundation_markdown,
                progress_tracker=progress_tracker,
                max_research_workers=args.research_workers,
            )
            last_actionable_count = len(actionable)
            for issue_number, reason in failed_issues:
                failed_by_issue[issue_number] = reason
            after_signature = _world_signature(gateway)

            if after_signature != before_signature:
                consecutive_idle = 0
                logger.info(f"Pass {pass_index} changed foundation state; continuing.")
            else:
                consecutive_idle += 1
                logger.info(
                    f"Pass {pass_index} made no changes "
                    f"({consecutive_idle}/{verify_passes} confirming passes with nothing to do)."
                )

            if consecutive_idle >= verify_passes:
                logger.info(
                    f"No actionable foundation work across {verify_passes} consecutive pass(es); run settled."
                )
                break
            if pass_index >= max_passes:
                logger.warning(
                    f"Reached max passes ({max_passes}) before the run settled; stopping."
                )
                break

        progress_tracker.save()
        if failed_by_issue:
            for issue_number, reason in sorted(failed_by_issue.items()):
                logger.error(f"Issue #{issue_number} failed this run: {reason}")
            return 3

        logger.info(
            f"✓ Foundation run complete after {pass_index} pass(es); "
            f"last pass processed {last_actionable_count} issue(s)"
        )
        logger.info(f"  Runlog: {log_db}")
        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 3


if __name__ == "__main__":
    sys.exit(main())
