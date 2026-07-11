from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters_schema: Dict[str, Any]


PM_PHASE1_TOOL = ToolSpec(
    name="submit_pm_phase1_decision",
    description="Submit PM Phase 1 strategic validation decision.",
    parameters_schema={
        "type": "object",
        "required": ["decision", "reason"],
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["PROVISIONAL_CHAMPION", "DEFER", "BLOCK"],
            },
            "reason": {"type": "string", "minLength": 1},
        },
    },
)

PM_RESEARCH_SYNTHESIS_TOOL = ToolSpec(
    name="submit_pm_research_synthesis",
    description="Submit PM research synthesis summary and confidence.",
    parameters_schema={
        "type": "object",
        "required": ["summary", "confidence_score", "closed_linked_research_count"],
        "properties": {
            "summary": {"type": "string", "minLength": 1},
            "confidence_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "closed_linked_research_count": {"type": "integer", "minimum": 0},
        },
    },
)

PM_PHASE2_TOOL = ToolSpec(
    name="submit_pm_phase2_decision",
    description="Submit PM Phase 2 final decision.",
    parameters_schema={
        "type": "object",
        "required": ["decision", "reason", "confidence_score"],
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["CHAMPION", "DEFER", "BLOCK", "ESCALATE"],
            },
            "reason": {"type": "string", "minLength": 1},
            "confidence_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        },
    },
)

PM_RESEARCH_TASK_PLAN_TOOL = ToolSpec(
    name="submit_pm_research_task_plan",
    description="Submit PM research task plan for missing evidence.",
    parameters_schema={
        "type": "object",
        "required": ["tasks"],
        "properties": {
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["topic", "persona"],
                    "properties": {
                        "topic": {"type": "string", "minLength": 1},
                        "persona": {"type": "string", "minLength": 1},
                    },
                },
            }
        },
    },
)

TASK_TOOL_MAP = {
    "pm_phase1": PM_PHASE1_TOOL,
    "pm_research_synthesis": PM_RESEARCH_SYNTHESIS_TOOL,
    "pm_phase2": PM_PHASE2_TOOL,
    "pm_research_task_plan": PM_RESEARCH_TASK_PLAN_TOOL,
}
