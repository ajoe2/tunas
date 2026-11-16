# Getting started

## Install

```
pip install tunas   # or: uv add tunas
```

Requires Python 3.12+.

## A first example

```python
from tunas import read_cl2, Event

# One MeetArchive per source file (path, directory, list of paths, or text stream)
for archive in read_cl2("results/"):
    for meet in archive.meets:
        swimmer = next((s for s in meet.swimmers
                        if s.id_short == "ABC123456789"), None)
        if swimmer is None:
            continue
        for swim in swimmer.swims_in(Event.FLY_200_LCM):
            outcome = swim.time if swim.time is not None else swim.status.value
            session = swim.session.value if swim.session else "-"  # None for an entry
            print(f"{meet.name}: {swimmer.full_name} {session} {outcome}")
```

## Walkthrough

### 1. Parsing

`read_cl2` lazily yields one [`MeetArchive`](parsing.md#meetarchive) per file, carrying that file's `meets` and its own `report`. Parsing is lenient: malformed records are skipped or recovered and recorded as warnings:

```python
for archive in read_cl2("results/"):
    for warning in archive.report.warnings:
        print(f"{warning.source}:{warning.line_no}: {warning.reason}")
```

The report also counts what was parsed (`meets_parsed`, `swimmers_parsed`, `individual_swims_parsed`, ...):

```python
print(archive.report.meets_parsed, "meets,", archive.report.individual_swims_parsed, "swims")
```

`strict=True` raises `ParseError` on the first warning. Files are parsed one at a time as you consume archives, so memory stays flat. See [parsing.md](parsing.md).

### 2. Swimmers and swims

Swimmers are grouped within each meet by member ID (`id_short`, falling back to `id_long`). `swimmer.swims_in(event)` returns every individual swim and relay leg in that event, including prelims, finals, scratches, and DQs. Both share the `Swim` interface (`time`, `status`, `event`, `date`, `meet`, `swimmer`).

### 3. Time standards

USA Swimming motivational cuts (B through AAAA) are bundled for offline use:

```python
from tunas import qualifies_for, all_qualified, standard_time, TimeStandard

# Fastest standard achieved (or None)
standard = qualifies_for(swim.time, swim.event, age=12, sex=swimmer.sex)

# All qualified standards, slowest first
standards = all_qualified(swim.time, swim.event, age=12, sex=swimmer.sex)

# Cutoff time for a specific standard (or None)
target = standard_time(TimeStandard.AAAA, swim.event, age=12, sex=swimmer.sex)
```

Ages are bucketed into 10 & under, 11-12, 13-14, 15-16, and 17-18; `Sex.MIXED` raises `ValueError`.

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
