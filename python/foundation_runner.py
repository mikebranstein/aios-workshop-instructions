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
from pathlib import Path

from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.llm.adapter_factory import create_adapter
from aios_orchestration_core.labels.foundation_labels import normalize_foundation_state_from_labels
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.repo_context import RepoContext
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.runlog.paths import default_runlog_dir
from aios_orchestration_core.states.foundation import FoundationState
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
            "foundation_research": {"decision": "RECOMMEND", "reason": "stub research"},
            "foundation_gate": {"decision": "REVISE_FOUNDATION", "reason": "stub gate review"},
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
    if "foundation:research" in labels:
        return True
    return any(label.startswith("foundation-source-") for label in labels)


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

        # Check for FOUNDATION.md
        logger.info("Checking for FOUNDATION.md at repo root...")
        if not gateway.foundation_markdown_exists():
            print(
                "Error: FOUNDATION.md not found at repository root. "
                "Create FOUNDATION.md before running the foundation orchestrator.",
                file=sys.stderr,
            )
            return 1

        run_registry = FoundationRunRegistry()

        # Create orchestrator
        log_db = f"{args.log_dir}/foundation_run.runlog.md"
        adapter = create_adapter(model=args.model, use_stub=args.stub, stub_class=StubLLMAdapter)
        orchestrator = FoundationRunOnceOrchestrator(
            gateway=gateway,
            log_store=TransitionLogStore(log_db),
            run_registry=run_registry,
            research_adapter=adapter,
            gate_adapter=adapter,
            retry_policy=RetryPolicy(max_attempts=3),
        )

        open_foundation_issues = gateway.list_open_issues_with_any_label(
            ["foundation:needed", "foundation:in-progress", "foundation:review", "foundation:needs-human"]
        )
        if args.force:
            logger.info("--force specified. Creating a fresh foundation issue for this run.")
            logger.info("No resumable foundation issue found. Creating a new foundation issue.")
            created_issue = gateway.create_foundation_issue(
                title="Foundation Setup",
                body="Establish foundational norms and standards for this repository.",
            )
            logger.info(f"Created new foundation issue #{created_issue}")
            open_foundation_issues.append(gateway.get_issue(created_issue))
        elif not open_foundation_issues:
            logger.info("No open foundation issues. Creating a new foundation issue.")
            created_issue = gateway.create_foundation_issue(
                title="Foundation Setup",
                body="Establish foundational norms and standards for this repository.",
            )
            logger.info(f"Created new foundation issue #{created_issue}")
            open_foundation_issues.append(gateway.get_issue(created_issue))

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

            _ensure_supporting_research_issue(gateway, issue_number)

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

        progress_tracker.save()
        if failed_issues:
            for issue_number, reason in failed_issues:
                logger.error(f"Issue #{issue_number} failed this run: {reason}")
            return 3

        logger.info(f"✓ Foundation run complete for {len(actionable)} issue(s)")
        logger.info(f"  Runlog: {log_db}")
        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 3


if __name__ == "__main__":
    sys.exit(main())
