# Data model

`read_cl2` returns a list of self-contained [`Meet`][tunas.models.Meet] objects. This page explains the object graph and its scoping rules. For field-by-field reference, see the [API Reference](reference.md#domain-model).

## Object graph

**Inheritance** — two small base types sit above the concrete results:

```
Swim (one swimmer's swim)           MeetResult (a row in Meet.results)
├── IndividualSwim                  ├── IndividualSwim
└── RelaySwim                       └── Relay
```

**Containment** — each `Meet` owns its results, swimmers, and clubs:

```
list[Meet]                                ← one Meet per .cl2 file
└── Meet
    ├── results   : list[MeetResult]      ← IndividualSwim or Relay
    │   ├── IndividualSwim
    │   │   └── swimmer  : Swimmer
    │   └── Relay
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

The parser wires every reference (including back-references like `RelaySwim.relay`)
in a single pass, so traversals are plain attribute reads.

## Two ways to look at a result

The same row can be viewed through two lenses, which is why there are two base
classes:

- **[`MeetResult`][tunas.models.MeetResult]** is a *row in `Meet.results`* — an
  [`IndividualSwim`][tunas.models.IndividualSwim] or a [`Relay`][tunas.models.Relay].
  It holds the shared event/place/time context but no `swimmer` or `splits`.
- **[`Swim`][tunas.models.Swim]** is *one swimmer's swim* — an `IndividualSwim` or a
  [`RelaySwim`][tunas.models.RelaySwim]. It is
  the common type behind `Swimmer.swims`, giving both kinds a uniform interface
  (`swimmer`, `time`, `status`, `session`, `event`, `date`, `meet`, `course`,
  `splits`, `is_relay_leg`).

An `IndividualSwim` is *both* — it appears in `Meet.results` and in its swimmer's
`swims`. A `Relay` is only a `MeetResult` (a squad, not a swim); its individual
legs are the `RelaySwim`s.

## Relay legs and their events

A `Relay` carries its swimmers as `RelaySwim` legs. Swimmers who raced are in
`legs` (ordered `LEG_1`–`LEG_4`); rostered swimmers who did not race are in
`alternates` and are **excluded** from `Swimmer.swims`. Splits live on the
individual legs (`RelaySwim.splits`), not on the squad.

A leg reports the *individual* event it amounts to, so it sorts alongside
flat-start swims:

```python
relay.event              # Event.FREE_400_RELAY_SCY  (the squad event)
relay.legs[0].event      # Event.FREE_100_SCY        (the leg's individual event)
```

This is why `swimmer.swims_in(Event.FREE_100_SCY)` returns both 100-free
flat-starts and matching relay legs.

## Identity and scoping

Meets are **independent** and never merged — the same competition exported twice
yields two unrelated `Meet` objects. Everything below a meet is scoped to it:

- **Swimmers** are grouped within a meet by `id_short`, falling back to `id_long`.
  Matching never falls back to names or birthdays, so distinct people are never
  fused. The same athlete at two meets is two distinct `Swimmer` objects;
  reconciling them across meets is left to application code (see
  [Recipes](cookbook.md)).
- **Clubs** are keyed within a meet by `(team_code, lsc)`. Unattached entries
  (team code ending `UN`, or a name containing "unattached") create no `Club`, and
  the swim's `club` is `None`.

## Times and outcomes

A timed swim has `status == ResultStatus.OK` and a [`Time`][tunas.time.Time].
Non-time outcomes (`NT`, `NS`, `DNF`, `DQ`, `SCR`) keep `time = None` — except a
course-`X` disqualification, which retains its recorded time with `status == DQ`.
Every swim is preserved either way, so DQs and scratches are available for
analysis rather than silently dropped.

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
