# Changelog

All notable changes to `tunas` will be documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — Unreleased

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

