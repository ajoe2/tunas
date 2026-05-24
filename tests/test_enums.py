import enum

import pytest

from tunas import (
    AttachStatus,
    Citizenship,
    Course,
    Ethnicity,
    EventTimeClass,
    FileType,
    MeetType,
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
from tunas.geography import LSC, Country, State


@pytest.mark.parametrize(
    "enum_cls",
    [
        Sex,
        Stroke,
        Course,
        Session,
        AttachStatus,
        MeetType,
        Region,
        EventTimeClass,
        Organization,
        FileType,
        Citizenship,
        SplitType,
        ResultStatus,
        RelayLegOrder,
        Season,
        Ethnicity,
        LSC,
        State,
        Country,
    ],
)
def test_no_value_collisions(enum_cls: type[enum.Enum]) -> None:
    members = list(enum_cls)
    assert len({m.value for m in members}) == len(members)


@pytest.mark.parametrize(
    "enum_cls",
    [Sex, Stroke, Course, MeetType, Region, Organization, FileType, Citizenship, Season],
)
def test_roundtrip_by_code(enum_cls: type[enum.Enum]) -> None:
    for m in enum_cls:
        assert enum_cls(m.value) is m


def test_sex_mixed() -> None:
    assert Sex("X") is Sex.MIXED


def test_meet_type_championship_codes() -> None:
    assert MeetType("6") is MeetType.NATIONAL_CHAMPIONSHIP
    assert MeetType("7") is MeetType.JUNIORS


def test_region_fourteen_members() -> None:
    assert len(Region) == 14
    assert Region("1") is Region.REGION_1
    assert Region("E") is Region.REGION_14


def test_citizenship_codes() -> None:
    assert Citizenship("2AL") is Citizenship.DUAL
    assert Citizenship("FGN") is Citizenship.FOREIGN


def test_filetype_meet_results() -> None:
    assert FileType("02") is FileType.MEET_RESULTS


def test_stroke_display() -> None:
    assert Stroke.FREESTYLE_RELAY.display() == "Free Relay"
    assert Stroke.INDIVIDUAL_MEDLEY.display() == "IM"


def test_unknown_code_raises() -> None:
    with pytest.raises(ValueError):
        Sex("Z")
    with pytest.raises(ValueError):
        Course("9")
