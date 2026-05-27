# API Reference

This reference is generated from source docstrings and type hints. All symbols are importable directly from the top-level `tunas` package:

```python
from tunas import read_cl2, Meet, Swimmer, Event, Time, qualifies_for
```

For guides and walkthoughs, see the [Getting Started Guide](../guide/getting_started.md).

### API Sections

- **[Parsing & Diagnostics](parsing.md)**: Parse function and report/warning classes.
- **[Exceptions](exceptions.md)**: Custom error and warning classes.
- **[Domain Model](models.md)**: Core classes representing meets, clubs, swimmers, and results.
- **[Events & Time](event_time.md)**: Objects representing individual swimming events and times.
- **[Enumerations](enums.md)**: Categorical SDIF/meet fields.
- **[Geography](geography.md)**: Local Swimming Committees, US states, and FINA country codes.
- **[Time Standards](standards.md)**: Lookups for USA Swimming motivational standards.

### Complete public API

Everything below is exported from the top-level `tunas` package (and re-exported in
`tunas.__all__`):

| Group | Symbols |
|---|---|
| Parsing | [`read_cl2`][tunas.read_cl2], [`read_hy3`][tunas.read_hy3], [`MeetArchive`][tunas.MeetArchive], [`ParseReport`][tunas.ParseReport], [`ParseWarning`][tunas.ParseWarning], [`Severity`][tunas.Severity], [`IssueKind`][tunas.IssueKind] |
| Exceptions | [`TunasError`][tunas.exceptions.TunasError], [`ParseError`][tunas.exceptions.ParseError], [`StandardsError`][tunas.exceptions.StandardsError] |
| Aggregates | [`Meet`][tunas.models.Meet], [`Club`][tunas.models.Club], [`Swimmer`][tunas.models.Swimmer] |
| Results | [`Swim`][tunas.models.Swim], [`MeetResult`][tunas.models.MeetResult], [`IndividualSwim`][tunas.models.IndividualSwim], [`Relay`][tunas.models.Relay], [`RelaySwim`][tunas.models.RelaySwim], [`Split`][tunas.models.Split] |
| Metadata / PII | [`MeetHost`][tunas.models.MeetHost], [`SourceFile`][tunas.models.SourceFile], [`ClubEntryCounts`][tunas.models.ClubEntryCounts], [`SwimmerContact`][tunas.models.SwimmerContact], [`SwimmerRegistration`][tunas.models.SwimmerRegistration] |
| Value types | [`Time`][tunas.time.Time], [`Event`][tunas.event.Event] |
| Enums | [`Sex`][tunas.enums.Sex], [`Stroke`][tunas.enums.Stroke], [`Course`][tunas.enums.Course], [`Session`][tunas.enums.Session], [`AttachStatus`][tunas.enums.AttachStatus], [`MeetType`][tunas.enums.MeetType], [`Region`][tunas.enums.Region], [`EventTimeClass`][tunas.enums.EventTimeClass], [`Organization`][tunas.enums.Organization], [`FileType`][tunas.enums.FileType], [`SplitType`][tunas.enums.SplitType], [`ResultStatus`][tunas.enums.ResultStatus], [`RelayLegOrder`][tunas.enums.RelayLegOrder], [`MemberStatus`][tunas.enums.MemberStatus], [`Season`][tunas.enums.Season], [`Ethnicity`][tunas.enums.Ethnicity], [`Affiliation`][tunas.enums.Affiliation], [`Citizenship`][tunas.enums.Citizenship] |
| Geography | [`LSC`][tunas.geography.LSC], [`State`][tunas.geography.State], [`Country`][tunas.geography.Country] |
| Standards | [`TimeStandard`][tunas.standards.TimeStandard], [`qualifies_for`][tunas.standards.qualifies_for], [`all_qualified`][tunas.standards.all_qualified], [`standard_time`][tunas.standards.standard_time] |
