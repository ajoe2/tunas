# `tunas.standards` — USA Swimming time standards

This module looks up whether a given swim time qualifies for a USA
Swimming motivational standard (B, BB, A, AA, AAA, AAAA) or championship
standard (AGC, FW, SECT, FUT, JNAT, NAT, OT). The standards data is
**bundled with the wheel** — there is nothing to download, configure, or
pass in. The first call lazily loads the bundled JSON; subsequent calls
hit a cache.

## `TimeStandard` enum

```python
class TimeStandard(IntEnum):
    B    = 1
    BB   = 2
    A    = 3
    AGC  = 4    # Age Group Championships
    AA   = 5
    FW   = 6    # Far Westerns
    AAA  = 7
    AAAA = 8
    SECT = 9    # Sectionals
    FUT  = 10   # Futures
    JNAT = 11   # Junior Nationals
    NAT  = 12   # Nationals (US Open / Summer Nats)
    OT   = 13   # Olympic Trials
```

Standards are ordered slowest → fastest. `TimeStandard.B <
TimeStandard.AA` because the standards `IntEnum` values are
monotonically increasing in difficulty. Use this when comparing or
sorting:

```python
max([TimeStandard.B, TimeStandard.AA, TimeStandard.AAA])
# → TimeStandard.AAA
```

Each member exposes a short, human-readable `display()` method:

```python
TimeStandard.AAAA.display()        # "AAAA"
TimeStandard.OT.display()          # "Olympic Trials"
```

## API

```python
from tunas import qualifies_for, standard_time, best_standard, all_qualified
```

### `qualifies_for(time, event, age, sex, *, quad="2025-2028") -> TimeStandard | None`

Returns the **best** (fastest) standard the time qualifies for, or `None`
if it doesn't qualify for any standard.

```python
from tunas import Time, Event, Sex, qualifies_for, TimeStandard

t = Time.parse("1:05.23")
qualifies_for(t, Event.FREE_100_SCY, age=12, sex=Sex.FEMALE)
# → TimeStandard.BB (or whatever cut the time meets)
```

- `time`: the swim time.
- `event`: the event (must be a member of `Event`).
- `age`: the swimmer's age on the date of the swim (`int`). Used to pick
  the right age-group cut.
- `sex`: `Sex.MALE` or `Sex.FEMALE`. `Sex.MIXED` raises `StandardsError`
  (mixed standards don't exist for individual events).
- `quad`: which standards table to use. Defaults to the current quad
  (`"2025-2028"`). See *Quad versioning* below.

Returns `None` if the time is slower than the `B` cut (or no standard
table exists for the given combination).

### `best_standard(...)` — alias for `qualifies_for`

The naming reads more naturally in some contexts:

```python
best = best_standard(swimmer.best_result(Event.FREE_100_SCY).time, ...)
```

### `all_qualified(time, event, age, sex, *, quad="2025-2028") -> list[TimeStandard]`

Returns every standard the time qualifies for, ordered slowest first:

```python
all_qualified(Time.parse("55.12"), Event.FREE_100_SCY, age=15, sex=Sex.FEMALE)
# → [TimeStandard.B, TimeStandard.BB, TimeStandard.A, TimeStandard.AA, TimeStandard.AAA]
```

Returns `[]` if the time doesn't qualify for any standard.

### `standard_time(standard, event, age, sex, *, quad="2025-2028") -> Time | None`

The reverse lookup — what time do I need to swim to qualify?

```python
standard_time(TimeStandard.AAAA, Event.FREE_100_SCY, age=12, sex=Sex.FEMALE)
# → Time(...)
```

Returns `None` if no cut is defined for the given combination — common
when an age group doesn't compete in that event (e.g. 10-and-under
swimmers don't have a 1650 Free standard).

## Caching and lazy loading

The first call to any of the standards functions triggers a one-shot
load of the bundled JSON file (~50–200 KB). Subsequent calls hit an
in-memory cache keyed by `(quad, standard, age_group, sex, event)` —
they are essentially free.

The cache is per-process and cleared automatically at interpreter exit.
There is no public API to clear it manually — if you need to force a
reload (e.g. in tests that monkeypatch the data file), restart the
process or import the private symbol from `tunas.standards`.

## Quad versioning

USA Swimming publishes a new set of motivational standards roughly every
four years, aligned to the Olympic quadrennium. Currently bundled:

| Quad | Status | Source |
|---|---|---|
| `2025-2028` | Current | USA Swimming "2028 Motivational Standards" + 2025 championship cuts |

Older quads are not bundled in v0.1.0; the `quad` kwarg accepts only
`"2025-2028"` and raises `StandardsError` for anything else. Future
releases will add new quads as they're published.

The intent is that **upgrading the library is the only action needed**
to get new standards. There is no separate data download, no
environment variable, no config file.

## Bundled JSON schema

The data ships as `src/tunas/_data/standards-2025-2028.json`. The schema
is intentionally flat — each row is one cut:

```json
{
  "version": "2025-2028",
  "season_start": "2024-09-01",
  "season_end": "2028-08-31",
  "source_notes": "USA Swimming 2028 motivational standards; 2025 championship standards",
  "standards": [
    {
      "standard": "B",
      "age_group": "10_U",
      "sex": "F",
      "event": "FREE_50_SCY",
      "cutoff_centiseconds": 3895
    },
    {
      "standard": "BB",
      "age_group": "10_U",
      "sex": "F",
      "event": "FREE_50_SCY",
      "cutoff_centiseconds": 3675
    }
  ]
}
```

Field types and semantics:

- `standard`: must match a `TimeStandard` name (`"B"`, `"BB"`, …,
  `"OT"`).
- `age_group`: must match an `AgeGroup` name (`"10_U"`, `"11_12"`, …,
  `"SENIOR"`, `"OPEN"`).
- `sex`: `"M"` or `"F"` (`Sex.value`).
- `event`: must match an `Event` name (`"FREE_50_SCY"`, …).
- `cutoff_centiseconds`: integer ≥ 1; the slowest time that qualifies
  for this standard.

Rows are unordered. Two rows with the same `(standard, age_group, sex,
event)` key are a fatal error — `StandardsError` is raised on first
load.

The JSON is generated offline by `scripts/convert_standards.py` from
the USA Swimming standards `.xlsx` files. The converter is not shipped
to end users; only the resulting JSON is.

## Errors

Functions in this module raise:

- `StandardsError` if the requested `quad` is not bundled, the bundled
  JSON cannot be parsed, or a consistency check fails.
- `ValueError` if `sex` is `Sex.MIXED` (no mixed standards exist for
  individual events).

See [`exceptions.md`](exceptions.md).

## Example: tagging an entire season

```python
from tunas import (
    read_cl2, Sex, qualifies_for, all_qualified, TimeStandard,
)

meets, _ = read_cl2("season/")
for meet in meets:
    for result in meet.individual_results:
        if result.event.is_relay():
            continue
        age = result.swimmer.age_on(result.date)
        if age is None:
            continue
        std = qualifies_for(result.time, result.event, age, result.swimmer.sex)
        if std and std >= TimeStandard.AA:
            print(f"{result.date} {result.swimmer.full_name:<25} {result.event} {result.time}  {std.name}")
```
