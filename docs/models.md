# `tunas.models` — the domain model

This document describes the dataclasses in the `tunas` domain model: their fields, properties, methods, identity rules, and relationships. All classes are importable from the top-level `tunas` package.

## Object graph

**Inheritance:**

```
Swim (one swimmer's swim)           MeetResult (a row in Meet.results)
├── IndividualSwim                  ├── IndividualSwim
└── RelaySwim                       └── Relay
```

**Containment:**

```
list[Meet]                                ← read_cl2 returns one Meet per cl2 file
└── Meet
    ├── results   : list[MeetResult]      ← IndividualSwim or Relay
    │   ├── IndividualSwim
    │   │   └── swimmer  : Swimmer
    │   └── Relay
    │       ├── legs       : list[RelaySwim]    ← the ≤4 swum legs (order LEG_1–LEG_4)
    │       │   └── RelaySwim
    │       │       ├── swimmer : Swimmer
    │       │       └── relay   : Relay         ← Back-reference
    │       └── alternates : list[RelaySwim]    ← rostered but did not swim (order ALTERNATE)
    ├── swimmers  : list[Swimmer]
    │   └── Swimmer
    │       ├── swims    : list[Swim]     ← IndividualSwims + RelaySwims
    │       └── club     : Club | None
    └── clubs     : list[Club]
        └── Club
            ├── results  : list[MeetResult]
            └── swimmers : list[Swimmer]
```

- **`Swim`:** Abstract base interface for a single swimmer's swim, subclassed by `IndividualSwim` and `RelaySwim`. Provides a uniform interface (`swimmer`, `time`, `event`, `date`, `meet`, `splits`, `status`) and shares `Swimmer.swims`.
- **`MeetResult`:** Shared base for results in `Meet.results`, subclassed by `IndividualSwim` and `Relay`. Shares event and place context. Holds no `swimmer` or `splits`.

Meets are independent; each `Meet` owns its swimmers and clubs. Aggregate classes are mutable to support single-pass parser graph wiring, but use slots (`slots=True`) and keyword-only construction (`kw_only=True`).

Aggregates also use identity equality (`eq=False`, so `==` is `is`) to avoid stack overflows from cyclic graph references (`meet ⇄ results`) and because the parser does not deduplicate objects.

## `Swim`

Abstract base interface for a single swimmer's swim (subclassed by `IndividualSwim` and `RelaySwim`). It has no stored fields, avoiding multiple inheritance layout conflicts.

| Member | Type | Meaning |
|---|---|---|
| `swimmer` | `Swimmer` | The swimmer who made this swim. |
| `time` | `Time \| None` | The swim time (`None` for a non-time outcome). |
| `status` | `ResultStatus` | `OK` for an official time, else `NT`/`NS`/`DNF`/`DQ`/`SCR`. |
| `session` | `Session` | `PRELIMS`, `FINALS`, or `SWIM_OFFS`. |
| `event` | `Event \| None` | Leg individual event (e.g. `FREE_100_SCY` for a 400 relay leg) or individual swim event. `None` only for a medley-relay alternate. |
| `date` | `datetime.date \| None` | Date of the swim. |
| `meet` | `Meet` | Back-reference to the meet. |
| `course` | `Course \| None` | Course of the swim. |
| `swimmer_age_class` | `str \| None` | Age/class as printed. |
| `splits` | `list[Split]` | Splits in distance order (empty if none). |
| `is_relay_leg` | `bool` | `True` for a `RelaySwim`, `False` for an `IndividualSwim`. |

## `MeetResult`

Shared base dataclass representing a row in `Meet.results`.

```python
@dataclass(slots=True, kw_only=True, eq=False)
class MeetResult:
    meet: Meet
    club: Club | None
    organization: Organization
    session: Session
    event: Event
    event_min_age: int | None
    event_max_age: int | None
    event_number: str | None = None
    event_sex: Sex
    status: ResultStatus
    time: Time | None
    date: datetime.date | None
    heat: int | None = None
    lane: int | None = None
    rank: int | None = None
    points: float | None = None
    seed_time: Time | None = None
    seed_course: Course | None = None
    event_min_time_class: EventTimeClass | None = None
    event_max_time_class: EventTimeClass | None = None
```

### Fields

| Field | Type | Notes |
|---|---|---|
| `meet` | `Meet` | Back-reference. Always set. |
| `club` | `Club \| None` | `None` for unattached swimmers. |
| `organization` | `Organization` | Usually `Organization.USS`. |
| `session` | `Session` | `PRELIMS`, `FINALS`, or `SWIM_OFFS`. |
| `event` | `Event` | The event swum. |
| `event_min_age`, `event_max_age` | `int \| None` | Event age limits. `None` if open-ended (`"UN"` or `"OV"`). |
| `event_number` | `str \| None` | Event program number (e.g., `"501"`). |
| `event_sex` | `Sex` | Competition sex classification of the event. |
| `status` | `ResultStatus` | Swim outcome: `OK`, `NT`, `NS`, `DNF`, `DQ`, or `SCR`. |
| `time` | `Time \| None` | Recorded time (non-`None` iff `status == OK`, or course `X` DQ). |
| `date` | `datetime.date \| None` | Date of the swim. |
| `heat`, `lane` | `int \| None` | Pool assignment. |
| `rank` | `int \| None` | Place awarded (e.g. `1` for first, `None` if DQ/SCR). |
| `points` | `float \| None` | Team points earned. |
| `seed_time`, `seed_course` | `Time \| None`, `Course \| None` | Seed/entry time and course. |
| `event_min_time_class`, `event_max_time_class` | `EventTimeClass \| None` | Qualifying-class limits. |

## `IndividualSwim`

The result type for individual events (`event.is_relay()` is `False`).

```python
@dataclass(slots=True, kw_only=True, eq=False)
class IndividualSwim(MeetResult, Swim):
    swimmer: Swimmer
    swimmer_age_class: str | None = None
    attach_status: AttachStatus = AttachStatus.ATTACHED
    splits: list[Split] = field(default_factory=list)
```

### Additional fields

| Field | Type | Notes |
|---|---|---|
| `swimmer` | `Swimmer` | The swimmer who performed the swim. |
| `swimmer_age_class` | `str \| None` | Print age class (e.g. `"12"` or `"FR"`). |
| `attach_status` | `AttachStatus` | `UNATTACHED` for unattached swimmers. |
| `splits` | `list[Split]` | Splits in distance order. |

## `Relay`

The result type for relay events (`event.is_relay()` is `True`).

```python
@dataclass(slots=True, kw_only=True, eq=False)
class Relay(MeetResult):
    relay_letter: str             # "A" / "B" / "C" ...
    total_age: int | None = None  # Combined squad age
    legs: list[RelaySwim] = field(default_factory=list)        # Counting swum legs (orders 1-4)
    alternates: list[RelaySwim] = field(default_factory=list)  # Rostered alternates (order A)
```

### Additional fields

| Field | Type | Notes |
|---|---|---|
| `relay_letter` | `str` | Letter code identifying the squad (e.g., `"A"`). |
| `total_age` | `int \| None` | Combined age of the relay squad. |
| `legs` | `list[RelaySwim]` | Counting swum legs (orders `LEG_1`–`LEG_4`). Max 4. |
| `alternates` | `list[RelaySwim]` | Rostered alternates who did not swim. Excluded from `Swimmer.swims`. |

Relays represent a squad; splits live on the swum legs (`RelaySwim.splits`).

## `RelaySwim`

A `Swim` representing one swimmer's leg or roster position on a relay.

```python
@dataclass(slots=True, kw_only=True, eq=False)
class RelaySwim(Swim):
    swimmer: Swimmer | None
    relay: Relay                       # Parent relay back-reference
    order: RelayLegOrder | None = None # Leg position or alternate code
    time: Time | None = None           # Leg split time
    status: ResultStatus = ResultStatus.OK
    takeoff_time: int | None = None    # Take-off time in hundredths of a second
    course: Course | None = None
    swimmer_age_class: str | None = None
    citizenship: Citizenship | Country | None = None
    splits: list[Split] = field(default_factory=list)

    is_relay_leg = True
```

### Fields

| Field | Type | Notes |
|---|---|---|
| `swimmer` | `Swimmer \| None` | The swimmer on the leg (`None` only if USS# is corrupt). |
| `relay` | `Relay` | Back-reference to the parent session-relay. |
| `order` | `RelayLegOrder \| None` | Leg position (`LEG_1`–`LEG_4`) or `ALTERNATE`. |
| `time` | `Time \| None` | Individual leg split time. |
| `status` | `ResultStatus` | Outcome; mirrors parent relay's status. |
| `takeoff_time` | `int \| None` | Relay take-off time in hundredths of a second (e.g., `29` = 0.29 s). |
| `course` | `Course \| None` | Course swum. |
| `swimmer_age_class` | `str \| None` | Print age class. |
| `citizenship` | `Citizenship \| Country \| None` | Leg citizenship from F0. |
| `splits` | `list[Split]` | Splits for this leg in distance order. |

### Swim interface on a leg

Computed properties delegating to the parent `relay`:

| Property | Returns |
|---|---|
| `event` | `self.relay.event.leg_event(int(self.order))` — the individual leg event (e.g., `FREE_100_SCY` on a 400 free relay). |
| `date` | `self.relay.date` |
| `meet` | `self.relay.meet` |
| `session` | `self.relay.session` |

```python
relay.event              # Event.FREE_400_RELAY_SCY
relay.legs[0].event      # Event.FREE_100_SCY (individual event swum)
```

Swimmers have their swum legs stored in `Swimmer.swims` under the **individual** leg event alongside flat-start swims. Alternates are filed under `Relay.alternates` and omitted from `Swimmer.swims`.

## `Split`

One split entry from a G0 record.

```python
@dataclass(frozen=True)
class Split:
    distance: int                # Cumulative distance from start (50, 100, 150...)
    time: Time | None            # None if split was unparseable
    split_type: SplitType        # CUMULATIVE (elapsed) or INTERVAL (segment)
```

`Split` is frozen and hashable. Splits are ordered by distance ascending.

## `SwimmerContact`

Contact details populated from D1/D2 records. Frozen and reachable via `Swimmer.contact`. **Contains PII.**

```python
@dataclass(frozen=True)
class SwimmerContact:
    address: str | None = None
    city: str | None = None
    state: State | None = None
    postal_code: str | None = None
    country: Country | None = None
    region: Region | None = None
    alt_mailing_name: str | None = None
    phone_primary: str | None = None
    phone_secondary: str | None = None
```

## `SwimmerRegistration`

Registration and demographic details populated from D1/D2/D3 records. Reachable via `Swimmer.registration`. **Contains sensitive PII.**

```python
@dataclass(frozen=True)
class SwimmerRegistration:
    member_status: MemberStatus | None = None
    registration_date: datetime.date | None = None
    season: Season | None = None
    ethnicity_primary: Ethnicity | None = None
    ethnicity_secondary: Ethnicity | None = None
    affiliations: frozenset[Affiliation] = frozenset()
    old_member_number: str | None = None
    fina_other_federation: str | None = None
    admin_info: str | None = None
```

## `Swimmer`

A swimmer scoped to a single meet and identified within it by member ID.

```python
@dataclass(slots=True, kw_only=True, eq=False)
class Swimmer:
    meet: Meet
    first_name: str
    last_name: str
    sex: Sex
    id_short: str | None = None  # 12-char short ID (USS#)
    id_long: str | None = None   # 14-char new ID (long USS#)
    middle_initial: str | None = None
    preferred_first_name: str | None = None
    birthday: datetime.date | None = None
    citizenship: Citizenship | Country | None = None
    contact: SwimmerContact | None = None
    registration: SwimmerRegistration | None = None
    club: Club | None = None     
    swims: list[Swim] = field(default_factory=list)  # Individual + Relay counting legs
```

### Computed properties

| Property | Returns |
|---|---|
| `individual_swims` | `swims` filtered to `IndividualSwim` instances. |
| `relay_swims` | `swims` filtered to `RelaySwim` instances (counting legs only). |
| `full_name` | `"First Middle Last"` or `"First Last"`. |

### Methods

#### `swims_in(event: Event) -> list[Swim]`

Returns swims for the individual event (e.g. flat-starts and relay legs matching the distance/stroke/course) in source order.

### Identity

- Grouped within a meet by `id_short` falling back to `id_long`. Every `Swimmer` carries at least one of these two.
- Matches never fallback to names/birthdays, preventing accidental swimmer fusion.
- Swimmers are meet-scoped; the same athlete at different meets represents distinct `Swimmer` objects.

## `Club`

A club scoped to a single meet.

```python
@dataclass(slots=True, kw_only=True, eq=False)
class Club:
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
```

`ClubEntryCounts` is a frozen sub-dataclass containing D0, athlete, E0, F0, and split counts.

### Computed properties

| Property | Returns |
|---|---|
| `individual_swims` | `results` filtered to `IndividualSwim`s. |
| `relays` | `results` filtered to `Relay`s. |

### Identity

Scoped to a single meet, keyed on `(team_code, lsc)`. `team_code` is the full SDIF code including LSC prefix and optional 5th extension character. Clubs are not merged across meets.

## `Meet`

Represents one meet's data from a single SDIF file B1 block.

```python
@dataclass(slots=True, kw_only=True, eq=False)
class Meet:
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
```

### Computed properties

| Property | Returns |
|---|---|
| `individual_swims` | `results` filtered to `IndividualSwim`s. |
| `relays` | `results` filtered to `Relay`s. |

### Methods

- `individual_swims_for(event: Event) -> list[IndividualSwim]`: Returns individual swims for an event in source order.
- `relays_for(event: Event) -> list[Relay]`: Returns relays for an event in source order.

Meets are independent and never merged, even if name/date match.

## `MeetHost`

```python
@dataclass(frozen=True)
class MeetHost:
    name: str | None = None
    address_one: str | None = None
    address_two: str | None = None
    city: str | None = None
    state: State | None = None
    postal_code: str | None = None
    country: Country | None = None
    phone: str | None = None
```

Reachable as `Meet.host`.

## `SourceFile`

File-level metadata from A0/Z0 records. Reachable as `Meet.source_file`.

```python
@dataclass(frozen=True)
class SourceFile:
    path: str | None = None            # Stream name or file path
    file_type: FileType | None = None  
    sdif_version: str | None = None
    software_name: str | None = None
    software_version: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    created: datetime.date | None = None
    submitted_by_lsc: LSC | None = None
    notes: str | None = None           # Z0 note text
```

Meets from the same file share the same `SourceFile` instance.

## Example: traversing the model

```python
from tunas import read_cl2, Event

meets, _ = read_cl2("results/")

for meet in meets:
    print(f"== {meet.name} ({meet.start_date}) ==")
    for swimmer in meet.swimmers:
        club = swimmer.club.abbreviated_name if swimmer.club else "UN"
        for swim in swimmer.swims_in(Event.FREE_100_SCY):
            outcome = swim.time if swim.time is not None else swim.status.value
            print(f"  {swimmer.full_name:<25} {club:>5} {swim.session.value} {outcome}")
```
