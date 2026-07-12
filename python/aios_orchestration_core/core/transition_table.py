from typing import Any, Dict, FrozenSet, Generic, Set, Tuple, TypeVar

S = TypeVar("S")
E = TypeVar("E")


class TransitionError(ValueError):
    """Raised when a transition is not defined in the table."""


class TransitionTable(Generic[S, E]):
    """Immutable, typed transition table used by all orchestration loops.

    Encapsulates a ``{(source_state, event): next_state}`` mapping and
    exposes safe query helpers so loop implementations share the same
    navigation logic without duplicating dictionary lookups.
    """

    def __init__(self, transitions: Dict[Tuple[S, E], S]) -> None:
        self._table: Dict[Tuple[S, E], S] = dict(transitions)

    # ------------------------------------------------------------------
    # Core navigation
    # ------------------------------------------------------------------

    def next_state(self, state: S, event: E) -> S:
        """Return the next state for *state* + *event*, or raise TransitionError."""
        key = (state, event)
        if key not in self._table:
            raise TransitionError(
                f"No transition defined for state={state!r} event={event!r}"
            )
        return self._table[key]

    def is_valid(self, state: S, event: E) -> bool:
        """Return True if *state* + *event* is a declared transition."""
        return (state, event) in self._table

    # ------------------------------------------------------------------
    # Inspection helpers
    # ------------------------------------------------------------------

    def allowed_events(self, state: S) -> FrozenSet[E]:
        """Return all events that can be fired from *state*."""
        events: Set[E] = set()
        for src, event in self._table:
            if src == state:
                events.add(event)
        return frozenset(events)

    def all_reachable_states(self) -> FrozenSet[Any]:
        """Return every state that appears as a source or target."""
        states: Set[Any] = set()
        for (src, _), tgt in self._table.items():
            states.add(src)
            states.add(tgt)
        return frozenset(states)

    def items(self) -> Any:
        """Expose underlying mapping items for registry cross-validation."""
        return self._table.items()
