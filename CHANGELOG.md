# Changelog

All notable changes to `tunas` are documented here in Keep a Changelog format, adhering to Semantic Versioning.

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

