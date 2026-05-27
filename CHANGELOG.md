# Changelog

All notable changes to `tunas` are documented here in Keep a Changelog format, adhering to Semantic Versioning.

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

