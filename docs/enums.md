# `tunas.enums` and `tunas.geography` — supporting enumerations

These enums model categorical fields in the SDIF v3 spec. All are importable from the top-level `tunas` package.

```python
from tunas import (
    Sex, Stroke, Course, Session, AttachStatus, MeetType, Region,
    EventTimeClass, Organization, FileType, SplitType, ResultStatus,
    RelayLegOrder, MemberStatus, Season, Ethnicity, Affiliation,
    Citizenship, LSC, State, Country,
)
```

## Sex

```python
class Sex(StrEnum):
    MALE = "M"
    FEMALE = "F"
    MIXED = "X"
```

Mixed-gender relays use `MIXED`. Values correspond to single-character SDIF codes.

## Stroke

```python
class Stroke(StrEnum):
    FREESTYLE = "1"
    BACKSTROKE = "2"
    BREASTSTROKE = "3"
    BUTTERFLY = "4"
    INDIVIDUAL_MEDLEY = "5"
    FREESTYLE_RELAY = "6"
    MEDLEY_RELAY = "7"
```

`display()` returns a human-readable display string (e.g., `"Free Relay"`, `"IM"`).

## Course

```python
class Course(StrEnum):
    SCM = "1"      # Short Course Meters
    SCY = "2"      # Short Course Yards
    LCM = "3"      # Long Course Meters
```

The parser normalizes both digit codes and SDIF letter codes (`"S"`, `"Y"`, `"L"`) to `Course` values.

## Session

```python
class Session(StrEnum):
    PRELIMS = "P"
    FINALS = "F"
    SWIM_OFFS = "S"
```

Represents the session of a swim. Prelim and final swims yield distinct result objects.

## AttachStatus

```python
class AttachStatus(StrEnum):
    ATTACHED = "A"
    UNATTACHED = "U"
```

`UNATTACHED` marks swimmers with no club affiliation (where the team portion of the SDIF code is `"UN"` or name contains `"unattached"`). For these, `result.club` is `None`.

## MeetType

```python
class MeetType(StrEnum):
    INVITATIONAL = "1"
    REGIONAL = "2"
    LSC_CHAMPIONSHIP = "3"
    ZONE = "4"
    ZONE_CHAMPIONSHIP = "5"
    NATIONAL_CHAMPIONSHIP = "6"
    JUNIORS = "7"
    SENIORS = "8"
    DUAL = "9"
    TIME_TRIAL = "0"
    INTERNATIONAL = "A"
    OPEN = "B"
    LEAGUE = "C"
```

SDIF MEET Code 005. Place/points calculations key on championship codes (6 and 7) — see [parsing.md](parsing.md#conditional-markers).

## Region

```python
class Region(StrEnum):
    REGION_1  = "1"
    REGION_2  = "2"
    REGION_3  = "3"
    REGION_4  = "4"
    REGION_5  = "5"
    REGION_6  = "6"
    REGION_7  = "7"
    REGION_8  = "8"
    REGION_9  = "9"
    REGION_10 = "A"
    REGION_11 = "B"
    REGION_12 = "C"
    REGION_13 = "D"
    REGION_14 = "E"
```

SDIF REGION Code 007 (fourteen USA Swimming regions). Set on `Club.region` and `SwimmerContact.region`.

## EventTimeClass

```python
class EventTimeClass(StrEnum):
    NOVICE = "1"
    B      = "2"
    BB     = "P"
    A      = "3"
    AA     = "4"
    AAA    = "5"
    AAAA   = "6"
    JUNIOR = "J"
    SENIOR = "S"
```

SDIF EVENT TIME CLASS Code 014. The parser splits 2-byte limits in the file into `event_min_time_class` and `event_max_time_class`. Represents meet-level eligibility, distinct from personal motivational standard lookups.

## Organization

```python
class Organization(StrEnum):
    USS = "1"           # USA Swimming
    MASTERS = "2"
    NCAA = "3"
    NCAA_DIV_I = "4"
    NCAA_DIV_II = "5"
    NCAA_DIV_III = "6"
    YMCA = "7"
    FINA = "8"
    HIGH_SCHOOL = "9"
```

Set on `Meet.organization` and `MeetResult.organization`.

## FileType

```python
class FileType(StrEnum):
    MEET_REGISTRATIONS         = "01"
    MEET_RESULTS               = "02"
    OVC                        = "03"
    NATIONAL_AGE_GROUP_RECORD  = "04"
    LSC_AGE_GROUP_RECORD       = "05"
    LSC_MOTIVATIONAL_LIST      = "06"
    NATIONAL_RECORDS_RANKINGS  = "07"
    TEAM_SELECTION             = "08"
    LSC_BEST_TIMES             = "09"
    USS_REGISTRATION           = "10"
    TOP_16                     = "16"
    VENDOR_DEFINED             = "20"
```

SDIF FILE Code 003, representing the type of data transmitted (usually `MEET_RESULTS`).

## Event age range

There is no `AgeGroup` enum because age bands are arbitrary (e.g., `11-12`, `13-OV`). The parser exposes limits directly as `event_min_age` and `event_max_age` integers.

## Citizenship

```python
class Citizenship(StrEnum):
    DUAL    = "2AL"
    FOREIGN = "FGN"
```

Parsed from SDIF CITIZEN Code 009. `Swimmer.citizenship` and `RelaySwim.citizenship` are typed `Citizenship | Country | None`.

## SplitType

```python
class SplitType(StrEnum):
    INTERVAL = "I"        # Segment time
    CUMULATIVE = "C"      # Elapsed time
```

Set on every `Split` instance. Most splits are cumulative.

## ResultStatus

```python
class ResultStatus(StrEnum):
    OK  = "OK"      # Official time
    NT  = "NT"      # No Time
    NS  = "NS"      # No Swim
    DNF = "DNF"     # Did Not Finish
    DQ  = "DQ"      # Disqualified
    SCR = "SCR"     # Scratch
```

Outcome code for a swim. `OK` denotes an official, recorded time. Other statuses represent non-timed outcomes and may have a `None` `time` (except course-`X` DQs, which retain recorded times).

## RelayLegOrder

```python
class RelayLegOrder(StrEnum):
    NOT_SWUM  = "0"
    LEG_1     = "1"
    LEG_2     = "2"
    LEG_3     = "3"
    LEG_4     = "4"
    ALTERNATE = "A"
```

SDIF ORDER Code 024. Represents leg position or `ALTERNATE`. Consumed by the parser to direct swimmer legs to `Relay.legs` or `Relay.alternates`.

## Registration enums

Used in administrative records and demographic data:

```python
class MemberStatus(StrEnum):       # SDIF MEMBER Code 021
    RENEW  = "R"
    NEW    = "N"
    CHANGE = "C"
    DELETE = "D"

class Season(StrEnum):             # SDIF SEASON Code 022
    SEASON_1   = "1"
    SEASON_2   = "2"
    YEAR_ROUND = "N"

class Ethnicity(StrEnum):          # SDIF ETHNICITY Code 026 (PII)
    AFRICAN_AMERICAN        = "Q"
    ASIAN_PACIFIC_ISLANDER  = "R"
    CAUCASIAN               = "S"
    HISPANIC                = "T"
    NATIVE_AMERICAN         = "U"
    OTHER                   = "V"
    DECLINE                 = "W"

class Affiliation(Enum):           # D3 program flags
    JUNIOR_HIGH = auto()
    SENIOR_HIGH = auto()
    YMCA_YWCA = auto()
    COLLEGE = auto()
    SUMMER_LEAGUE = auto()
    MASTERS = auto()
    DISABLED_SPORTS = auto()
    WATER_POLO = auto()
```

`Affiliation` is a plain `Enum` consumed as a `frozenset[Affiliation]` on `Swimmer.registration.affiliations`. `Ethnicity` and registration details are **sensitive personal data (PII)**.

## LSC — Local Swimming Committee

`tunas.geography.LSC` enumerates the 59 Local Swimming Committees (e.g., `PC` for Pacific). Values contain SDIF two-letter codes.

## State

`tunas.geography.State` enumerates US states, territories, and Canadian provinces as two-letter postal codes (e.g., `"CA"`).

## Country

`tunas.geography.Country` enumerates the ~150 FINA country codes (e.g., `"USA"`, `"CAN"`).

## Lookup pattern

Enums subclass `enum.StrEnum` (Python 3.11+) and can be resolved by their SDIF string codes:

```python
Stroke("1")           # Stroke.FREESTYLE
Course("3")           # Course.LCM
Sex("F")              # Sex.FEMALE
LSC("PC")             # LSC.PACIFIC
```

Unknown codes raise `ValueError`.

