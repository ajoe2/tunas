import enum

import pytest

from tunas import (
    AttachStatus,
    Citizenship,
    Course,
    Ethnicity,
    EventTimeClass,
    FileType,
    Hy3FileType,
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
        Hy3FileType,
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
    [
        Sex,
        Stroke,
        Course,
        MeetType,
        Region,
        Organization,
        FileType,
        Hy3FileType,
        Citizenship,
        Season,
    ],
)
def test_roundtrip_by_code(enum_cls: type[enum.Enum]) -> None:
    for m in enum_cls:
        assert enum_cls(m.value) is m


@pytest.mark.parametrize(
    "enum_cls,code,member",
    [
        (Sex, "X", Sex.MIXED),
        (MeetType, "6", MeetType.NATIONAL_CHAMPIONSHIP),
        (MeetType, "7", MeetType.JUNIORS),
        (Region, "1", Region.REGION_1),
        (Region, "E", Region.REGION_14),
        (Citizenship, "2AL", Citizenship.DUAL),
        (Citizenship, "FGN", Citizenship.FOREIGN),
        (FileType, "02", FileType.MEET_RESULTS),
        # The `.hy3` code space differs from SDIF's: "07" is results there, rankings here.
        (Hy3FileType, "07", Hy3FileType.MEET_RESULTS),
        (FileType, "07", FileType.NATIONAL_RECORDS_RANKINGS),
        (ResultStatus, "EX", ResultStatus.EXHIBITION),
    ],
)
def test_specific_codes(enum_cls: type[enum.Enum], code: str, member: enum.Enum) -> None:
    assert enum_cls(code) is member


def test_region_fourteen_members() -> None:
    assert len(Region) == 14


def test_stroke_display() -> None:
    assert Stroke.FREESTYLE_RELAY.display() == "Free Relay"
    assert Stroke.INDIVIDUAL_MEDLEY.display() == "IM"


def test_unknown_code_raises() -> None:
    with pytest.raises(ValueError):
        Sex("Z")
    with pytest.raises(ValueError):
        Course("9")
