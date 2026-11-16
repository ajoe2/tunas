"""``read_cl2`` on SDIF entries / psych-sheet files.

A `D0` / `E0` with no time in any session (prelims, swim-off, finals) is an entry
that has not been swum: it is returned as a ``ResultStatus.ENTERED`` swim (no
session, time, or date) carrying its seed.
"""

from __future__ import annotations

from conftest import B1, C1, d0, e0, f0, parse_lines, rec

from tunas import Course, FileType, RelayLegOrder, ResultStatus, Session
from tunas.event import Event

# A TeamUnify-style "Meet Entries" header (file code 01).
_A0_ENTRIES = rec(
    (1, "A0"), (3, "1"), (4, "V3"), (12, "01"), (14, "Meet Entries"), (44, "TeamUnify, LLC")
)
_HEAD = [_A0_ENTRIES, B1, C1]  # B1's meet course is SCY


def _entry(**kw: str) -> str:
    """A D0 with a seed and nothing in any session."""
    return d0(date="", finals="", finals_course="", finals_place="", **kw)


def test_d0_without_times_is_an_entry() -> None:
    archive = parse_lines([*_HEAD, _entry(seed="1:02.00", seed_course="Y")])
    meet = archive.meets[0]
    assert meet.source_file is not None
    assert meet.source_file.file_type is FileType.MEET_REGISTRATIONS

    (swim,) = meet.individual_swims
    assert swim.status is ResultStatus.ENTERED
    assert swim.session is None and swim.time is None and swim.date is None
    assert swim.heat is None and swim.lane is None and swim.rank is None
    assert swim.event is Event.FREE_100_SCY
    assert str(swim.seed_time) == "1:02.00" and swim.seed_course is Course.SCY
    assert swim.swimmer is meet.swimmers[0] and swim in meet.swimmers[0].swims
    assert swim.club is meet.clubs[0]
    assert archive.report.individual_swims_parsed == 1
    # An entry has no swim date, so a blank one is not flagged.
    assert not archive.report.warnings_for(field="date")


def test_entry_with_nt_seed() -> None:
    (swim,) = parse_lines([*_HEAD, _entry(seed="NT", seed_course="")]).meets[0].individual_swims
    assert swim.status is ResultStatus.ENTERED
    assert swim.seed_time is None and swim.seed_course is None


def test_result_with_blank_date_is_still_flagged() -> None:
    archive = parse_lines([*_HEAD, d0(date="")])
    assert archive.meets[0].individual_swims[0].status is ResultStatus.OK
    assert archive.report.warnings_for(field="date")


def test_roster_row_without_an_event_is_not_an_entry() -> None:
    # "Meet Registrations" files list swimmers with no event or times at all.
    roster = d0(esex="", dist="", stroke="", eage="", date="", seed="", seed_course="", finals="")
    archive = parse_lines([*_HEAD, roster])
    meet = archive.meets[0]
    assert meet.results == [] and len(meet.swimmers) == 1
    assert not archive.report.warnings_for(field="date")


def test_entry_uses_meet_course_unless_the_event_is_not_swum_in_it() -> None:
    long_course_b1 = B1[:149] + "3" + B1[150:]  # B1 course code 3 = LCM
    lines = [
        _A0_ENTRIES,
        long_course_b1,
        C1,
        _entry(dist="100", seed="55.00", seed_course="Y"),
        _entry(dist="1650", seed="17:30.00", seed_course="Y"),
    ]
    free_100, free_1650 = parse_lines(lines).meets[0].individual_swims
    # A yards seed for a long-course meet: the event is still long course...
    assert free_100.event is Event.FREE_100_LCM
    # ...but a 1650 is only swum in yards, so the seed's course is used instead.
    assert free_1650.event is Event.FREE_1650_SCY


def test_entry_without_meet_course_uses_seed_course() -> None:
    no_course_b1 = B1[:149] + " " + B1[150:]
    lines = [_A0_ENTRIES, no_course_b1, C1, _entry(seed="1:00.00", seed_course="L")]
    (swim,) = parse_lines(lines).meets[0].individual_swims
    assert swim.event is Event.FREE_100_LCM


def test_e0_without_times_is_a_relay_entry() -> None:
    lines = [
        *_HEAD,
        d0(),
        e0(date="", seed="1:50.00", seed_course="Y", finals="", finals_course=""),
        # Entries files name the relay's swimmers without assigning legs.
        f0(order_finals="0", leg_time="", leg_course="", takeoff=""),
    ]
    archive = parse_lines(lines)
    meet = archive.meets[0]
    (relay,) = meet.relays
    assert relay.status is ResultStatus.ENTERED
    assert relay.session is None and relay.time is None and relay.date is None
    assert relay.event is Event.FREE_200_RELAY_SCY
    assert str(relay.seed_time) == "1:50.00"
    assert relay.legs == []
    (slot,) = relay.alternates
    assert slot.order is RelayLegOrder.NOT_SWUM and slot.swimmer is meet.swimmers[0]
    assert slot.status is ResultStatus.ENTERED and slot.session is None
    assert meet.swimmers[0].relay_swims == []  # an unassigned slot is not a swim
    assert archive.report.relays_parsed == 1
    assert not archive.report.warnings_for(field="date")


def test_relay_entry_honours_a_given_leg_order() -> None:
    lines = [
        *_HEAD,
        d0(),
        e0(date="", finals="", finals_course=""),
        f0(order_finals="2", leg_time="", leg_course="", takeoff=""),
    ]
    meet = parse_lines(lines).meets[0]
    (relay,) = meet.relays
    assert [leg.order for leg in relay.legs] == [RelayLegOrder.LEG_2]
    assert meet.swimmers[0].relay_swims[0].relay is relay


def test_relay_with_results_is_unchanged() -> None:
    lines = [*_HEAD, d0(), e0(), f0()]
    (relay,) = parse_lines(lines).meets[0].relays
    assert relay.status is ResultStatus.OK and relay.session is Session.FINALS
    assert [leg.order for leg in relay.legs] == [RelayLegOrder.LEG_1]
