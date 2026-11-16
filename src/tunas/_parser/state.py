"""Per-meet parser state (reset at each meet record)."""

from __future__ import annotations

from dataclasses import dataclass, field

from tunas._parser.fields import Record
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
    # Swimmers whose D0 carried no USS# at all, keyed by name, sex, birthday and
    # club so one person's consecutive records share a swimmer.
    swimmers_without_id: dict[tuple[object, ...], Swimmer] = field(default_factory=dict)
    current_club: Club | None = None
    unattached: bool = False
    current_swimmer: Swimmer | None = None
    current_individual_swims: list[IndividualSwim] = field(default_factory=list)
    pending_individual: PendingIndividual | None = None
    # Keyed by session; an entered (not-yet-swum) relay is keyed by None.
    current_relays: dict[Session | None, Relay] = field(default_factory=dict)
    current_relay_legs: dict[Session | None, RelaySwim] = field(default_factory=dict)
    # Running 0-based leg index per relay session for G0 split-distance offsetting:
    # seeded from each F0 leg number, advanced once per G0 record (see cl2._h_g0).
    relay_split_index: dict[Session | None, int] = field(default_factory=dict)
    last_result_kind: str | None = None  # "individual" | "relay"

    @property
    def attached_club(self) -> Club | None:
        """The current club, or None while parsing unattached entries."""
        return None if self.unattached else self.current_club


# `.hy3` splits entry and result across records (E1+E2, F1+F2), so the entry is
# buffered until its result arrives; one with no result is emitted as ENTERED.


@dataclass
class _Hy3EntryBase:
    """Event/seed fields shared by an individual (`E1`) and a relay (`F1`) entry."""

    event_sex: Sex | None
    distance: int | None
    stroke: Stroke | None
    event_min_age: int | None
    event_max_age: int | None
    event_number: str | None
    seed_time: Time | None
    seed_course: Course | None
    converted_seed_time: Time | None
    converted_seed_course: Course | None
    record: Record  # the entry line, for diagnostics if it is emitted unswum


@dataclass
class Hy3Entry(_Hy3EntryBase):
    """A parsed `E1` individual entry, awaiting its `E2` result."""

    swimmer: Swimmer | None


@dataclass
class Hy3RelayEntry(_Hy3EntryBase):
    """A parsed `F1` relay entry, awaiting its `F2` result."""

    relay_letter: str


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
    last_result_kind: str | None = None  # "individual" | "relay"

    @property
    def attached_club(self) -> Club | None:
        """The current club, or None while parsing unattached entries."""
        return None if self.unattached else self.current_club
