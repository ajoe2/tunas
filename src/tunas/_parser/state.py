"""Per-meet parser state (reset at each B1 record)."""

from __future__ import annotations

from dataclasses import dataclass, field

from tunas.enums import Session
from tunas.geography import LSC
from tunas.models import Club, IndividualSwim, Meet, Relay, RelaySwim, Swimmer

__all__ = ["PendingIndividual", "ParserState"]


@dataclass
class PendingIndividual:
    """A D0 swimmer with an unresolved identity (blank id_short), pending a D3 record."""

    swimmer: Swimmer
    results: list[IndividualSwim]
    raw_line: str
    line_no: int


@dataclass
class ParserState:
    """Mutable assembly state for the current meet."""

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
