# Getting started

This guide covers installation and basic usage of `tunas`.

## Install

```
pip install tunas
```

`tunas` requires Python 3.12 or newer. With `uv`:

```
uv add tunas
```

## A first example

```python
from tunas import read_cl2, Event

meets, report = read_cl2("results/")        # path, dir, list of paths, or file-like

for meet in meets:
    swimmer = next((s for s in meet.swimmers
                    if s.id_short == "ABC123456789"), None)
    if swimmer is None:
        continue
    for swim in swimmer.swims_in(Event.FLY_200_LCM):
        outcome = swim.time if swim.time is not None else swim.status.value
        print(f"{meet.name}: {swimmer.full_name} {swim.session.value} {outcome}")
```

Every `tunas` program follows this pattern: parse input into self-contained [`Meet`](models.md) objects, then traverse the data graph.

## Walking through the example

### 1. Parsing

```python
meets, report = read_cl2("results/")
```

`read_cl2` accepts a file path, directory, list of paths, or text file-like object, returning `(list[Meet], ParseReport)`.

By default, parsing is lenient: malformed records are skipped and collected as warnings. Pass `strict=True` to fail fast on the first error.

```python
for w in report.warnings:
    print(f"{w.source}:{w.line_no} ({w.record_type}): {w.reason}")
```

Meets are independent. Swimmers and clubs are scoped to each meet; the same swimmer in two different meets is parsed as two distinct `Swimmer` objects.

### 2. Finding a swimmer in a meet

Filter `Meet.swimmers` to locate a specific athlete:

```python
swimmer = next((s for s in meet.swimmers
                if s.id_short == "ABC123456789"), None)
```

Swimmers within a meet are grouped by member ID (`id_short` falling back to `id_long`). Names are not guaranteed to be unique. See [models.md](models.md) for details.

### 3. A swimmer's swims in an event

```python
swims = swimmer.swims_in(Event.FLY_200_LCM)
```

`Event` covers all USA Swimming events across courses (SCY, SCM, LCM) — see [event.md](event.md). `swimmer.swims_in(event)` returns all swims (including prelims, finals, DQs, and scratches). Both `IndividualSwim` and `RelaySwim` share a uniform interface (`time`, `status`, `event`, `date`, `meet`, `swimmer`).

Get the fastest swim:
```python
fastest = min((s for s in swims if s.time), key=lambda s: s.time, default=None)
```

### 4. Time standards

```python
std = qualifies_for(swim.time, swim.event, age, swimmer.sex)
```

`qualifies_for` checks the highest USA Swimming motivational standard achieved. Standards are bundled locally (no internet access required). See [standards.md](standards.md).

## What's in the box

| Concept | Class | Where to read more |
|---|---|---|
| Reading a file | `read_cl2` | [parsing.md](parsing.md) |
| A meet | `Meet` | [models.md](models.md) |
| A swimmer | `Swimmer` | [models.md](models.md) |
| A club | `Club` | [models.md](models.md) |
| One swimmer's swim | `Swim` (base of the next two) | [models.md](models.md#swim) |
| An individual swim | `IndividualSwim` | [models.md](models.md) |
| A relay (+ its legs / alternates) | `Relay`, `RelaySwim` | [models.md](models.md) |
| Splits | `Split` | [models.md](models.md) |
| A time | `Time` | [time.md](time.md) |
| An event | `Event` | [event.md](event.md) |
| Strokes, courses, etc. | `Stroke`, `Course`, ... | [enums.md](enums.md) |
| Time standards | `qualifies_for`, `standard_time`, `TimeStandard` | [standards.md](standards.md) |

## Where to go next

- [parsing.md](parsing.md) — `read_cl2` options and error handling.
- [models.md](models.md) — the complete object graph.
- [cookbook.md](cookbook.md) — recipes for common tasks.
- [architecture.md](architecture.md) — codebase design and layout.

