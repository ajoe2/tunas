# `tunas.models` — the domain model

This document describes every dataclass in the `tunas` domain model: its
fields, computed properties, methods, identity rules, and how it relates
to the other models. All classes documented here are importable from the
top-level `tunas` package.

## Object graph

```
Meet
├── individual_results : list[IndividualMeetResult]
│       │
│       └── swimmer : Swimmer ─────────────────┐
│                                              │
└── relay_results     : list[RelayMeetResult]  │
        │                                      │
        └── legs : list[RelayLeg]              │
                ├── swimmer : Swimmer ──────── │
                                               │
Club ─────── (referenced by every result) ─────┘
```

`Meet` is the entry point. The two result lists on `Meet` are the **single
source of truth**; every other "list of swimmers", "list of clubs", "list
of results" exposed on `Swimmer`, `Club`, or `Meet` is a computed
`@property` view derived from those lists. There is no synchronization to
get wrong.

## `MeetResult` — base class

```python
@dataclass
class MeetResult:
    meet: Meet
    club: Club | None
    organization: Organization
    session: Session
    date: datetime.date
    event: Event
    event_min_age: int
    event_max_age: int
    event_number: str
    event_sex: Sex
    time: Time
    heat: int | None = None
    lane: int | None = None
    rank: int | None = None
    points: float | None = None
    seed_time: Time | None = None
    seed_course: Course | None = None
    event_min_time_class: EventTimeClass | None = None
    event_max_time_class: EventTimeClass | None = None
    splits: list[Split] = field(default_factory=list)
```

`MeetResult` is **abstract in spirit but not enforced** — every actual
result is either an `IndividualMeetResult` or a `RelayMeetResult`.

### Fields

| Field | Type | Notes |
|---|---|---|
| `meet` | `Meet` | Back-reference. Always set. |
| `club` | `Club \| None` | `None` for unattached swimmers (`AttachStatus.UNATTACHED`). |
| `organization` | `Organization` | Usually `Organization.USS`. |
| `session` | `Session` | `PRELIMS`, `FINALS`, or `SWIM_OFFS`. |
| `date` | `datetime.date` | Date of the swim, not the meet start date. |
| `event` | `Event` | The event swum. |
| `event_min_age`, `event_max_age` | `int` | The event's age limits. `0` for "UN" (no min), `1000` for "OV" (no max). |
| `event_number` | `str` | The meet's program number for this event, e.g. `"501"`. |
| `event_sex` | `Sex` | Whether the event is a male, female, or mixed event. |
| `time` | `Time` | The result time. Use `Time(0)` for "no time"; the parser drops `NT`/`NS`/`DNF`/`DQ`/`SCR` entries entirely. |
| `heat`, `lane` | `int \| None` | Pool assignment. `None` if not in the source file. |
| `rank` | `int \| None` | Place. `None` if not awarded (e.g. a heat result, or `≤ 0` in the source). |
| `points` | `float \| None` | Team points earned. `None` if not awarded. |
| `seed_time`, `seed_course` | `Time \| None`, `Course \| None` | The seed time the swimmer entered with. Both may be present, both may be `None`. |
| `event_min_time_class`, `event_max_time_class` | `EventTimeClass \| None` | The qualifying-class cap on the event (e.g. "BB and slower"). |
| `splits` | `list[Split]` | Splits in distance order. Empty if no G0 records were present. |

### Mutability

`MeetResult` and its subclasses are **mutable dataclasses** so the parser
can populate them incrementally as it reads. Application code is free to
treat them as immutable after parsing; the library makes no further
mutations once `read_cl2` returns.

### Identity / equality

`MeetResult` uses default dataclass equality (compares all fields). In
practice, two distinct results from different files should compare equal
only if they encode the same swim. Don't rely on hashing — results are
mutable and not hashable by default.

## `IndividualMeetResult(MeetResult)`

```python
@dataclass
class IndividualMeetResult(MeetResult):
    swimmer: Swimmer
    swimmer_age_class: str | None = None
    attach_status: AttachStatus = AttachStatus.ATTACHED
    swimmer_contact: SwimmerContact | None = None
```

The result type for individual events (anything where `event.is_relay()`
is `False`).

### Additional fields

| Field | Type | Notes |
|---|---|---|
| `swimmer` | `Swimmer` | The swimmer who produced this result. |
| `swimmer_age_class` | `str \| None` | Age class as printed in the source — usually a numeric age (`"12"`) but may be `"FR"`, `"SO"`, `"JR"`, `"SR"` for collegiate meets. |
| `attach_status` | `AttachStatus` | `UNATTACHED` for swimmers not affiliated with the parsed club at the time of this swim. |
| `swimmer_contact` | `SwimmerContact \| None` | Contact info from D1/D2 records. **Personally identifying information**; `None` unless the source file included it. |

### `swimmer_contact` and PII

D1 and D2 records carry swimmer addresses, phone numbers, and email
addresses. The library parses them when present but separates them onto
their own dataclass so callers can ignore them. If you don't read
`result.swimmer_contact`, you never see the data; if you do, you're
expected to handle it responsibly.

## `RelayMeetResult(MeetResult)`

```python
@dataclass
class RelayMeetResult(MeetResult):
    relay_letter: str             # "A" / "B" / "C" ...
    legs: list[RelayLeg] = field(default_factory=list)
```

The result type for relay events. `event.is_relay()` is `True`.

### Additional fields

| Field | Type | Notes |
|---|---|---|
| `relay_letter` | `str` | Single character identifying the squad within the team. Concatenated with the club abbreviation when displaying, e.g. `"SCSC A"`. |
| `legs` | `list[RelayLeg]` | One entry per F0 record. Up to four entries (the swimmers who actually competed); may be empty if no F0 records were present. |

The relay's overall `time` is on the base `MeetResult` (from the E0
record). Leg times live on each `RelayLeg`.

### Splits

`RelayMeetResult.splits` is populated from G0 records that follow the F0
records for this relay. They represent the relay's elapsed time at each
50/100 segment of the race.

## `RelayLeg`

```python
@dataclass
class RelayLeg:
    swimmer: Swimmer | None
    leg_order_prelim: int | None = None
    leg_order_finals: int | None = None
    leg_time: Time | None = None
    course: Course | None = None
    swimmer_age_class: str | None = None
    citizenship: Country | None = None
```

One per F0 record. Order within `RelayMeetResult.legs` matches the order
of F0 records in the source file, which is **not** necessarily the swim
order — that is recorded in `leg_order_prelim` / `leg_order_finals`
(SDIF "ORDER" code).

| Field | Type | Notes |
|---|---|---|
| `swimmer` | `Swimmer \| None` | The swimmer on this leg. `None` only if the F0 record cannot be resolved to a known swimmer (in which case a `ParseWarning` is emitted). |
| `leg_order_prelim` | `int \| None` | 1–4 if this swimmer raced this position in prelims, else `None`. |
| `leg_order_finals` | `int \| None` | 1–4 if this swimmer raced this position in finals, else `None`. |
| `leg_time` | `Time \| None` | The split time for this leg. `None` if not in the source. |
| `course` | `Course \| None` | Course the leg was swum in (usually matches the relay course). |
| `swimmer_age_class` | `str \| None` | Age class as printed (numeric or `"FR"`/`"SO"`/`"JR"`/`"SR"`). |
| `citizenship` | `Country \| None` | Citizenship as reported on the F0 record. |

## `Split`

```python
@dataclass(frozen=True)
class Split:
    distance: int                # in meters or yards (matches event course)
    time: Time
    split_type: SplitType        # INTERVAL or CUMULATIVE
```

One per split entry on a G0 record. `Split` is frozen and hashable.
`MeetResult.splits` is ordered by `distance` ascending; multiple G0
records for the same swim are concatenated.

## `SwimmerContact`

```python
@dataclass(frozen=True)
class SwimmerContact:
    address_1: str | None = None
    address_2: str | None = None
    city: str | None = None
    state: State | None = None
    postal_code: str | None = None
    country: Country | None = None
    phone_home: str | None = None
    phone_work: str | None = None
    email: str | None = None
```

Populated from D1 (address) and D2 (phone, email) records. Always frozen
and optional. **This is PII** — treat it accordingly.

## `Swimmer`

```python
@dataclass
class Swimmer:
    first_name: str
    last_name: str
    sex: Sex
    usa_id_short: str | None = None
    middle_initial: str | None = None
    preferred_first_name: str | None = None
    birthday: datetime.date | None = None
    usa_id_long: str | None = None
    citizenship: Country | None = None
```

### Stored fields

| Field | Type | Notes |
|---|---|---|
| `first_name`, `last_name` | `str` | Legal name as printed in the source. |
| `sex` | `Sex` | The swimmer's competition sex. |
| `usa_id_short` | `str \| None` | 12-character USA Swimming short ID. Optional because not every record carries it. |
| `middle_initial` | `str \| None` | Single letter, or `None`. |
| `preferred_first_name` | `str \| None` | From a D3 record. |
| `birthday` | `datetime.date \| None` | `None` if the source omits it. The library **never** infers a birthday — see [parsing.md](parsing.md) for why. |
| `usa_id_long` | `str \| None` | 14-character USA Swimming long ID, from D3 records. |
| `citizenship` | `Country \| None` | From the D0 record. |

### Computed properties

| Property | Returns | Notes |
|---|---|---|
| `full_name` | `str` | `"First Middle Last"` if middle initial present, else `"First Last"`. |
| `individual_results` | `list[IndividualMeetResult]` | All this swimmer's individual results across all parsed meets. |
| `relay_legs` | `list[tuple[RelayMeetResult, RelayLeg]]` | Every relay this swimmer appeared on. |
| `meets` | `list[Meet]` | Unique meets the swimmer competed in, ordered by date. |
| `clubs` | `list[Club]` | Unique clubs the swimmer has competed for, ordered by first appearance. |
| `current_club` | `Club \| None` | Club from the most recent result, or `None` if no club results exist. |
| `date_most_recent_swim` | `datetime.date \| None` | `None` if no results exist. |

### Methods

#### `best_result(event: Event) -> IndividualMeetResult | None`

Returns the result with the fastest `time` for the given event, or `None`
if the swimmer has no result in that event.

```python
swimmer.best_result(Event.FREE_100_SCY)
```

#### `results_in(event: Event) -> list[IndividualMeetResult]`

All results for the given event, ordered fastest first.

#### `results_between(start: datetime.date, end: datetime.date) -> list[IndividualMeetResult]`

All results with `start <= result.date <= end`, ordered by date.

#### `relays_in(event: Event) -> list[RelayMeetResult]`

All relays the swimmer competed on for the given (relay) event.

#### `age_on(date: datetime.date) -> int | None`

The swimmer's age on `date`, or `None` if `birthday` is unknown.

#### `age_range_on(date: datetime.date) -> tuple[int, int]`

The swimmer's possible age on `date` inferred from `birthday` and from
`swimmer_age_class` values across their result history.

- If `birthday` is set, returns `(age, age)`.
- Otherwise, infers a range from numeric age classes in past results
  (each recorded age `A` swum on date `D` implies the swimmer was age
  `A` on `D`, which bounds their birthday).
- If no numeric age classes are available either, returns `(0, 1000)`.

### Identity

Two `Swimmer` instances are considered the same swimmer by the parser when:

1. Their `usa_id_short` matches (exact), or
2. Their `(first_name.lower(), last_name.lower(), birthday)` matches (exact).

When the parser merges duplicates across files, it fills `None` fields
from the duplicate but never overwrites a non-`None` field. Application
code is free to build its own identity rules — `Swimmer` defines no
`__eq__` or `__hash__` overrides, so reference equality is what `==` and
`hash()` give you.

## `Club`

```python
@dataclass
class Club:
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
    entry_counts: ClubEntryCounts | None = None
```

`ClubEntryCounts` is a small frozen sub-dataclass populated from C2
records: `num_individual_swims`, `num_split_records`, `num_relay_entries`,
`num_relay_name_records`, `num_relay_split_records`. All fields are
optional `int`s.

### Computed properties

| Property | Returns | Notes |
|---|---|---|
| `swimmers` | `list[Swimmer]` | Unique swimmers who have any result with this club. |
| `individual_results` | `list[IndividualMeetResult]` | All individual results recorded for this club across parsed meets. |
| `relay_results` | `list[RelayMeetResult]` | All relay results recorded for this club. |
| `meets` | `list[Meet]` | Unique meets the club has results at. |

### Methods

#### `find_swimmer(*, usa_id=None, name=None, birthday=None) -> Swimmer | None`

Search the club's swimmers. Provide one or more of:

- `usa_id` — matches either `usa_id_short` (12 chars) or `usa_id_long`
  (14 chars).
- `name` — case-insensitive match against `full_name`, `"last, first"`,
  or `"first last"`.
- `birthday` — exact match.

Returns the first matching swimmer or `None`.

#### `roster(on_date: datetime.date | None = None) -> list[Swimmer]`

All swimmers who have at least one result with this club. If `on_date` is
provided, only swimmers with a result on or before that date.

#### `relay_results_for(event: Event | None = None) -> list[RelayMeetResult]`

All relay results for the club, optionally filtered to a single event.

### Identity

A club's identity is `(team_code, lsc)`. Two `Club` records with the same
pair are treated as the same club by the parser and merged
(non-`None` fields filled).

## `Meet`

```python
@dataclass
class Meet:
    organization: Organization
    name: str
    start_date: datetime.date
    end_date: datetime.date
    city: str
    address_one: str
    state: State | None = None
    address_two: str | None = None
    postal_code: str | None = None
    country: Country | None = None
    course: Course | None = None
    altitude: int | None = None
    meet_type: MeetType | None = None
    host_team_code: str | None = None
    host_phone: str | None = None
    individual_results: list[IndividualMeetResult] = field(default_factory=list)
    relay_results: list[RelayMeetResult] = field(default_factory=list)
```

### Stored fields

| Field | Type | Notes |
|---|---|---|
| `organization` | `Organization` | Usually `Organization.USS`. |
| `name` | `str` | As printed in the source. |
| `start_date`, `end_date` | `datetime.date` | Inclusive range. May be equal for single-day meets. |
| `city`, `address_one` | `str` | Mandatory per spec. |
| `state`, `address_two`, `postal_code`, `country` | various `\| None` | Optional. |
| `course` | `Course \| None` | The meet's primary course, if set on the B1 record. Individual results carry their own course on `seed_course`; this is a meet-level summary. |
| `altitude` | `int \| None` | Altitude in feet, if recorded. |
| `meet_type` | `MeetType \| None` | Classification of the meet. |
| `host_team_code`, `host_phone` | `str \| None` | From the B2 record, if present. |
| `individual_results` | `list[IndividualMeetResult]` | All individual results. **Source of truth.** |
| `relay_results` | `list[RelayMeetResult]` | All relay results. **Source of truth.** |

### Computed properties

| Property | Returns | Notes |
|---|---|---|
| `results` | `list[MeetResult]` | Concatenation of `individual_results` + `relay_results`. |
| `swimmers` | `list[Swimmer]` | Unique swimmers across both result lists. |
| `clubs` | `list[Club]` | Unique clubs across both result lists. |

### Methods

#### `find_swimmer(*, usa_id=None, name=None, birthday=None) -> Swimmer | None`

Search across all of the meet's swimmers. Same parameter shape as
`Club.find_swimmer`.

#### `individual_results_for(event: Event) -> list[IndividualMeetResult]`

All individual results for the given event, ordered fastest first.

#### `relay_results_for(event: Event) -> list[RelayMeetResult]`

All relay results for the given event, ordered fastest first.

### Identity

A meet is identified by `(name, start_date, organization)`. The parser
will treat two files reporting the same triple as the same meet and merge
their result lists.

## Multi-file merging — rules

When `read_cl2` is called with multiple files (or a directory), records
that refer to the same logical entity are merged:

- **Clubs** (matched on `(team_code, lsc)`): fields that are `None` on
  the existing record are filled from the new record; non-`None` fields
  are preserved.
- **Swimmers** (matched on `usa_id_short`, then on `(first_name,
  last_name, birthday)`): same null-fill policy. `IndividualMeetResult`s
  from both files attach to the merged swimmer.
- **Meets** (matched on `(name, start_date, organization)`): result lists
  concatenated, other fields null-filled.

This is the same semantics whether files arrive via a glob, a directory
walk, or a list — order within a single call doesn't matter for the
output, only for warnings (warnings are reported in file order).

## Example: traversing the model

```python
from tunas import read_cl2, Event, Sex

meets, _ = read_cl2("results/")

for meet in meets:
    print(f"== {meet.name} ({meet.start_date}) ==")
    for swimmer in meet.swimmers:
        best = swimmer.best_result(Event.FREE_100_SCY)
        if best is None:
            continue
        age = swimmer.age_on(best.date)
        club = best.club.abbreviated_name if best.club else "UN"
        print(f"  {swimmer.full_name:<25} {club:>5} {best.time}  (age {age})")
```
