# tunas

[![PyPI](https://img.shields.io/pypi/v/tunas.svg)](https://pypi.org/project/tunas/)
[![Python](https://img.shields.io/pypi/pyversions/tunas.svg)](https://pypi.org/project/tunas/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A Python library for parsing and analyzing USA Swimming meet result files (`.cl2` / Hy-Tek SDIF v3).

`tunas` parses `.cl2` files into clean, idiomatic Python objects (`Meet`, `Club`, `Swimmer`, `IndividualSwim`, `Relay`) and bundles USA Swimming time standards for offline qualifying-time lookups.

## Install

```
pip install tunas
```

Requires Python 3.12+ and has zero third-party runtime dependencies.

## Quick example

```python
from tunas import read_cl2

meets, report = read_cl2("results.cl2")

for meet in meets:
    print(f"{meet.name} ({meet.start_date})")
    for swim in meet.individual_swims:
        outcome = swim.time if swim.time is not None else swim.status.value  # DQ / NS / ...
        print(f"  {swim.swimmer.full_name:<24} {swim.event.name:<16} {outcome}")

if report.warnings:
    print(f"{len(report.warnings)} records flagged — see report.warnings")
```

`read_cl2` parses files into self-contained `Meet` objects and a `ParseReport`. Swimmers are scoped to each meet; reconcile cross-meet swimmers by grouping on `id_short` or `id_long` in your application.

## Features

- **SDIF v3 Parser:** Parses `.cl2` meet result files including relays (E0/F0) and splits (G0).
- **Self-Contained Meets:** No global state or cross-file merging; parsing is a pure function of input bytes.
- **Clean Object Model:** Slotted dataclasses with direct object references (swimmers, clubs, swims, splits, and contact/registration data).
- **Offline Time Standards:** Local lookup of USA Swimming B through AAAA motivational cuts.
- **Lenient Parsing:** Recovers from data-quality issues by default with a detailed `ParseReport`. Opt-in `strict=True` raises on the first violation.
- **Type-Safe:** Fully typed and carries the `py.typed` marker.

## Documentation

Full documentation is available in [`docs/`](docs/):

- [Getting started](docs/getting_started.md)
- [Architecture](docs/architecture.md)
- [Parsing](docs/parsing.md) · [Models](docs/models.md) · [Time](docs/time.md) · [Event](docs/event.md) · [Enums](docs/enums.md) · [Exceptions](docs/exceptions.md) · [Standards](docs/standards.md)
- [CL2 / SDIF v3 format](docs/cl2_format.md) · [Cookbook](docs/cookbook.md)

## Development

Managed with [`uv`](https://docs.astral.sh/uv/) (Python 3.12+):

```bash
uv sync                     # set up the environment
uv run pytest               # run the (offline, self-contained) test suite
uv run pytest --cov=tunas   # with coverage (gated at 95%)
uv run ruff check && uv run mypy src/tunas   # lint + type-check
```

See [docs/architecture.md](docs/architecture.md#development) for the full
workflow and the release process.

## Status

`tunas` is in **alpha**. The API documented in `docs/` is stable, but breaking changes may occur before 1.0 based on real-world feedback.

## License

[MIT](LICENSE)


