"""Continuous Dev Orchestrator — processes all dev:intake issues in a loop.

Continuously finds issues with the 'dev:intake' label and processes them through
the Dev loop until no more intake issues remain.
"""

import logging
from typing import Optional

from aios_orchestration_core.github.dev_gateway import DevGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from dev_orchestrator.run_once import DevRunOnceOrchestrator, DevRunRegistry

logger = logging.getLogger(__name__)


class DevContinuousOrchestrator:
    """Continuously processes Dev loop issues until queue is empty.
    
    Finds all issues with 'dev:intake' label and processes each one through
    DevRunOnceOrchestrator. After each issue completes, checks for new intake
    issues and repeats until none remain.
    """

    def __init__(
        self,
        gateway: DevGateway,
        log_store: TransitionLogStore,
        intake_adapter: JudgmentLLMAdapter,
        design_adapter: JudgmentLLMAdapter,
        build_adapter: JudgmentLLMAdapter,
        qa_adapter: JudgmentLLMAdapter,
        policy_adapter: JudgmentLLMAdapter,
        handoff_contract_version: str = "1.0.0",
        prompt_version: str = "dev-pilot-v1",
    ):
        self.gateway = gateway
        self.log_store = log_store
        self.intake_adapter = intake_adapter
        self.design_adapter = design_adapter
        self.build_adapter = build_adapter
        self.qa_adapter = qa_adapter
        self.policy_adapter = policy_adapter
        self.handoff_contract_version = handoff_contract_version
        self.prompt_version = prompt_version
        self.run_registry = DevRunRegistry()

    def run_continuous(self) -> dict:
        """Process all dev:intake issues until none remain.
        
        Returns:
            dict with keys:
                - issues_processed: int count of issues processed
                - final_issues: list of final issue states
                - errors: list of (issue_number, error) tuples
        """
        issues_processed = []
        errors = []

        while True:
            # Find next intake issue
            intake_issues = self.gateway.list_open_issues_with_any_label(["dev:intake"])
            
            if not intake_issues:
                logger.info("No more dev:intake issues. Continuous loop complete.")
                break
            
            # Process first intake issue (FIFO)
            issue = intake_issues[0]
            logger.info(f"Processing dev:intake issue #{issue.number}: {issue.title}")
            
            try:
                # Create run_once orchestrator for this issue
                orchestrator = DevRunOnceOrchestrator(
                    gateway=self.gateway,
                    log_store=self.log_store,
                    run_registry=self.run_registry,
                    intake_adapter=self.intake_adapter,
                    design_adapter=self.design_adapter,
                    build_adapter=self.build_adapter,
                    qa_adapter=self.qa_adapter,
                    policy_adapter=self.policy_adapter,
                    handoff_contract_version=self.handoff_contract_version,
                    prompt_version=self.prompt_version,
                )
                
                # Run issue through Dev loop
                result = orchestrator.run_once(issue.number)
                issues_processed.append({
                    "issue_number": issue.number,
                    "final_state": result.current_state,
                    "run_id": result.run_id if hasattr(result, "run_id") else None,
                })
                logger.info(f"✓ Issue #{issue.number} completed with state: {result.current_state}")
                
            except Exception as e:
                logger.error(f"✗ Error processing issue #{issue.number}: {e}")
                errors.append((issue.number, str(e)))
                # Continue to next issue instead of failing
        
        return {
            "issues_processed": len(issues_processed),
            "final_issues": issues_processed,
            "errors": errors,
        }
