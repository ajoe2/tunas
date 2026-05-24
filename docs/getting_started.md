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

Every `tunas` program parses input into self-contained [`Meet`](models.md) objects and traverses the resulting data graph.

## Walkthrough

### 1. Parsing

`read_cl2` parses a file path, directory, list of paths, or text stream, returning `(list[Meet], ParseReport)`.

Parsing is lenient by default. Malformed records are skipped or recovered and listed as warnings on the report:

```python
for w in report.warnings:
    print(f"{w.source}:{w.line_no}: {w.reason}")
```

Use `strict=True` to fail fast and raise `ParseError` on the first warning instead.

### 2. Finding a Swimmer

Swimmers are grouped within each meet by member ID (`id_short` falling back to `id_long`):

```python
swimmer = next((s for s in meet.swimmers if s.id_short == "ABC123456789"), None)
```

### 3. Querying Swims

`swimmer.swims_in(event)` returns all flat-start individual swims and relay legs for the given event, including prelims, finals, scratches, and DQs:

```python
swims = swimmer.swims_in(Event.FLY_200_LCM)
```

Both `IndividualSwim` and `RelaySwim` share a uniform `Swim` interface (`time`, `status`, `event`, `date`, `meet`, `swimmer`).

### 4. Time Standards

USA Swimming motivational cuts (B through AAAA) are bundled locally:

```python
std = qualifies_for(swim.time, swim.event, age, swimmer.sex)
```

## What's in the box

| Concept | Class | Where to read more |
|---|---|---|
| Reading a file | [`read_cl2`][tunas.read_cl2] | [parsing.md](parsing.md) |
| A meet | [`Meet`][tunas.models.Meet] | [models.md](models.md) |
| A swimmer | [`Swimmer`][tunas.models.Swimmer] | [models.md](models.md) |
| A club | [`Club`][tunas.models.Club] | [models.md](models.md) |
| One swimmer's swim | [`Swim`][tunas.models.Swim] (base of the next two) | [models.md](models.md) |
| An individual swim | [`IndividualSwim`][tunas.models.IndividualSwim] | [models.md](models.md) |
| A relay (+ its legs / alternates) | [`Relay`][tunas.models.Relay], [`RelaySwim`][tunas.models.RelaySwim] | [models.md](models.md) |
| Splits | [`Split`][tunas.models.Split] | [models.md](models.md) |
| A time | [`Time`][tunas.time.Time] | [reference.md](reference.md#events-and-time) |
| An event | [`Event`][tunas.event.Event] | [reference.md](reference.md#events-and-time) |
| Strokes, courses, etc. | [`Stroke`][tunas.enums.Stroke], [`Course`][tunas.enums.Course], ... | [reference.md](reference.md#enumerations) |
| Time standards | [`qualifies_for`][tunas.standards.qualifies_for], [`standard_time`][tunas.standards.standard_time], [`TimeStandard`][tunas.standards.TimeStandard] | [reference.md](reference.md#time-standards) |

## Where to go next

- [parsing.md](parsing.md) — `read_cl2` options and error handling.
- [models.md](models.md) — the complete object graph.
- [cookbook.md](cookbook.md) — recipes for common tasks.
- [architecture.md](architecture.md) — codebase design and layout.

