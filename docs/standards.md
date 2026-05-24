# `tunas.standards` — USA Swimming time standards

This module resolves USA Swimming motivational time standards (B through AAAA) using data **bundled with the package**. First calls lazily load the bundled JSON; subsequent calls are cached.

## `TimeStandard` enum

```python
class TimeStandard(IntEnum):
    B    = 1
    BB   = 2
    A    = 3
    AA   = 4
    AAA  = 5
    AAAA = 6
```

Standards are ordered slowest to fastest based on difficulty (e.g., `TimeStandard.B < TimeStandard.AA`). Use this for sorting or comparison:

```python
max([TimeStandard.B, TimeStandard.AA, TimeStandard.AAA])
# → TimeStandard.AAA
```

Supports a human-readable `display()` method:

```python
TimeStandard.AAAA.display()        # "AAAA"
TimeStandard.BB.display()          # "BB"
```

## API

```python
from tunas import qualifies_for, standard_time, all_qualified
```

### `qualifies_for(time, event, age, sex) -> TimeStandard | None`

Returns the fastest standard a time achieves, or `None` if it does not qualify.

```python
from tunas import Time, Event, Sex, qualifies_for, TimeStandard

t = Time.parse("1:05.23")
qualifies_for(t, Event.FREE_100_SCY, age=12, sex=Sex.FEMALE)
# → TimeStandard.BB (or whatever cut the time meets)
```

- `time`: the swim time.
- `event`: the event (must be a member of `Event`).
- `age`: the swimmer's age on the swim date (`int`).
- `sex`: `Sex.MALE` or `Sex.FEMALE`. `Sex.MIXED` raises `ValueError`.

### `all_qualified(time, event, age, sex) -> list[TimeStandard]`

Returns all standards the time qualifies for, ordered slowest first:

```python
all_qualified(Time.parse("55.12"), Event.FREE_100_SCY, age=15, sex=Sex.FEMALE)
# → [TimeStandard.B, TimeStandard.BB, TimeStandard.A, TimeStandard.AA, TimeStandard.AAA]
```

### `standard_time(standard, event, age, sex) -> Time | None`

Reverse lookup: returns the cutoff time required to qualify. Returns `None` if no standard is defined for the combination.

```python
standard_time(TimeStandard.AAAA, Event.FREE_100_SCY, age=12, sex=Sex.FEMALE)
# → Time(...)
```

## Caching and lazy loading

The bundled JSON file is loaded once on the first call into a per-process cache index keyed by `(standard, age_group, sex, event)`. Subsequent lookups are O(1). Clear the cache in tests using `.cache_clear()` on the internal loader.

## Standards versioning

Motivational standards are updated by USA Swimming every four years. Upgrading `tunas` is the only action required to get the latest cuts.

## Bundled JSON schema

The schema (`src/tunas/_data/standards-2025-2028.json`) maps cuts flatly:

```json
{
  "version": "2025-2028",
  "season_start": "2024-09-01",
  "season_end": "2028-08-31",
  "source_notes": "USA Swimming 2028 motivational standards",
  "standards": [
    {
      "standard": "B",
      "age_group": "10_U",
      "sex": "F",
      "event": "FREE_50_SCY",
      "cutoff_centiseconds": 3895
    }
  ]
}
```

Semantics:
- `standard`: Matches a `TimeStandard` name (e.g., `"B"`, `"AAAA"`).
- `age_group`: Standard age-group label (e.g., `"10_U"`, `"SENIOR"`) used only as a lookup key within the table.
- `sex`: `"M"` or `"F"`.
- `event`: Matches an `Event` name (e.g., `"FREE_50_SCY"`).
- `cutoff_centiseconds`: Slowest qualifying time in centiseconds.

Duplicate rows raise `StandardsError` on load.

## Errors

Functions in this module raise:
- `StandardsError` if the bundled JSON is missing, corrupt, or fails consistency checks.
- `ValueError` if `sex` is `Sex.MIXED`.

## Example: tagging a season

Compute age from the birthdate and swim date, then look up cuts:

```python
from tunas import read_cl2, qualifies_for, TimeStandard

def age_at(swimmer, on_date):
    b = swimmer.birthday
    if b is None or on_date is None:
        return None
    return on_date.year - b.year - ((on_date.month, on_date.day) < (b.month, b.day))

meets, _ = read_cl2("season/")
for meet in meets:
    for swim in meet.individual_swims:
        if swim.time is None:               # skip non-time outcomes (DQ/NS/...)
            continue
        age = age_at(swim.swimmer, swim.date)
        if age is None:
            continue
        std = qualifies_for(swim.time, swim.event, age, swim.swimmer.sex)
        if std and std >= TimeStandard.AA:
            print(f"{swim.date} {swim.swimmer.full_name:<25} {swim.event} {swim.time}  {std.name}")
```


