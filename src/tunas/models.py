"""The tunas domain model.

Aggregates (``Meet``, ``Club``, ``Swimmer``, ``MeetResult`` and subclasses,
``RelaySwim``) are slotted, keyword-only dataclasses with identity equality
(``eq=False``) so the parser can wire a cyclic object graph in a single pass
without deduplication or hashing cost. Value types (``Time``, ``Split``,
``SwimmerContact``, ...) are frozen and hashable.
"""

from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tunas.enums import (
    Affiliation,
    AttachStatus,
    Citizenship,
    Course,
    Ethnicity,
    EventTimeClass,
    FileType,
    MeetType,
    MemberStatus,
    Organization,
    Region,
    RelayLegOrder,
    ResultStatus,
    Season,
    Sex,
    SplitType,
    Stroke,
)
from tunas.event import Event
from tunas.geography import LSC, Country, State
from tunas.time import Time

if TYPE_CHECKING:
    from tunas.enums import Session

__all__ = [
    "Swim",
    "MeetResult",
    "IndividualSwim",
    "Relay",
    "RelaySwim",
    "Split",
    "SwimmerContact",
    "SwimmerRegistration",
    "MeetHost",
    "SourceFile",
    "ClubEntryCounts",
    "Swimmer",
    "Club",
    "Meet",
]


# --------------------------------------------------------------------------- #
# Value types (frozen, hashable)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Split:
    """One split entry from a G0 record."""

    distance: int  # Cumulative distance from the start (50, 100, 150, ...)
    time: Time | None  # None if the split slot was present but unparseable
    split_type: SplitType


@dataclass(frozen=True)
class SwimmerContact:
    """Contact details from D1/D2. **Contains PII.** Reached via ``Swimmer.contact``."""

    address: str | None = None
    city: str | None = None
    state: State | None = None
    postal_code: str | None = None
    country: Country | None = None
    region: Region | None = None
    alt_mailing_name: str | None = None
    phone_primary: str | None = None
    phone_secondary: str | None = None


@dataclass(frozen=True)
class SwimmerRegistration:
    """Registration/demographic details from D1/D2/D3. **Contains sensitive PII.**"""

    member_status: MemberStatus | None = None
    registration_date: datetime.date | None = None
    season: Season | None = None
    ethnicity_primary: Ethnicity | None = None
    ethnicity_secondary: Ethnicity | None = None
    affiliations: frozenset[Affiliation] = frozenset()
    old_member_number: str | None = None
    fina_other_federation: str | None = None
    admin_info: str | None = None


@dataclass(frozen=True)
class MeetHost:
    """Meet host details from B2. Reached via ``Meet.host``."""

    name: str | None = None
    address_one: str | None = None
    address_two: str | None = None
    city: str | None = None
    state: State | None = None
    postal_code: str | None = None
    country: Country | None = None
    phone: str | None = None


@dataclass(frozen=True)
class SourceFile:
    """File-level metadata from A0/Z0. Shared by all meets in one file."""

    path: str | None = None
    file_type: FileType | None = None
    sdif_version: str | None = None
    software_name: str | None = None
    software_version: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    created: datetime.date | None = None
    submitted_by_lsc: LSC | None = None
    notes: str | None = None


@dataclass(frozen=True)
class ClubEntryCounts:
    """The five entry counts from a C2 record. Reached via ``Club.entry_counts``."""

    num_individual_swims: int | None = None
    num_athletes: int | None = None
    num_relay_entries: int | None = None
    num_relay_name_records: int | None = None
    num_split_records: int | None = None


# --------------------------------------------------------------------------- #
# Swim interface
# --------------------------------------------------------------------------- #


class Swim(ABC):
    """Abstract base for one swimmer's swim — ``IndividualSwim`` or ``RelaySwim``.

    Declares no instance fields, so it can be mixed into the slotted
    ``MeetResult`` dataclass without a slot-layout conflict. It is the common
    type behind ``Swimmer.swims``; both subclasses expose a uniform interface
    (``swimmer``, ``time``, ``status``, ``session``, ``event``, ``date``,
    ``meet``, ``course``, ``swimmer_age_class``, ``splits``, ``is_relay_leg``).
    """

    __slots__ = ()

    @property
    @abstractmethod
    def is_relay_leg(self) -> bool:
        """``True`` for a ``RelaySwim``, ``False`` for an ``IndividualSwim``."""


# --------------------------------------------------------------------------- #
# Meet results
# --------------------------------------------------------------------------- #


@dataclass(slots=True, kw_only=True, eq=False)
class MeetResult:
    """Shared base for a row in ``Meet.results`` (``IndividualSwim`` or ``Relay``)."""

    meet: Meet
    club: Club | None
    organization: Organization
    session: Session
    event: Event
    event_min_age: int | None
    event_max_age: int | None
    event_sex: Sex
    status: ResultStatus
    time: Time | None
    date: datetime.date | None
    event_number: str | None = None
    heat: int | None = None
    lane: int | None = None
    rank: int | None = None
    points: float | None = None
    seed_time: Time | None = None
    seed_course: Course | None = None
    event_min_time_class: EventTimeClass | None = None
    event_max_time_class: EventTimeClass | None = None


@dataclass(slots=True, kw_only=True, eq=False)
class IndividualSwim(MeetResult, Swim):
    """The result of an individual event — both a meet result and a swim."""

    swimmer: Swimmer
    swimmer_age_class: str | None = None
    attach_status: AttachStatus = AttachStatus.ATTACHED
    splits: list[Split] = field(default_factory=list)

    @property
    def is_relay_leg(self) -> bool:
        return False

    @property
    def course(self) -> Course | None:
        return self.event.course


@dataclass(slots=True, kw_only=True, eq=False)
class Relay(MeetResult):
    """A squad relay result (not a ``Swim`` — its legs are)."""

    relay_letter: str
    total_age: int | None = None
    legs: list[RelaySwim] = field(default_factory=list)
    alternates: list[RelaySwim] = field(default_factory=list)


@dataclass(slots=True, kw_only=True, eq=False)
class RelaySwim(Swim):
    """One swimmer's leg (or roster slot) on a relay, in one session."""

    swimmer: Swimmer | None
    relay: Relay
    order: RelayLegOrder | None = None
    time: Time | None = None
    status: ResultStatus = ResultStatus.OK
    takeoff_time: int | None = None  # hundredths of a second
    course: Course | None = None
    swimmer_age_class: str | None = None
    citizenship: Citizenship | Country | None = None
    splits: list[Split] = field(default_factory=list)

    @property
    def is_relay_leg(self) -> bool:
        return True

    @property
    def event(self) -> Event | None:
        """The individual event swum on this leg (e.g. ``FREE_100_SCY``)."""
        relay_event = self.relay.event
        if relay_event is None or self.order is None:
            return None
        try:
            order_num = int(self.order)
        except ValueError:  # ALTERNATE
            order_num = None
        if order_num is None or not (1 <= order_num <= 4):
            # A free relay's legs are all the same event even for alternates;
            # a medley alternate's stroke is undetermined.
            if relay_event.stroke is Stroke.FREESTYLE_RELAY:
                return relay_event.leg_event(1)
            return None
        return relay_event.leg_event(order_num)

    @property
    def date(self) -> datetime.date | None:
        return self.relay.date

    @property
    def meet(self) -> Meet:
        return self.relay.meet

    @property
    def session(self) -> Session:
        return self.relay.session


# --------------------------------------------------------------------------- #
# Aggregates
# --------------------------------------------------------------------------- #


@dataclass(slots=True, kw_only=True, eq=False)
class Swimmer:
    """A swimmer scoped to one meet, identified by member ID within it."""

    meet: Meet
    first_name: str
    last_name: str
    sex: Sex
    id_short: str | None = None  # 12-char short ID (USS#)
    id_long: str | None = None  # 14-char new long ID
    middle_initial: str | None = None
    preferred_first_name: str | None = None
    birthday: datetime.date | None = None
    citizenship: Citizenship | Country | None = None
    contact: SwimmerContact | None = None
    registration: SwimmerRegistration | None = None
    club: Club | None = None
    # Individual swims + counting relay legs. Typed as the concrete union (their
    # common base is Swim) so attribute access on elements is precise.
    swims: list[IndividualSwim | RelaySwim] = field(default_factory=list)

    @property
    def individual_swims(self) -> list[IndividualSwim]:
        return [s for s in self.swims if isinstance(s, IndividualSwim)]

    @property
    def relay_swims(self) -> list[RelaySwim]:
        return [s for s in self.swims if isinstance(s, RelaySwim)]

    @property
    def full_name(self) -> str:
        if self.middle_initial:
            return f"{self.first_name} {self.middle_initial} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    def swims_in(self, event: Event) -> list[IndividualSwim | RelaySwim]:
        """This swimmer's swims for an individual event, in source order (all outcomes).

        Matches flat-start individual swims and relay legs whose individual leg
        event equals ``event``.
        """
        return [s for s in self.swims if s.event == event]


@dataclass(slots=True, kw_only=True, eq=False)
class Club:
    """A club scoped to one meet, keyed by ``(team_code, lsc)``."""

    meet: Meet
    organization: Organization
    team_code: str
    lsc: LSC | None = None
    full_name: str | None = None
    abbreviated_name: str | None = None
    address_one: str | None = None
    address_two: str | None = None
    city: str | None = None
    state: State | None = None
    postal_code: str | None = None
    country: Country | None = None
    region: Region | None = None
    coach: str | None = None
    coach_phone: str | None = None
    short_name: str | None = None
    entry_counts: ClubEntryCounts | None = None
    results: list[MeetResult] = field(default_factory=list)
    swimmers: list[Swimmer] = field(default_factory=list)

    @property
    def individual_swims(self) -> list[IndividualSwim]:
        return [r for r in self.results if isinstance(r, IndividualSwim)]

    @property
    def relays(self) -> list[Relay]:
        return [r for r in self.results if isinstance(r, Relay)]


@dataclass(slots=True, kw_only=True, eq=False)
class Meet:
    """One meet's data, from a single SDIF file's B1 block."""

    organization: Organization
    name: str
    start_date: datetime.date
    end_date: datetime.date | None = None
    city: str | None = None
    address_one: str | None = None
    state: State | None = None
    address_two: str | None = None
    postal_code: str | None = None
    country: Country | None = None
    course: Course | None = None
    altitude: int | None = None
    meet_type: MeetType | None = None
    host: MeetHost | None = None
    source_file: SourceFile | None = None
    results: list[MeetResult] = field(default_factory=list)
    swimmers: list[Swimmer] = field(default_factory=list)
    clubs: list[Club] = field(default_factory=list)

    @property
    def individual_swims(self) -> list[IndividualSwim]:
        return [r for r in self.results if isinstance(r, IndividualSwim)]

    @property
    def relays(self) -> list[Relay]:
        return [r for r in self.results if isinstance(r, Relay)]

    def individual_swims_for(self, event: Event) -> list[IndividualSwim]:
        """Individual swims for an event, in source order."""
        return [r for r in self.individual_swims if r.event == event]

    def relays_for(self, event: Event) -> list[Relay]:
        """Relays for an event, in source order."""
        return [r for r in self.relays if r.event == event]
