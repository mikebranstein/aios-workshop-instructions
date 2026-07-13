#!/usr/bin/env python3
"""
Discovery Orchestrator Runner — Generate strategic opportunities from focus areas.

Reads docs/discovery-focus.md from repo, invokes idea-scout to identify market opportunities,
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
    1   Invalid arguments or docs/discovery-focus.md not found
    2   GitHub authentication failed
    3   Orchestration failed
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from aios_orchestration_core.llm.adapter_factory import create_adapter
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.repo_context import RepoContext
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.runlog.paths import default_runlog_dir
from discovery_orchestrator.idea_scout_adapter import (
    IdeaCandidate,
    IdeaScoutAdapter,
    IdeaScoutResult,
)
from discovery_orchestrator.run_once import DiscoveryRunOnceOrchestrator, DiscoveryRunRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_LOG_DIR = default_runlog_dir("discovery")


class StubLLMAdapter(JudgmentLLMAdapter):
    """Stub LLM adapter for discovery decisions."""

    def __init__(self, model: str = "copilot-standard"):
        self.model = model

    @property
    def adapter_source(self) -> str:
        return "stub"

    def invoke_json(self, task_type: str, prompt_vars: dict, model_hint: str = ""):
        return type(
            "Result",
            (),
            {
                "payload": {
                    "candidates": [
                        {
                            "title": "Stub opportunity 1",
                            "body": "generated opportunity",
                            "decision": "CREATE_PM_IDEA",
                        }
                    ]
                },
                "model": self.model,
            },
        )()


class DiscoveryIdeaScoutAdapter(IdeaScoutAdapter):
    """Adapter bridge from JudgmentLLMAdapter to Discovery IdeaScoutAdapter."""

    def __init__(self, llm_adapter: JudgmentLLMAdapter):
        self._llm_adapter = llm_adapter

    @property
    def adapter_source(self) -> str:
        return self._llm_adapter.adapter_source

    def run(self, context_summary: str, creation_cap: int) -> IdeaScoutResult:
        result = self._llm_adapter.invoke_json(
            "discovery_idea_scout",
            {"context_summary": context_summary, "creation_cap": creation_cap},
        )
        payload = result.payload or {}
        raw_candidates = payload.get("candidates")
        if raw_candidates is None:
            raw_candidates = [
                {
                    "title": item.get("title", "Untitled opportunity"),
                    "body": item.get("description", ""),
                    "decision": "CREATE_PM_IDEA",
                }
                for item in payload.get("opportunities", [])
            ]

        candidates = []
        for item in raw_candidates[:creation_cap]:
            decision = str(item.get("decision", "CREATE_PM_IDEA")).upper()
            if decision not in {"CREATE_PM_IDEA", "DEFER", "DROP"}:
                decision = "DROP"
            candidates.append(
                IdeaCandidate(
                    title=str(item.get("title", "Untitled opportunity")),
                    body=str(item.get("body", item.get("description", ""))),
                    decision=decision,
                )
            )
        return IdeaScoutResult(candidates=candidates)


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
        print(f"[DRY RUN] Discovery Orchestrator (Idea Scout):")
        print(f"  Repo: {context}")
        print(f"  Mode: {'restart (--force)' if args.force else 'normal run'}")
        print(f"  Log directory: {args.log_dir}")
        print(f"  Note: Reads docs/discovery-focus.md from repo root to guide opportunity generation")
        return 0

    Path(args.log_dir).mkdir(parents=True, exist_ok=True)

    try:
        gateway = context.create_discovery_gateway()
    except Exception as e:
        print(f"Error creating gateway: {e}", file=sys.stderr)
        return 2

    try:
        logger.info(f"Discovery Orchestrator: {context}")
        logger.info("Loading discovery context from target repository...")
        discovery_context = gateway.get_context()

        # Check if there's a prior discovery run to skip (unless --force)
        run_registry = DiscoveryRunRegistry()
        if args.force:
            logger.info("--force specified. Re-running discovery from scratch.")

        # Create orchestrator
        log_db = f"{args.log_dir}/discovery_run.runlog.md"
        adapter = create_adapter(model=args.model, use_stub=args.stub, stub_class=StubLLMAdapter)
        idea_scout_adapter = DiscoveryIdeaScoutAdapter(adapter)
        orchestrator = DiscoveryRunOnceOrchestrator(
            context=discovery_context,
            idea_scout=idea_scout_adapter,
            pm_idea_store=gateway,
            log_store=TransitionLogStore(log_db),
            run_registry=run_registry,
            retry_policy=RetryPolicy(max_attempts=3),
        )

        logger.info("Generating strategic opportunities from focus areas...")
        result = orchestrator.run()

        opportunities_created = len(result.created_pm_idea_numbers)
        logger.info(f"✓ Discovery complete. Final state: {result.state}")
        logger.info(f"  Created {opportunities_created} pm-idea issue(s)")
        logger.info(f"  Runlog: {log_db}")
        if result.created_pm_idea_numbers:
            logger.info(f"  Issues: {', '.join(f'#{n}' for n in result.created_pm_idea_numbers)}")
        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 3


if __name__ == "__main__":
    sys.exit(main())
