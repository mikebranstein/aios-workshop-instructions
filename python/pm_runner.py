#!/usr/bin/env python3
"""
PM Orchestrator Runner — Execute PM loop against any GitHub repo.

Two modes:

1. CONTINUOUS MODE (default): Process all pm:queued issues until queue is empty
   python pm_runner.py owner/my-repo --continuous
   
   Continuously finds issues with 'pm:queued' label and processes them one by one
   until no more queued issues remain.

2. SINGLE ISSUE MODE: Process one specific issue
   python pm_runner.py owner/my-repo 42
   python pm_runner.py 42  (if AIOS_TARGET_REPO is set)
   
   Processes a single issue through the PM loop.

Usage Examples:
    # Run continuous mode against specific repo
    python pm_runner.py owner/my-repo --continuous
    
    # Run single issue
    python pm_runner.py owner/my-repo 42
    
    # Use environment variable for repo, run continuous
    $env:AIOS_TARGET_REPO = "owner/my-repo"
    python pm_runner.py --continuous
    
    # Use environment variable, run single issue
    $env:AIOS_TARGET_REPO = "owner/my-repo"
    python pm_runner.py 42

Environment Variables:
    AIOS_TARGET_REPO      Target GitHub repo (owner/repo format)
    AIOS_PM_LOG_DIR       Directory for runlog output (default: temp/aios-orchestrator-runlogs/pm)
    AIOS_LLM_MODEL        LLM model hint (default: "auto")

Exit Codes:
    0   Success
    1   Invalid arguments
    2   Repo not found or GitHub authentication failed
    3   Issue processing failed
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.llm.adapter_factory import create_adapter
from aios_orchestration_core.github.comment_formatter import build_comment_formatter
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.repo_context import RepoContext
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.runlog.paths import default_runlog_dir
from pm_orchestrator.run_once import PMRunOnceOrchestrator, PMRunRegistry
from pm_orchestrator.continuous import PMContinuousOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

DEFAULT_LOG_DIR = default_runlog_dir("pm")


class StubLLMAdapter(JudgmentLLMAdapter):
    """Stub adapter for demonstration. Replace with real adapter in production."""

    def __init__(self, model: str = "auto"):
        self.model = model

    @property
    def adapter_source(self) -> str:
        return "stub"

    def invoke_json(self, task_type: str, prompt_vars: dict, model_hint: str = ""):
        """Return stub response. In production, invoke actual LLM."""
        # Stub responses for different task types
        stubs = {
            "PM_PHASE1": {"decision": "PROVISIONAL_CHAMPION", "reason": "stub response"},
            "PM_RESEARCH_PLANNING": {"tasks": []},
            "PM_RESEARCH_SYNTHESIS": {
                "summary": "stub synthesis",
                "confidence_score": 0.75,
                "closed_linked_research_count": 0,
            },
            "PM_PHASE2": {"decision": "CHAMPION", "reason": "stub", "confidence_score": 0.75},
        }
        return type("Result", (), {"payload": stubs.get(task_type, {}), "model": self.model})()


def main():
    parser = argparse.ArgumentParser(
        description="Run PM orchestrator against a GitHub repo (continuous or single issue)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "repo_or_issue",
        nargs="?",
        help="Either: (1) 'owner/repo' if AIOS_TARGET_REPO not set, or (2) issue number if AIOS_TARGET_REPO is set",
    )
    parser.add_argument(
        "issue_number",
        nargs="?",
        type=int,
        help="Issue number (omit if first arg is repo, required for single-issue mode if first arg is issue number)",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuously until no more pm:queued issues remain (default mode if no issue number)",
    )
    parser.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR), help="Directory for runlog output")
    parser.add_argument("--model", default="auto", help="LLM model hint")
    parser.add_argument("--max-retries", type=int, default=3, help="Circuit breaker max retries")
    parser.add_argument("--min-research", type=int, default=1, help="Minimum research count required")
    parser.add_argument("--min-synthesis-conf", type=float, default=0.75, help="Minimum synthesis confidence")
    parser.add_argument("--stub", action="store_true", help="Use stub adapter instead of GitHub Copilot")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run without executing")

    args = parser.parse_args()

    # Parse target repo and issue number
    target_repo = os.environ.get("AIOS_TARGET_REPO")
    issue_number = None
    mode = None
    
    # Logic: determine repo and mode from arguments
    if args.repo_or_issue is None:
        # No positional argument
        if not target_repo:
            print("Error: Must provide 'owner/repo' or set AIOS_TARGET_REPO", file=sys.stderr)
            return 1
        # Use target_repo from env, and optional second positional as issue number
        issue_number = args.issue_number
    elif "/" in args.repo_or_issue:
        # First positional looks like a repo (has "/")
        target_repo = args.repo_or_issue
        issue_number = args.issue_number
    else:
        # First positional looks like an issue number
        if target_repo:
            # Already have repo from env, so this is issue number
            try:
                issue_number = int(args.repo_or_issue)
            except ValueError:
                print(f"Error: Expected issue number, got '{args.repo_or_issue}'", file=sys.stderr)
                return 1
        else:
            # No repo set, so we need one
            print(f"Error: Expected 'owner/repo', got '{args.repo_or_issue}'", file=sys.stderr)
            return 1
    
    # Determine mode
    if issue_number:
        mode = "single"
    elif args.continuous:
        mode = "continuous"
    else:
        mode = "continuous"  # Default
    
    # Validate
    if not target_repo:
        print("Error: No target repo determined", file=sys.stderr)
        return 1
    
    # Parse repo context
    try:
        context = RepoContext.from_string(target_repo)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[DRY RUN] Would run PM orchestrator:")
        print(f"  Repo: {context}")
        print(f"  Mode: {mode}")
        if mode == "single":
            print(f"  Issue: {issue_number}")
        print(f"  Log directory: {args.log_dir}")
        print(f"  Model: {args.model}")
        return 0

    # Create directories
    Path(args.log_dir).mkdir(parents=True, exist_ok=True)

    # Create gateway
    try:
        gateway = context.create_pm_gateway()
    except Exception as e:
        print(f"Error creating gateway: {e}", file=sys.stderr)
        return 2

    try:
        if mode == "single":
            return _run_single_issue(gateway, args, issue_number)
        else:
            return _run_continuous(gateway, args)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 3


def _run_single_issue(gateway, args, issue_number: int) -> int:
    """Run orchestrator on a single issue."""
    print(f"Running PM orchestrator on single issue...")
    print(f"  Issue: {issue_number}")
    print(f"  Adapter: {'stub' if args.stub else 'GitHub Copilot'}")

    log_db = f"{args.log_dir}/pm_issue_{issue_number}.runlog.md"
    
    # Create adapter using factory
    adapter = create_adapter(model=args.model, use_stub=args.stub, stub_class=StubLLMAdapter)
    gateway.comment_formatter = build_comment_formatter(adapter)
    
    orchestrator = PMRunOnceOrchestrator(
        gateway=gateway,
        log_store=TransitionLogStore(log_db),
        run_registry=PMRunRegistry(),
        phase1_adapter=adapter,
        research_planning_adapter=adapter,
        synthesis_adapter=adapter,
        phase2_adapter=adapter,
        retry_policy=RetryPolicy(max_attempts=args.max_retries),
        min_research_count=args.min_research,
        min_synthesis_confidence=args.min_synthesis_conf,
    )

    result = orchestrator.run_once(issue_number)
    print(f"✓ Completed. Final state: {result.current_state}")
    print(f"  Runlog: {log_db}")
    return 0


def _run_continuous(gateway, args) -> int:
    """Run orchestrator in continuous mode."""
    print(f"Running PM orchestrator in CONTINUOUS mode...")
    print(f"  Processing all pm:queued issues until none remain")
    print(f"  Adapter: {'stub' if args.stub else 'GitHub Copilot'}")

    log_db = f"{args.log_dir}/pm_continuous.runlog.md"
    
    # Startup preflight: validate adapter availability before batch begins.
    try:
        adapter = create_adapter(model=args.model, use_stub=args.stub, stub_class=StubLLMAdapter)
    except Exception as e:
        print(
            "Startup health check failed: adapter initialization failed before continuous batch start.",
            file=sys.stderr,
        )
        print(f"Detail: {type(e).__name__}: {e}", file=sys.stderr)
        return 3
    
    gateway.comment_formatter = build_comment_formatter(adapter)
    orchestrator = PMContinuousOrchestrator(
        gateway=gateway,
        log_store=TransitionLogStore(log_db),
        phase1_adapter=adapter,
        research_planning_adapter=adapter,
        synthesis_adapter=adapter,
        phase2_adapter=adapter,
        retry_policy=RetryPolicy(max_attempts=args.max_retries),
        min_research_count=args.min_research,
        min_synthesis_confidence=args.min_synthesis_conf,
    )

    result = orchestrator.run_continuous()
    
    print(f"\n{'='*60}")
    print(f"Continuous run complete:")
    print(f"  Issues processed: {result['issues_processed']}")
    print(f"  Runlog: {log_db}")
    
    if result['errors']:
        print(f"\n  Errors encountered:")
        for issue_num, error in result['errors']:
            print(f"    - Issue #{issue_num}: {error}")
    
    for issue_info in result['final_issues']:
        print(f"  - Issue #{issue_info['issue_number']}: {issue_info['final_state']}")
    
    print(f"{'='*60}")
    return 0 if not result['errors'] else 3


if __name__ == "__main__":
    sys.exit(main())
