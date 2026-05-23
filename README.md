# tunas

[![PyPI](https://img.shields.io/pypi/v/tunas.svg)](https://pypi.org/project/tunas/)
[![Python](https://img.shields.io/pypi/pyversions/tunas.svg)](https://pypi.org/project/tunas/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A Python library for parsing and analyzing USA Swimming meet result files
(`.cl2` / Hy-Tek SDIF v3).

`tunas` reads `.cl2` files into clean, idiomatic Python objects — `Meet`,
`Club`, `Swimmer`, `IndividualMeetResult`, `RelayMeetResult` — and ships
USA Swimming time standards as bundled data so qualifying-time lookups
work out of the box.

## Install

```
pip install tunas
```

`tunas` has zero runtime dependencies and supports Python 3.12+.

## Quick example

```python
from tunas import read_cl2, Event, Sex, TimeStandard, qualifies_for

meets, report = read_cl2("results/")

for meet in meets:
    swimmer = meet.find_swimmer(name="Phelps, Michael")
    if swimmer is None:
        continue

    best = swimmer.best_result(Event.FLY_200_LCM)
    if best is None:
        continue

    standard = qualifies_for(best.time, best.event, swimmer.age_on(best.date), swimmer.sex)
    print(f"{swimmer.full_name}: {best.time} ({standard.name if standard else 'no standard'})")

if report.warnings:
    print(f"{len(report.warnings)} records were skipped — see report.warnings for details")
```

## Features

- Parse `.cl2` (Hy-Tek SDIF v3) meet result files — every record type in the
  spec, including relay events (E0/F0) and splits (G0).
- Pythonic dataclass models with computed views — no manual synchronization.
- Best-time lookup, swimmer search by USA ID / name / birthday.
- USA Swimming time-standards lookup (B / BB / A / AA / AAA / AAAA + championship cuts), shipped as bundled data.
- Lenient parsing by default with a detailed `ParseReport`; opt-in `strict=True`
  raises on the first malformed record.
- Zero runtime dependencies; fully type-hinted (`py.typed`).

## Documentation

Full documentation lives in [`docs/`](docs/):

- [Getting started](docs/getting_started.md)
- [Architecture](docs/architecture.md)
- [Parsing](docs/parsing.md) · [Models](docs/models.md) · [Time](docs/time.md) · [Event](docs/event.md) · [Enums](docs/enums.md) · [Exceptions](docs/exceptions.md) · [Standards](docs/standards.md)
- [CL2 / SDIF v3 format](docs/cl2_format.md) · [Cookbook](docs/cookbook.md)

## Status

`tunas` is in **alpha**. The API is documented in `docs/` and stable enough to
build on, but breaking changes may occur before 1.0 if real-world usage
surfaces design issues.

## License

[MIT](LICENSE)
