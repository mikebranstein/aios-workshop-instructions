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

FOUNDATION_RESEARCH_PLAN_TOOL = ToolSpec(
    name="submit_foundation_research_plan",
    description="Submit foundation research plan (decision areas to spawn as issues).",
    parameters_schema={
        "type": "object",
        "required": ["research_areas"],
        "properties": {
            "research_areas": {
                "type": "array",
                "minItems": 1,
                "maxItems": 10,
                "items": {"type": "string", "minLength": 1},
            },
            "reason": {"type": "string", "minLength": 1},
        },
    },
)

FOUNDATION_RESEARCH_WORKER_TOOL = ToolSpec(
    name="submit_foundation_research_worker_result",
    description="Submit foundation research worker result for a linked research issue.",
    parameters_schema={
        "type": "object",
        "required": ["decision", "summary", "next_actions"],
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["COMPLETE", "NEEDS_MORE_RESEARCH", "BLOCKED"],
            },
            "summary": {"type": "string", "minLength": 1},
            "wiki_page_title": {"type": "string", "minLength": 1},
            "wiki_summary": {"type": "string", "minLength": 1},
            "adr_title": {"type": "string", "minLength": 1},
            "adr_summary": {"type": "string", "minLength": 1},
            "next_actions": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
            },
        },
    },
)

FOUNDATION_WIKI_MANAGER_TOOL = ToolSpec(
    name="submit_foundation_wiki_manager_result",
    description="Submit wiki management decision for foundation research outputs.",
    parameters_schema={
        "type": "object",
        "required": ["decision", "page_path", "page_content", "content_index_summary"],
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["CREATE_PAGE", "UPDATE_PAGE", "REORGANIZE_AND_WRITE"],
            },
            "page_path": {"type": "string", "minLength": 1},
            "page_content": {"type": "string", "minLength": 1},
            "content_index_summary": {"type": "string", "minLength": 1},
            "page_moves": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["from_path", "to_path"],
                    "properties": {
                        "from_path": {"type": "string", "minLength": 1},
                        "to_path": {"type": "string", "minLength": 1},
                    },
                },
            },
            "reason": {"type": "string", "minLength": 1},
        },
    },
)

FOUNDATION_ADR_GENERATOR_TOOL = ToolSpec(
    name="submit_foundation_adr",
    description="Submit a generated Foundation ADR for writing to docs/adr/.",
    parameters_schema={
        "type": "object",
        "required": [
            "adr_title",
            "context_section",
            "decision_section",
            "alternatives_section",
            "rationale_section",
            "consequences_section",
            "validation_strategy_section",
            "rollback_section",
            "related_decisions_section",
        ],
        "properties": {
            "adr_title": {"type": "string", "minLength": 1},
            "context_section": {"type": "string", "minLength": 1},
            "decision_section": {"type": "string", "minLength": 1},
            "alternatives_section": {"type": "string", "minLength": 1},
            "rationale_section": {"type": "string", "minLength": 1},
            "consequences_section": {"type": "string", "minLength": 1},
            "validation_strategy_section": {"type": "string", "minLength": 1},
            "rollback_section": {"type": "string", "minLength": 1},
            "related_decisions_section": {"type": "string", "minLength": 1},
        },
    },
)

TASK_TOOL_MAP.update(
    {
        "foundation_research": FOUNDATION_RESEARCH_TOOL,
        "foundation_gate": FOUNDATION_GATE_TOOL,
        "foundation_research_plan": FOUNDATION_RESEARCH_PLAN_TOOL,
        "foundation_research_worker": FOUNDATION_RESEARCH_WORKER_TOOL,
        "foundation_wiki_manager": FOUNDATION_WIKI_MANAGER_TOOL,
        "wiki_manager": FOUNDATION_WIKI_MANAGER_TOOL,
        "adr_generator": FOUNDATION_ADR_GENERATOR_TOOL,
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

# ---------------------------------------------------------------------------
# Cross-cutting tools
# ---------------------------------------------------------------------------

FORMAT_ISSUE_COMMENT_TOOL = ToolSpec(
    name="submit_formatted_issue_comment",
    description="Submit the polished Markdown rewrite of a GitHub issue comment.",
    parameters_schema={
        "type": "object",
        "required": ["formatted_markdown"],
        "properties": {
            "formatted_markdown": {"type": "string", "minLength": 1},
        },
    },
)

TASK_TOOL_MAP.update(
    {
        "format_issue_comment": FORMAT_ISSUE_COMMENT_TOOL,
    }
)

# ---------------------------------------------------------------------------
# Discovery tools
# ---------------------------------------------------------------------------

DISCOVERY_IDEA_SCOUT_TOOL = ToolSpec(
    name="submit_discovery_idea_scout_result",
    description="Submit discovered pm-idea candidates from Idea Scout.",
    parameters_schema={
        "type": "object",
        "required": ["candidates"],
        "properties": {
            "candidates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["title", "body", "decision"],
                    "properties": {
                        "title": {"type": "string", "minLength": 1},
                        "body": {"type": "string", "minLength": 1},
                        "decision": {
                            "type": "string",
                            "enum": ["CREATE_PM_IDEA", "DEFER", "DROP"],
                        },
                    },
                },
            }
        },
    },
)

TASK_TOOL_MAP.update(
    {
        "discovery_idea_scout": DISCOVERY_IDEA_SCOUT_TOOL,
    }
)

# ---------------------------------------------------------------------------
# Foundation discovery-focus synthesis tool
# ---------------------------------------------------------------------------

FOUNDATION_DISCOVERY_FOCUS_SYNTHESIS_TOOL = ToolSpec(
    name="submit_foundation_discovery_focus",
    description=(
        "Submit the synthesized DISCOVERY-FOCUS.md content derived from FOUNDATION.md. "
        "Populate every field that can be inferred; leave placeholder_fields for sections "
        "that require human input (e.g. success metrics, signal sources)."
    ),
    parameters_schema={
        "type": "object",
        "required": ["focus_content", "confidence", "placeholder_fields"],
        "properties": {
            "focus_content": {
                "type": "string",
                "minLength": 1,
                "description": "Full Markdown content for DISCOVERY-FOCUS.md.",
            },
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "Confidence level for the synthesized content.",
            },
            "placeholder_fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Names of sections whose body is a TODO placeholder "
                    "(i.e. contains <!-- TODO: fill in this section -->). "
                    "Do NOT include sections that contain only '(inferred)' content."
                ),
            },
        },
    },
)

TASK_TOOL_MAP.update(
    {
        "foundation_discovery_focus_synthesis": FOUNDATION_DISCOVERY_FOCUS_SYNTHESIS_TOOL,
        "foundation_discovery_focus_verify": ToolSpec(
            name="submit_discovery_focus_verification",
            description=(
                "Submit the result of verifying DISCOVERY-FOCUS.md has the required sections "
                "populated with substantive content (not TODO placeholders or empty bodies)."
            ),
            parameters_schema={
                "type": "object",
                "required": ["passed", "verdict", "failing_sections"],
                "properties": {
                    "passed": {
                        "type": "boolean",
                        "description": (
                            "True if every required section contains substantive content. "
                            "False if one or more required sections are empty, TODO-only, or missing."
                        ),
                    },
                    "verdict": {
                        "type": "string",
                        "minLength": 1,
                        "description": "One-paragraph summary of the verification result.",
                    },
                    "failing_sections": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Names of required sections that are empty, contain only a TODO placeholder, "
                            "or are missing entirely. Empty list if passed=true."
                        ),
                    },
                },
            },
        ),
    }
)
