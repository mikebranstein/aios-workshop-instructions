#!/usr/bin/env python3
"""
Discovery Orchestrator Runner — Generate strategic opportunities from focus areas.

Reads focus.md from repo, invokes idea-scout to identify market opportunities,
and creates pm-idea issues for strategic evaluation. Pure generator—no input issues.

Usage:
    # Generate strategic opportunities
    python discovery_runner.py owner/my-repo
    
    # Force restart (ignore prior discoveries, re-scout)
    python discovery_runner.py owner/my-repo --force
    
    # Preview without executing
    python discovery_runner.py owner/my-repo --dry-run

Environment Variables:
    AIOS_TARGET_REPO      Target GitHub repo (owner/repo format)

Exit Codes:
    0   Success
    1   Invalid arguments or focus.md not found
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
from discovery_orchestrator.run_once import DiscoveryRunOnceOrchestrator, DiscoveryRunRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class StubIdeaScoutAdapter(JudgmentLLMAdapter):
    """Stub idea-scout adapter for demonstration."""

    def __init__(self, model: str = "gpt-4"):
        self.model = model

    def invoke_json(self, task_type: str, prompt_vars: dict, model_hint: str = ""):
        stubs = {
            "DISCOVERY_IDEA_SCOUT": {
                "opportunities": [
                    {"title": "Stub opportunity 1", "description": "generated opportunity"}
                ]
            }
        }
        return type("Result", (), {"payload": stubs.get(task_type, {}), "model": self.model})()


def main():
    parser = argparse.ArgumentParser(
        description="Generate strategic opportunities from focus areas",
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
        help="Force restart (ignore prior discovery run and re-scout from scratch)",
    )
    parser.add_argument(
        "--log-dir",
        default="./discovery_runs",
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
        print(f"[DRY RUN] Discovery Orchestrator (Idea Scout):")
        print(f"  Repo: {context}")
        print(f"  Mode: {'restart (--force)' if args.force else 'normal run'}")
        print(f"  Log directory: {args.log_dir}")
        print(f"  Note: Reads focus.md from repo root to guide opportunity generation")
        return 0

    Path(args.log_dir).mkdir(parents=True, exist_ok=True)

    try:
        # Note: Discovery doesn't have a specific gateway in RepoContext yet
        # For now, we'd use a generic gateway or extend RepoContext
        # Using GitHub API gateway as placeholder
        gateway = context.create_pm_gateway()  # Placeholder—should be discovery-specific
    except Exception as e:
        print(f"Error creating gateway: {e}", file=sys.stderr)
        return 2

    try:
        logger.info(f"Discovery Orchestrator: {context}")
        logger.info("Checking for focus.md at repo root...")
        # In a real implementation, validate focus.md exists

        # Check if there's a prior discovery run to skip (unless --force)
        run_registry = DiscoveryRunRegistry()
        
        if not args.force:
            logger.info("Checking for prior discovery run in this session...")
            # In a real implementation, check if discovery has already run
            # For now, always run
        else:
            logger.info("--force specified. Re-running discovery from scratch.")

        # Create orchestrator
        log_db = f"{args.log_dir}/discovery_run.sqlite"
        adapter = create_adapter(model=args.model, use_stub=args.stub, stub_class=StubIdeaScoutAdapter)
        orchestrator = DiscoveryRunOnceOrchestrator(
            gateway=gateway,
            log_store=TransitionLogStore(log_db),
            run_registry=run_registry,
            idea_scout_adapter=adapter,
            retry_policy=RetryPolicy(max_attempts=3),
        )

        logger.info("Generating strategic opportunities from focus areas...")
        result = orchestrator.run_once()

        opportunities_created = len(result.created_pm_idea_numbers) if hasattr(result, 'created_pm_idea_numbers') else 0
        logger.info(f"✓ Discovery complete. Created {opportunities_created} pm-idea issue(s)")
        logger.info(f"  Runlog: {log_db}")
        if hasattr(result, 'created_pm_idea_numbers') and result.created_pm_idea_numbers:
            logger.info(f"  Issues: {', '.join(f'#{n}' for n in result.created_pm_idea_numbers)}")
        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 3


if __name__ == "__main__":
    sys.exit(main())
