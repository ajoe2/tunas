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

Requires Python 3.12+. Currently, the runtime depends only on the Python standard library.

## Quick Start

`read_cl2` is the primary entry point. It parses file paths, directories, lists of paths, or text streams, yielding one `MeetArchive` per source file — each holding that file's `meets` and its own `ParseReport`:

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

The reader is lazy, so a large directory is parsed one file at a time. To pull everything into memory, flatten the archives: `meets = [m for arc in read_cl2(src) for m in arc.meets]`.

Hy-Tek `.hy3` results parse the same way via `read_hy3`, producing the identical `Meet` object graph:

```python
from tunas import read_hy3

(archive,) = read_hy3("Meet Results-Winter Champs-001.hy3")  # a single file -> one archive
```

## Core Concepts

All parsed data is contained in independent `Meet` objects:

- **`Meet`**: Owns `swimmers`, `clubs`, and `results` (accessible via `meet.individual_swims` and `meet.relays`, or filtered via `meet.individual_swims_for(event)` and `meet.relays_for(event)`). Carries metadata including name, dates, location, `course`, `meet_type`, `host` (`MeetHost`), and `source_file` (`SourceFile` for file-level provenance).
- **`Swimmer`**: Scoped to one meet. Exposes `full_name`, `swims`, `individual_swims`, `relay_swims`, and `swims_in(event)`. Includes identity (`id_short`/`id_long`), `birthday`, `sex`, `citizenship`, and optional contact/registration PII.
- **`Club`**: Scoped to one meet and keyed by `(team_code, lsc)`. Carries `coach`, `entry_counts`, address, and associated results and swimmers.
- **`Swim`**: The uniform interface for individual swims (`IndividualSwim`) and relay legs (`RelaySwim`), exposing `swimmer`, `time` (`Time` or `None`), `status` (`ResultStatus`), `session`, `event`, `date`, `meet`, `course`, and `splits`. Scratches and disqualifications are preserved.
- **`Event`**: A 90+ member enum of `(distance, stroke, course)`, comparable in declaration order, with helpers (`is_relay`, `leg_event`, `leg_strokes`, `Event.find`). Filter with `swimmer.swims_in(event)` or `meet.individual_swims_for(event)`.
- **Relays**: `Relay` squads contain `RelaySwim` legs (`legs`) and `alternates`. Each leg reports its individual event, so it sorts alongside flat-start swims.
- **`Time`**: Immutable centisecond value type — `Time.parse("1:04.87")`, ordering, addition/subtraction, and `minute`/`second`/`hundredth`/`total_seconds` accessors.
- **`Split`**: Per-leg splits (`distance`, `time`, `split_type`) attach to the swim that produced them.
- **Scoping**: Meets are independent and never merged; swimmers and clubs are scoped to their respective meet. Group by `id_short` (or `id_long`) to track athletes across meets.

```python
from tunas import read_cl2, Event

meets = [m for arc in read_cl2("season/") for m in arc.meets]
for meet in meets:
    for swim in meet.swimmers[0].swims_in(Event.FREE_100_SCY):
        print(meet.name, swim.session.value, swim.time)
```

## Offline Time Standards

USA Swimming motivational standards (B through AAAA, the bundled 2025–2028 cuts) are
available locally with no setup or network access. Lookups are keyed by single-year age
group (`10 & under`, `11-12`, `13-14`, `15-16`, `17-18`) and sex:

```python
from tunas import qualifies_for, all_qualified, standard_time, Sex, Event, Time

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

Standards are defined for `MALE`/`FEMALE` only; passing `Sex.MIXED` raises `ValueError`.

## Error Handling

Parsing is **lenient by default** to recover from common exporter bugs; warnings are collected in a `ParseReport`.

```python
for archive in read_cl2("messy/"):
    for w in archive.report.warnings:
        print(f"{w.source}:{w.line_no} [{w.severity.value}] {w.record_type}: {w.reason}")
```

Use `strict=True` to fail fast and raise `ParseError` on the first warning (surfaced as the iterator is consumed). Structural violations always raise.

## Features

- **Complete SDIF v3 coverage**: Parses every meet-results record type (`A0`–`G0`, `Z0`), including relays, relay alternates, and per-leg splits. Registration (`D1`/`D2`) and demographic (`D3`) records populate optional PII fields; qualifying-time records (`J0`–`J2`) surface as warnings.
- **Hy-Tek `.hy3` support**: `read_hy3` parses the reverse-engineered `.hy3` results format (confirmed fields only) into the same `Meet` object graph, capturing data SDIF omits — disqualification codes/reasons, converted seed times, and meet sanction numbers.
- **Clean object model**: Slotted dataclasses with pre-wired object references (including back-references) and zero global state. Value types (`Time`, `Split`, `MeetHost`, …) are frozen and hashable.
- **Zero data loss**: All entered swims are kept — including non-time outcomes (scratches, DQs, no-shows via `ResultStatus`). Missing optional fields become `None`; raw line contents are preserved on validation failures.
- **Lenient by default, strict on demand**: Recovers from common exporter bugs and reports each issue as a structured `ParseWarning` (with `severity`, `kind`, column, and raw line); `strict=True` fails fast on the first problem.
- **Offline standards**: Local O(1) lookup of USA Swimming B through AAAA motivational cuts, bundled as JSON — no setup or network.
- **Robust decoding**: Defaults to CP-1252 (to preserve column alignment and accented names), tolerates BOMs, short/long lines, and mixed line endings.
- **Streaming, parallel-ready execution**: Readers yield one `MeetArchive` per file lazily, so large corpora parse one file at a time with bounded memory. `max_workers` dispatches files across a thread pool behind an order-preserving look-ahead window (output identical to sequential), parsing in genuine parallel on free-threaded Python.
- **Type-safe**: Fully type-hinted and marked `py.typed`; passes `mypy --strict`.

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

Full docs site: <https://ajoe2.github.io/tunas/>

## Development

Managed with `uv`:

```bash
uv sync                                      # Setup environment (incl. dev deps)
uv run pytest                                # Run offline test suite
uv run pytest --cov=tunas                    # Run with coverage check (95% gate)
uv run ruff check && uv run ruff format      # Lint and format
uv run mypy src/tunas                        # Type-check (strict)
uv run mkdocs serve                          # Preview the docs site locally
```

The test suite is fully self-contained and offline — real-world coverage comes from
committed "golden" `.cl2` files plus hand-verified expected-state JSON under `tests/data/`,
so no data download is needed.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the test layout, golden-file regeneration,
and the release process.

## Status

`tunas` is in **alpha**. The public API is stable, but subject to revision before 1.0.

## License

[MIT](LICENSE)
