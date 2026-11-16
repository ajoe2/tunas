# Data model

Each [`MeetArchive`](parsing.md#meetarchive) wraps a list of self-contained [`Meet`][tunas.models.Meet] objects. This page covers the object graph and its scoping rules; the [API Reference](../reference/models.md) has every field.

## Object graph

**Inheritance**: two base types sit above the concrete results:

```
Swim (one swimmer's swim)           MeetResult (a row in Meet.results)
├── IndividualSwim                  ├── IndividualSwim
└── RelaySwim                       └── Relay
```

**Containment**: each `Meet` owns its results, swimmers, and clubs:

```
list[Meet]                                ← usually one Meet per file
└── Meet
    ├── results   : list[MeetResult]      ← IndividualSwim or Relay
    │   ├── IndividualSwim
    │   │   └── swimmer  : Swimmer
    │   └── Relay
    │       ├── splits     : list[Split]        ← whole-relay cumulative marks
    │       ├── legs       : list[RelaySwim]    ← the ≤4 swum legs (LEG_1–LEG_4)
    │       │   └── RelaySwim
    │       │       ├── swimmer : Swimmer
    │       │       └── relay   : Relay         ← back-reference
    │       └── alternates : list[RelaySwim]    ← rostered but did not swim
    ├── swimmers  : list[Swimmer]
    │   └── Swimmer
    │       ├── swims    : list[IndividualSwim | RelaySwim]   ← common base: Swim
    │       └── club     : Club | None
    └── clubs     : list[Club]
        └── Club
            ├── results  : list[MeetResult]
            └── swimmers : list[Swimmer]
```

Every reference, including back-references like `RelaySwim.relay`, is wired during
parsing, so traversals are plain attribute reads. Because the graph is cyclic, each
aggregate's `repr()`/`str()` summarises collections by count and names related objects by
a short label, so printing a `Meet` stays one line:

```python
>>> meet
Meet(name='Champs', organization=USS, start_date=2025-01-01, clubs=12, swimmers=480, results=2310)
>>> print(meet)
Champs (2025-01-01)
```

## Two ways to look at a result

- **[`MeetResult`][tunas.models.MeetResult]** is a *row in `Meet.results`* — an
  [`IndividualSwim`][tunas.models.IndividualSwim] or a [`Relay`][tunas.models.Relay].
  It holds the shared event/place/time context but no `swimmer` or `splits`.
- **[`Swim`][tunas.models.Swim]** is *one swimmer's swim* — an `IndividualSwim` or a
  [`RelaySwim`][tunas.models.RelaySwim], the common type behind `Swimmer.swims`
  (`swimmer`, `time`, `status`, `session`, `event`, `date`, `meet`, `course`,
  `splits`, `is_relay_leg`).

An `IndividualSwim` is *both* — it appears in `Meet.results` and in its swimmer's
`swims`. A `Relay` is only a `MeetResult` (a squad, not a swim); its individual
legs are the `RelaySwim`s.

## Relay legs and their events

Swimmers who raced are in `legs` (ordered `LEG_1`–`LEG_4`); rostered swimmers who did
not race are in `alternates` and are **excluded** from `Swimmer.swims`. The squad's
splits are whole-relay cumulative marks on `Relay.splits` (e.g. 50/100/150/200 for a
4×50), from both readers. Each leg's `RelaySwim.splits` is **derived** from that row:
the marks swum during the leg, re-based to the leg start so it reads like a flat-start
swim. A cumulative split's `time` is `None` when the relay has no mark at the leg's
start. Alternates, and legs of relays with no splits, get an empty list:

```python
relay.splits          # [Split(50, 31.60), Split(100, 1:10.63), Split(150, 1:40.63), Split(200, 2:16.27)]
relay.legs[1].splits  # [Split(50, 39.03)]  — leg 2's own 50, = 1:10.63 − 31.60
relay.alternates[0].splits   # []
```

A leg reports the *individual* event it amounts to, so it sorts alongside
flat-start swims:

```python
relay.event              # Event.FREE_400_RELAY_SCY  (the squad event)
relay.legs[0].event      # Event.FREE_100_SCY        (the leg's individual event)
```

This is why `swimmer.swims_in(Event.FREE_100_SCY)` returns both 100-free
flat-starts and matching relay legs.

## Identity and scoping

Meets are independent and never merged; exporting the same meet twice yields two unrelated `Meet` objects. Swimmers are grouped within a meet by `id_short` (falling back to `id_long`), never by name or birthday alone. The same athlete in two meets is two `Swimmer` instances; cross-meet tracking is left to the application (see [Recipes](cookbook.md)).

Clubs are scoped within a meet and keyed by `(team_code, lsc)`. Unattached entries (team code ending in `UN`, or a name containing "unattached") create no `Club` instance, and the swimmer's `club` is set to `None`.

## Times and outcomes

A timed swim has `status == ResultStatus.OK` and a [`Time`][tunas.time.Time]. Non-time outcomes (`NT`, `NS`, `DNF`, `DQ`, `SCR`) have `time = None`, except course-`X` (and `.hy3`) disqualifications, which keep the swum time with `status == DQ`.

An entry that hasn't been swum — every row of an entries / psych-sheet file — has `status == ResultStatus.ENTERED`, `time = None`, `date = None`, and `session = None`; its `seed_time` is the entry time (see [Entries files](parsing.md#entries-files-psych-sheets)).

`ResultStatus` values: `OK` (official time), `NT` (no time), `NS` (no show), `DNF` (did not finish), `DQ` (disqualified), `SCR` (scratch), `EXHIBITION` (Hy-Tek exhibition swim), `ENTERED` (entered, not yet swum).

## Field reference by type

A summary of what each type carries. Aggregates (`Meet`, `Club`, `Swimmer`, result types) are mutable, slotted dataclasses with identity equality; value types are frozen and hashable.

!!! note "`.hy3`-only fields"
    Populated only by [`read_hy3`](parsing.md#read_hy3) (`None` or default under `read_cl2`):

    * **`SourceFile`**: `hy3_file_type`, `created_time`, `licensee`
    * **`Meet`**: `venue`, `age_up_date`, `sanction_number`
    * **`Club`**: `email`
    * **`MeetResult`**: `dq_code`, `dq_reason`, `converted_seed_time`, `converted_seed_course`, `backup_times`

### `Meet` — and its metadata

A [`Meet`][tunas.models.Meet] represents one `B1` block and all elements beneath it.

| Field | Type | Notes |
|---|---|---|
| `name`, `start_date` | `str`, `date` | Required (M1). |
| `end_date`, `city`, `state`, `country`, `postal_code`, `address_one`, `address_two` | optional | Location. `state` is a [`State`][tunas.geography.State]; `country` is a [`Country`][tunas.geography.Country]. |
| `organization` | [`Organization`][tunas.enums.Organization] `\| None` | ORG code (USS, Masters, NCAA, ...). `None` when the source carries no org code (`.hy3` always; `.cl2` when the field is blank). |
| `course` | [`Course`][tunas.enums.Course] `\| None` | Default course (`B1` col 150). |
| `altitude` | `int \| None` | Pool altitude in feet. |
| `meet_type` | [`MeetType`][tunas.enums.MeetType] `\| None` | Almost always blank in real `.cl2`. |
| `host` | `MeetHost \| None` | From `B2` (see below). |
| `source_file` | `SourceFile \| None` | File-level provenance, shared by all meets in one file. |
| `results`, `swimmers`, `clubs` | lists | Contents of the meet. |

Convenience accessors: `meet.individual_swims`, `meet.relays`,
`meet.individual_swims_for(event)`, `meet.relays_for(event)`.

[`MeetHost`][tunas.models.MeetHost] (frozen) holds `name`, `address_one`, `address_two`,
`city`, `state`, `postal_code`, `country`, `phone`. Real `.cl2` files never emit `B2`, so
`host` is usually `None` (host details live in the sibling `.hy3` file).

[`SourceFile`][tunas.models.SourceFile] (frozen) captures the file header (SDIF `A0`/`Z0` or Hy-Tek `A1`): `path`, `file_type` ([`FileType`][tunas.enums.FileType]), `sdif_version`, `software_name`, `software_version`, `contact_name`, `contact_phone`, `created` (date), `submitted_by_lsc` ([`LSC`][tunas.geography.LSC]), and `notes`. For `.hy3` files, it also carries `hy3_file_type` ([`Hy3FileType`][tunas.enums.Hy3FileType]), `created_time`, and `licensee`.

### `Club` — and entry counts

A [`Club`][tunas.models.Club] is keyed within a meet by `(team_code, lsc)`. Beyond identity
(`team_code`, `lsc`, `full_name`, `abbreviated_name`, `short_name`) it carries `organization`,
the address fields, `region` ([`Region`][tunas.enums.Region]), `coach`, `coach_phone`,
`entry_counts`, and its own `results`/`swimmers` (plus `club.individual_swims` /
`club.relays`).

[`ClubEntryCounts`][tunas.models.ClubEntryCounts] (frozen, from `C2`) records the team's
declared totals: `num_individual_swims`, `num_athletes`, `num_relay_entries`,
`num_relay_name_records`, `num_split_records`. Real `.cl2` files never emit `C2`, so this is
usually `None`.

### `Swimmer` — identity and PII

A [`Swimmer`][tunas.models.Swimmer] is scoped to one meet.

| Field | Type | Notes |
|---|---|---|
| `first_name`, `last_name`, `sex` | `str`, `str`, [`Sex`][tunas.enums.Sex] | Required. |
| `middle_initial`, `preferred_first_name` | `str \| None` | `preferred_first_name` comes from `D3`. |
| `id_short` | `str \| None` | 12-char USS# — the primary identity key. |
| `id_long` | `str \| None` | 14-char modern SWIMS ID (from `D3`); identity fallback. |
| `birthday` | `date \| None` | Often blank ("WODOB" privacy exports). |
| `citizenship` | `Citizenship \| Country \| None` | A non-country code or a country (see below). |
| `club` | `Club \| None` | `None` when the swimmer is unattached. |
| `contact` | `SwimmerContact \| None` | PII; absent in results files. |
| `registration` | `SwimmerRegistration \| None` | Sensitive PII; absent in results files. |
| `swims` | `list[IndividualSwim \| RelaySwim]` | Counting swims (relay alternates excluded). |

Accessors: `full_name`, `individual_swims`, `relay_swims`, `swims_in(event)`.

[`SwimmerContact`][tunas.models.SwimmerContact] (frozen, from `D1`/`D2`): `address`, `city`,
`state`, `postal_code`, `country`, `region`, `alt_mailing_name`, `phone_primary`,
`phone_secondary`.

[`SwimmerRegistration`][tunas.models.SwimmerRegistration] (frozen, from `D1`/`D2`/`D3`):
`member_status` ([`MemberStatus`][tunas.enums.MemberStatus]), `registration_date`, `season`
([`Season`][tunas.enums.Season]), `ethnicity_primary`/`ethnicity_secondary`
([`Ethnicity`][tunas.enums.Ethnicity]), `affiliations` (`frozenset[Affiliation]`),
`old_member_number`, `fina_other_federation`, `admin_info`.

!!! note "Citizenship is `Citizenship | Country`"
    SDIF's CITIZEN code is either one of two non-country codes — [`Citizenship.DUAL`][tunas.enums.Citizenship]
    (`2AL`) or `Citizenship.FOREIGN` (`FGN`) — *or* any FINA [`Country`][tunas.geography.Country]
    code. So `Swimmer.citizenship` and `RelaySwim.citizenship` are typed
    `Citizenship | Country | None`.

### Result rows: `IndividualSwim`, `Relay`, `RelaySwim`

Every row in `Meet.results` (an [`IndividualSwim`][tunas.models.IndividualSwim] or a
[`Relay`][tunas.models.Relay]) shares the [`MeetResult`][tunas.models.MeetResult] base:

| Field | Type | Notes |
|---|---|---|
| `meet`, `club` | `Meet`, `Club \| None` | Back-references. |
| `organization` | [`Organization`][tunas.enums.Organization] `\| None` | As on `Meet`. |
| `event` | [`Event`][tunas.event.Event] | The `(distance, stroke, course)` event. |
| `event_sex` | [`Sex`][tunas.enums.Sex] | `M`/`F`/`X` (mixed). |
| `event_min_age`, `event_max_age` | `int \| None` | Event age range. |
| `session` | [`Session`][tunas.enums.Session] `\| None` | `PRELIMS`/`FINALS`/`SWIM_OFFS`; `None` for an entry (`ENTERED`). |
| `status` | [`ResultStatus`][tunas.enums.ResultStatus] | Outcome. |
| `time`, `date` | `Time \| None`, `date \| None` | |
| `seed_time`, `seed_course` | `Time \| None`, `Course \| None` | |
| `heat`, `lane`, `rank` | `int \| None` | `rank` is the place. |
| `points` | `float \| None` | Scored at finals. |
| `event_number` | `str \| None` | Meet program event number. |
| `event_min_time_class`, `event_max_time_class` | [`EventTimeClass`][tunas.enums.EventTimeClass] `\| None` | Almost always blank. |

[`IndividualSwim`][tunas.models.IndividualSwim] adds `swimmer`, `swimmer_age_class`,
`attach_status` ([`AttachStatus`][tunas.enums.AttachStatus]), and `splits`; its `course`
derives from the event and `is_relay_leg` is always `False`.

[`Relay`][tunas.models.Relay] adds `relay_letter` (the `A`/`B`/… squad designator),
`total_age`, `legs`, `alternates`, and `splits`. A `Relay` is *not* a `Swim`; its swims are the legs.

[`RelaySwim`][tunas.models.RelaySwim] is one swimmer's leg or roster slot: `swimmer`
(`None` if unidentified), `relay` (back-reference), `order` ([`RelayLegOrder`][tunas.enums.RelayLegOrder]),
`time`, `status`, `takeoff_time` (relay-exchange reaction, in hundredths of a second),
`course`, `swimmer_age_class`, `citizenship`, and `splits`. Its `event`, `date`, `meet`, and
`session` are derived from the parent relay, and `is_relay_leg` is always `True`.

### `Split`

[`Split`][tunas.models.Split] (frozen) is one segment from a `G0` record: `distance`
(cumulative distance from the start, e.g. 50/100/150), `time` (`Time \| None`), and
`split_type` ([`SplitType.INTERVAL`][tunas.enums.SplitType] or `CUMULATIVE`). Individual
splits attach to their `IndividualSwim`; relay splits to the `Relay` (legs derive theirs).

## Times

[`Time`][tunas.time.Time] is an immutable, hashable value storing `centiseconds: int`:

```python
from tunas import Time

t = Time.parse("1:04.87")     # accepts "[M:]SS.HH"; whitespace tolerated
t.centiseconds                # 6487
t.minute, t.second, t.hundredth   # (1, 4, 87)
t.total_seconds               # 64.87
str(t)                        # "1:04.87"  (round-trips with Time.parse)

Time.parse("23.45") < t       # True — faster times sort first
t - Time.parse("4.87")        # Time(...) for "1:00.00"
```

Faster times compare as *less than* slower ones, so `min(...)`/`sorted(...)` give the
fastest first. Addition and subtraction return a new `Time`; subtracting a larger time from
a smaller one raises `ValueError`, as does constructing a negative `Time`.

## Enumerations

Every categorical field is an enum whose **value is the raw file code**, so a byte from the
file resolves directly (`Sex("F")`, `Course("3")`, `Stroke("5")`); an unknown code raises
`ValueError`. The full members are in the [enums reference](../reference/enums.md) and
[geography reference](../reference/geography.md); in brief:

| Enum | Models | Notes |
|---|---|---|
| [`Sex`][tunas.enums.Sex] | swimmer / event sex | `MALE`, `FEMALE`, `MIXED` (events only). |
| [`Stroke`][tunas.enums.Stroke] | stroke | `.display()` gives `"Free"`, `"IM"`, `"Medley Relay"`, … |
| [`Course`][tunas.enums.Course] | pool course | `SCM`/`SCY`/`LCM`; parser also accepts the alpha forms `S`/`Y`/`L`. |
| [`Session`][tunas.enums.Session] | session | `PRELIMS`, `FINALS`, `SWIM_OFFS`. |
| [`ResultStatus`][tunas.enums.ResultStatus] | swim outcome | `OK`, `NT`, `NS`, `DNF`, `DQ`, `SCR`, `EXHIBITION`, `ENTERED`. |
| [`AttachStatus`][tunas.enums.AttachStatus] | club attachment | `ATTACHED`, `UNATTACHED`. |
| [`RelayLegOrder`][tunas.enums.RelayLegOrder] | relay leg position | `LEG_1`–`LEG_4`, `ALTERNATE`, `NOT_SWUM`. |
| [`SplitType`][tunas.enums.SplitType] | split kind | `INTERVAL`, `CUMULATIVE`. |
| [`MeetType`][tunas.enums.MeetType] | meet type | Invitational, championship, dual, … |
| [`Organization`][tunas.enums.Organization] | sanctioning org | USS, Masters, NCAA, YMCA, … |
| [`FileType`][tunas.enums.FileType] | transmission type | `MEET_RESULTS`, `TOP_16`, … |
| [`Region`][tunas.enums.Region] | USA Swimming region | Regions 1–14. |
| [`EventTimeClass`][tunas.enums.EventTimeClass] | time-standard class | Novice…AAAA, Junior, Senior. |
| [`MemberStatus`][tunas.enums.MemberStatus], [`Season`][tunas.enums.Season], [`Ethnicity`][tunas.enums.Ethnicity], [`Affiliation`][tunas.enums.Affiliation], [`Citizenship`][tunas.enums.Citizenship] | registration / demographics | Populate PII value types. |
| [`LSC`][tunas.geography.LSC], [`State`][tunas.geography.State], [`Country`][tunas.geography.Country] | geography | Two-letter LSC, USPS state, FINA country. |

## Example: traversing the model

```python
from tunas import read_cl2, Event

meets = [m for arc in read_cl2("results/") for m in arc.meets]

for meet in meets:
    print(f"== {meet.name} ({meet.start_date}) ==")
    for swimmer in meet.swimmers:
        club = swimmer.club.abbreviated_name if swimmer.club else "UN"
        for swim in swimmer.swims_in(Event.FREE_100_SCY):
            outcome = swim.time if swim.time is not None else swim.status.value
            session = swim.session.value if swim.session else "-"  # None for an entry
            print(f"  {swimmer.full_name:<25} {club:>5} {session} {outcome}")
```
