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

# ---------------------------------------------------------------------------
# PO tools
# ---------------------------------------------------------------------------

PO_PRIORITIZE_TOOL = ToolSpec(
    name="submit_po_prioritization_decision",
    description="Submit PO prioritization decision for a strategic opportunity.",
    parameters_schema={
        "type": "object",
        "required": ["decision", "reason"],
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["CREATE_FEATURE_REQUESTS", "DEFER", "REJECT"],
            },
            "reason": {"type": "string", "minLength": 1},
        },
    },
)

PO_CREATE_FEATURES_TOOL = ToolSpec(
    name="submit_po_feature_request_plan",
    description="Submit the list of feature requests to create from a strategic opportunity.",
    parameters_schema={
        "type": "object",
        "required": ["feature_requests"],
        "properties": {
            "feature_requests": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["title", "body", "priority_score"],
                    "properties": {
                        "title": {"type": "string", "minLength": 1},
                        "body": {"type": "string", "minLength": 1},
                        "priority_score": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                        },
                    },
                },
            }
        },
    },
)

TASK_TOOL_MAP.update(
    {
        "po_prioritize": PO_PRIORITIZE_TOOL,
        "po_create_features": PO_CREATE_FEATURES_TOOL,
    }
)

# ---------------------------------------------------------------------------
# Dev tools
# ---------------------------------------------------------------------------

DEV_INTAKE_TOOL = ToolSpec(
    name="submit_dev_intake_decision",
    description="Submit dev intake completeness gate decision.",
    parameters_schema={
        "type": "object",
        "required": ["decision", "reason"],
        "properties": {
            "decision": {"type": "string", "enum": ["APPROVED", "BLOCKED"]},
            "reason": {"type": "string", "minLength": 1},
        },
    },
)

DEV_DESIGN_TOOL = ToolSpec(
    name="submit_dev_design_decision",
    description="Submit dev design gate decision.",
    parameters_schema={
        "type": "object",
        "required": ["decision", "reason"],
        "properties": {
            "decision": {"type": "string", "enum": ["APPROVED", "REVISE", "BLOCKED"]},
            "reason": {"type": "string", "minLength": 1},
        },
    },
)

DEV_BUILD_TOOL = ToolSpec(
    name="submit_dev_build_decision",
    description="Submit dev build completion decision.",
    parameters_schema={
        "type": "object",
        "required": ["decision", "reason"],
        "properties": {
            "decision": {"type": "string", "enum": ["COMPLETE", "BLOCKED"]},
            "reason": {"type": "string", "minLength": 1},
        },
    },
)

DEV_QA_TOOL = ToolSpec(
    name="submit_dev_qa_decision",
    description="Submit dev QA gate decision.",
    parameters_schema={
        "type": "object",
        "required": ["decision", "reason"],
        "properties": {
            "decision": {"type": "string", "enum": ["PASSED", "FAILED"]},
            "reason": {"type": "string", "minLength": 1},
        },
    },
)

DEV_POLICY_TOOL = ToolSpec(
    name="submit_dev_policy_decision",
    description="Submit dev policy gate decision.",
    parameters_schema={
        "type": "object",
        "required": ["decision", "reason"],
        "properties": {
            "decision": {"type": "string", "enum": ["APPROVED", "REVIEW_REQUIRED"]},
            "reason": {"type": "string", "minLength": 1},
        },
    },
)

TASK_TOOL_MAP.update(
    {
        "dev_intake": DEV_INTAKE_TOOL,
        "dev_design": DEV_DESIGN_TOOL,
        "dev_build": DEV_BUILD_TOOL,
        "dev_qa": DEV_QA_TOOL,
        "dev_policy": DEV_POLICY_TOOL,
    }
)

# ---------------------------------------------------------------------------
# Foundation tools
# ---------------------------------------------------------------------------

FOUNDATION_RESEARCH_TOOL = ToolSpec(
    name="submit_foundation_research_decision",
    description="Submit foundation research agent decision.",
    parameters_schema={
        "type": "object",
        "required": ["decision", "reason"],
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["RECOMMEND", "NEEDS_MORE_RESEARCH", "BLOCKED"],
            },
            "reason": {"type": "string", "minLength": 1},
        },
    },
)

FOUNDATION_GATE_TOOL = ToolSpec(
    name="submit_foundation_gate_decision",
    description="Submit foundation architect gate decision.",
    parameters_schema={
        "type": "object",
        "required": ["decision", "reason"],
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["APPROVE_FOUNDATION", "REVISE_FOUNDATION", "BLOCK_FOUNDATION"],
            },
            "reason": {"type": "string", "minLength": 1},
        },
    },
)

TASK_TOOL_MAP.update(
    {
        "foundation_research": FOUNDATION_RESEARCH_TOOL,
        "foundation_gate": FOUNDATION_GATE_TOOL,
    }
)

# ---------------------------------------------------------------------------
# Architecture Review tools
# ---------------------------------------------------------------------------

ARCH_REVIEW_TOOL = ToolSpec(
    name="submit_arch_review_decision",
    description="Submit architecture review agent decision.",
    parameters_schema={
        "type": "object",
        "required": ["decision", "reason"],
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["NO_ACTION", "CREATE_REFACTOR_PLAN", "ESCALATE"],
            },
            "reason": {"type": "string", "minLength": 1},
        },
    },
)

ARCH_REFACTOR_PLAN_TOOL = ToolSpec(
    name="submit_arch_refactor_plan",
    description="Submit refactor planner decision and optional refactor-request titles.",
    parameters_schema={
        "type": "object",
        "required": ["decision", "reason"],
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["CREATE_REFACTOR_REQUESTS", "DEFER", "BLOCKED"],
            },
            "reason": {"type": "string", "minLength": 1},
            "refactor_requests": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["title", "body"],
                    "properties": {
                        "title": {"type": "string", "minLength": 1},
                        "body": {"type": "string", "minLength": 1},
                    },
                },
            },
        },
    },
)

DEBT_TRIAGE_TOOL = ToolSpec(
    name="submit_debt_triage_decision",
    description="Submit architecture debt triage decision.",
    parameters_schema={
        "type": "object",
        "required": ["decision", "reason"],
        "properties": {
            "decision": {"type": "string", "enum": ["TRIAGE", "DEFER"]},
            "reason": {"type": "string", "minLength": 1},
        },
    },
)

TASK_TOOL_MAP.update(
    {
        "arch_review": ARCH_REVIEW_TOOL,
        "arch_refactor_plan": ARCH_REFACTOR_PLAN_TOOL,
        "debt_triage": DEBT_TRIAGE_TOOL,
    }
)
