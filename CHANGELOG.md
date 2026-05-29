# Changelog

All notable changes to `tunas` are documented here in Keep a Changelog format, adhering to Semantic Versioning.

## [Unreleased]

### Changed
- **Breaking — `read_hy3` club `team_code` now carries the LSC prefix**: a Hy-Tek club's `team_code` is now the LSC-prefixed code (e.g. `PCSCSC` instead of `SCSC`), matching `read_cl2`, which already stores the prefixed code from the SDIF `C1` record. The bare code is kept only when the file carries no LSC. This aligns club (and relay) identity across the two readers — previously the prefix difference made the same club look different between a meet's `.cl2` and `.hy3` exports.

### Fixed
- **`.hy3` `D1` with a blank athlete name no longer aborts the file**: a missing first (or last) name on a `D1` athlete record was treated as a fatal structural violation, so a single malformed record made the entire meet unparseable even in lenient mode. The record is now skipped with a `SKIPPED` warning (and its following entries/results orphan-skip cleanly); strict mode still raises.

## [0.5.0] — 2026-05-29

### Changed
- **Relay leg splits (`RelaySwim.splits`) are now derived, not stored**: relay splits live on the relay row (`Relay.splits`) as whole-relay cumulative marks, and a leg's `splits` is computed on demand from that row — the marks swum during the leg, re-based to the leg start so the leg reads like a flat-start swim (distances from 0, cumulative time from the leg's takeoff). It remains a `list[Split]` (empty when there is nothing to derive — the relay has no splits, or the slot is an alternate), preserving the uniform `Swim.splits` type. The property is read-only.

### Fixed
- **`.cl2` relay splits misplaced on legs at a bogus distance, and some dropped entirely**: SDIF `G0` relay splits are whole-relay cumulative times (e.g. a 200 medley relay's 50/100/150/200 marks), but the reader attached each to an individual leg and, because every leg's `G0` restarts at slot 0, stamped *every* split with `distance=50` — so leg 2's cumulative time read as a 50-yard split. Relays whose `G0`s followed the `E0` directly with no `F0` leg records had their splits orphaned and dropped. Relay splits now attach to the relay row (`Relay.splits`, matching the `.hy3` reader and the documented "whole-relay cumulative splits" contract) with distances climbing 50/100/150/200/… across the relay's `G0` records, and the no-`F0` case is rescued rather than dropped. Per-leg segments are exposed through the derived `RelaySwim.splits` described above.
- **`.hy3` split distances on half-length-counter files**: some timing systems index `G1` split counters by half-length (e.g. a 200 SCY at counters `4/8/12/16` instead of `2/4/6/8`), which a blind `counter × 25` mapped to impossible 100/200/300/400-yard splits. The per-counter distance is now resolved by anchoring the furthest counter in the swim to the event distance (halving the pool-length unit until it fits), so these resolve to the correct 50/100/150/200 and a lone finishing split lands on the event distance. The mapping is also course-aware now (50 m per length for LCM rather than a hardcoded 25).
- **Compound first names truncated in `.cl2` (and any SDIF `Last, First MI` field)**: a whole-word second given-name token (e.g. `Zhou, Melissa Hanlin`, `Lam, Lok Yiu`) was treated as a middle *initial*, yielding `first="Melissa"`, `middle="H"`. A trailing token is now taken as a middle initial only when it is genuinely initial-like (a single letter, optionally dotted); otherwise it stays part of `first_name` (`first="Melissa Hanlin"`, no middle initial). Real trailing initials (`Smith, John Q`) are unchanged.

## [0.4.0] — 2026-05-28

### Changed
- **Breaking — removed the `max_workers` parameter** from `read_cl2` and `read_hy3`. Parsing is now always single-threaded. The work is CPU-bound pure Python, so the thread pool serialized under the GIL and, even on a free-threaded build (3.13t+), plateaued at a sublinear ~2.4× before regressing as workers contended on atomic refcounts over shared immutables and on cyclic-GC coordination — complexity that bought no reliable speed-up. The readers remain lazy and yield one `MeetArchive` per file in source order, keeping peak memory flat regardless of corpus size.
  - **Migration**: drop the `max_workers` argument (the default `1` was already the only value worth using). To parse across multiple cores, shard the file list over separate processes and fold the per-file reports with `ParseReport.merge`.

### Internal
- Simplified the `parser.py` driver to a plain sequential generator, removing the `ThreadPoolExecutor` and the bounded order-preserving `_imap_ordered` look-ahead.

## [0.3.1] — 2026-05-27

### Fixed
- **Model `repr()`/`str()` no longer blow up**: the aggregates form a cyclic graph (`Meet` ↔ `Club` ↔ `Swimmer` ↔ result, plus `RelaySwim.relay`), so the dataclass-generated `__repr__` walked the back-references and expanded combinatorially — a populated meet rendered into megabytes and effectively hung (and could hit `RecursionError`). `Meet`, `Club`, `Swimmer`, `MeetResult`, `IndividualSwim`, `Relay`, and `RelaySwim` now define a concise `__repr__`/`__str__` that summarises collections by count and names related objects by a short label (a club's `team_code`, a swimmer's `full_name`) instead of recursing, so each renders as a single short line.

## [0.3.0] — 2026-05-26

### Changed
- **Breaking — streaming reader API**: `read_cl2` and `read_hy3` now return a **lazy `Iterator[MeetArchive]`** — one archive per source file — instead of `tuple[list[Meet], ParseReport]`. Files are parsed as the iterator is consumed, so a large corpus is processed one file at a time without holding every meet in memory at once, and each file's diagnostics stay attached to that file rather than being merged into one report. `max_workers` now dispatches files across a thread pool behind a bounded, order-preserving look-ahead window (archives are still yielded in source order); on a free-threaded interpreter the per-file work parses in genuine parallel.
  - **Migration**: to recover the old behaviour, flatten the iterator — `meets = [m for arc in read_cl2(src) for m in arc.meets]` — and, if a single combined report is needed, fold the per-file reports with `ParseReport.merge`. For a single file/stream, `(archive,) = read_cl2(src)` or `archive = next(iter(read_cl2(src)))` yields the one archive.

### Added
- **`MeetArchive`**: the per-file parse result yielded by both readers, wrapping `source` (path or `"<stream>"`), `meets` (a file may hold more than one), and a per-file `report`. Exported from the top-level package.
- **`.hy3` event metadata**: `read_hy3` now populates `event_min_age`, `event_max_age`, and `event_number` on individual (`E1`/`E2`) and relay (`F1`/`F2`) results, decoded from the newly-confirmed `E1`/`F1` columns (age range 23–28, event number 39–42). Open-ended age bounds use the SDIF `None` convention (the `0`/`109` file sentinels map to `None`).

### Fixed
- **`.hy3` format reference**: Corrected the `E1`/`F1` field map — cols 23–28 are the event age range (min 23–25, max 26–28), and the event number is at cols 39–42, not 25–28 as previously documented.
- **SDIF club back-reference**: when a swimmer appears unattached and then attached to a real team under the same USS# within one file, merging now registers the swimmer on `club.swimmers` (not just `swimmer.club`), so the two sides of the graph stay consistent.
- **`.hy3` unresolvable-event diagnostic**: the skip warning for an `E2`/`F2` result now reports the parsed entry stroke instead of mis-reading the result record's heat column (the stroke lives on the `E1`/`F1` entry, not the result).

### Internal
- Reworked the `parser.py` driver into a lazy archive iterator: eager argument validation, a per-file engine, and a bounded order-preserving `_imap_ordered` look-ahead over the thread pool (at most `2 * max_workers` files in flight) in place of the old map-and-merge parallel path.
- Refactored the shared parse engine for readability with **no change** to per-file parse output: hoisted the duplicated event-resolution and split-appending logic out of `_parser/cl2.py` and `_parser/hy3.py` into `_BaseEngine` (`_resolve_event`, `_append_split`), and unified the generic code-enum helpers on Python 3.12 type-parameter syntax.

## [0.2.0] — 2026-05-25

### Added
- **`read_hy3`**: A reader for Hy-Tek `.hy3` result files, mirroring `read_cl2`'s signature and producing the same `Meet` object graph. Parses confirmed fields from `A1` through `H2` records.
- **`.hy3`-only model fields**: Added fields for data carried only by `.hy3` files (defaulting to `None`/empty for `read_cl2`): `SourceFile` (`hy3_file_type`, `created_time`, `licensee`), `Meet` (`venue`, `age_up_date`, `sanction_number`), `Club` (`email`), `MeetResult` (`dq_code`, `dq_reason`, `converted_seed_time`, `converted_seed_course`, `backup_times`), and `Relay.splits` (whole-relay cumulative splits). Added `Hy3FileType` enum and `ResultStatus.EXHIBITION`.

### Changed
- **Parser refactoring**: Shared a common parsing core (`_BaseEngine` in `_parser/engine.py`) between SDIF (`_parser/cl2.py`) and Hy-Tek (`_parser/hy3.py`) formats, with no change to `read_cl2` output.

### Documentation
- **`.hy3` parsing**: Updated guides, API references, and format documentation to cover `read_hy3` and `.hy3` support.
- **Expanded `.hy3` format reference:** Reverse-engineered the `.hy3` format using meet results from Pacific Swimming (2013–2026, ~1,680 meets) and Michigan Swimming (425 meets) matched against `.cl2` siblings. Decoded the line checksum, athlete numbering, springboard diving strokes, watch-time columns, exhibition statuses, and relay structures.
- **Complete `.cl2` / SDIF v3 reference:** Rewrote the `.cl2` guide into a comprehensive field-level reference covering all record types (`A0`–`Z0`, registration `D1`/`D2`, time-standards `J0`–`J2`), column ranges, and code tables. Documented empirically-verified deviations of real-world Hy-Tek/TeamUnify output (measured over 2,190 files).
- **Guide & API Reference Updates:** Expanded the data model guide with PII value types, `Time` accessors, and event helpers. Added cookbook recipes for split arithmetic, concurrent parsing, and standards lookups. Added a parser-internals breakdown to the architecture page and a public symbol index.
- **Docs Styling & Organization:** Set a neutral black dark mode theme and renamed the "Data" navigation section to "File Format".
- **README Polish:** Simplified the dependency note and improved core concept definitions.

## [0.1.1] — 2026-05-24

### Added
- **Parallel parsing:** `read_cl2` gains a `max_workers` parameter (default `1`); `max_workers > 1` parses multiple files concurrently (one file per thread) and merges the per-file results back in source order, producing output identical to the sequential default.

### Documentation
- **Hosted docs site:** Published a MkDocs Material site at <https://ajoe2.github.io/tunas/>, deployed automatically on release.
- **Guide:** Getting started, parsing & error handling, the data model, a recipe cookbook, and the SDIF/`.cl2` file-format reference.
- **Complete API reference:** Generated from source docstrings and type hints, so it always matches the installed version; docstrings now cover every public class, function, property, and enum.

### Internal
- Refactored the parse engine and supporting modules for readability with **no change** to the public API or parse output: unified the duplicated per-session result parsing, replaced magic column offsets with named `SessionColumns` layouts, centralized record-orphan handling, and named the remaining magic constants (split layout, Z0 count checks, affiliation flags).

## [0.1.0] — 2026-05-24

Initial release of the `tunas` library, providing a parser and domain model for USA Swimming `.cl2` (Hy-Tek SDIF v3) files.

### Added
- **Unified Entry Point:** `read_cl2(source, *, strict=False, encoding="cp1252", errors="replace") -> tuple[list[Meet], ParseReport]` accepts paths, directories, lists, or file-like objects.
- **Spec Coverage:** Parses every meet-results record type (`A0`–`G0`, `Z0`); qualifying-time records (`J0`–`J2`) surface as warnings.
- **Domain Model:** Dataclass graph covering `Meet`, `Club`, `Swimmer`, and the swim/result hierarchy (`Swim` → `IndividualSwim`, `RelaySwim`; `MeetResult` → `IndividualSwim`, `Relay`), as well as `Split`, `SwimmerContact`, `SwimmerRegistration`, `MeetHost`, `SourceFile`, `Time`, and `Event`. Swimmers expose a unified `swims` list.
- **Pure and Faithful Parsing:** Meets are self-contained. Swimmers are unified within a meet by member ID (`id_short`, falling back to `id_long`).
- **Zero Data Loss:** All entered swims are kept, including non-time outcomes (scratches, DQs, no-shows tracked via `ResultStatus`). Missing optional fields are set to `None`. Raw line contents are preserved on validation failures.
- **Structured Error Model:** Structural (M1) violations raise `ParseError`. Data quality (M2) violations emit warnings or raise in `strict` mode. `ParseReport` provides query helpers (`by_severity`, `warnings_for`) and aggregates counts.
- **Time Standards:** Offline lookup helpers (`qualifies_for`, `standard_time`, `all_qualified`) using bundled 2025–2028 motivational standards.
- **Type-hinted:** Fully type-hinted and marked `py.typed`.

