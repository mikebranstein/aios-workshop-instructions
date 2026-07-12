from typing import Dict, FrozenSet

from aios_orchestration_core.core.label_registry import LabelRegistry
from aios_orchestration_core.states.dev import DevState

DEV_CANONICAL_LABEL_BY_STATE: Dict[DevState, str] = {
    DevState.DEV_INTAKE: "dev:intake",
    DevState.DEV_DESIGN: "dev:design",
    DevState.DEV_BUILD: "dev:build",
    DevState.DEV_QA: "dev:qa",
    DevState.DEV_POLICY: "dev:policy",
    DevState.DEV_RELEASED: "dev:released",
    DevState.DEV_BLOCKED: "dev:blocked",
    DevState.DEV_NEEDS_HUMAN: "dev:needs-human",
}

DEV_CANONICAL_STATE_LABELS: FrozenSet[str] = frozenset(DEV_CANONICAL_LABEL_BY_STATE.values())

DEV_LEGACY_LABEL_BY_STATE: Dict[DevState, str] = {
    DevState.DEV_INTAKE: "feature-request",
    DevState.DEV_DESIGN: "intake-approved",
    DevState.DEV_BUILD: "design-approved",
    DevState.DEV_QA: "build-complete",
    DevState.DEV_POLICY: "qa-passed",
    DevState.DEV_RELEASED: "released",
    DevState.DEV_BLOCKED: "feature-blocked",
}

DEV_LABEL_REGISTRY: LabelRegistry[DevState] = LabelRegistry(
    canonical=DEV_CANONICAL_LABEL_BY_STATE,
    legacy=DEV_LEGACY_LABEL_BY_STATE,
)
