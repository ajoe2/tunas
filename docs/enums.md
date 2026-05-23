# `tunas.enums` and `tunas.geography` — supporting enumerations

The enums on this page model the categorical fields in the SDIF v3 spec —
sex, stroke, course, session type, attach status, age group, and the
geography enums (LSC, US state, country). All values are importable from
the top-level `tunas` package; the split between `tunas.enums` and
`tunas.geography` is internal organization (the geography enums are
larger).

```python
from tunas import (
    Sex, Stroke, Course, Session, AttachStatus, MeetType, Region,
    EventTimeClass, Organization, AgeGroup, SplitType,
    LSC, State, Country,
)
```

## Sex

```python
class Sex(str, Enum):
    MALE = "M"
    FEMALE = "F"
    MIXED = "X"
```

`MIXED` is used for mixed-gender relay results. The `.value` is the SDIF
single-character code.

## Stroke

```python
class Stroke(str, Enum):
    FREESTYLE = "1"
    BACKSTROKE = "2"
    BREASTSTROKE = "3"
    BUTTERFLY = "4"
    INDIVIDUAL_MEDLEY = "5"
    FREESTYLE_RELAY = "6"
    MEDLEY_RELAY = "7"
```

`Stroke` exposes a `display()` method that returns the human-readable name
(`"Free"`, `"Back"`, `"Breast"`, `"Fly"`, `"IM"`, `"Free Relay"`,
`"Medley Relay"`).

## Course

```python
class Course(str, Enum):
    SCM = "1"      # Short Course Meters
    SCY = "2"      # Short Course Yards
    LCM = "3"      # Long Course Meters
```

The parser accepts the SDIF letter codes (`"S"`, `"Y"`, `"L"`) as well as
the digit codes and normalizes both to a `Course` value.

## Session

```python
class Session(str, Enum):
    PRELIMS = "P"
    FINALS = "F"
    SWIM_OFFS = "S"
```

Every `IndividualMeetResult` and `RelayMeetResult` belongs to exactly one
session. A swimmer who races prelims and finals produces two distinct
`IndividualMeetResult` instances.

## AttachStatus

```python
class AttachStatus(str, Enum):
    ATTACHED = "A"
    UNATTACHED = "U"
```

A swimmer who appears at a meet without club affiliation (`LSC == "UN"`
or `team_code == "UN"`, or the C1 club name contains "unattached") gets
`UNATTACHED`. `result.club` is `None` for unattached swimmers.

## MeetType

```python
class MeetType(str, Enum):
    INVITATIONAL = "1"
    REGIONAL = "2"
    LSC_CHAMPIONSHIP = "3"
    ZONE = "4"
    ZONE_CHAMPIONSHIP = "5"
    NATIONAL_CHAMPIONSHIP = "6"
    JUNIOR_NATIONAL = "7"
    SENIOR_NATIONAL = "8"
    OLYMPIC_TRIALS = "9"
    INTERNATIONAL = "0"
    OPEN = "A"
    DUAL = "B"
    TIME_TRIAL = "C"
    AGE_GROUP = "D"
    SENIOR = "E"
```

Set on `Meet.meet_type`. May be `None` if the source file omits the field.

## Region

```python
class Region(str, Enum):
    EAST = "1"
    SOUTH = "2"
    MIDWEST = "3"
    WEST = "4"
```

Set on `Club.region` for USA Swimming clubs. Optional.

## EventTimeClass

```python
class EventTimeClass(str, Enum):
    NOVICE = "N"
    B = "B"
    BB = "P"
    A = "A"
    AA = "AA"
    AAA = "AAA"
    AAAA = "AAAA"
    JNAT = "J"
    NAT = "T"
    OPEN = "O"
    INVITATIONAL_ONLY = "I"
    UNCLASSIFIED = "U"
```

Captures the meet's qualifying classification for the result's event
(e.g. a meet may have a "BB and slower" cap). Distinct from the
[`TimeStandard`](standards.md) enum, which represents the standard a time
*qualifies for*.

## Organization

```python
class Organization(str, Enum):
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

## AgeGroup

```python
class AgeGroup(str, Enum):
    _8_U = "8_U"
    _10_U = "10_U"
    _11_12 = "11_12"
    _13_14 = "13_14"
    _15_16 = "15_16"
    _17_18 = "17_18"
    _15_18 = "15_18"
    SENIOR = "SENIOR"          # 13 and over, used in some standards
    OPEN = "OPEN"
```

Each member supports `in` testing against an integer age:

```python
12 in AgeGroup._11_12          # True
13 in AgeGroup._11_12          # False
12 in AgeGroup.SENIOR          # False
17 in AgeGroup.SENIOR          # True
```

`AgeGroup` is used as a key in the bundled time-standards data and may be
returned from `Swimmer.age_range_on(date)` when no birthday is known.

## SplitType

```python
class SplitType(str, Enum):
    INTERVAL = "I"        # Each split is the time for that single segment
    CUMULATIVE = "C"      # Each split is the elapsed time at that distance
```

Set on every `Split` instance and on the G0 record. Most G0 splits are
`CUMULATIVE`.

## LSC — Local Swimming Committee

`tunas.geography.LSC` enumerates all 59 USA Swimming Local Swimming
Committees. Members include `PC` (Pacific), `SR` (Sierra Nevada), `CC`
(Central California), `SI` (San Diego–Imperial), `MA` (Middle Atlantic),
`NE` (New England), `FL` (Florida), `NT` (North Texas), and so on.

`LSC.<MEMBER>.value` is the SDIF two-letter code (e.g. `"PC"`).

The full member list is large; consult `src/tunas/geography.py` for the
authoritative listing. The parser accepts unknown codes by setting the
field to `None` and emitting a `ParseWarning` (lenient mode) or raising
`ParseError` (strict mode).

## State

`tunas.geography.State` enumerates the 50 US states plus DC, US
territories, and the Canadian provinces commonly appearing in SDIF
files. `.value` is the two-letter postal code (`"CA"`, `"NY"`, `"ON"`,
…).

## Country

`tunas.geography.Country` enumerates IOC country codes (`"USA"`, `"CAN"`,
`"GBR"`, `"FRA"`, etc.) for roughly 150 members. Used on `Meet.country`,
`Club.country`, and `Swimmer.citizenship`.

`tunas` corrects one collision present in older SDIF tables:
`Country.EQUATORIAL_GUINEA` is encoded as `"GEQ"`, not `"GEO"` — `"GEO"`
is the IOC code for Georgia.

## Lookup pattern

All enums are `(str, Enum)` subclasses, so the SDIF code itself can be
used to look up the member:

```python
Stroke("1")           # Stroke.FREESTYLE
Course("3")           # Course.LCM
Sex("F")              # Sex.FEMALE
LSC("PC")             # LSC.PACIFIC
```

Unknown codes raise `ValueError`. The parser wraps this with safe-lookup
helpers in `_parser/fields.py`; library users who construct enums by
value are expected to handle `ValueError` themselves.
