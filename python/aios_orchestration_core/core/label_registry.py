from typing import Dict, FrozenSet, Generic, Optional, TypeVar

S = TypeVar("S")


class LabelRegistry(Generic[S]):
    """Maps loop states to canonical and legacy GitHub labels.

    Each loop instantiates one registry from its state→label dicts.
    Canonical labels use the ``loop:state`` scheme (e.g. ``pm:queued``).
    Legacy labels are the older ``pm-idea``-style strings kept for
    bridge-mode dual-write during migrations.

    Reverse lookup (label → state) prefers canonical over legacy so
    that any conflict during migration resolves deterministically.
    """

    def __init__(
        self,
        canonical: Dict[S, str],
        legacy: Optional[Dict[S, str]] = None,
    ) -> None:
        self._canonical: Dict[S, str] = dict(canonical)
        self._legacy: Dict[S, str] = dict(legacy or {})

        # Build reverse lookup; canonical wins on collision.
        self._by_label: Dict[str, S] = {}
        for state, label in self._legacy.items():
            self._by_label[label] = state
        for state, label in self._canonical.items():
            self._by_label[label] = state

    # ------------------------------------------------------------------
    # Forward lookups (state → label)
    # ------------------------------------------------------------------

    def canonical_label(self, state: S) -> str:
        """Return the canonical label for *state*."""
        return self._canonical[state]

    def legacy_label(self, state: S) -> Optional[str]:
        """Return the legacy label for *state*, or None if not defined."""
        return self._legacy.get(state)

    # ------------------------------------------------------------------
    # Reverse lookup (label → state)
    # ------------------------------------------------------------------

    def state_for_label(self, label: str) -> Optional[S]:
        """Return the state mapped to *label*, or None if unrecognised."""
        return self._by_label.get(label)

    # ------------------------------------------------------------------
    # Label-set properties
    # ------------------------------------------------------------------

    @property
    def all_canonical_labels(self) -> FrozenSet[str]:
        return frozenset(self._canonical.values())

    @property
    def all_legacy_labels(self) -> FrozenSet[str]:
        return frozenset(self._legacy.values())

    @property
    def all_known_labels(self) -> FrozenSet[str]:
        return self.all_canonical_labels | self.all_legacy_labels
