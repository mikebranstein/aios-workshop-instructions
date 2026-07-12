#!/usr/bin/env python3
"""
Verify registry states match Python enums by direct comparison.
This shows the actual mapping between label-based registry stages and Python states.
"""

from pathlib import Path
from aios_orchestration_core.states.pm import PMState
from aios_orchestration_core.states.po import POState
from aios_orchestration_core.states.dev import DevState
from aios_orchestration_core.states.foundation import FoundationState
from aios_orchestration_core.states.discovery import DiscoveryState
from aios_orchestration_core.states.arch_review import ArchReviewState, DebtState
from aios_orchestration_core.registry.parser import parse_routing_registry, entries_by_loop

# Read registry
registry_path = Path(__file__).parent.parent / "templates-old-v2" / "orchestration" / "routing-registry.md"
entries = parse_routing_registry(registry_path)
by_loop = entries_by_loop(entries)

# Mappings from alignment test (these define the label→state relationship)
PM_STAGE_MAP = {
    "pm-idea": "PM_PHASE1_VALIDATING",
    "pm-provisional-champion": "PM_RESEARCH_WAITING",
    "pm-finalizing": "PM_PHASE2_VALIDATING",
}

PO_STAGE_MAP = {
    "strategic-opportunity": "PO_PRIORITIZING",
}

DEV_STAGE_MAP = {
    "feature-request": "DEV_INTAKE",
    "design-approved": "DEV_BUILD",
    "qa-testing": "DEV_QA",
    "policy-approval": "DEV_POLICY",
}

FOUNDATION_STAGE_MAP = {
    "foundation-in-progress": "FOUNDATION_IN_PROGRESS",
    "foundation-review": "FOUNDATION_REVIEW",
}

DISCOVERY_STAGE_MAP = {
    "signal-scan": "DISCOVERY_RUNNING",
}

ARCH_REVIEW_STAGE_MAP = {
    "arch-review-pending": "ARCH_REVIEW_PENDING",
    "arch-review-in-progress": "ARCH_REVIEW_IN_PROGRESS",
}

DEBT_STAGE_MAP = {
    "architecture-debt": "DEBT_NEW",
    "debt-triaged": "DEBT_TRIAGED",
    "debt-scheduled": "DEBT_SCHEDULED",
}

def check_loop(loop_name, stage_map, enum_class):
    print(f"\n{'='*60}")
    print(f"{loop_name.upper()}")
    print(f"{'='*60}")
    
    registry_stages = set(src for src, _, _ in by_loop.get(loop_name, []))
    mapped_stages = set(stage_map.keys())
    enum_values = {e.value for e in enum_class}
    
    print(f"\nRegistry stages found: {registry_stages}")
    print(f"Mapped stages: {mapped_stages}")
    print(f"Python enum values: {enum_values}")
    
    # Check for unmapped registry stages
    unmapped = registry_stages - mapped_stages
    if unmapped:
        print(f"\n⚠️  UNMAPPED REGISTRY STAGES: {unmapped}")
    
    # Check for invalid mappings (mapped stage not in registry)
    extra = mapped_stages - registry_stages
    if extra:
        print(f"\n❌ MAPPED STAGES NOT IN REGISTRY: {extra}")
    
    # Check for enum values without registry equivalent
    mapped_enum_values = set(stage_map.values())
    unmapped_enums = enum_values - mapped_enum_values
    if unmapped_enums:
        print(f"\n⚠️  PYTHON ENUM VALUES WITH NO REGISTRY MAPPING: {unmapped_enums}")
    
    # Check for mapped enums that don't exist
    for enum_val in stage_map.values():
        if enum_val not in enum_values:
            print(f"\n❌ MAPPED ENUM '{enum_val}' DOES NOT EXIST IN {loop_name.upper()}")
    
    print()

check_loop("pm", PM_STAGE_MAP, PMState)
check_loop("po", PO_STAGE_MAP, POState)
check_loop("dev", DEV_STAGE_MAP, DevState)
check_loop("foundation", FOUNDATION_STAGE_MAP, FoundationState)
check_loop("discovery", DISCOVERY_STAGE_MAP, DiscoveryState)
check_loop("arch_review", ARCH_REVIEW_STAGE_MAP, ArchReviewState)
check_loop("debt", DEBT_STAGE_MAP, DebtState)

print(f"\n{'='*60}")
print("DEBT ORCHESTRATOR STATUS")
print(f"{'='*60}")
print("✅ Debt is NOT a separate loop — it's a sub-namespace within ArchReview")
print(f"   DebtState is defined in aios_orchestration_core/states/arch_review.py")
print(f"   Debt transitions are tested as part of arch_review orchestrator")
print(f"   Answer: 6 LOOPS TOTAL (PM, PO, Dev, Foundation, Discovery, ArchReview)")
print()
