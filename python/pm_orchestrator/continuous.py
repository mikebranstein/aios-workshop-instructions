"""Continuous PM Orchestrator — processes all pm-queued issues in a loop.

Continuously finds issues with the 'pm:queued' label and processes them through
the PM loop until no more queued issues remain.
"""

import logging
from typing import Optional

from aios_orchestration_core.github.pm_gateway import PMGateway
from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.policies.retry import RetryPolicy
from aios_orchestration_core.runlog.in_memory_store import TransitionLogStore
from aios_orchestration_core.states.pm import PMState
from pm_orchestrator.run_once import PMRunOnceOrchestrator, PMRunRegistry

logger = logging.getLogger(__name__)


class PMContinuousOrchestrator:
    """Continuously processes PM loop issues until queue is empty.
    
    Finds all issues with 'pm:queued' label and processes each one through
    PMRunOnceOrchestrator. After each issue completes, checks for new queued
    issues and repeats until none remain.
    """

    def __init__(
        self,
        gateway: PMGateway,
        log_store: TransitionLogStore,
        phase1_adapter: JudgmentLLMAdapter,
        research_planning_adapter: JudgmentLLMAdapter,
        synthesis_adapter: JudgmentLLMAdapter,
        phase2_adapter: JudgmentLLMAdapter,
        retry_policy: Optional[RetryPolicy] = None,
        min_research_count: int = 1,
        min_synthesis_confidence: float = 0.75,
        handoff_contract_version: str = "1.0.0",
        prompt_version: str = "pm-pilot-v1",
    ):
        self.gateway = gateway
        self.log_store = log_store
        self.phase1_adapter = phase1_adapter
        self.research_planning_adapter = research_planning_adapter
        self.synthesis_adapter = synthesis_adapter
        self.phase2_adapter = phase2_adapter
        self.retry_policy = retry_policy or RetryPolicy(max_attempts=3)
        self.min_research_count = min_research_count
        self.min_synthesis_confidence = min_synthesis_confidence
        self.handoff_contract_version = handoff_contract_version
        self.prompt_version = prompt_version
        self.run_registry = PMRunRegistry()

    def run_continuous(self) -> dict:
        """Process all pm:queued issues until none remain.
        
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
            queued_issues = self.gateway.list_open_issues_with_any_label(["pm:queued"])
            
            if not queued_issues:
                logger.info("No more pm:queued issues. Continuous loop complete.")
                break
            
            # Process first queued issue (FIFO)
            issue = queued_issues[0]
            logger.info(f"Processing pm:queued issue #{issue.number}: {issue.title}")
            
            try:
                # Create run_once orchestrator for this issue
                orchestrator = PMRunOnceOrchestrator(
                    gateway=self.gateway,
                    log_store=self.log_store,
                    run_registry=self.run_registry,
                    phase1_adapter=self.phase1_adapter,
                    research_planning_adapter=self.research_planning_adapter,
                    synthesis_adapter=self.synthesis_adapter,
                    phase2_adapter=self.phase2_adapter,
                    retry_policy=self.retry_policy,
                    min_research_count=self.min_research_count,
                    min_synthesis_confidence=self.min_synthesis_confidence,
                    handoff_contract_version=self.handoff_contract_version,
                    prompt_version=self.prompt_version,
                )
                
                # Run issue through PM loop
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
