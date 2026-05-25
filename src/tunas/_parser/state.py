"""Per-meet parser state (reset at each meet record)."""

from __future__ import annotations

from dataclasses import dataclass, field

from tunas.enums import Course, Session, Sex, Stroke
from tunas.geography import LSC
from tunas.models import Club, IndividualSwim, Meet, Relay, RelaySwim, Swimmer
from tunas.time import Time

__all__ = [
    "PendingIndividual",
    "ParserState",
    "Hy3Entry",
    "Hy3RelayEntry",
    "Hy3State",
]


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


# --------------------------------------------------------------------------- #
# Hy-Tek `.hy3` state — entry/result are split across separate records
# (E1+E2 for individuals, F1+F2 for relays), so the entry is buffered until
# its result arrives.
# --------------------------------------------------------------------------- #


@dataclass
class Hy3Entry:
    """A parsed `E1` individual entry, awaiting its `E2` result."""

    swimmer: Swimmer | None
    event_sex: Sex | None
    distance: int | None
    stroke: Stroke | None
    seed_time: Time | None
    seed_course: Course | None
    converted_seed_time: Time | None
    converted_seed_course: Course | None


@dataclass
class Hy3RelayEntry:
    """A parsed `F1` relay entry, awaiting its `F2` result."""

    relay_letter: str
    event_sex: Sex | None
    distance: int | None
    stroke: Stroke | None
    seed_time: Time | None
    seed_course: Course | None
    converted_seed_time: Time | None
    converted_seed_course: Course | None


@dataclass
class Hy3State:
    """Mutable assembly state for the current `.hy3` meet."""

    meet: Meet
    clubs_by_key: dict[tuple[str, LSC | None], Club] = field(default_factory=dict)
    swimmers_by_number: dict[str, Swimmer] = field(default_factory=dict)
    current_club: Club | None = None
    unattached: bool = False
    current_swimmer: Swimmer | None = None
    current_age_class: str | None = None  # D1 age, applied to that athlete's swims
    pending_entry: Hy3Entry | None = None
    pending_relay_entry: Hy3RelayEntry | None = None
    current_individual_swim: IndividualSwim | None = None
    current_relay: Relay | None = None
    last_leaf: str | None = None  # "individual" | "relay"
