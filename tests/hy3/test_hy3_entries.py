"""``read_hy3`` on entries / psych-sheet files.

An `E1`/`F1` entry that no `E2`/`F2` result follows has not been swum: it is
returned as a ``ResultStatus.ENTERED`` swim (no session, time, or date) carrying
its seed.
"""

from __future__ import annotations

from conftest import (
    B1_HY3,
    B2_HY3,
    C1_HY3,
    d1,
    e1,
    e2,
    f1,
    f3,
    f3_slot,
    g1,
    g1_block,
    hy3_rec,
    parse_hy3_lines,
)

from tunas import Course, Hy3FileType, IssueKind, RelayLegOrder, ResultStatus, Session, Severity
from tunas.event import Event

# A Meet Manager "Merge Meet Entries" export header.
_ENTRIES_A1 = hy3_rec(
    (1, "A1"),
    (3, "01"),
    (5, "Merge Meet Entries"),
    (30, "Hy-Tek, Ltd"),
    (45, "MM5 8.0Ge"),
    (59, "05142026"),
    (68, "9:15 PM"),
    (76, "Pacific Swimming"),
)
_HEAD = [_ENTRIES_A1, B1_HY3, B2_HY3, C1_HY3]


def _athlete(number: str, last: str) -> str:
    return d1(number=number, last=last, member=f"MEMBER{last.upper() * 3}{number.zfill(2)}"[:14])


def test_entries_file_yields_entered_swims() -> None:
    lines = [
        *_HEAD,
        d1(),
        e1(dist="100", stroke="A", seed="62.50", seed_course="Y", event_number="7"),
        e1(dist="50", stroke="D", seed="0.00", seed_course="Y"),  # NT seed
    ]
    archive = parse_hy3_lines(lines)
    meet = archive.meets[0]
    assert meet.source_file is not None
    assert meet.source_file.hy3_file_type is Hy3FileType.MERGED_ENTRIES

    free, fly = meet.individual_swims
    assert free.status is ResultStatus.ENTERED
    assert free.session is None and free.time is None and free.date is None
    assert free.heat is None and free.lane is None and free.rank is None
    assert free.event is Event.FREE_100_SCY  # course from the meet (B2)
    assert str(free.seed_time) == "1:02.50" and free.seed_course is Course.SCY
    assert free.event_number == "7"
    assert free.swimmer is meet.swimmers[0] and free in meet.swimmers[0].swims
    assert free.club is meet.clubs[0] and free in meet.clubs[0].results
    assert free.swimmer_age_class == "9"
    # The last record is an entry: it is emitted at end of file.
    assert fly.event is Event.FLY_50_SCY
    assert fly.seed_time is None and fly.seed_course is None

    assert archive.report.individual_swims_parsed == 2
    assert archive.report.warnings == []


def test_entry_followed_by_its_result_is_a_normal_swim() -> None:
    (swim,) = parse_hy3_lines([*_HEAD, d1(), e1(), e2()]).meets[0].individual_swims
    assert swim.status is ResultStatus.OK and swim.session is Session.FINALS


def test_entry_belongs_to_the_athlete_and_team_it_was_listed_under() -> None:
    other_team = hy3_rec((1, "C1"), (3, "TOSC"), (8, "Thurston Olympians"), (54, "PN"))
    lines = [
        *_HEAD,
        _athlete("1", "Aa"),
        e1(number="1"),
        other_team,
        d1(number="2", last="Bb", member="MEMBERBBBBBB02", age="12"),
        e1(number="2"),
    ]
    first, second = parse_hy3_lines(lines).meets[0].individual_swims
    assert first.swimmer.last_name == "Aa" and first.swimmer_age_class == "9"
    assert first.club is not None and first.club.team_code == "PCPASA"
    assert second.swimmer.last_name == "Bb" and second.swimmer_age_class == "12"
    assert second.club is not None and second.club.team_code == "PNTOSC"


def test_entry_uses_meet_course_unless_the_event_is_not_swum_in_it() -> None:
    long_course = hy3_rec((1, "B2"), (99, "L"))
    lines = [
        _ENTRIES_A1,
        B1_HY3,
        long_course,
        C1_HY3,
        d1(),
        e1(dist="100", stroke="A", seed="60.00", seed_course="Y"),
        e1(dist="500", stroke="A", seed="330.00", seed_course="Y"),
    ]
    free_100, free_500 = parse_hy3_lines(lines).meets[0].individual_swims
    # A yards seed for a long-course meet: the event is still long course...
    assert free_100.event is Event.FREE_100_LCM
    # ...but there is no long-course 500, so the seed's course is used instead.
    assert free_500.event is Event.FREE_500_SCY


def test_entry_without_meet_course_uses_seed_course() -> None:
    no_course = hy3_rec((1, "B2"), (109, "21-042"))
    lines = [
        _ENTRIES_A1,
        B1_HY3,
        no_course,
        C1_HY3,
        d1(),
        e1(seed="60.00", seed_course="L", conv_course=""),
    ]
    (swim,) = parse_hy3_lines(lines).meets[0].individual_swims
    assert swim.event is Event.FREE_100_LCM


def test_nt_entry_without_meet_course_uses_the_seed_course_letter() -> None:
    # A `0.00` seed still carries a course letter; it isn't reported as the seed's
    # course, but it still tells the event's course when the meet has none.
    no_course = hy3_rec((1, "B2"), (109, "21-042"))
    lines = [
        _ENTRIES_A1,
        B1_HY3,
        no_course,
        C1_HY3,
        d1(),
        e1(seed="0.00", seed_course="L", conv_course=""),
    ]
    (swim,) = parse_hy3_lines(lines).meets[0].individual_swims
    assert swim.event is Event.FREE_100_LCM
    assert swim.seed_time is None and swim.seed_course is None


def test_entry_for_unknown_athlete_is_skipped() -> None:
    archive = parse_hy3_lines([*_HEAD, d1(), e1(number="99")])
    assert archive.meets[0].individual_swims == []
    assert archive.report.warnings_for(record_type="E1", kind=IssueKind.ORPHANED)


def test_entry_with_unresolvable_event_is_skipped() -> None:
    archive = parse_hy3_lines([*_HEAD, d1(), e1(dist="6", stroke="F")])  # 1 m diving
    assert archive.meets[0].individual_swims == []
    assert archive.report.warnings_for(record_type="E1", field="event", severity=Severity.SKIPPED)


def test_splits_after_an_entry_are_orphaned() -> None:
    archive = parse_hy3_lines([*_HEAD, d1(), e1(), g1(g1_block("F", 2, "30.00"))])
    assert archive.meets[0].individual_swims[0].splits == []
    assert archive.report.warnings_for(record_type="G1", kind=IssueKind.ORPHANED)


def test_relay_entry_with_athletes() -> None:
    lines = [
        *_HEAD,
        _athlete("1", "Aa"),
        _athlete("2", "Bb"),
        f1(letter="A", dist="200", stroke="A", seed="105.95"),
        f3(f3_slot("F", "1", "Aa", "F", "1"), f3_slot("F", "2", "Bb", "F", "2")),
    ]
    archive = parse_hy3_lines(lines)
    meet = archive.meets[0]
    (relay,) = meet.relays
    assert relay.status is ResultStatus.ENTERED
    assert relay.session is None and relay.time is None and relay.date is None
    assert relay.event is Event.FREE_200_RELAY_SCY
    assert str(relay.seed_time) == "1:45.95"
    assert [leg.order for leg in relay.legs] == [RelayLegOrder.LEG_1, RelayLegOrder.LEG_2]
    assert all(leg.status is ResultStatus.ENTERED for leg in relay.legs)
    assert relay.legs[0].session is None
    assert meet.swimmers[0].relay_swims[0].relay is relay
    assert archive.report.relays_parsed == 1
    assert archive.report.warnings == []


def test_consecutive_relay_entries_keep_their_own_athletes() -> None:
    lines = [
        *_HEAD,
        _athlete("1", "Aa"),
        _athlete("2", "Bb"),
        f1(letter="A"),
        f3(f3_slot("F", "1", "Aa", "F", "1")),
        f1(letter="B"),
        f3(f3_slot("F", "2", "Bb", "F", "1")),
        f1(letter="C"),  # no athletes named
    ]
    relays = parse_hy3_lines(lines).meets[0].relays
    assert [r.relay_letter for r in relays] == ["A", "B", "C"]
    assert [[leg.swimmer.last_name for leg in r.legs if leg.swimmer] for r in relays] == [
        ["Aa"],
        ["Bb"],
        [],
    ]


def test_relay_entry_takes_no_splits() -> None:
    archive = parse_hy3_lines([*_HEAD, f1(), g1(g1_block("F", 2, "50.00"))])
    assert archive.meets[0].relays[0].splits == []
    assert archive.report.warnings_for(record_type="G1", kind=IssueKind.ORPHANED)


def test_relay_entry_with_unresolvable_event_orphans_its_athletes() -> None:
    lines = [
        *_HEAD,
        _athlete("1", "Aa"),
        f1(dist="100", stroke="E"),
        f3(f3_slot("F", "1", "Aa", "F", "1")),
    ]
    archive = parse_hy3_lines(lines)
    assert archive.meets[0].relays == []
    assert archive.report.warnings_for(record_type="F1", field="event", severity=Severity.SKIPPED)
    assert archive.report.warnings_for(record_type="F3", kind=IssueKind.ORPHANED)


def test_empty_entries_export() -> None:
    # Meet Manager sometimes exports an entries file with only its header records.
    archive = parse_hy3_lines([_ENTRIES_A1, B1_HY3, B2_HY3])
    meet = archive.meets[0]
    assert meet.results == [] and meet.swimmers == [] and meet.clubs == []
    assert archive.report.warnings == []
