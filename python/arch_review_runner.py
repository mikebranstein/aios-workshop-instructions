#!/usr/bin/env python3
"""
Architecture Review Orchestrator Runner — Audit codebase for refactoring opportunities.

Wholistically reviews the codebase to identify abstraction opportunities, refactoring needs,
and architectural improvements. Supports recovery from interrupted audits.

Usage:
    # Start or resume architecture audit
    python arch_review_runner.py owner/my-repo
    
    # Force restart (ignore any open arch-review issues)
    python arch_review_runner.py owner/my-repo --force
    
    # Preview without executing
    python arch_review_runner.py owner/my-repo --dry-run

Environment Variables:
    AIOS_TARGET_REPO      Target GitHub repo (owner/repo format)

Exit Codes:
    0   Success
    1   Invalid arguments
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
from aios_orchestration_core.runlog.paths import default_runlog_dir
from arch_review_orchestrator.run_once import ArchReviewRunOnceOrchestrator, ArchReviewRunRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_LOG_DIR = default_runlog_dir("arch-review")


class StubLLMAdapter(JudgmentLLMAdapter):
    """Stub adapter for demonstration."""

    def __init__(self, model: str = "copilot-standard"):
        self.model = model

    def invoke_json(self, task_type: str, prompt_vars: dict, model_hint: str = ""):
        stubs = {
            "ARCH_REVIEW": {"fitness_score": 0.8, "findings": "stub review"},
            "ARCH_PLANNER": {"refactoring_tasks": []},
        }
        return type("Result", (), {"payload": stubs.get(task_type, {}), "model": self.model})()


def main():
    parser = argparse.ArgumentParser(
        description="Audit codebase for architectural improvements",
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
        help="Force restart (ignore any open arch-review issues and re-audit entire codebase)",
    )
    parser.add_argument(
        "--log-dir",
        default=str(DEFAULT_LOG_DIR),
        help="Directory for runlog output",
    )
    parser.add_argument(
        "--model",
        default="copilot-standard",
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
        print(f"[DRY RUN] Architecture Review Orchestrator:")
        print(f"  Repo: {context}")
        print(f"  Mode: {'restart (--force)' if args.force else 'resume or start'}")
        print(f"  Log directory: {args.log_dir}")
        return 0

    Path(args.log_dir).mkdir(parents=True, exist_ok=True)

    try:
        gateway = context.create_arch_review_gateway()
    except Exception as e:
        print(f"Error creating gateway: {e}", file=sys.stderr)
        return 2

    try:
        logger.info(f"Architecture Review Orchestrator: {context}")

        # Check if there's an existing open arch-review issue to resume from
        run_registry = ArchReviewRunRegistry()
        
        if not args.force:
            # Try to find an open arch-review:* issue to resume from
            logger.info("Checking for interrupted architecture reviews...")
            open_arch_issues = gateway.list_open_issues_with_any_label(
                ["arch:review-pending", "arch:review-in-progress", "arch:refactor-planned"]
            )
            if open_arch_issues:
                logger.info(
                    f"Found {len(open_arch_issues)} open architecture review issue(s). "
                    f"Resuming audit."
                )
                issue_number = open_arch_issues[0].number
            else:
                logger.info("No open architecture review issues. Starting fresh codebase audit.")
                issue_number = None
        else:
            logger.info("--force specified. Starting fresh codebase audit.")
            issue_number = None

        # Create orchestrator
        log_db = f"{args.log_dir}/arch_review_run.runlog.md"
        adapter = create_adapter(model=args.model, use_stub=args.stub, stub_class=StubLLMAdapter)
        orchestrator = ArchReviewRunOnceOrchestrator(
            gateway=gateway,
            log_store=TransitionLogStore(log_db),
            run_registry=run_registry,
            review_adapter=adapter,
            planner_adapter=adapter,
            retry_policy=RetryPolicy(max_attempts=3),
        )

        if issue_number:
            logger.info(f"Resuming from issue #{issue_number}")
        else:
            logger.info("No resumable architecture review issue found. Creating a new review issue.")
            issue_number = gateway.create_arch_review_issue(
                title="Architecture Review",
                body="Run architecture review loop and capture findings and refactor planning.",
            )
            logger.info(f"Created new architecture review issue #{issue_number}")

        result = orchestrator.run_once(issue_number)
        logger.info(f"✓ Architecture audit complete for issue #{result.source_issue_number}")
        logger.info(f"  Runlog: {log_db}")
        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 3


if __name__ == "__main__":
    sys.exit(main())
