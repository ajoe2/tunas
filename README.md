# tunas

[![PyPI](https://img.shields.io/pypi/v/tunas.svg)](https://pypi.org/project/tunas/)
[![Python](https://img.shields.io/pypi/pyversions/tunas.svg)](https://pypi.org/project/tunas/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A Python library for parsing USA Swimming meet result files (`.cl2` / Hy-Tek SDIF v3) into structured Python objects and performing offline qualifying time standard lookups.

📖 **Documentation: <https://ajoe2.github.io/tunas/>**

## Installation

```bash
pip install tunas
```

Requires Python 3.12+ and has zero runtime dependencies outside the standard library.

## Quick Start

`read_cl2` is the main entry point. It parses files, directories, lists of paths, or text streams, returning a list of `Meet` objects and a `ParseReport`:

```python
from tunas import read_cl2

meets, report = read_cl2("results.cl2")

for meet in meets:
    print(f"{meet.name} ({meet.start_date})")
    for swim in meet.individual_swims:
        outcome = swim.time if swim.time is not None else swim.status.value
        print(f"  {swim.swimmer.full_name:<24} {swim.event.name:<16} {outcome}")

if report.warnings:
    print(f"{len(report.warnings)} records flagged — inspect report.warnings")
```

## Core Concepts

All parsed data is contained in independent `Meet` objects:

- **`Meet`**: Owns `swimmers`, `clubs`, and `results` (split into `meet.individual_swims` and `meet.relays`).
- **Swim**: Has a `.time` (`Time` or `None`) and `.status` (`ResultStatus` e.g., `OK`, `DQ`, `NS`). Scratches and disqualifications are preserved.
- **`Event`**: An enum of `(distance, stroke, course)`. Filter with `swimmer.swims_in(event)` or `meet.individual_swims_for(event)`.
- **Relays**: Contain `RelaySwim` legs. Each leg reports its individual event, sorting alongside flat-start swims.
- **Scoping**: Meets are independent; swimmers and clubs are scoped to their respective meet. Group by `id_short` (or `id_long`) to track athletes across meets.

```python
from tunas import read_cl2, Event

meets, _ = read_cl2("season/")
for meet in meets:
    for swim in meet.swimmers[0].swims_in(Event.FREE_100_SCY):
        print(meet.name, swim.session.value, swim.time)
```

## Offline Time Standards

USA Swimming motivational standards (B through AAAA) are bundled locally for offline lookup:

```python
from tunas import qualifies_for, Sex, Event, Time

# Get the fastest standard achieved (or None):
qualifies_for(Time.parse("1:05.23"), Event.FREE_100_SCY, age=12, sex=Sex.FEMALE)
# → TimeStandard.BB
```
Also supports `all_qualified(...)` and `standard_time(...)` lookups.

## Error Handling

Parsing is **lenient by default** to recover from common exporter bugs; warnings are collected in a `ParseReport`.

```python
meets, report = read_cl2("messy/")
for w in report.warnings:
    print(f"{w.source}:{w.line_no} [{w.severity.value}] {w.record_type}: {w.reason}")
```

Use `strict=True` to fail fast and raise `ParseError` on the first warning. Structural violations always raise.

## Features

- **SDIF v3 Parser**: Parses `.cl2` meet result files including relays and splits.
- **Clean Object Model**: Slotted dataclasses with direct object references and zero global state.
- **Offline Standards**: Local O(1) lookup of USA Swimming B through AAAA motivational cuts.
- **Lenient Parsing**: Detailed warning reports by default; strict validation mode available.
- **Parallel Execution**: Deterministic concurrent parsing of multiple files on thread pool.
- **Type-Safe**: Fully typed (`py.typed`).

## Documentation

- [Getting Started](docs/getting_started.md)
- [Parsing & Errors](docs/parsing.md)
- [Data Model](docs/models.md)
- [Cookbook / Recipes](docs/cookbook.md)
- [File Format (SDIF)](docs/cl2_format.md)
- [API Reference](docs/reference.md)
- [Architecture & Design](docs/architecture.md)

Full docs site: <https://ajoe2.github.io/tunas/>

## Development

Managed with `uv`:

```bash
uv sync                                      # Setup environment
uv run pytest                                # Run offline test suite
uv run pytest --cov=tunas                    # Run with coverage check (95% gate)
uv run ruff check && uv run mypy src/tunas   # Lint and type check
```

## Status

`tunas` is in **alpha**. The public API is stable, but subject to revision before 1.0.

## License

[MIT](LICENSE)
