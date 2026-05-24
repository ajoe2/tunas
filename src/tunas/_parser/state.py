"""Per-meet parser state (dict-indexed for O(1) lookups, reset at each B1)."""

from __future__ import annotations

from dataclasses import dataclass, field

from tunas.enums import Session
from tunas.geography import LSC
from tunas.models import Club, IndividualSwim, Meet, Relay, RelaySwim, Swimmer

__all__ = ["PendingIndividual", "ParserState"]


@dataclass
class PendingIndividual:
    """A D0 swimmer whose identity isn't resolvable yet (blank id_short).

    Held until a following D3 supplies an ``id_long``, or discarded (skipped) at
    the next non-continuation record.
    """

    swimmer: Swimmer
    results: list[IndividualSwim]
    raw_line: str
    line_no: int


@dataclass
class ParserState:
    """Mutable state for the meet currently being assembled."""

    meet: Meet
    clubs_by_key: dict[tuple[str, LSC | None], Club] = field(default_factory=dict)
    swimmers_by_id: dict[str, Swimmer] = field(default_factory=dict)
    current_club: Club | None = None
    unattached: bool = False
    current_swimmer: Swimmer | None = None
    current_individual_swims: list[IndividualSwim] = field(default_factory=list)
    pending_individual: PendingIndividual | None = None
    current_relays: dict[Session, Relay] = field(default_factory=dict)
    current_relay_legs: dict[Session, RelaySwim] = field(default_factory=dict)
    last_leaf: str | None = None  # "individual" | "relay"
