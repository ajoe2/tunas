# Architecture

Design decisions and parser internals. The repository layout and development workflow are in [CONTRIBUTING.md](https://github.com/ajoe2/tunas/blob/main/CONTRIBUTING.md).

## Design Decisions

### Self-contained meets

Swimmers and clubs are scoped to their `Meet`; an athlete in two meets is two unrelated `Swimmer` objects, grouped within each meet by `id_short` (falling back to `id_long`). Cross-meet grouping is left to the application (see the [cookbook](../guide/cookbook.md)).

### Lenient parsing by default

Buggy exporters make formatting errors common, so the readers default to `strict=False`: corrupt records are skipped or recovered and recorded in the `ParseReport`.

### Slotted domain dataclasses

Aggregates (`Meet`, `Club`, `Swimmer`, the result types) are mutable `@dataclass(slots=True, kw_only=True, eq=False)` classes, built up during a single pass. `kw_only` keeps wide constructors readable and frees subclass field ordering; identity equality avoids recursing through the cyclic graph (`meet ⇄ results`), and the parser never deduplicates objects anyway. Value types (`Time`, `Split`, `SwimmerContact`, `ParseWarning`, ...) are frozen and hashable.

### Pre-populated cross-references

The parser wires every reference (`Meet.results`, `Swimmer.swims`, back-references) as it goes, so reads are attribute lookups, not computations.

### `Time`: a centisecond integer value type

`Time` stores `centiseconds: int` and exposes minutes, seconds, and hundredths as properties, so comparisons and arithmetic are exact.

### `Event`: a hand-rolled enum

`Event` enumerates every `(distance, stroke, course)` explicitly, giving static autocomplete plus helpers such as `Event.find`.

### Zero setup time standards

Motivational standards ship as JSON (`src/tunas/_data/standards-2025-2028.json`), loaded
on first use into a cached dict keyed by `(standard, age_group, sex, event)`. Each row is
flat (`standard`, `age_group`, `sex`, `event`, `cutoff_centiseconds`); duplicate rows raise
`StandardsError`. New cuts ship with new releases.

### Lightweight runtime footprint

`tunas` currently needs only the standard library at runtime. That reflects scope, not a rule: dependencies are adopted on merit.

## Parser internals

`read_cl2` and `read_hy3` are thin entry points in `parser.py` sharing one driver: resolve the
source eagerly, then lazily yield one `MeetArchive` per file, parsing each only as the consumer
advances. The engines live in the internal `_parser/` package and make one streaming pass per file:

| Module | Responsibility |
|---|---|
| `engine.py` | `_BaseEngine` — the format-agnostic core shared by both readers: the streaming line loop, record sizing/padding, structured diagnostics, the typed field-coercion helpers, and the shared assembly helpers for event resolution and split appending. |
| `cl2.py` | `_Cl2Engine(_BaseEngine)` — the SDIF engine: dispatches `A0`–`Z0`, holds the `SessionColumns` layouts, per-session result assembly, and the `Z0` count check. |
| `hy3.py` | `_Hy3Engine(_BaseEngine)` — the Hy-Tek engine: dispatches records `A1` through `H2`, buffering entries (`E1`/`F1`) until their results (`E2`/`F2`). Parses confirmed fields only. |
| `checksum.py` | The documented `.hy3` line-checksum algorithm and record dimensions (used to build test fixtures; not validated at parse time). |
| `state.py` | `ParserState` (SDIF) and `Hy3State` — per-meet mutable context (current club/swimmer/relay, pending records), reset at every meet record. |
| `fields.py` | Fixed-width field extraction: slicing `start/length` columns and coercing to `int` / `date` / `Time` / code enums, emitting diagnostics on failure. |
| `names.py` | SDIF `NAME` parsing (`Last, First MI` → components). |
| `diagnostics.py` | `Severity`, `IssueKind`, `ParseWarning`, `ParseReport` (re-exported from `parser.py`). |

**Data flow.** Each line is decoded (CP-1252 by default), normalised (BOM and line endings
stripped, short lines right-padded), and routed to a handler that wires cross-references as
objects are created, so the returned graph needs no post-processing. For SDIF, `A0`/`Z0`
populate the shared `SourceFile`; `B1` opens a `Meet`; `C1`/`C2` establish club context;
`D0`/`E0` create result rows; `D1`/`D2`/`D3`/`G0` enrich the most recent swimmer/result; `F0`
adds relay legs. The `.hy3` flow is analogous but splits athlete/entry/result across `D1`
(athlete), `E1` (entry/seed), and `E2` (result), with relays in `F1`/`F2`/`F3`.

Each file gets a fresh engine state, so files never share mutable state, and peak memory is one
file's graph. Parsing is single-threaded by design: the work is CPU-bound pure Python, so threads
serialize under the GIL, and even free-threaded builds plateaued at a sublinear ~2.4× before
regressing (contention on refcounts of shared immutables and cyclic-GC coordination). To use
multiple cores, shard the file list across processes. `ParseReport.merge` folds per-file reports
into one.
