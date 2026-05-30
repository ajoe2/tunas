"""Record-level coverage for ``read_hy3`` — every handler, enum mapping, and edge case.

Builds `.hy3` records in-memory with the conftest builders (each carries a valid
checksum) and asserts the assembled object graph and diagnostics.
"""

from __future__ import annotations

import datetime

import pytest
from conftest import (
    A1,
    B1_HY3,
    B2_HY3,
    C1_HY3,
    d1,
    e1,
    e2,
    f1,
    f2,
    f3,
    f3_slot,
    g1,
    g1_block,
    h1,
    hy3_rec,
    parse_hy3_lines,
)

from tunas import (
    Course,
    Hy3FileType,
    IssueKind,
    ParseError,
    ResultStatus,
    Severity,
    Sex,
    SplitType,
    Stroke,
)
from tunas.event import Event

# A minimal valid single-swim meet, reused as a backbone in many tests.
_HEAD = [A1, B1_HY3, B2_HY3, C1_HY3]


def _one_swim(**e2_kw: str) -> list[str]:
    return [*_HEAD, d1(), e1(), e2(**e2_kw)]


# --------------------------------------------------------------------------- #
# File / meet / source-file records (A1, B1, B2)
# --------------------------------------------------------------------------- #


def test_a1_source_file() -> None:
    archive = parse_hy3_lines(_one_swim())
    sf = archive.meets[0].source_file
    assert sf is not None
    assert sf.hy3_file_type is Hy3FileType.MEET_RESULTS
    assert sf.software_name == "MM5 7.0Gb"
    assert sf.created == datetime.date(2021, 5, 1)
    assert sf.created_time == datetime.time(6, 52)
    assert sf.licensee == "Pacific Swimming"
    # SDIF-only fields are never populated by the .hy3 reader.
    assert sf.file_type is None and sf.submitted_by_lsc is None


def test_a1_file_type_variants() -> None:
    merged = hy3_rec((1, "A1"), (3, "04"), (45, "MM5 7.0Gb"))
    export = hy3_rec((1, "A1"), (3, "17"), (45, "MM5 7.0Gb"))
    for line, expected in (
        (merged, Hy3FileType.MERGED_RESULTS),
        (export, Hy3FileType.CLUB_TIMES_EXPORT),
    ):
        archive = parse_hy3_lines([line, B1_HY3, C1_HY3, d1(), e1(), e2()])
        assert archive.meets[0].source_file is not None
        assert archive.meets[0].source_file.hy3_file_type is expected


def test_a1_malformed_time_recovers() -> None:
    bad = hy3_rec((1, "A1"), (3, "07"), (45, "MM5"), (68, "99:99 ZZ"))
    archive = parse_hy3_lines([bad, B1_HY3, C1_HY3, d1(), e1(), e2()])
    assert archive.meets[0].source_file is not None
    assert archive.meets[0].source_file.created_time is None
    assert archive.report.warnings_for(field="created_time", kind=IssueKind.MALFORMED)


def test_b1_meet_metadata() -> None:
    archive = parse_hy3_lines(_one_swim())
    m = archive.meets[0]
    assert m.name == "Winter Distance Classic"
    assert m.venue == "Rinconada Pool"
    assert m.start_date == datetime.date(2021, 5, 1)
    assert m.end_date == datetime.date(2021, 5, 2)
    assert m.age_up_date == datetime.date(2021, 5, 1)
    assert m.altitude == 12


def test_organization_is_none() -> None:
    # `.hy3` carries no ORG code, so it must never be fabricated: every node that
    # has an `organization` field is left as None rather than defaulted to USS.
    archive = parse_hy3_lines(_one_swim())
    meet = archive.meets[0]
    assert meet.organization is None
    assert all(club.organization is None for club in meet.clubs)
    assert meet.clubs  # guard: the assertion above is vacuous on an empty meet
    assert all(result.organization is None for result in meet.results)
    assert meet.results


def test_b1_missing_start_date_is_fatal() -> None:
    b1 = hy3_rec((1, "B1"), (3, "No Date Meet"))
    with pytest.raises(ParseError):
        parse_hy3_lines([A1, b1, C1_HY3, d1(), e1(), e2()])


def test_b1_missing_name_is_fatal() -> None:
    b1 = hy3_rec((1, "B1"), (93, "05012021"))
    with pytest.raises(ParseError):
        parse_hy3_lines([A1, b1, C1_HY3])


def test_b2_course_and_sanction() -> None:
    archive = parse_hy3_lines(_one_swim())
    assert archive.meets[0].course is Course.SCY
    assert archive.meets[0].sanction_number == "21-042"


def test_b2_lcm_course() -> None:
    b2 = hy3_rec((1, "B2"), (99, "L"))
    archive = parse_hy3_lines(
        [A1, B1_HY3, b2, C1_HY3, d1(), e1(stroke="A", dist="100"), e2(course="L")]
    )
    assert archive.meets[0].course is Course.LCM
    assert archive.meets[0].individual_swims[0].event is Event.FREE_100_LCM


# --------------------------------------------------------------------------- #
# Team records (C1, C3) and the ignored C2
# --------------------------------------------------------------------------- #


def test_c1_club() -> None:
    archive = parse_hy3_lines(_one_swim())
    club = archive.meets[0].clubs[0]
    # team_code carries the LSC prefix to match read_cl2 ("PC" + "PASA").
    assert club.team_code == "PCPASA"
    assert club.full_name == "Palo Alto Stanford Aquatics"
    assert club.lsc is not None and club.lsc.name == "PACIFIC"
    assert len(club.swimmers) == 1 and len(club.results) == 1


def test_c1_team_code_without_lsc() -> None:
    # When the LSC field is blank the team code stays bare (same fallback as cl2).
    c1 = hy3_rec((1, "C1"), (3, "ABC"), (8, "Some Team"))
    archive = parse_hy3_lines([A1, B1_HY3, B2_HY3, c1, d1(), e1(), e2()])
    club = archive.meets[0].clubs[0]
    assert club.team_code == "ABC"
    assert club.lsc is None


def test_c3_email() -> None:
    c3 = hy3_rec((1, "C3"), (93, "coach@pasa.org"))
    archive = parse_hy3_lines([A1, B1_HY3, B2_HY3, C1_HY3, c3, d1(), e1(), e2()])
    assert archive.meets[0].clubs[0].email == "coach@pasa.org"


def test_c2_ignored_without_warning() -> None:
    c2 = hy3_rec((1, "C2"), (3, "123 Pool St"), (63, "Palo Alto"))
    archive = parse_hy3_lines([A1, B1_HY3, B2_HY3, C1_HY3, c2, d1(), e1(), e2()])
    assert len(archive.meets[0].clubs) == 1
    assert not archive.report.warnings_for(record_type="C2")


def test_c8_ignored_without_warning() -> None:
    c8 = hy3_rec((1, "C8"))
    archive = parse_hy3_lines([A1, B1_HY3, B2_HY3, C1_HY3, c8, d1(), e1(), e2()])
    assert not archive.report.warnings_for(record_type="C8")


def test_c1_repeated_team_reused() -> None:
    lines = [
        A1,
        B1_HY3,
        B2_HY3,
        C1_HY3,
        d1(number="1"),
        e1(number="1"),
        e2(),
        C1_HY3,
        d1(number="2"),
        e1(number="2"),
        e2(),
    ]
    archive = parse_hy3_lines(lines)
    assert len(archive.meets[0].clubs) == 1
    assert len(archive.meets[0].clubs[0].swimmers) == 2


def test_unattached_team_creates_no_club() -> None:
    un = hy3_rec((1, "C1"), (3, "UN"), (8, "Unattached"), (54, "PC"))
    archive = parse_hy3_lines([A1, B1_HY3, B2_HY3, un, d1(), e1(), e2()])
    m = archive.meets[0]
    assert m.clubs == []
    assert m.swimmers[0].club is None
    assert m.individual_swims[0].club is None


# --------------------------------------------------------------------------- #
# Athlete (D1)
# --------------------------------------------------------------------------- #


def test_d1_swimmer_fields() -> None:
    line = d1(
        sex="M",
        number="7",
        last="Lim",
        first="Adrian",
        preferred="AJ",
        middle="Q",
        member="ADR*LIM*082299",
        birth="08221999",
        age="17",
        citizen="USA",
    )
    archive = parse_hy3_lines([A1, B1_HY3, B2_HY3, C1_HY3, line, e1(number="7"), e2()])
    sw = archive.meets[0].swimmers[0]
    assert sw.sex is Sex.MALE
    assert (sw.last_name, sw.first_name) == ("Lim", "Adrian")
    assert sw.preferred_first_name == "AJ"
    assert sw.middle_initial == "Q"
    # The D1 member-ID field (cols 70-83) is the 14-char SWIMS ID -> id_long; id_short
    # is its 12-char prefix, matching read_cl2 (whose id_short == id_long[:12]).
    assert sw.id_long == "ADR*LIM*082299"
    assert sw.id_short == "ADR*LIM*0822"
    assert sw.birthday == datetime.date(1999, 8, 22)
    assert sw.citizenship is not None and sw.citizenship.name == "UNITED_STATES"
    # D1 age is surfaced as the per-swim age class.
    assert sw.individual_swims[0].swimmer_age_class == "17"


def test_d1_age_class_prefers_grade_when_age_absent() -> None:
    # Scholastic meets record a grade (cols 100-101) with a blank/zero age (cols 98-99);
    # surface the grade so it matches read_cl2's single "age or class" field.
    line = d1(age="0", grade="JR")
    archive = parse_hy3_lines([A1, B1_HY3, B2_HY3, C1_HY3, line, e1(), e2()])
    assert archive.meets[0].swimmers[0].individual_swims[0].swimmer_age_class == "JR"


def test_d1_age_class_prefers_real_age_over_grade() -> None:
    # When both a real age and a grade are present, the numeric age wins (read_cl2
    # stores the age in this field for non-scholastic meets).
    line = d1(age="17", grade="JR")
    archive = parse_hy3_lines([A1, B1_HY3, B2_HY3, C1_HY3, line, e1(), e2()])
    assert archive.meets[0].swimmers[0].individual_swims[0].swimmer_age_class == "17"


def test_d1_unattached_swim_marks_attach_status() -> None:
    # A swimmer under the "UN" Unattached team swims unattached, matching read_cl2.
    from tunas.enums import AttachStatus

    c1_un = hy3_rec((1, "C1"), (3, "UN"), (8, "Unattached"), (54, "PC"))
    archive = parse_hy3_lines([A1, B1_HY3, B2_HY3, c1_un, d1(), e1(), e2()])
    swim = archive.meets[0].individual_swims[0]
    assert swim.attach_status is AttachStatus.UNATTACHED
    assert swim.club is None


def test_d1_attached_swim_default_attach_status() -> None:
    from tunas.enums import AttachStatus

    archive = parse_hy3_lines([A1, B1_HY3, B2_HY3, C1_HY3, d1(), e1(), e2()])
    assert archive.meets[0].individual_swims[0].attach_status is AttachStatus.ATTACHED


def test_d1_wodob_blank_birthday() -> None:
    line = d1(birth="", age="11")
    archive = parse_hy3_lines([A1, B1_HY3, B2_HY3, C1_HY3, line, e1(), e2()])
    sw = archive.meets[0].swimmers[0]
    assert sw.birthday is None
    assert sw.individual_swims[0].swimmer_age_class == "11"
    assert archive.report.warnings_for(record_type="D1", field="birthday")


def test_d1_no_number_skipped() -> None:
    line = d1(number="")
    archive = parse_hy3_lines([A1, B1_HY3, B2_HY3, C1_HY3, line, e1(number=""), e2()])
    # No swimmer registered; the following E2 has no athlete to attach to.
    assert archive.meets[0].swimmers == []
    assert archive.report.warnings_for(
        record_type="D1", field="athlete_number", severity=Severity.SKIPPED
    )


def test_d1_blank_first_name_skipped() -> None:
    # A blank name is data-quality, not structural: skip the record in lenient
    # mode (it used to abort the whole file) and orphan the following results.
    line = d1(first="")
    archive = parse_hy3_lines([A1, B1_HY3, B2_HY3, C1_HY3, line, e1(), e2()])
    assert archive.meets[0].swimmers == []
    assert archive.meets[0].individual_swims == []
    assert archive.report.warnings_for(
        record_type="D1", field="first_name", severity=Severity.SKIPPED
    )


def test_d1_blank_first_name_strict_raises() -> None:
    from tunas import ParseError

    line = d1(first="")
    with pytest.raises(ParseError):
        parse_hy3_lines([A1, B1_HY3, B2_HY3, C1_HY3, line, e1(), e2()], strict=True)


def test_d1_orphan_without_meet() -> None:
    archive = parse_hy3_lines([A1, d1()])
    assert archive.report.warnings_for(record_type="D1", kind=IssueKind.ORPHANED)


# --------------------------------------------------------------------------- #
# Individual entry + result (E1, E2)
# --------------------------------------------------------------------------- #


def test_e1_e2_individual_swim() -> None:
    lines = [
        *_HEAD,
        d1(),
        e1(
            dist="100",
            stroke="A",
            seed="62.50",
            seed_course="Y",
            conv_seed="61.00",
            conv_course="Y",
        ),
        e2(rnd="F", time="61.64", course="Y", heat="4", lane="7", place="3"),
    ]
    archive = parse_hy3_lines(lines)
    swim = archive.meets[0].individual_swims[0]
    assert swim.event is Event.FREE_100_SCY
    assert swim.event_sex is Sex.FEMALE  # event-sex 'G' (Girls) -> FEMALE
    assert swim.session.name == "FINALS"
    assert swim.status is ResultStatus.OK
    assert str(swim.time) == "1:01.64"
    assert swim.heat == 4 and swim.lane == 7 and swim.rank == 3
    assert str(swim.seed_time) == "1:02.50" and swim.seed_course is Course.SCY
    assert str(swim.converted_seed_time) == "1:01.00"
    assert swim.date == datetime.date(2021, 5, 1)


@pytest.mark.parametrize(
    "letter,stroke,sex",
    [
        ("A", Stroke.FREESTYLE, None),
        ("B", Stroke.BACKSTROKE, None),
        ("C", Stroke.BREASTSTROKE, None),
        ("D", Stroke.BUTTERFLY, None),
        ("E", Stroke.INDIVIDUAL_MEDLEY, None),
    ],
)
def test_e1_stroke_letters(letter: str, stroke: Stroke, sex: object) -> None:
    archive = parse_hy3_lines([*_HEAD, d1(), e1(dist="100", stroke=letter), e2(course="Y")])
    assert archive.meets[0].individual_swims[0].event.stroke is stroke


@pytest.mark.parametrize(
    "code,sex",
    [("W", Sex.FEMALE), ("G", Sex.FEMALE), ("M", Sex.MALE), ("B", Sex.MALE), ("X", Sex.MIXED)],
)
def test_e1_event_sex_mapping(code: str, sex: Sex) -> None:
    archive = parse_hy3_lines([*_HEAD, d1(), e1(event_sex=code), e2()])
    assert archive.meets[0].individual_swims[0].event_sex is sex


def test_e1_unknown_event_sex_skips_swim() -> None:
    archive = parse_hy3_lines([*_HEAD, d1(), e1(event_sex="Z"), e2()])
    assert archive.meets[0].individual_swims == []
    assert archive.report.warnings_for(field="event_sex", kind=IssueKind.UNKNOWN_CODE)


def test_e1_blank_event_sex_skips_swim_silently() -> None:
    # A blank event-sex is not a code error; the swim is skipped (no event_sex warning).
    archive = parse_hy3_lines([*_HEAD, d1(), e1(event_sex=" "), e2()])
    assert archive.meets[0].individual_swims == []
    assert not archive.report.warnings_for(field="event_sex")
    assert archive.report.warnings_for(field="event", severity=Severity.SKIPPED)


def test_e1_diving_stroke_unresolvable_skipped() -> None:
    archive = parse_hy3_lines([*_HEAD, d1(), e1(dist="6", stroke="F"), e2()])
    assert archive.meets[0].individual_swims == []
    assert archive.report.warnings_for(field="event", severity=Severity.SKIPPED)


def test_e2_blank_course_unresolvable_skipped() -> None:
    archive = parse_hy3_lines([*_HEAD, d1(), e1(), e2(course="")])
    assert archive.meets[0].individual_swims == []
    assert archive.report.warnings_for(field="event", severity=Severity.SKIPPED)


def test_unresolvable_event_warning_reports_entry_stroke_not_heat() -> None:
    # The stroke lives on E1; the E2 result record has a heat number at col 22. The
    # skip warning must report the parsed entry stroke, not whatever digit sits in
    # the E2 heat column. Here the stroke maps (A->Free) but the blank course makes
    # the event unresolvable.
    archive = parse_hy3_lines([*_HEAD, d1(), e1(stroke="A"), e2(course="", heat="25")])
    warning = archive.report.warnings_for(field="event", severity=Severity.SKIPPED)[0]
    assert f"stroke={Stroke.FREESTYLE}" in warning.reason  # parsed stroke, e.g. "stroke=1"
    assert "stroke=2" not in warning.reason  # the heat tens digit must not leak in


def test_e2_orphan_without_e1() -> None:
    archive = parse_hy3_lines([*_HEAD, d1(), e2()])
    assert archive.meets[0].individual_swims == []
    assert archive.report.warnings_for(record_type="E2", kind=IssueKind.ORPHANED)


def test_e2_no_athlete_skipped() -> None:
    # E1 references an unknown athlete number, so its E2 cannot attach.
    archive = parse_hy3_lines([*_HEAD, d1(number="1"), e1(number="999"), e2()])
    assert archive.meets[0].individual_swims == []
    assert archive.report.warnings_for(record_type="E2", kind=IssueKind.ORPHANED)


@pytest.mark.parametrize(
    "flag,status,has_time",
    [
        ("", ResultStatus.OK, True),
        ("Q", ResultStatus.DQ, True),
        ("D", ResultStatus.DNF, False),
        ("F", ResultStatus.NS, False),
        ("R", ResultStatus.SCR, False),
        ("S", ResultStatus.EXHIBITION, True),
    ],
)
def test_e2_status_flags(flag: str, status: ResultStatus, has_time: bool) -> None:
    archive = parse_hy3_lines([*_HEAD, d1(), e1(), e2(time="61.64", status=flag)])
    swim = archive.meets[0].individual_swims[0]
    assert swim.status is status
    assert (swim.time is not None) == has_time


def test_e2_dq_keeps_time_and_code() -> None:
    archive = parse_hy3_lines([*_HEAD, d1(), e1(), e2(time="61.64", status="Q", dqcode="3D")])
    swim = archive.meets[0].individual_swims[0]
    assert swim.status is ResultStatus.DQ
    assert str(swim.time) == "1:01.64"
    assert swim.dq_code == "3D"


def test_e2_unknown_status_recovers_to_ok() -> None:
    archive = parse_hy3_lines([*_HEAD, d1(), e1(), e2(status="Z")])
    assert archive.meets[0].individual_swims[0].status is ResultStatus.OK
    assert archive.report.warnings_for(field="status", kind=IssueKind.UNKNOWN_CODE)


def test_e2_zero_time_is_none() -> None:
    archive = parse_hy3_lines([*_HEAD, d1(), e1(), e2(time="0.00", status="F")])
    assert archive.meets[0].individual_swims[0].time is None


def test_e2_negative_or_zero_place_is_none() -> None:
    archive = parse_hy3_lines([*_HEAD, d1(), e1(), e2(place="0")])
    assert archive.meets[0].individual_swims[0].rank is None


def test_e2_backup_times() -> None:
    archive = parse_hy3_lines(
        [*_HEAD, d1(), e1(), e2(time="61.64", watch1="61.60", watch2="61.70", watch3="0.00")]
    )
    swim = archive.meets[0].individual_swims[0]
    # The 0.00 watch slot is dropped; the two real backups are kept.
    assert [str(t) for t in swim.backup_times] == ["1:01.60", "1:01.70"]


# --------------------------------------------------------------------------- #
# Relays (F1, F2, F3)
# --------------------------------------------------------------------------- #


def _relay_meet() -> list[str]:
    return [
        *_HEAD,
        d1(number="1", last="Aa", first="A", member="MEMBERAAAAAA01"),
        e1(number="1"),
        e2(),
        d1(number="2", last="Bb", first="B", member="MEMBERBBBBBB02"),
        e1(number="2"),
        e2(),
        f1(letter="A", dist="200", stroke="A"),
        f2(time="105.95", place="1"),
        f3(f3_slot("F", "1", "Aa", "F", "1"), f3_slot("F", "2", "Bb", "F", "2")),
    ]


def test_relay_basic() -> None:
    archive = parse_hy3_lines(_relay_meet())
    relay = archive.meets[0].relays[0]
    assert relay.event is Event.FREE_200_RELAY_SCY
    assert relay.event_sex is Sex.MIXED
    assert relay.relay_letter == "A"
    assert str(relay.time) == "1:45.95"
    assert relay.rank == 1
    assert [leg.order.name for leg in relay.legs] == ["LEG_1", "LEG_2"]
    assert [leg.swimmer.last_name for leg in relay.legs] == ["Aa", "Bb"]
    # Counting legs are surfaced on their swimmers' swims.
    assert archive.meets[0].swimmers[0].relay_swims[0].relay is relay


def test_relay_medley_stroke() -> None:
    lines = [*_HEAD, f1(letter="A", dist="200", stroke="E"), f2(time="120.00")]
    archive = parse_hy3_lines(lines)
    assert archive.meets[0].relays[0].event is Event.MEDLEY_200_RELAY_SCY


def test_relay_alternate_leg() -> None:
    lines = [
        *_HEAD,
        d1(number="3", last="Cc", first="C", member="MEMBERCCCCCC03"),
        f1(letter="A", dist="200", stroke="A"),
        f2(time="105.95"),
        f3(f3_slot("F", "3", "Cc", "F", "A")),  # leg char 'A' -> alternate
    ]
    archive = parse_hy3_lines(lines)
    relay = archive.meets[0].relays[0]
    assert relay.legs == []
    assert len(relay.alternates) == 1 and relay.alternates[0].swimmer is not None
    # Alternates are excluded from the swimmer's counting relay swims.
    assert archive.meets[0].swimmers[0].relay_swims == []


def test_relay_leg_unknown_athlete_kept_with_none_swimmer() -> None:
    lines = [
        *_HEAD,
        f1(letter="A", dist="200", stroke="A"),
        f2(time="105.95"),
        f3(f3_slot("F", "99", "Zz", "F", "1")),
    ]
    archive = parse_hy3_lines(lines)
    assert archive.meets[0].relays[0].legs[0].swimmer is None


def test_f2_orphan_without_f1() -> None:
    archive = parse_hy3_lines([*_HEAD, f2(time="105.95")])
    assert archive.meets[0].relays == []
    assert archive.report.warnings_for(record_type="F2", kind=IssueKind.ORPHANED)


def test_f3_orphan_without_f2() -> None:
    archive = parse_hy3_lines([*_HEAD, f3(f3_slot("F", "1", "Aa", "F", "1"))])
    assert archive.report.warnings_for(record_type="F3", kind=IssueKind.ORPHANED)


def test_f1_missing_letter_is_fatal() -> None:
    bad = hy3_rec((1, "F1"), (15, "X"), (19, "200"), (22, "A"))
    with pytest.raises(ParseError):
        parse_hy3_lines([*_HEAD, bad, f2(time="105.95")])


def test_relay_unresolvable_event_skipped() -> None:
    archive = parse_hy3_lines([*_HEAD, f1(letter="A", dist="201", stroke="A"), f2(time="105.95")])
    assert archive.meets[0].relays == []
    assert archive.report.warnings_for(field="event", severity=Severity.SKIPPED)


# --------------------------------------------------------------------------- #
# Splits (G1)
# --------------------------------------------------------------------------- #


def test_g1_individual_splits() -> None:
    lines = [
        *_HEAD,
        d1(),
        e1(dist="100", stroke="A"),
        e2(time="61.64"),
        g1(g1_block("F", 2, "29.00"), g1_block("F", 4, "61.64")),
    ]
    archive = parse_hy3_lines(lines)
    splits = archive.meets[0].individual_swims[0].splits
    assert [(s.distance, str(s.time), s.split_type) for s in splits] == [
        (50, "29.00", SplitType.CUMULATIVE),
        (100, "1:01.64", SplitType.CUMULATIVE),
    ]
    assert archive.report.splits_parsed == 2


def test_g1_skips_zero_placeholder() -> None:
    lines = [
        *_HEAD,
        d1(),
        e1(dist="100", stroke="A"),
        e2(),
        g1(g1_block("F", 2, "0.00"), g1_block("F", 4, "61.64")),
    ]
    archive = parse_hy3_lines(lines)
    splits = archive.meets[0].individual_swims[0].splits
    assert [s.distance for s in splits] == [100]  # the 0.00 placeholder is dropped
    assert archive.report.splits_parsed == 1


def test_g1_malformed_time_kept_as_none() -> None:
    lines = [
        *_HEAD,
        d1(),
        e1(dist="100", stroke="A"),
        e2(),
        g1(g1_block("F", 2, "29.00"), "F 4 xx.yy "),
    ]
    archive = parse_hy3_lines(lines)
    splits = archive.meets[0].individual_swims[0].splits
    assert any(s.time is None for s in splits)
    assert archive.report.warnings_for(field="split_time", kind=IssueKind.MALFORMED)


def test_g1_malformed_counter_skipped() -> None:
    lines = [*_HEAD, d1(), e1(dist="100", stroke="A"), e2(), g1("F** 29.00 ")]
    archive = parse_hy3_lines(lines)
    assert archive.meets[0].individual_swims[0].splits == []
    assert archive.report.warnings_for(field="split_distance", kind=IssueKind.MALFORMED)


def test_g1_relay_splits() -> None:
    lines = _relay_meet() + [g1(g1_block("F", 2, "0.00"), g1_block("F", 4, "105.95"))]
    archive = parse_hy3_lines(lines)
    relay = archive.meets[0].relays[0]
    assert [(s.distance, str(s.time)) for s in relay.splits] == [(100, "1:45.95")]


def test_g1_orphan_without_swim() -> None:
    archive = parse_hy3_lines([*_HEAD, d1(), g1(g1_block("F", 2, "29.00"))])
    assert archive.report.warnings_for(record_type="G1", kind=IssueKind.ORPHANED)


def test_g1_continuation_across_records() -> None:
    # A 1000 free has 20 length-counter splits (2,4,...,40), spilling past the
    # 11-block limit into a second G1 record.
    blocks1 = [g1_block("F", c, f"{c * 15}.00") for c in range(2, 24, 2)]  # counters 2..22
    blocks2 = [g1_block("F", c, f"{c * 15}.00") for c in range(24, 42, 2)]  # counters 24..40
    lines = [
        *_HEAD,
        d1(),
        e1(dist="1000", stroke="A"),
        e2(time="600.00"),
        g1(*blocks1),
        g1(*blocks2),
    ]
    archive = parse_hy3_lines(lines)
    splits = archive.meets[0].individual_swims[0].splits
    assert len(splits) == 20
    assert splits[0].distance == 50  # counter 2 * 25
    assert splits[-1].distance == 1000  # counter 40 * 25


def test_g1_doubled_counter_scales_to_event_distance() -> None:
    # Some timing systems record at half-length granularity: a 200 SCY shows
    # counters 4/8/12/16 (odd slots blank) instead of 2/4/6/8. The cumulative
    # distances must still resolve to 50/100/150/200, not 100/200/300/400.
    blocks = [
        g1_block("F", 2, "0.00"),
        g1_block("F", 4, "27.72"),
        g1_block("F", 6, "0.00"),
        g1_block("F", 8, "59.14"),
        g1_block("F", 10, "0.00"),
        g1_block("F", 12, "92.78"),
        g1_block("F", 14, "0.00"),
        g1_block("F", 16, "127.30"),
    ]
    lines = [*_HEAD, d1(), e1(dist="200", stroke="D"), e2(time="127.30"), g1(*blocks)]
    archive = parse_hy3_lines(lines)
    splits = archive.meets[0].individual_swims[0].splits
    assert [s.distance for s in splits] == [50, 100, 150, 200]


def test_g1_lone_finishing_split_uses_event_distance() -> None:
    # A lone finishing split for a 100 IM arrives with the doubled counter 8; it
    # must map to the event distance (100), not 200.
    lines = [
        *_HEAD,
        d1(),
        e1(dist="100", stroke="E"),
        e2(time="71.31"),
        g1(g1_block("F", 8, "71.31")),
    ]
    archive = parse_hy3_lines(lines)
    splits = archive.meets[0].individual_swims[0].splits
    assert [s.distance for s in splits] == [100]


# --------------------------------------------------------------------------- #
# DQ reason (H1 / H2)
# --------------------------------------------------------------------------- #


def test_h1_dq_reason() -> None:
    lines = [*_HEAD, d1(), e1(), e2(status="Q", dqcode="3D"), h1(code="3D", text="One hand touch")]
    archive = parse_hy3_lines(lines)
    assert archive.meets[0].individual_swims[0].dq_reason == "One hand touch"


def test_h1_h2_dq_reason_concatenated() -> None:
    h2 = hy3_rec((1, "H2"), (3, "3D"), (5, "on the turn"))
    lines = [*_HEAD, d1(), e1(), e2(status="Q", dqcode="3D"), h1(text="One hand touch"), h2]
    archive = parse_hy3_lines(lines)
    assert archive.meets[0].individual_swims[0].dq_reason == "One hand touch on the turn"


def test_h1_on_relay() -> None:
    lines = [
        *_HEAD,
        f1(letter="A", dist="200", stroke="A"),
        f2(time="105.95", status="Q", dqcode="62"),
        h1(code="62", text="Early takeoff"),
    ]
    archive = parse_hy3_lines(lines)
    relay = archive.meets[0].relays[0]
    assert relay.status is ResultStatus.DQ
    assert relay.dq_code == "62"
    assert relay.dq_reason == "Early takeoff"


def test_h1_without_result_ignored() -> None:
    # An H1 right after D1 (no result yet) attaches to nothing and is dropped silently.
    archive = parse_hy3_lines([*_HEAD, d1(), h1()])
    assert not archive.report.warnings_for(record_type="H1")


# --------------------------------------------------------------------------- #
# Structural: checksum, unknown records, lengths, strict mode
# --------------------------------------------------------------------------- #


def test_trailing_checksum_is_ignored() -> None:
    # The 2-digit checksum (cols 129-130) is not validated: `USAS Club Times
    # Export` files omit it, and it is not a data field. A wrong checksum still parses.
    good = e2(time="61.64")
    corrupt = good[:128] + "99"  # valid data body, deliberately wrong checksum
    archive = parse_hy3_lines([*_HEAD, d1(), e1(), corrupt])
    assert str(archive.meets[0].individual_swims[0].time) == "1:01.64"
    assert not archive.report.warnings_for(field="checksum")


def test_unknown_record_warns() -> None:
    unknown = hy3_rec((1, "Z9"))
    archive = parse_hy3_lines([*_HEAD, unknown, d1(), e1(), e2()])
    assert archive.report.warnings_for(record_type="Z9", kind=IssueKind.UNKNOWN_RECORD)


def test_over_long_line_skipped() -> None:
    archive = parse_hy3_lines([*_HEAD, "B1" + "x" * 200, d1(), e1(), e2()])
    assert archive.report.warnings_for(kind=IssueKind.BAD_LENGTH)


def test_short_line_padded() -> None:
    # A blank-ish C1 truncated short still parses after right-padding.
    short = "C1   ABCD"
    archive = parse_hy3_lines([A1, B1_HY3, B2_HY3, short, d1(), e1(), e2()])
    assert archive.meets[0].individual_swims  # parsing continued past the short line


def test_blank_lines_skipped() -> None:
    archive = parse_hy3_lines([A1, "", B1_HY3, "   ", B2_HY3, C1_HY3, d1(), e1(), e2()])
    assert len(archive.meets) == 1


def test_strict_mode_raises_on_first_warning() -> None:
    with pytest.raises(ParseError):
        parse_hy3_lines([*_HEAD, d1(), e1(event_sex="Z"), e2()], strict=True)


def test_report_counts() -> None:
    archive = parse_hy3_lines(_relay_meet() + [g1(g1_block("F", 4, "105.95"))])
    assert archive.report.files_read == 1
    assert archive.report.meets_parsed == 1
    assert archive.report.swimmers_parsed == 2
    assert archive.report.individual_swims_parsed == 2
    assert archive.report.relays_parsed == 1
    assert archive.report.splits_parsed == 1


def test_records_before_meet_are_noops() -> None:
    # B2/C1/C3/E1/E2/F1/F2/G1/H1 before any B1 must not crash.
    pre = [
        A1,
        B2_HY3,
        C1_HY3,
        hy3_rec((1, "C3"), (93, "x@y.z")),
        e1(),
        e2(),
        f1(),
        f2(),
        g1(g1_block("F", 2, "29.00")),
        h1(),
    ]
    archive = parse_hy3_lines(pre + [B1_HY3, C1_HY3, d1(), e1(), e2()])
    assert len(archive.meets) == 1 and archive.meets[0].individual_swims
