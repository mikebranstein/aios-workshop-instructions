#!/usr/bin/env python3
"""
Discovery Orchestrator Runner — Generate strategic opportunities from focus areas.

Reads DISCOVERY-FOCUS.md from repo, invokes idea-scout LLM to identify market
opportunities, and creates pm-idea issues for strategic evaluation. Pure generator—no
input issues required.

Usage:
    # Generate strategic opportunities
    python discovery_runner.py owner/my-repo

    # Force restart (re-scout from scratch)
    python discovery_runner.py owner/my-repo --force

    # Preview without executing
    python discovery_runner.py owner/my-repo --dry-run

Environment Variables:
    AIOS_TARGET_REPO      Target GitHub repo (owner/repo format)

Exit Codes:
    0   Success
    1   Invalid arguments or DISCOVERY-FOCUS.md not found
    2   GitHub authentication failed
    3   Orchestration failed
"""

import json
import argparse
import logging
import os
import sys
from pathlib import Path

from aios_orchestration_core.llm.adapter_factory import create_adapter
from aios_orchestration_core.llm.base import JudgmentLLMAdapter, LLMInvocationResult
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.repo_context import RepoContext
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.runlog.paths import default_runlog_dir
from discovery_orchestrator.run_once import DiscoveryRunOnceOrchestrator, DiscoveryRunRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_LOG_DIR = default_runlog_dir("discovery")

_STUBS_DIR = Path(__file__).resolve().parent / "discovery_orchestrator" / "stubs"


class StubLLMAdapter(JudgmentLLMAdapter):
    """Stub LLM adapter for discovery smoke-testing (--stub flag).

    Payloads are loaded from discovery_orchestrator/stubs/{task_type}.json.
    The idea-scout candidate body lives in a companion _body.md file to keep
    the JSON free of escaped markdown.
    """

    def __init__(self, model: str = "auto"):
        self.model = model
        self._cache: dict = {}

    def _load(self, task_type: str) -> dict:
        if task_type in self._cache:
            return self._cache[task_type]
        json_path = _STUBS_DIR / f"{task_type}.json"
        if not json_path.exists():
            self._cache[task_type] = {}
            return {}
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        # For idea scout, candidate body is stored in companion .md to keep JSON clean.
        body_path = _STUBS_DIR / f"{task_type}_body.md"
        if body_path.exists() and payload.get("candidates"):
            payload["candidates"][0]["body"] = body_path.read_text(encoding="utf-8")
        self._cache[task_type] = payload
        return payload

    @property
    def adapter_source(self) -> str:
        return "stub"

    def invoke_json(self, task_type: str, prompt_vars: dict, model_hint: str = "") -> LLMInvocationResult:
        return LLMInvocationResult(payload=self._load(task_type), model=self.model, request_id="stub")


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
        log_db = f"{args.log_dir}/discovery_run.runlog.md"
        llm_adapter = create_adapter(model=args.model, use_stub=args.stub, stub_class=StubLLMAdapter)

        run_registry = DiscoveryRunRegistry()
        if args.force:
            logger.info("--force specified: re-running discovery from scratch.")

        orchestrator = DiscoveryRunOnceOrchestrator(
            gateway=gateway,
            llm_adapter=llm_adapter,
            run_registry=run_registry,
            log_store=TransitionLogStore(log_db),
            retry_policy=RetryPolicy(max_attempts=3),
        )

        logger.info("Generating strategic opportunities from focus areas...")
        result = orchestrator.run()

        opportunities_created = len(result.created_pm_idea_numbers)
        logger.info(f"✓ Discovery complete. Final state: {result.state}")
        logger.info(f"  Created {opportunities_created} pm-idea issue(s)")
        logger.info(f"  Runlog: {log_db}")
        if hasattr(gateway, "publish_discovery_run_artifact"):
            gateway.publish_discovery_run_artifact(
                state=result.state,
                created_pm_idea_numbers=result.created_pm_idea_numbers,
                deferred_count=result.deferred_count,
                dropped_count=result.dropped_count,
            )
            logger.info("  Published discovery run summary to wiki")
        if result.created_pm_idea_numbers:
            logger.info(f"  Issues: {', '.join(f'#{n}' for n in result.created_pm_idea_numbers)}")
        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 3


if __name__ == "__main__":
    sys.exit(main())
