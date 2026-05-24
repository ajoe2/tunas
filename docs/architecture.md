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
├── tests/                  Pytest suite and .cl2 test fixtures
├── scripts/                Developer tools (e.g., standard sheets parser)
└── docs/                   Markdown documentation
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

