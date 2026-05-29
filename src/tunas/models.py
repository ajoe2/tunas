"""Tunas domain model.

Aggregates (Meet, Club, Swimmer, MeetResult subclasses, RelaySwim) are slotted,
keyword-only dataclasses with identity equality (eq=False) to support efficient
single-pass parsing. Value types (Time, Split, SwimmerContact, SwimmerRegistration,
MeetHost, SourceFile, ClubEntryCounts) are frozen and hashable.
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
    Hy3FileType,
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

# A swimmer/leg citizenship is either one of the two non-country SDIF codes or a
# country code (see :class:`~tunas.enums.Citizenship`).
type CitizenshipOrCountry = Citizenship | Country

# Relay leg position -> 1-based leg number (NOT_SWUM/ALTERNATE are absent).
_LEG_NUMBERS: dict[RelayLegOrder, int] = {
    RelayLegOrder.LEG_1: 1,
    RelayLegOrder.LEG_2: 2,
    RelayLegOrder.LEG_3: 3,
    RelayLegOrder.LEG_4: 4,
}


# --------------------------------------------------------------------------- #
# repr / str helpers
# --------------------------------------------------------------------------- #
#
# The aggregates form a cyclic graph (Meet <-> Club <-> Swimmer <-> result),
# so the dataclass-generated ``__repr__`` walks the back-references and explodes
# combinatorially -- a populated meet renders into megabytes and effectively
# hangs. Each aggregate therefore defines a concise ``__repr__``/``__str__`` that
# summarises collections by count and references related objects by a short
# label (below) rather than recursing into their full repr, which breaks the
# cycle.


def _enum_name(value: object) -> str:
    """Render an enum member by its bare ``name`` (or ``"None"``).

    Avoids the verbose default enum repr (e.g. ``<Organization.USS: '1'>``).
    """
    return value.name if value is not None else "None"  # type: ignore[attr-defined]


def _club_label(club: Club | None) -> str | None:
    """A club's identifying ``team_code`` (or ``None``), without recursing into it."""
    return club.team_code if club is not None else None


def _swimmer_label(swimmer: Swimmer | None) -> str | None:
    """A swimmer's ``full_name`` (or ``None``), without recursing into it."""
    return swimmer.full_name if swimmer is not None else None


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
    """A split entry representing the swim time at a cumulative distance of a swim.

    Attributes:
        distance: Cumulative distance from start (50, 100, 150, etc.).
        time: The split time, or None if present but unparseable.
        split_type: Split representation style (INTERVAL or CUMULATIVE).
    """

    distance: int  # Cumulative distance from start (50, 100, 150, etc.)
    time: Time | None  # None if split was present but unparseable
    split_type: SplitType


@dataclass(frozen=True)
class SwimmerContact:
    """Contact details for a swimmer (contains PII).

    Attributes:
        address: Mailing street address.
        city: Mailing city.
        state: Mailing US state.
        postal_code: Mailing ZIP or postal code.
        country: Mailing country code.
        region: Geographic region code.
        alt_mailing_name: Alternate mailing recipient name.
        phone_primary: Primary contact phone number.
        phone_secondary: Secondary contact phone number.
    """

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
    """Registration and demographic details for a swimmer (contains sensitive PII).

    Attributes:
        member_status: USS membership status (e.g. member, non-member).
        registration_date: Original registration date.
        season: Swim season identifier.
        ethnicity_primary: Primary ethnicity category.
        ethnicity_secondary: Secondary ethnicity category.
        affiliations: Set of organizational affiliations.
        old_member_number: Historic member registration number.
        fina_other_federation: FINA federation identifier.
        admin_info: Administrative metadata or flags.
    """

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
    """Meet host details from B2.

    Attributes:
        name: Name of the host organization.
        address_one: Primary mailing address.
        address_two: Secondary mailing address.
        city: City of the host.
        state: US state of the host.
        postal_code: Postal or ZIP code.
        country: Country code.
        phone: Host contact phone number.
    """

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
    """File-level metadata from a results file's header/terminator.

    Fields are sourced from SDIF `A0`/`Z0` records or, for `.hy3` files, the
    `A1` record. The `hy3_*` fields and `created_time`/`licensee` are only
    populated by :func:`~tunas.read_hy3`; the SDIF-only fields are only
    populated by :func:`~tunas.read_cl2`.

    Attributes:
        path: Original file path or stream label.
        file_type: Coded SDIF file type.
        sdif_version: SDIF version string.
        software_name: Generating software product name.
        software_version: Generating software version.
        contact_name: Contact person for the file.
        contact_phone: Contact phone number.
        created: Date the file was generated.
        submitted_by_lsc: LSC that submitted or processed the file.
        notes: Arbitrary text notes or comments.
        hy3_file_type: Coded Hy-Tek file type.
        created_time: Time the file was generated.
        licensee: Organization licensed to run the software.
    """

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
    # `.hy3`-only (A1 record)
    hy3_file_type: Hy3FileType | None = None
    created_time: datetime.time | None = None
    licensee: str | None = None


@dataclass(frozen=True)
class ClubEntryCounts:
    """Entry counts from a C2 record.

    Attributes:
        num_individual_swims: Expected individual-swim count.
        num_athletes: Expected athlete count.
        num_relay_entries: Expected relay-entry count.
        num_relay_name_records: Expected relay-swimmer record count.
        num_split_records: Expected split-time record count.
    """

    num_individual_swims: int | None = None
    num_athletes: int | None = None
    num_relay_entries: int | None = None
    num_relay_name_records: int | None = None
    num_split_records: int | None = None


# --------------------------------------------------------------------------- #
# Swim interface
# --------------------------------------------------------------------------- #


class Swim(ABC):
    """Abstract base class for a swimmer's swim (IndividualSwim or RelaySwim).

    Declares no instance fields to prevent slotted layout conflicts. Both subclasses
    expose a uniform interface (swimmer, time, status, session, event, date, meet,
    course, swimmer_age_class, splits, is_relay_leg).
    """

    __slots__ = ()

    @property
    @abstractmethod
    def is_relay_leg(self) -> bool:
        """True for a RelaySwim, False for an IndividualSwim."""


# --------------------------------------------------------------------------- #
# Meet results
# --------------------------------------------------------------------------- #


@dataclass(slots=True, kw_only=True, eq=False)
class MeetResult:
    """Base class for a meet result row (IndividualSwim or Relay).

    Attributes:
        meet: Meet this result belongs to.
        club: Club the swimmer or squad represents.
        organization: Governing body code (e.g. USA Swimming).
        session: Meet session (prelims, finals, swim-offs).
        event: The swum event.
        event_min_age: Minimum age restriction for the event.
        event_max_age: Maximum age restriction for the event.
        event_sex: Sex category for the event.
        status: The result status (OK, DQ, scratch, etc.).
        time: The final swim time, or None if no time was recorded/OK.
        date: Date the event was swum.
        event_number: Coded event number.
        heat: Swum heat number.
        lane: Swum lane number.
        rank: Official place finish.
        points: Scored points.
        seed_time: Entry/seed time.
        seed_course: Entry/seed course.
        event_min_time_class: Minimum entry time class required.
        event_max_time_class: Maximum entry time class.
        dq_code: 2-character Hy-Tek DQ code (e.g. "3D").
        dq_reason: Human-readable DQ description.
        converted_seed_time: Seed time converted to the meet's course (Hy-Tek only).
        converted_seed_course: Seed course converted to the meet's course (Hy-Tek only).
        backup_times: Watch or manual backup times (Hy-Tek only).
    """

    meet: Meet
    club: Club | None
    organization: Organization | None
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
    dq_code: str | None = None  # 2-char Hy-Tek DQ code (e.g. "3D"); see `dq_reason`
    dq_reason: str | None = None  # human-readable DQ text (`.hy3` H1/H2 records)
    # `.hy3` carries both an as-entered seed (`seed_time`) and a copy converted to
    # the meet's course; SDIF stores only the as-entered seed.
    converted_seed_time: Time | None = None
    converted_seed_course: Course | None = None
    backup_times: tuple[Time, ...] = ()  # manual watch/backup times (`.hy3`-only)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(event={_enum_name(self.event)}, "
            f"session={_enum_name(self.session)}, status={_enum_name(self.status)}, "
            f"time={self.time}, club={_club_label(self.club)!r})"
        )

    def __str__(self) -> str:
        return f"{_enum_name(self.event)} {_enum_name(self.status)} {self.time}"


@dataclass(slots=True, kw_only=True, eq=False)
class IndividualSwim(MeetResult, Swim):
    """Result of an individual swim event.

    Attributes:
        swimmer: Swimmer who produced this result.
        swimmer_age_class: Coded age class at the time of the swim.
        attach_status: Attached or unattached status.
        splits: Cumulative splits recorded for this swim.
    """

    swimmer: Swimmer
    swimmer_age_class: str | None = None
    attach_status: AttachStatus = AttachStatus.ATTACHED
    splits: list[Split] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"IndividualSwim(swimmer={_swimmer_label(self.swimmer)!r}, "
            f"event={_enum_name(self.event)}, status={_enum_name(self.status)}, "
            f"time={self.time}, splits={len(self.splits)})"
        )

    def __str__(self) -> str:
        return f"{self.swimmer.full_name} {_enum_name(self.event)} {self.time}"

    @property
    def is_relay_leg(self) -> bool:
        """Always False."""
        return False

    @property
    def course(self) -> Course | None:
        """Swim course (derived from the event)."""
        return self.event.course


@dataclass(slots=True, kw_only=True, eq=False)
class Relay(MeetResult):
    """Squad relay result (the legs are RelaySwims).

    Attributes:
        relay_letter: Squad designation letter (e.g. "A", "B").
        total_age: Combined age of all squad members.
        legs: Ordered list of swimmers who raced (positions 1-4).
        alternates: Roster alternates who did not race.
        splits: Whole-relay cumulative split times (e.g. 50/100/150/200).
    """

    relay_letter: str
    total_age: int | None = None
    legs: list[RelaySwim] = field(default_factory=list)
    alternates: list[RelaySwim] = field(default_factory=list)
    splits: list[Split] = field(default_factory=list)  # whole-relay cumulative splits

    def __repr__(self) -> str:
        return (
            f"Relay(relay_letter={self.relay_letter!r}, event={_enum_name(self.event)}, "
            f"club={_club_label(self.club)!r}, status={_enum_name(self.status)}, "
            f"time={self.time}, legs={len(self.legs)})"
        )

    def __str__(self) -> str:
        club = _club_label(self.club) or "?"
        return f"{club} {self.relay_letter} {_enum_name(self.event)} {self.time}"


@dataclass(slots=True, kw_only=True, eq=False)
class RelaySwim(Swim):
    """A swimmer's relay leg or roster slot.

    Attributes:
        swimmer: The rostered swimmer, or None if unnamed.
        relay: The parent Relay result row.
        order: Leg sequence or alternate order.
        time: Time swum on this specific leg, or None.
        status: The leg's result status.
        takeoff_time: Hundredths of a second takeoff reaction time.
        course: Course code (derived or stored).
        swimmer_age_class: Coded age class at the time of the swim.
        citizenship: Citizenship or country code.
    """

    swimmer: Swimmer | None
    relay: Relay
    order: RelayLegOrder | None = None
    time: Time | None = None
    status: ResultStatus = ResultStatus.OK
    takeoff_time: int | None = None  # hundredths of a second
    course: Course | None = None
    swimmer_age_class: str | None = None
    citizenship: CitizenshipOrCountry | None = None

    def __repr__(self) -> str:
        return (
            f"RelaySwim(swimmer={_swimmer_label(self.swimmer)!r}, "
            f"order={_enum_name(self.order)}, time={self.time}, "
            f"status={_enum_name(self.status)}, relay={self.relay.relay_letter!r})"
        )

    def __str__(self) -> str:
        return f"{_swimmer_label(self.swimmer)} {_enum_name(self.order)} {self.time}"

    @property
    def is_relay_leg(self) -> bool:
        """Always True."""
        return True

    @property
    def event(self) -> Event | None:
        """Individual event swum on this leg (e.g., FREE_100_SCY)."""
        relay_event = self.relay.event
        if relay_event is None or self.order is None:
            return None
        leg_number = _LEG_NUMBERS.get(self.order)
        if leg_number is not None:
            return relay_event.leg_event(leg_number)
        # Free relay alternates swum event is well-defined; medley alternates are not.
        if relay_event.stroke is Stroke.FREESTYLE_RELAY:
            return relay_event.leg_event(1)
        return None

    @property
    def splits(self) -> list[Split]:
        """This leg's splits, derived from the relay's whole-relay cumulative splits.

        Both readers store splits on the relay row (:attr:`Relay.splits`) as
        whole-relay cumulative marks (e.g. 50/100/150/200 for a 4×50). A leg's
        splits are the marks swum during that leg, re-based to the leg start so
        the leg reads like a flat-start swim: distances count from 0 and a
        cumulative time is measured from the leg's takeoff. (Interval splits keep
        their per-segment time; only the distance is re-based.)

        Empty when there is nothing to derive — the relay carries no splits, the
        slot is an alternate / has no leg number, or no relay mark falls within
        this leg's distance window.
        """
        relay_splits = self.relay.splits
        leg_number = _LEG_NUMBERS.get(self.order) if self.order is not None else None
        if not relay_splits or leg_number is None:
            return []
        per_leg = self.relay.event.leg_distance()
        lo, hi = (leg_number - 1) * per_leg, leg_number * per_leg
        window = [s for s in relay_splits if lo < s.distance <= hi]
        if not window:
            return []
        # Leg-start cumulative time: zero for the lead-off leg, otherwise the
        # relay mark at the leg boundary (left as None if that mark is absent).
        start: Time | None = Time(0) if lo == 0 else next(
            (s.time for s in relay_splits if s.distance == lo), None
        )
        derived: list[Split] = []
        for s in window:
            if s.split_type is SplitType.CUMULATIVE and start is not None and s.time is not None:
                time: Time | None = s.time - start
            else:
                time = s.time
            derived.append(Split(distance=s.distance - lo, time=time, split_type=s.split_type))
        return derived

    @property
    def date(self) -> datetime.date | None:
        """Date of the swim (parent relay date)."""
        return self.relay.date

    @property
    def meet(self) -> Meet:
        """Meet this leg belongs to."""
        return self.relay.meet

    @property
    def session(self) -> Session:
        """Session of the swim."""
        return self.relay.session


# --------------------------------------------------------------------------- #
# Aggregates
# --------------------------------------------------------------------------- #


@dataclass(slots=True, kw_only=True, eq=False)
class Swimmer:
    """A swimmer scoped to one meet.

    Attributes:
        meet: The meet this swimmer is registered for.
        first_name: The swimmer's first name.
        last_name: The swimmer's last name.
        sex: The swimmer's sex.
        id_short: 12-character short ID (USS#).
        id_long: 14-character new long ID.
        middle_initial: Swimmer's middle initial.
        preferred_first_name: Swimmer's preferred first name.
        birthday: Swimmer's birthday.
        citizenship: Citizenship or country code.
        contact: Swimmer contact details (contains PII).
        registration: Swimmer registration details (contains PII).
        club: The club the swimmer belongs to at this meet.
        swims: List of individual and relay swims for this swimmer at the meet.
    """

    meet: Meet
    first_name: str
    last_name: str
    sex: Sex
    id_short: str | None = None  # 12-char short ID (USS#)
    id_long: str | None = None  # 14-char new long ID
    middle_initial: str | None = None
    preferred_first_name: str | None = None
    birthday: datetime.date | None = None
    citizenship: CitizenshipOrCountry | None = None
    contact: SwimmerContact | None = None
    registration: SwimmerRegistration | None = None
    club: Club | None = None
    swims: list[IndividualSwim | RelaySwim] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"Swimmer(full_name={self.full_name!r}, id_short={self.id_short!r}, "
            f"sex={_enum_name(self.sex)}, club={_club_label(self.club)!r}, "
            f"swims={len(self.swims)})"
        )

    def __str__(self) -> str:
        return self.full_name

    @property
    def individual_swims(self) -> list[IndividualSwim]:
        """Swimmer's individual swims."""
        return [s for s in self.swims if isinstance(s, IndividualSwim)]

    @property
    def relay_swims(self) -> list[RelaySwim]:
        """Swimmer's counting relay legs (excluding alternates)."""
        return [s for s in self.swims if isinstance(s, RelaySwim)]

    @property
    def full_name(self) -> str:
        """Combined first, middle initial, and last name."""
        if self.middle_initial:
            return f"{self.first_name} {self.middle_initial} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    def swims_in(self, event: Event) -> list[IndividualSwim | RelaySwim]:
        """Swims for an individual event in source order."""
        return [s for s in self.swims if s.event == event]


@dataclass(slots=True, kw_only=True, eq=False)
class Club:
    """A club scoped to one meet, keyed by `(team_code, lsc)`.

    Attributes:
        meet: The meet this club is scoped to.
        organization: Governing body code.
        team_code: Unique code identifying the team.
        lsc: Local Swimming Committee code.
        full_name: Full team/club name.
        abbreviated_name: Shortened club name.
        address_one: Primary club address.
        address_two: Secondary club address.
        city: Club city.
        state: Club US state.
        postal_code: ZIP or postal code.
        country: Country code.
        region: Geographic region code.
        coach: Head coach name.
        coach_phone: Coach contact phone.
        short_name: Alternate short name.
        email: Contact email address.
        entry_counts: Official entry counts from the file.
        results: Club's individual and relay results at the meet.
        swimmers: Swimmers representing this club at the meet.
    """

    meet: Meet
    organization: Organization | None
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
    email: str | None = None  # contact email (`.hy3` C3 record)
    entry_counts: ClubEntryCounts | None = None
    results: list[MeetResult] = field(default_factory=list)
    swimmers: list[Swimmer] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"Club(team_code={self.team_code!r}, lsc={_enum_name(self.lsc)}, "
            f"full_name={self.full_name!r}, swimmers={len(self.swimmers)}, "
            f"results={len(self.results)})"
        )

    def __str__(self) -> str:
        return self.full_name or self.team_code

    @property
    def individual_swims(self) -> list[IndividualSwim]:
        """Club's individual-event results at the meet."""
        return [r for r in self.results if isinstance(r, IndividualSwim)]

    @property
    def relays(self) -> list[Relay]:
        """Club's relay results at the meet."""
        return [r for r in self.results if isinstance(r, Relay)]


@dataclass(slots=True, kw_only=True, eq=False)
class Meet:
    """A single swimming meet containing clubs, swimmers, and results.

    Attributes:
        organization: Governing body hosting the meet.
        name: Name of the meet.
        start_date: Start date of the competition.
        end_date: End date of the competition.
        city: City where the meet took place.
        address_one: Primary venue address.
        state: US state where the meet took place.
        address_two: Secondary venue address.
        postal_code: Venue postal or ZIP code.
        country: Venue country code.
        course: Course code (SCY, SCM, LCM).
        altitude: Venue altitude in feet or meters.
        meet_type: Meet classification code.
        venue: Facility or pool name.
        age_up_date: Age-determination date for the meet.
        sanction_number: Meet sanction identifier.
        host: Host details.
        source_file: Metadata of the file this meet was parsed from.
        results: All individual and relay results at this meet.
        swimmers: All athletes registered at this meet.
        clubs: All clubs registered at this meet.
    """

    organization: Organization | None
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
    venue: str | None = None  # facility / location name (`.hy3` B1 record)
    age_up_date: datetime.date | None = None  # age-determination date (`.hy3` B1 record)
    sanction_number: str | None = None  # sanction number (`.hy3` B2 record)
    host: MeetHost | None = None
    source_file: SourceFile | None = None
    results: list[MeetResult] = field(default_factory=list)
    swimmers: list[Swimmer] = field(default_factory=list)
    clubs: list[Club] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"Meet(name={self.name!r}, organization={_enum_name(self.organization)}, "
            f"start_date={self.start_date.isoformat()}, clubs={len(self.clubs)}, "
            f"swimmers={len(self.swimmers)}, results={len(self.results)})"
        )

    def __str__(self) -> str:
        return f"{self.name} ({self.start_date.isoformat()})"

    @property
    def individual_swims(self) -> list[IndividualSwim]:
        """All individual-event results at the meet."""
        return [r for r in self.results if isinstance(r, IndividualSwim)]

    @property
    def relays(self) -> list[Relay]:
        """All relay results at the meet."""
        return [r for r in self.results if isinstance(r, Relay)]

    def individual_swims_for(self, event: Event) -> list[IndividualSwim]:
        """Individual swims for an event in source order."""
        return [r for r in self.individual_swims if r.event == event]

    def relays_for(self, event: Event) -> list[Relay]:
        """Relays for an event in source order."""
        return [r for r in self.relays if r.event == event]
