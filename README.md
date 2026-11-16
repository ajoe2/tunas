# tunas

[![PyPI](https://img.shields.io/pypi/v/tunas.svg)](https://pypi.org/project/tunas/)
[![Python](https://img.shields.io/pypi/pyversions/tunas.svg)](https://pypi.org/project/tunas/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A Python library for parsing USA Swimming meet result files (`.cl2` / SDIF v3 and Hy-Tek `.hy3`) into structured Python objects and performing offline qualifying time standard lookups.

📖 **Documentation: <https://ajoe2.github.io/tunas/>**

## Installation

```bash
pip install tunas
```

Requires Python 3.12+. No runtime dependencies.

## Quick Start

`read_cl2` takes a path, directory, list of paths, or text stream and lazily yields one `MeetArchive` per source file, each holding that file's `meets` and its own `ParseReport`:

```python
from tunas import read_cl2

for archive in read_cl2("results.cl2"):
    for meet in archive.meets:
        print(f"{meet.name} ({meet.start_date})")
        for swim in meet.individual_swims:
            outcome = swim.time if swim.time is not None else swim.status.value
            print(f"  {swim.swimmer.full_name:<24} {swim.event.name:<16} {outcome}")

    if archive.report.warnings:
        print(f"{len(archive.report.warnings)} records flagged — inspect archive.report.warnings")
```

To load everything at once: `meets = [m for arc in read_cl2(src) for m in arc.meets]`.

`read_hy3` parses Hy-Tek `.hy3` files the same way, into the same `Meet` object graph:

```python
from tunas import read_hy3

(archive,) = read_hy3("Meet Results-Winter Champs-001.hy3")  # a single file -> one archive
```

## Core Concepts

- **`Meet`**: owns `swimmers`, `clubs`, and `results` (also `individual_swims`, `relays`, `individual_swims_for(event)`, `relays_for(event)`), plus metadata such as dates, location, `course`, `meet_type`, `host`, and `source_file`.
- **`Swimmer`**: `full_name`, `swims`, `individual_swims`, `relay_swims`, `swims_in(event)`, identity (`id_short`/`id_long`), `birthday`, `sex`, and optional contact/registration PII.
- **`Club`**: keyed by `(team_code, lsc)`, with `coach`, `entry_counts`, address, results, and swimmers.
- **`Swim`**: common interface of `IndividualSwim` and relay legs (`RelaySwim`): `swimmer`, `time` (`Time` or `None`), `status` (`ResultStatus`), `session`, `event`, `date`, `meet`, `course`, `splits`. Unswum entries have `status=ResultStatus.ENTERED` and `session=None`.
- **`Relay`**: holds `legs` and `alternates`; each leg reports its individual event, so it sorts alongside flat-start swims.
- **`Event`**: enum of `(distance, stroke, course)`, ordered by declaration, with `is_relay`, `leg_event`, `leg_strokes`, and `Event.find`.
- **`Time`**: immutable centisecond value: `Time.parse("1:04.87")`, ordering, `+`/`-`, and `minute`/`second`/`hundredth`/`total_seconds`.
- **Scoping**: meets are never merged; swimmers and clubs belong to one meet. Group by `id_short` (or `id_long`) to track athletes across meets.

```python
from tunas import read_cl2, Event

meets = [m for arc in read_cl2("season/") for m in arc.meets]
for meet in meets:
    for swim in meet.swimmers[0].swims_in(Event.FREE_100_SCY):
        print(meet.name, swim.session, swim.time)  # session is None for an entry
```

## Offline Time Standards

The bundled 2025–2028 USA Swimming motivational standards (B through AAAA) are keyed by
age group (`10 & under`, `11-12`, `13-14`, `15-16`, `17-18`) and sex:

```python
from tunas import Event, Sex, Time, TimeStandard, all_qualified, qualifies_for, standard_time

# Fastest standard achieved (or None):
qualifies_for(Time.parse("1:05.23"), Event.FREE_100_SCY, age=12, sex=Sex.FEMALE)
# → TimeStandard.BB

# Every standard met, slowest first:
all_qualified(Time.parse("1:05.23"), Event.FREE_100_SCY, age=12, sex=Sex.FEMALE)
# → [TimeStandard.B, TimeStandard.BB]

# The cutoff time for a given standard (or None if undefined):
standard_time(TimeStandard.AAAA, Event.FREE_100_SCY, age=12, sex=Sex.FEMALE)
# → Time(...)
```

`Sex.MIXED` raises `ValueError`.

## Error Handling

Parsing is lenient by default: recoverable problems become `ParseWarning`s in the `ParseReport`.

```python
for archive in read_cl2("messy/"):
    for w in archive.report.warnings:
        print(f"{w.source}:{w.line_no} [{w.severity.value}] {w.record_type}: {w.reason}")
```

`strict=True` raises `ParseError` on the first warning (as the iterator is consumed). Structural violations always raise.

## Features

- **SDIF v3**: every meet-results record (`A0`–`G0`, `Z0`), including relays, alternates, and splits; `D1`–`D3` fill optional PII fields.
- **Hy-Tek `.hy3`**: the reverse-engineered results format (confirmed fields only), adding DQ codes/reasons, converted seeds, and sanction numbers.
- **Entries / psych sheets**: `.hy3` and `.cl2`/`.sd3` entries files yield `ResultStatus.ENTERED` swims with seed times.
- **No data loss**: scratches, DQs, and no-shows are kept; missing optional fields become `None`; warnings carry the raw line.
- **Robust decoding**: CP-1252 by default; tolerates BOMs, short/long lines, and mixed line endings.
- **Typed**: slotted dataclasses, no global state, `py.typed`, `mypy --strict` clean.

## Documentation

- [Getting Started](docs/guide/getting_started.md)
- [Parsing & Errors](docs/guide/parsing.md)
- [Data Model](docs/guide/models.md)
- [Cookbook / Recipes](docs/guide/cookbook.md)
- [SDIF `.cl2` format reference](docs/formats/cl2_format.md)
- [Hy-Tek `.hy3` format reference](docs/formats/hy3_format.md)
- [API Reference](docs/reference/index.md)
- [Architecture & Design](docs/about/architecture.md)
- [Changelog](CHANGELOG.md)

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, tests, golden-file regeneration, and releases.

## Status

Alpha: the API may still change before 1.0.

## License

[MIT](LICENSE)
