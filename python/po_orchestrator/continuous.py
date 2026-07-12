"""Continuous PO Orchestrator — processes all po:queued issues in a loop.

Continuously finds issues with the 'po:queued' label and processes them through
the PO loop until no more queued issues remain.
"""

import logging
from typing import Optional

from aios_orchestration_core.github.po_gateway import POGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from po_orchestrator.run_once import PORunOnceOrchestrator, PORunRegistry

logger = logging.getLogger(__name__)


class POContinuousOrchestrator:
    """Continuously processes PO loop issues until queue is empty.
    
    Finds all issues with 'po:queued' label and processes each one through
    PORunOnceOrchestrator. After each issue completes, checks for new queued
    issues and repeats until none remain.
    """

    def __init__(
        self,
        gateway: POGateway,
        log_store: TransitionLogStore,
        prioritize_adapter: JudgmentLLMAdapter,
        create_features_adapter: JudgmentLLMAdapter,
        handoff_contract_version: str = "1.0.0",
        prompt_version: str = "po-pilot-v1",
    ):
        self.gateway = gateway
        self.log_store = log_store
        self.prioritize_adapter = prioritize_adapter
        self.create_features_adapter = create_features_adapter
        self.handoff_contract_version = handoff_contract_version
        self.prompt_version = prompt_version
        self.run_registry = PORunRegistry()

    def run_continuous(self) -> dict:
        """Process all po:queued issues until none remain.
        
        Returns:
            dict with keys:
                - issues_processed: int count of issues processed
                - final_issues: list of final issue states
                - errors: list of (issue_number, error) tuples
        """
        issues_processed = []
        errors = []

        while True:
            # Find next queued issue
            queued_issues = self.gateway.list_open_issues_with_any_label(["po:queued"])
            
            if not queued_issues:
                logger.info("No more po:queued issues. Continuous loop complete.")
                break
            
            # Process first queued issue (FIFO)
            issue = queued_issues[0]
            logger.info(f"Processing po:queued issue #{issue.number}: {issue.title}")
            
            try:
                # Create run_once orchestrator for this issue
                orchestrator = PORunOnceOrchestrator(
                    gateway=self.gateway,
                    log_store=self.log_store,
                    run_registry=self.run_registry,
                    prioritize_adapter=self.prioritize_adapter,
                    create_features_adapter=self.create_features_adapter,
                    handoff_contract_version=self.handoff_contract_version,
                    prompt_version=self.prompt_version,
                )
                
                # Run issue through PO loop
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
