# Getting started

This page walks through installing `tunas` and using it for the first
time. For deeper material, see the per-module pages linked at the end.

## Install

```
pip install tunas
```

`tunas` requires Python 3.12 or newer and has **no runtime dependencies**.
If you use `uv`, the equivalent command is:

```
uv add tunas
```

## A 15-line example

```python
from tunas import read_cl2, Event, qualifies_for

meets, report = read_cl2("results/")          # path, dir, list of paths, or file-like

for meet in meets:
    swimmer = meet.find_swimmer(name="Phelps, Michael")
    if swimmer is None:
        continue

    best = swimmer.best_result(Event.FLY_200_LCM)
    if best is None:
        continue

    age = swimmer.age_on(best.date)
    std = qualifies_for(best.time, best.event, age, swimmer.sex)
    print(f"{swimmer.full_name}: {best.time} ({std.name if std else 'no standard'})")
```

That's the shape of every `tunas` program: parse, traverse, ask
questions of the model.

## Walking through the example

### 1. Parsing

```python
meets, report = read_cl2("results/")
```

`read_cl2` is the single entry point. It accepts a path, a directory, a
list of paths, or any text file-like object. It returns a list of
`Meet` objects plus a `ParseReport` summarizing what was processed.

If any records were malformed, they're listed on `report.warnings`:

```python
for w in report.warnings:
    print(f"{w.source}:{w.line_no} ({w.record_type}): {w.reason}")
```

The default mode is lenient — malformed records are skipped, never
raised. Pass `strict=True` if you want a hard failure on the first bad
record. See [`parsing.md`](parsing.md) for details.

### 2. Finding a swimmer

```python
swimmer = meet.find_swimmer(name="Phelps, Michael")
```

`find_swimmer` accepts `name`, `usa_id`, and/or `birthday`. Pass at
least one. The name match is case-insensitive and accepts the
SDIF-canonical `"Last, First"` order as well as `"First Last"`.

`Club.find_swimmer` works the same way but is scoped to one club's
roster.

### 3. Best time in an event

```python
best = swimmer.best_result(Event.FLY_200_LCM)
```

`Event` is an enum of every USA Swimming event across SCY, SCM, and
LCM — see [`event.md`](event.md). `best_result` returns the swimmer's
fastest `IndividualMeetResult` for that event, or `None` if they haven't
swum it.

### 4. Time standards

```python
std = qualifies_for(best.time, best.event, age, swimmer.sex)
```

`qualifies_for` looks up the best USA Swimming standard the time
qualifies for. The data is bundled — no setup, no file paths, no
network. See [`standards.md`](standards.md).

If the swim doesn't qualify for any standard, `std` is `None`.

## What's in the box

| Concept | Class | Where to read more |
|---|---|---|
| Reading a file | `read_cl2` | [parsing.md](parsing.md) |
| A meet | `Meet` | [models.md](models.md) |
| A swimmer | `Swimmer` | [models.md](models.md) |
| A club | `Club` | [models.md](models.md) |
| An individual result | `IndividualMeetResult` | [models.md](models.md) |
| A relay | `RelayMeetResult`, `RelayLeg` | [models.md](models.md) |
| Splits | `Split` | [models.md](models.md) |
| A time | `Time` | [time.md](time.md) |
| An event | `Event` | [event.md](event.md) |
| Strokes, courses, etc. | `Stroke`, `Course`, ... | [enums.md](enums.md) |
| Time standards | `qualifies_for`, `standard_time`, `TimeStandard` | [standards.md](standards.md) |

## Where to go next

- [`cookbook.md`](cookbook.md) — end-to-end recipes for common tasks
  (top-10 fastest in a club, season qualifying check, CSV export, …).
- [`parsing.md`](parsing.md) — every edge case the parser handles, and
  how to write strict-mode validators.
- [`models.md`](models.md) — the full object graph, identity rules, and
  multi-file merging behavior.
- [`architecture.md`](architecture.md) — design decisions and
  publishing notes (for forks and contributors).
