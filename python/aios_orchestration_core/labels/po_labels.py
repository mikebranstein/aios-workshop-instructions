from typing import Dict, FrozenSet

from aios_orchestration_core.core.label_registry import LabelRegistry
from aios_orchestration_core.states.po import POState

PO_CANONICAL_LABEL_BY_STATE: Dict[POState, str] = {
    POState.PO_QUEUED: "po:queued",
    POState.PO_PRIORITIZING: "po:prioritizing",
    POState.PO_CREATING_FEATURES: "po:creating-features",
    POState.PO_FEATURE_REQUESTS_CREATED: "po:feature-requests-created",
    POState.PO_DEFERRED: "po:deferred",
    POState.PO_REJECTED: "po:rejected",
    POState.PO_NEEDS_HUMAN: "po:needs-human",
}

PO_CANONICAL_STATE_LABELS: FrozenSet[str] = frozenset(PO_CANONICAL_LABEL_BY_STATE.values())

# Legacy labels match the templates-v2 orchestrator style for bridge compatibility.
PO_LEGACY_LABEL_BY_STATE: Dict[POState, str] = {
    POState.PO_QUEUED: "strategic-opportunity",
    POState.PO_FEATURE_REQUESTS_CREATED: "feature-requests-created",
    POState.PO_DEFERRED: "po-deferred",
    POState.PO_REJECTED: "po-rejected",
}

PO_LABEL_REGISTRY: LabelRegistry[POState] = LabelRegistry(
    canonical=PO_CANONICAL_LABEL_BY_STATE,
    legacy=PO_LEGACY_LABEL_BY_STATE,
)
