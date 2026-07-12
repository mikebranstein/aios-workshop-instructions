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
import logging
import os
import sys
from pathlib import Path

from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.llm.adapter_factory import create_adapter
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.repo_context import RepoContext
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.foundation import FoundationState
from foundation_orchestrator.run_once import FoundationRunOnceOrchestrator, FoundationRunRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class StubLLMAdapter(JudgmentLLMAdapter):
    """Stub adapter for demonstration."""

    def __init__(self, model: str = "gpt-4"):
        self.model = model

    def invoke_json(self, task_type: str, prompt_vars: dict, model_hint: str = ""):
        stubs = {
            "FOUNDATION_RESEARCH": {"findings": "stub research", "ready": True},
            "FOUNDATION_GATE": {"decision": "APPROVED", "reason": "stub approval"},
        }
        return type("Result", (), {"payload": stubs.get(task_type, {}), "model": self.model})()


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
        default="./foundation_runs",
        help="Directory for runlog database",
    )
    parser.add_argument(
        "--model",
        default="gpt-4",
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

        # Check if there's an existing open foundation issue to resume from
        run_registry = FoundationRunRegistry()
        
        if not args.force:
            # Try to find an open foundation:* issue to resume from
            logger.info("Checking for interrupted foundation runs...")
            open_foundation_issues = gateway.list_open_issues_with_any_label(
                ["foundation:needed", "foundation:in-progress", "foundation:review"]
            )
            if open_foundation_issues:
                logger.info(
                    f"Found {len(open_foundation_issues)} open foundation issue(s). "
                    f"Resuming from issue #{open_foundation_issues[0].number}"
                )
                # In a real implementation, we'd extract state from labels
                issue_number = open_foundation_issues[0].number
            else:
                logger.info("No open foundation issues. Starting fresh.")
                issue_number = None
        else:
            logger.info("--force specified. Starting fresh foundation run.")
            issue_number = None

        # Create orchestrator
        log_db = f"{args.log_dir}/foundation_run.sqlite"
        adapter = create_adapter(model=args.model, use_stub=args.stub, stub_class=StubLLMAdapter)
        orchestrator = FoundationRunOnceOrchestrator(
            gateway=gateway,
            log_store=TransitionLogStore(log_db),
            run_registry=run_registry,
            research_adapter=adapter,
            gate_adapter=adapter,
            retry_policy=RetryPolicy(max_attempts=3),
        )

        if issue_number:
            logger.info(f"Resuming from issue #{issue_number}")
        else:
            logger.info("No resumable foundation issue found. Creating a new foundation issue.")
            issue_number = gateway.create_foundation_issue(
                title="Foundation Setup",
                body="Bootstrap foundational norms and standards for this repository.",
            )
            logger.info(f"Created new foundation issue #{issue_number}")

        result = orchestrator.run_once(issue_number)
        logger.info(f"✓ Foundation run complete for issue #{result.source_issue_number}")
        logger.info(f"  Runlog: {log_db}")
        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 3


if __name__ == "__main__":
    sys.exit(main())
