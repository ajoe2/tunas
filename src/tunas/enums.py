"""SDIF v3 categorical enumerations.

Every enum here models a coded field in the SDIF v3 specification. Codes are the
enum *values*, so a raw SDIF byte resolves with ``Sex("F")`` etc. The large
geographic enums (``LSC``, ``State``, ``Country``) live in
:mod:`tunas.geography`.
"""

from __future__ import annotations

from enum import Enum, StrEnum, auto

__all__ = [
    "Sex",
    "Stroke",
    "Course",
    "Session",
    "AttachStatus",
    "MeetType",
    "Region",
    "EventTimeClass",
    "Organization",
    "FileType",
    "Citizenship",
    "SplitType",
    "ResultStatus",
    "RelayLegOrder",
    "MemberStatus",
    "Season",
    "Ethnicity",
    "Affiliation",
    "Hy3FileType",
]


class Sex(StrEnum):
    """SDIF SEX Code 010 / EVENT SEX Code 011."""

    MALE = "M"
    FEMALE = "F"
    MIXED = "X"


class Stroke(StrEnum):
    """SDIF STROKE Code 012."""

    FREESTYLE = "1"
    BACKSTROKE = "2"
    BREASTSTROKE = "3"
    BUTTERFLY = "4"
    INDIVIDUAL_MEDLEY = "5"
    FREESTYLE_RELAY = "6"
    MEDLEY_RELAY = "7"

    def display(self) -> str:
        """Human-readable stroke name (e.g. ``"Free Relay"``, ``"IM"``)."""
        return _STROKE_DISPLAY[self]


_STROKE_DISPLAY: dict[Stroke, str] = {
    Stroke.FREESTYLE: "Free",
    Stroke.BACKSTROKE: "Back",
    Stroke.BREASTSTROKE: "Breast",
    Stroke.BUTTERFLY: "Fly",
    Stroke.INDIVIDUAL_MEDLEY: "IM",
    Stroke.FREESTYLE_RELAY: "Free Relay",
    Stroke.MEDLEY_RELAY: "Medley Relay",
}


class Course(StrEnum):
    """SDIF COURSE Code 013 (numeric form).

    The parser also accepts the alphabetic forms ``S`` (SCM), ``Y`` (SCY), and
    ``L`` (LCM) and normalizes them to these members.
    """

    SCM = "1"  # Short Course Meters
    SCY = "2"  # Short Course Yards
    LCM = "3"  # Long Course Meters


class Session(StrEnum):
    """Which session a swim belongs to."""

    PRELIMS = "P"
    FINALS = "F"
    SWIM_OFFS = "S"


class AttachStatus(StrEnum):
    """Whether a swimmer is attached to a club at the meet."""

    ATTACHED = "A"
    UNATTACHED = "U"


class MeetType(StrEnum):
    """SDIF MEET Code 005."""

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


class Region(StrEnum):
    """SDIF REGION Code 007 (fourteen USA Swimming regions)."""

    REGION_1 = "1"
    REGION_2 = "2"
    REGION_3 = "3"
    REGION_4 = "4"
    REGION_5 = "5"
    REGION_6 = "6"
    REGION_7 = "7"
    REGION_8 = "8"
    REGION_9 = "9"
    REGION_10 = "A"
    REGION_11 = "B"
    REGION_12 = "C"
    REGION_13 = "D"
    REGION_14 = "E"


class EventTimeClass(StrEnum):
    """SDIF EVENT TIME CLASS Code 014 (per-character).

    The 2-byte file field is split into ``event_min_time_class`` (lower) and
    ``event_max_time_class`` (upper).
    """

    NOVICE = "1"
    B = "2"
    BB = "P"
    A = "3"
    AA = "4"
    AAA = "5"
    AAAA = "6"
    JUNIOR = "J"
    SENIOR = "S"


class Organization(StrEnum):
    """SDIF ORG Code 001."""

    USS = "1"  # USA Swimming
    MASTERS = "2"
    NCAA = "3"
    NCAA_DIV_I = "4"
    NCAA_DIV_II = "5"
    NCAA_DIV_III = "6"
    YMCA = "7"
    FINA = "8"
    HIGH_SCHOOL = "9"


class FileType(StrEnum):
    """SDIF FILE Code 003 (type of data transmitted)."""

    MEET_REGISTRATIONS = "01"
    MEET_RESULTS = "02"
    OVC = "03"
    NATIONAL_AGE_GROUP_RECORD = "04"
    LSC_AGE_GROUP_RECORD = "05"
    LSC_MOTIVATIONAL_LIST = "06"
    NATIONAL_RECORDS_RANKINGS = "07"
    TEAM_SELECTION = "08"
    LSC_BEST_TIMES = "09"
    USS_REGISTRATION = "10"
    TOP_16 = "16"
    VENDOR_DEFINED = "20"


class Citizenship(StrEnum):
    """SDIF CITIZEN Code 009 (the two non-country codes).

    Any other citizenship value is a :class:`~tunas.geography.Country` code, so
    citizenship fields are typed ``Citizenship | Country | None``.
    """

    DUAL = "2AL"  # USA and another country
    FOREIGN = "FGN"


class SplitType(StrEnum):
    """SDIF record G0 split-type code."""

    INTERVAL = "I"  # Segment time
    CUMULATIVE = "C"  # Elapsed time from the start


class ResultStatus(StrEnum):
    """Outcome of a swim.

    ``OK`` denotes an official, recorded time. The others are non-time outcomes
    whose ``time`` is ``None`` (except course-``X`` disqualifications, which
    retain a recorded time).
    """

    OK = "OK"
    NT = "NT"  # No Time
    NS = "NS"  # No Swim
    DNF = "DNF"  # Did Not Finish
    DQ = "DQ"  # Disqualified
    SCR = "SCR"  # Scratch
    EXHIBITION = "EX"  # Hy-Tek exhibition swim — a valid, recorded time that does not score


class RelayLegOrder(StrEnum):
    """SDIF ORDER Code 024 (relay leg position)."""

    NOT_SWUM = "0"
    LEG_1 = "1"
    LEG_2 = "2"
    LEG_3 = "3"
    LEG_4 = "4"
    ALTERNATE = "A"


class MemberStatus(StrEnum):
    """SDIF MEMBER Code 021."""

    RENEW = "R"
    NEW = "N"
    CHANGE = "C"
    DELETE = "D"


class Season(StrEnum):
    """SDIF SEASON Code 022."""

    SEASON_1 = "1"
    SEASON_2 = "2"
    YEAR_ROUND = "N"


class Ethnicity(StrEnum):
    """SDIF ETHNICITY Code 026 (sensitive personal data)."""

    AFRICAN_AMERICAN = "Q"
    ASIAN_PACIFIC_ISLANDER = "R"
    CAUCASIAN = "S"
    HISPANIC = "T"
    NATIVE_AMERICAN = "U"
    OTHER = "V"
    DECLINE = "W"


class Affiliation(Enum):
    """D3 program-affiliation flags (sensitive personal data)."""

    JUNIOR_HIGH = auto()
    SENIOR_HIGH = auto()
    YMCA_YWCA = auto()
    COLLEGE = auto()
    SUMMER_LEAGUE = auto()
    MASTERS = auto()
    DISABLED_SPORTS = auto()
    WATER_POLO = auto()


class Hy3FileType(StrEnum):
    """Hy-Tek `.hy3` file-type code (``A1`` cols 3-4).

    A distinct code space from the SDIF :class:`FileType`; only `MEET_RESULTS`
    files carry meet results (and are what :func:`~tunas.read_hy3` parses).
    """

    MEET_RESULTS = "07"
    MERGED_RESULTS = "04"
    CLUB_TIMES_EXPORT = "17"
