# Architecture

This document describes how `tunas` is organized and the design decisions behind its public API.

## Description

`tunas` is a data-access library for USA Swimming meet results. It parses `.cl2` files (Hy-Tek SDIF v3) into clean, well-typed Python objects and bundles USA Swimming time standards for offline qualifying-time lookups.

### Scope

- **SDIF v3 Parsing:** Every meet-results record type, including relays and splits.
- **Domain Model:** Dataclasses for `Meet`, `Club`, `Swimmer`, `MeetResult`, `IndividualSwim`, `Relay`, `RelaySwim`, `Split`, `SwimmerContact`, `SwimmerRegistration`, `MeetHost`, and `SourceFile`.
- **Value Types:** `Time`, `Event`, and standard SDIF enums.
- **Offline Standards:** Motivational cut lookups.
- **Error Model:** Lenient parsing with structured `ParseWarning` entries, or opt-in `strict=True` validation.

## Repository layout

```
tunas/
├── pyproject.toml          Project metadata and build config (Hatchling)
├── README.md               PyPI long-description
├── LICENSE                 MIT License
├── CHANGELOG.md            Semantic version changelog
├── src/tunas/              Source package (src-layout)
│   ├── __init__.py             Public API exports
│   ├── py.typed                PEP 561 type-marker
│   ├── _version.py             Package version
│   ├── time.py                 Time value type
│   ├── enums.py                SDIF enums
│   ├── geography.py            LSC, US state, and country enums
│   ├── event.py                Event enum and helper properties
│   ├── exceptions.py           Error hierarchy
│   ├── models.py               Slotted domain dataclasses
│   ├── parser.py               read_cl2, ParseReport, and ParseWarning
│   ├── standards.py            Time-standards lookups
│   ├── _parser/                Per-record parsing logic (internal)
│   └── _data/                  Bundled package data (JSON standards, spec doc)
├── tests/                  Pytest suite (fully self-contained, no network)
│   └── data/                   Committed real `.cl2` meets + golden expected JSON
├── scripts/                Developer tools (e.g., standard sheets parser)
├── docs/                   Markdown documentation
└── .github/workflows/      CI (test.yml) and PyPI release (publish.yml)
```

The package uses a **src-layout** to ensure tests run against the installed wheel rather than the working directory.

## Design decisions

### Self-contained meets

Meets are independent. Swimmers and clubs are scoped to their respective `Meet`. A swimmer competing in multiple meets exists as distinct, unrelated `Swimmer` objects, grouped by `id_short` (falling back to `id_long`). Cross-meet grouping is delegated to application code (see [cookbook.md](cookbook.md)).

### Lenient parsing by default

Formatting errors are common in real-world `.cl2` files due to buggy exporters. `read_cl2` defaults to `strict=False`, skipping corrupt records and accumulating warnings in `ParseReport` to maximize data recovery. Use `strict=True` for strict data validation.

### Slotted domain dataclasses

We use slotted dataclasses (`@dataclass(slots=True)`) to minimize memory overhead and accelerate attribute lookups—critical for meets with tens of thousands of swims. Value types (`Time`, `Split`, `SwimmerContact`, `ParseWarning`) are frozen and hashable, while aggregates (`Meet`, `Club`, `Swimmer`, `IndividualSwim`, `Relay`) are mutable to support single-pass parsing.

Aggregate classes use `kw_only=True` to keep wide constructors readable and avoid field ordering constraints in subclassing. We use identity equality (`eq=False`) to avoid stack overflows from cyclic graph references (`meet ⇄ results`) and because the parser does not deduplicate objects.

### Pre-populated cross-references

The parser wires all graph references (e.g., `Meet.results`, `Swimmer.swims`, and back-references) in a single pass. Subsequent reads are O(1) instead of computed.

### `Time`: a centisecond integer value type

`Time` stores `centiseconds: int` internally, exposing minutes, seconds, and hundredths as properties. This ensures precise comparisons and arithmetic without floating-point drift.

### `Event`: a hand-rolled enum

`Event` is a 90+ member enum representing swim distances, strokes, and courses. Hand-rolling provides static autocomplete and helpers (e.g., `Event.find`).

### Zero setup time standards

Motivational standards are bundled as JSON and lazily loaded into an O(1) index on first use.

### Lightweight runtime footprint

`tunas` depends exclusively on the standard library, keeping the runtime footprint light.

### Pythonic API

Data is exposed via plain attributes and properties rather than getter/setter methods, facilitating clean IDE auto-complete and static typing.

## Development

The project is managed with [`uv`](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
uv sync                       # create/refresh the virtual environment (incl. dev deps)

uv run pytest                 # run the test suite
uv run pytest --cov=tunas     # run with coverage (gated at 95% via pyproject)
uv run ruff check             # lint
uv run ruff format            # auto-format (use --check in CI)
uv run mypy src/tunas         # type-check (strict)
```

The test suite is **fully self-contained and offline**: real-world coverage comes
from committed "golden" files under `tests/data/` (a real meet `.cl2` plus its
hand-verified expected-state JSON), so no data download or external checkout is
needed. CI (`.github/workflows/test.yml`) runs lint, type-check, and the
coverage-gated suite on Python 3.12 and 3.13.

> If `uv run pytest` fails with "Failed to spawn", the virtual environment is
> stale (e.g. the project directory was renamed) — run `rm -rf .venv && uv sync`.

### Releasing

Releases publish to PyPI automatically via `.github/workflows/publish.yml`
(PyPI [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) — no API
token is stored). To cut a release:

1. Bump `__version__` in `src/tunas/_version.py` and update `CHANGELOG.md`.
2. Push, and let CI pass.
3. Create a GitHub Release whose tag matches the version (e.g. `v0.1.0`). The
   workflow verifies the tag matches `__version__`, builds the sdist + wheel,
   runs `twine check`, and uploads to PyPI.

One-time setup: register a Trusted Publisher (or a "pending publisher" for the
first upload) on PyPI for owner `ajoe2`, repo `tunas`, workflow `publish.yml`,
environment `pypi`.

