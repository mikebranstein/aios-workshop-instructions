#!/usr/bin/env python3
"""Dev Orchestrator Runner — Execute Dev loop against any GitHub repo (continuous or single issue)."""

import argparse
import logging
import os
import sys
from pathlib import Path

from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.llm.adapter_factory import create_adapter
from aios_orchestration_core.github.comment_formatter import build_comment_formatter
from aios_orchestration_core.repo_context import RepoContext
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.runlog.paths import default_runlog_dir
from dev_orchestrator.run_once import DevRunOnceOrchestrator, DevRunRegistry
from dev_orchestrator.continuous import DevContinuousOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_LOG_DIR = default_runlog_dir("dev")


class StubLLMAdapter(JudgmentLLMAdapter):
    def __init__(self, model: str = "auto"):
        self.model = model

    def invoke_json(self, task_type: str, prompt_vars: dict, model_hint: str = ""):
        stubs = {
            "DEV_INTAKE": {"ready_for_design": True},
            "DEV_DESIGN": {"design_complete": True},
            "DEV_BUILD": {"build_complete": True},
            "DEV_QA": {"qa_passed": True},
            "DEV_POLICY": {"policy_approved": True},
        }
        return type("Result", (), {"payload": stubs.get(task_type, {}), "model": self.model})()


def main():
    parser = argparse.ArgumentParser(description="Run Dev orchestrator (continuous or single issue)")
    parser.add_argument("repo_or_issue", nargs="?", help="'owner/repo' or issue number")
    parser.add_argument("issue_number", nargs="?", type=int)
    parser.add_argument("--continuous", action="store_true")
    parser.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR), help="Directory for runlog output")
    parser.add_argument("--model", default="auto")
    parser.add_argument("--stub", action="store_true", help="Use stub adapter instead of GitHub Copilot")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    target_repo = os.environ.get("AIOS_TARGET_REPO")
    issue_number = None

    if args.repo_or_issue is None:
        if not target_repo:
            print("Error: Must provide 'owner/repo' or set AIOS_TARGET_REPO", file=sys.stderr)
            return 1
        issue_number = args.issue_number
    elif "/" in args.repo_or_issue:
        target_repo = args.repo_or_issue
        issue_number = args.issue_number
    else:
        if target_repo:
            try:
                issue_number = int(args.repo_or_issue)
            except ValueError:
                print(f"Error: Expected issue number, got '{args.repo_or_issue}'", file=sys.stderr)
                return 1
        else:
            print(f"Error: Expected 'owner/repo', got '{args.repo_or_issue}'", file=sys.stderr)
            return 1

    mode = "single" if issue_number else "continuous"

    if not target_repo:
        print("Error: No target repo", file=sys.stderr)
        return 1

    try:
        context = RepoContext.from_string(target_repo)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[DRY RUN] Dev orchestrator: {context}, Mode: {mode}")
        if mode == "single":
            print(f"  Issue: {issue_number}")
        return 0

    Path(args.log_dir).mkdir(parents=True, exist_ok=True)

    try:
        gateway = context.create_dev_gateway()
    except Exception as e:
        print(f"Error creating gateway: {e}", file=sys.stderr)
        return 2

    try:
        if mode == "single":
            return _run_single(gateway, args, issue_number)
        else:
            return _run_continuous(gateway, args)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 3


def _run_single(gateway, args, issue_number: int) -> int:
    print(f"Running Dev orchestrator on issue {issue_number}")
    print(f"  Adapter: {'stub' if args.stub else 'GitHub Copilot'}")
    log_db = f"{args.log_dir}/dev_issue_{issue_number}.runlog.md"
    adapter = create_adapter(model=args.model, use_stub=args.stub, stub_class=StubLLMAdapter)
    gateway.comment_formatter = build_comment_formatter(adapter)
    orchestrator = DevRunOnceOrchestrator(
        gateway=gateway,
        log_store=TransitionLogStore(log_db),
        run_registry=DevRunRegistry(),
        intake_adapter=adapter,
        design_adapter=adapter,
        build_adapter=adapter,
        qa_adapter=adapter,
        policy_adapter=adapter,
    )
    result = orchestrator.run_once(issue_number)
    print(f"✓ Completed. Final state: {result.current_state}")
    return 0


def _run_continuous(gateway, args) -> int:
    print(f"Running Dev orchestrator in CONTINUOUS mode")
    print(f"  Adapter: {'stub' if args.stub else 'GitHub Copilot'}")
    log_db = f"{args.log_dir}/dev_continuous.runlog.md"
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
    orchestrator = DevContinuousOrchestrator(
        gateway=gateway,
        log_store=TransitionLogStore(log_db),
        intake_adapter=adapter,
        design_adapter=adapter,
        build_adapter=adapter,
        qa_adapter=adapter,
        policy_adapter=adapter,
    )
    result = orchestrator.run_continuous()
    print(f"✓ Continuous run complete: {result['issues_processed']} issues processed")
    return 0 if not result['errors'] else 3


if __name__ == "__main__":
    sys.exit(main())
