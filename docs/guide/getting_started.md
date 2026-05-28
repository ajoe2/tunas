# Getting started

Install `tunas` and parse your first meet results file.

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

# read_cl2 yields one MeetArchive per source file (path, dir, list of paths, or file-like)
for archive in read_cl2("results/"):
    for meet in archive.meets:
        swimmer = next((s for s in meet.swimmers
                        if s.id_short == "ABC123456789"), None)
        if swimmer is None:
            continue
        for swim in swimmer.swims_in(Event.FLY_200_LCM):
            outcome = swim.time if swim.time is not None else swim.status.value
            print(f"{meet.name}: {swimmer.full_name} {swim.session.value} {outcome}")
```

Every `tunas` program parses input into self-contained [`Meet`](models.md) objects and traverses the resulting data graph.

## Walkthrough

### 1. Parsing

`read_cl2` parses a file path, directory, list of paths, or text stream, yielding a lazy iterator of [`MeetArchive`](parsing.md#meetarchive) objects — one per file. Each archive carries that file's `meets` and its own `report`.

Parsing is lenient by default. Malformed records are skipped or recovered, and recorded as warnings in the per-file report:

```python
for archive in read_cl2("results/"):
    for warning in archive.report.warnings:
        print(f"{warning.source}:{warning.line_no}: {warning.reason}")
```

Each `report` aggregates running metrics for its file like `files_read`, `meets_parsed`, `swimmers_parsed`, and `individual_swims_parsed`:

```python
print(archive.report.meets_parsed, "meets,", archive.report.individual_swims_parsed, "swims")
```

Pass `strict=True` to fail fast and raise `ParseError` on the first warning. For large datasets, the iterator is lazy — files are parsed one at a time as you consume archives, so peak memory stays flat regardless of corpus size. See [parsing.md](parsing.md) for more details.

### 2. Finding a Swimmer

Swimmers are grouped within each meet by member ID (`id_short` falling back to `id_long`):

```python
swimmer = next((s for s in meet.swimmers if s.id_short == "ABC123456789"), None)
```

### 3. Querying Swims

`swimmer.swims_in(event)` returns all flat-start individual swims and relay legs for the given event, including prelims, finals, scratches, and disqualifications:

```python
swims = swimmer.swims_in(Event.FLY_200_LCM)
```

Both `IndividualSwim` and `RelaySwim` share the uniform `Swim` interface (`time`, `status`, `event`, `date`, `meet`, `swimmer`).

### 4. Time Standards

USA Swimming motivational cuts (B through AAAA) are bundled locally for offline use:

```python
from tunas import qualifies_for, all_qualified, standard_time, TimeStandard

# Fastest standard achieved (or None)
standard = qualifies_for(swim.time, swim.event, age=12, sex=swimmer.sex)

# All qualified standards, slowest first
standards = all_qualified(swim.time, swim.event, age=12, sex=swimmer.sex)

# Cutoff time for a specific standard (or None)
target = standard_time(TimeStandard.AAAA, swim.event, age=12, sex=swimmer.sex)
```

Ages are bucketed into single-year groups (10 & under, 11-12, 13-14, 15-16, 17-18). Lookups are defined for `MALE` and `FEMALE` only; `Sex.MIXED` raises `ValueError`.

## What's in the box

| Concept | Class | Where to read more |
|---|---|---|
| Reading a file | [`read_cl2`][tunas.read_cl2], [`read_hy3`][tunas.read_hy3] | [parsing.md](parsing.md) |
| A meet | [`Meet`][tunas.models.Meet] | [models.md](models.md) |
| A swimmer | [`Swimmer`][tunas.models.Swimmer] | [models.md](models.md) |
| A club | [`Club`][tunas.models.Club] | [models.md](models.md) |
| One swimmer's swim | [`Swim`][tunas.models.Swim] (base of the next two) | [models.md](models.md) |
| An individual swim | [`IndividualSwim`][tunas.models.IndividualSwim] | [models.md](models.md) |
| A relay (+ its legs / alternates) | [`Relay`][tunas.models.Relay], [`RelaySwim`][tunas.models.RelaySwim] | [models.md](models.md) |
| Splits | [`Split`][tunas.models.Split] | [models.md](models.md) |
| A time | [`Time`][tunas.time.Time] | [API reference](../reference/event_time.md) |
| An event | [`Event`][tunas.event.Event] | [API reference](../reference/event_time.md) |
| Strokes, courses, etc. | [`Stroke`][tunas.enums.Stroke], [`Course`][tunas.enums.Course], ... | [API reference](../reference/enums.md) |
| Time standards | [`qualifies_for`][tunas.standards.qualifies_for], [`standard_time`][tunas.standards.standard_time], [`TimeStandard`][tunas.standards.TimeStandard] | [API reference](../reference/standards.md) |

## Where to go next

- [parsing.md](parsing.md) — `read_cl2` options and error handling.
- [models.md](models.md) — the complete object graph.
- [cookbook.md](cookbook.md) — recipes for common tasks.
- [architecture.md](../about/architecture.md) — codebase design and layout.

