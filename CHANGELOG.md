# Changelog

All notable changes to `tunas` will be documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — Unreleased

Initial release.

### Added
- `read_cl2(source, *, strict=False)` — parse one or more `.cl2` files, a
  directory of `.cl2` files, or a file-like object into a list of `Meet`
  objects plus a `ParseReport`.
- Parser support for every record type in the SDIF v3 spec
  (`A0`, `B1`, `B2`, `C1`, `C2`, `D0`, `D1`, `D2`, `D3`, `E0`, `F0`, `G0`, `Z0`).
- Domain model: `Meet`, `Club`, `Swimmer`, `MeetResult`, `IndividualMeetResult`,
  `RelayMeetResult`, `RelayLeg`, `Split`, `SwimmerContact`, `Time`, `Event`,
  and supporting enums.
- Convenience methods on `Swimmer` (`best_result`, `results_in`,
  `results_between`, `relays_in`, `age_on`, `age_range_on`), `Meet`
  (`find_swimmer`, `individual_results_for`, `relay_results_for`), and `Club`
  (`find_swimmer`, `roster`, `relay_results`).
- Time-standards lookup: `qualifies_for`, `standard_time`, `all_qualified`,
  `best_standard`, bundled with the USA Swimming 2025–2028 motivational
  standards.
- `py.typed` marker — fully type-hinted public API.
