# Architecture

This document describes the design decisions and parser internals of `tunas`.

## Scope

- **SDIF v3 (`.cl2`) Parsing:** Parses all results-related record types, including relays and splits.
- **Hy-Tek (`.hy3`) Parsing:** `read_hy3` parses the reverse-engineered `.hy3` results format (confirmed fields only) into the same domain model.
- **Domain Model:** Dataclasses representing `Meet`, `Club`, `Swimmer`, `IndividualSwim`, `Relay`, and supporting structures.
- **Value Types:** Immutable representation of `Time`, `Event`, and enums.
- **Offline Standards:** Motivational time standard lookups.
- **Error Model:** Lenient-by-default parsing via `ParseWarning` collections, with optional `strict=True` validation.

## Repository Layout

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
│   ├── parser.py               read_cl2, read_hy3, MeetArchive, ParseReport, ParseWarning
│   ├── standards.py            Time-standards lookups
│   ├── _parser/                Per-record parsing logic (internal)
│   └── _data/                  Bundled package data (JSON standards, spec doc)
├── tests/                  Pytest suite (fully self-contained, no network)
│   ├── conftest.py             Shared record builders + fixtures
│   ├── unit/                   Value types, enums, models, standards (no file I/O)
│   ├── cl2/                    `read_cl2` records, I/O, parallelism, diagnostics, golden meets
│   ├── hy3/                    `read_hy3` records, I/O, golden meet
│   └── data/                   Committed real `.cl2`/`.hy3` meets + golden expected JSON
├── scripts/                Developer tools (e.g., standard sheets parser)
├── docs/                   Markdown documentation
└── .github/workflows/      CI (test.yml) and PyPI release (publish.yml)
```

The package uses a **src-layout** to ensure tests run against the installed wheel rather than the working directory.

## Design Decisions

### Self-contained meets

Meets are independent; swimmers and clubs are scoped to their respective `Meet`. A swimmer competing in multiple meets exists as distinct, unrelated `Swimmer` objects, grouped by `id_short` (falling back to `id_long`). Cross-meet grouping is delegated to application code (see [cookbook.md](../guide/cookbook.md)).

### Lenient parsing by default

Formatting errors are common in real-world `.cl2` files due to buggy exporters. `read_cl2` defaults to `strict=False`, skipping corrupt records and accumulating warnings in `ParseReport` to maximize data recovery. Use `strict=True` for strict validation.

### Slotted domain dataclasses

We use slotted dataclasses (`@dataclass(slots=True)`) to minimize memory overhead and accelerate attribute lookups. Value types (`Time`, `Split`, `SwimmerContact`, `ParseWarning`) are frozen and hashable, while aggregates (`Meet`, `Club`, `Swimmer`, `IndividualSwim`, `Relay`) are mutable to support single-pass parsing.

Aggregate classes use `kw_only=True` to keep wide constructors readable and avoid field ordering constraints in subclassing. We use identity equality (`eq=False`) to avoid stack overflows from cyclic graph references (`meet ⇄ results`) and because the parser does not deduplicate objects.

### Pre-populated cross-references

The parser wires all graph references (e.g., `Meet.results`, `Swimmer.swims`, and back-references) in a single pass. Subsequent reads are O(1) instead of computed.

### `Time`: a centisecond integer value type

`Time` stores `centiseconds: int` internally, exposing minutes, seconds, and hundredths as properties. This ensures precise comparisons and arithmetic without floating-point drift.

### `Event`: a hand-rolled enum

`Event` is a 90+ member enum representing swim distances, strokes, and courses. Hand-rolling provides static autocomplete and helpers (e.g., `Event.find`).

### Zero setup time standards

Motivational standards are bundled as JSON (`src/tunas/_data/standards-2025-2028.json`)
and lazily loaded into an O(1) index keyed by `(standard, age_group, sex, event)` on
first use; subsequent lookups hit the per-process cache. Each row is flat —
`standard`, `age_group`, `sex`, `event`, and `cutoff_centiseconds` — and duplicate
rows raise `StandardsError` on load. USA Swimming revises the cuts every four years,
so refreshing them is just a matter of upgrading the package; no setup or network
access is required.

### Lightweight runtime footprint

At present `tunas` relies only on the Python standard library at runtime. This reflects the
current scope rather than a zero-dependency rule — third-party libraries are adopted on merit
where they are the better tool.

### Pythonic API

Data is exposed via plain attributes and properties rather than getter/setter methods, facilitating clean IDE auto-complete and static typing.

## Parser internals

`read_cl2` and `read_hy3` are thin entry points in `parser.py` that share one generic driver
(path resolution, then a lazy archive iterator). They validate arguments eagerly and return an
iterator that yields one `MeetArchive` (a file's `meets` plus its own `ParseReport`) per source,
parsing each file only as the consumer advances. Each engine lives in the internal `_parser/`
package and runs a single streaming pass per file:

| Module | Responsibility |
|---|---|
| `engine.py` | `_BaseEngine` — the format-agnostic core shared by both readers: the streaming line loop, record sizing/padding, structured diagnostics, the typed field-coercion helpers, and the shared assembly helpers for event resolution and split appending. |
| `cl2.py` | `_Cl2Engine(_BaseEngine)` — the SDIF engine: dispatches `A0`–`Z0`, holds the `SessionColumns` layouts, per-session result assembly, and the `Z0` count check. |
| `hy3.py` | `_Hy3Engine(_BaseEngine)` — the Hy-Tek engine: dispatches records `A1` through `H2`, buffering entries (`E1`/`F1`) until their results (`E2`/`F2`). Parses confirmed fields only. |
| `checksum.py` | The documented `.hy3` line-checksum algorithm and record dimensions (used to build test fixtures; not validated at parse time). |
| `state.py` | `ParserState` (SDIF) and `Hy3State` — per-meet mutable context (current club/swimmer/relay, pending records), reset at every meet record. |
| `fields.py` | Fixed-width field extraction: slicing `start/length` columns and coercing to `int` / `date` / `Time` / code enums, emitting diagnostics on failure. |
| `names.py` | SDIF `NAME` parsing (`Last, First MI` → components). |
| `ids.py` | Member-ID (USS#) normalization and the `id_short` → `id_long` identity rule. |
| `diagnostics.py` | `Severity`, `IssueKind`, `ParseWarning`, `ParseReport` (re-exported from `parser.py`). |

**Data flow.** Each line is decoded (CP-1252 by default), normalised (BOM and line endings
stripped, short lines right-padded), and routed to a handler that wires cross-references as
objects are created, so the returned graph needs no post-processing. For SDIF, `A0`/`Z0`
populate the shared `SourceFile`; `B1` opens a `Meet`; `C1`/`C2` establish club context;
`D0`/`E0` create result rows; `D1`/`D2`/`D3`/`G0` enrich the most recent swimmer/result; `F0`
adds relay legs. The `.hy3` flow is analogous but splits athlete/entry/result across `D1`
(athlete), `E1` (entry/seed), and `E2` (result), with relays in `F1`/`F2`/`F3`.

Each file is parsed by its own engine, so files never share mutable state. The driver iterates
files lazily and sequentially, yielding one archive per file in source order; a file is only read
and parsed when its archive is consumed, keeping peak memory flat regardless of corpus size.
Parsing is single-threaded by design: the work is CPU-bound pure Python, so a thread pool serializes
under the GIL and (even on a free-threaded build) plateaus at a sublinear ~2.4× before regressing,
as workers contend on atomic refcounts over shared immutables and on cyclic-GC coordination over the
meet graph — complexity that bought no reliable gain. To use multiple cores, shard the file list
across separate processes. Callers that want a single combined report can fold the per-file ones
with `ParseReport.merge`.

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

