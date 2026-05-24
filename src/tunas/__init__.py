"""tunas: A Python library for parsing USA Swimming meet result files (.cl2 / Hy-Tek SDIF v3).

Parses meet results into structured domain models and queries offline motivational time standards.
"""

from __future__ import annotations

from tunas._version import __version__
from tunas.enums import (
    Affiliation,
    AttachStatus,
    Citizenship,
    Course,
    Ethnicity,
    EventTimeClass,
    FileType,
    MeetType,
    MemberStatus,
    Organization,
    Region,
    RelayLegOrder,
    ResultStatus,
    Season,
    Session,
    Sex,
    SplitType,
    Stroke,
)
from tunas.event import Event
from tunas.exceptions import ParseError, StandardsError, TunasError
from tunas.geography import LSC, Country, State
from tunas.models import (
    Club,
    ClubEntryCounts,
    IndividualSwim,
    Meet,
    MeetHost,
    MeetResult,
    Relay,
    RelaySwim,
    SourceFile,
    Split,
    Swim,
    Swimmer,
    SwimmerContact,
    SwimmerRegistration,
)
from tunas.parser import IssueKind, ParseReport, ParseWarning, Severity, read_cl2
from tunas.standards import TimeStandard, all_qualified, qualifies_for, standard_time
from tunas.time import Time

__all__ = [
    "__version__",
    # parsing
    "read_cl2",
    "ParseReport",
    "ParseWarning",
    "Severity",
    "IssueKind",
    # exceptions
    "TunasError",
    "ParseError",
    "StandardsError",
    # models
    "Meet",
    "Club",
    "Swimmer",
    "Swim",
    "MeetResult",
    "IndividualSwim",
    "Relay",
    "RelaySwim",
    "Split",
    "SwimmerContact",
    "SwimmerRegistration",
    "MeetHost",
    "SourceFile",
    "ClubEntryCounts",
    # value types
    "Time",
    "Event",
    # enums
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
    "SplitType",
    "ResultStatus",
    "RelayLegOrder",
    "MemberStatus",
    "Season",
    "Ethnicity",
    "Affiliation",
    "Citizenship",
    "LSC",
    "State",
    "Country",
    # standards
    "TimeStandard",
    "qualifies_for",
    "standard_time",
    "all_qualified",
]
