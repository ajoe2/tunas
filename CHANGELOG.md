# Changelog

All notable changes to `tunas` are documented here in Keep a Changelog format, adhering to Semantic Versioning.

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

