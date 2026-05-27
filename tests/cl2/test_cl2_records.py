"""One test per record type, plus the relay/split fan-out behaviors."""

from __future__ import annotations

import datetime

from conftest import A0, B1, C1, Z0, d0, e0, f0, g0, parse_lines, rec

from tunas import (
    LSC,
    Affiliation,
    Course,
    Ethnicity,
    Event,
    FileType,
    RelayLegOrder,
    ResultStatus,
    Session,
    State,
)


def test_a0_source_file_shared() -> None:
    archive = parse_lines([A0, B1, C1, d0(), Z0])
    sf = archive.meets[0].source_file
    assert sf is not None
    assert sf.file_type is FileType.MEET_RESULTS
    assert sf.sdif_version == "V3"
    assert sf.software_name == "Hy-Tek"
    assert sf.contact_name == "Jane Admin"
    assert sf.created == datetime.date(2024, 7, 1)
    assert sf.submitted_by_lsc is LSC.PACIFIC
    assert sf.notes == "Build OK"  # set from Z0


def test_b1_meet_fields() -> None:
    archive = parse_lines([A0, B1, C1, d0(), Z0])
    m = archive.meets[0]
    assert m.name == "Winter Champs"
    assert m.start_date == datetime.date(2025, 1, 1)
    assert m.end_date == datetime.date(2025, 1, 3)
    assert m.city == "Santa Clara"
    assert m.state is State.CALIFORNIA
    assert m.course is Course.SCY


def test_b2_host() -> None:
    b2 = rec(
        (1, "B2"),
        (3, "1"),
        (12, "Santa Clara Hosts"),
        (42, "500 Pool Rd"),
        (86, "Santa Clara"),
        (106, "CA"),
        (108, "95051"),
        (121, "5557654321"),
    )
    archive = parse_lines([A0, B1, b2, C1, d0(), Z0])
    host = archive.meets[0].host
    assert host is not None
    assert host.name == "Santa Clara Hosts"
    assert host.address_one == "500 Pool Rd"
    assert host.state is State.CALIFORNIA
    assert host.phone == "5557654321"


def test_c1_club() -> None:
    archive = parse_lines([A0, B1, C1, d0(), Z0])
    club = archive.meets[0].clubs[0]
    assert club.team_code == "PCSCSC"
    assert club.lsc is LSC.PACIFIC
    assert club.full_name == "Santa Clara Swim Club"
    assert club.abbreviated_name == "SCSC"


def test_c1_unattached() -> None:
    c1u = rec((1, "C1"), (3, "1"), (12, "PCUN  "), (18, "Unattached"), (143, "1"))
    archive = parse_lines([A0, B1, c1u, d0(), Z0])
    assert archive.meets[0].clubs == []
    assert archive.meets[0].individual_swims[0].club is None


def test_swimmer_unattached_then_attached_keeps_club_backref_consistent() -> None:
    # The same swimmer (one USS#) swims unattached, then attached to a real team.
    # Backfilling the merged swimmer's club must also register it on the club, so
    # `swimmer.club` and `club.swimmers` stay in sync.
    c1u = rec((1, "C1"), (3, "1"), (12, "PCUN  "), (18, "Unattached"))
    archive = parse_lines(
        [A0, B1, c1u, d0(name="Doe, John"), C1, d0(name="Doe, John", dist="200"), Z0]
    )
    meet = archive.meets[0]
    (swimmer,) = meet.swimmers  # one swimmer, merged across the two records
    (club,) = meet.clubs  # only the real (attached) team is a club
    assert swimmer.club is club
    assert swimmer in club.swimmers


def test_c2_team_entry() -> None:
    c2 = rec(
        (1, "C2"),
        (3, "1"),
        (12, "PCSCSC"),
        (18, "Coach Bob"),
        (48, "5559999"),
        (60, "2"),
        (66, "1"),
        (72, "0"),
        (77, "0"),
        (83, "1"),
        (89, "SCSC"),
    )
    archive = parse_lines([A0, B1, C1, c2, d0(), Z0])
    club = archive.meets[0].clubs[0]
    assert club.coach == "Coach Bob"
    assert club.coach_phone == "5559999"
    assert club.short_name == "SCSC"
    assert club.entry_counts is not None
    assert club.entry_counts.num_individual_swims == 2
    assert club.entry_counts.num_athletes == 1
    assert club.entry_counts.num_split_records == 1


def test_d0_individual_swim() -> None:
    archive = parse_lines([A0, B1, C1, d0(prelim="1:01.00", prelim_course="Y"), Z0])
    swims = archive.meets[0].swimmers[0].individual_swims
    sessions = {s.session for s in swims}
    assert sessions == {Session.PRELIMS, Session.FINALS}
    finals = next(s for s in swims if s.session is Session.FINALS)
    assert finals.status is ResultStatus.OK
    assert finals.time is not None
    assert finals.rank == 1
    assert finals.event is Event.FREE_100_SCY


def test_d0_missing_birthday_kept() -> None:
    archive = parse_lines([A0, B1, C1, d0(birth=""), Z0])
    sw = archive.meets[0].swimmers[0]
    assert sw.birthday is None
    assert archive.report.warnings_for(record_type="D0", field="birthday")
    assert archive.report.records_skipped == 0


def test_d0_missing_date_kept() -> None:
    archive = parse_lines([A0, B1, C1, d0(date=""), Z0])
    assert archive.meets[0].individual_swims[0].date is None
    assert archive.report.warnings_for(record_type="D0", field="date")


def test_d0_missing_id_skipped() -> None:
    archive = parse_lines([A0, B1, C1, d0(uss=""), Z0])
    assert archive.meets[0].swimmers == []
    assert archive.report.records_skipped == 1


def test_d0_id_long_fallback() -> None:
    d3 = rec((1, "D3"), (3, "49AC52F6961843"), (17, "Reney"))
    archive = parse_lines([A0, B1, C1, d0(uss=""), d3, Z0])
    sw = archive.meets[0].swimmers[0]
    assert sw.id_short is None
    assert sw.id_long == "49AC52F6961843"
    assert archive.report.records_skipped == 0
    assert len(sw.individual_swims) == 1


def test_d0_relay_only() -> None:
    archive = parse_lines(
        [
            A0,
            B1,
            C1,
            d0(
                esex="",
                dist="",
                stroke="",
                eage="",
                finals="",
                seed="",
                seed_course="",
                finals_course="",
                finals_place="",
            ),
            Z0,
        ]
    )
    assert len(archive.meets[0].swimmers) == 1
    assert archive.meets[0].individual_swims == []


def test_d0_outcome_codes() -> None:
    archive = parse_lines([A0, B1, C1, d0(finals="NS"), Z0])
    res = archive.meets[0].swimmers[0].individual_swims[0]
    assert res.status is ResultStatus.NS
    assert res.time is None
    assert not archive.report.warnings_for(record_type="D0", field="finals_time")


def test_d0_course_x_dq_keeps_time() -> None:
    archive = parse_lines([A0, B1, C1, d0(finals="1:00.00", finals_course="X"), Z0])
    res = archive.meets[0].swimmers[0].individual_swims[0]
    assert res.status is ResultStatus.DQ
    assert res.time is not None


def test_d0_missing_course_present_time() -> None:
    archive = parse_lines([A0, B1, C1, d0(finals="1:00.00", finals_course=""), Z0])
    course_warnings = [
        w for w in archive.report.warnings if w.field == "course" and w.mandatory == "*"
    ]
    assert course_warnings
    assert len(archive.meets[0].individual_swims) == 1


def test_d1_d2_contact_and_registration() -> None:
    d1 = rec(
        (1, "D1"),
        (3, "1"),
        (19, "Zhong, Irene"),
        (48, "49AC52F69618"),
        (125, "5551112222"),
        (149, "09012024"),
        (157, "N"),
        (75, "admin note"),
    )
    d2 = rec(
        (1, "D2"),
        (3, "1"),
        (19, "Zhong, Irene"),
        (47, "I. Zhong"),
        (77, "1 Pool St"),
        (107, "Santa Clara"),
        (127, "CA"),
        (154, "1"),
        (156, "1"),
    )
    archive = parse_lines([A0, B1, C1, d0(), d1, d2, Z0])
    sw = archive.meets[0].swimmers[0]
    assert sw.contact is not None
    assert sw.contact.phone_primary == "5551112222"
    assert sw.contact.address == "1 Pool St"
    assert sw.contact.alt_mailing_name == "I. Zhong"
    assert sw.contact.state is State.CALIFORNIA
    assert sw.registration is not None
    assert sw.registration.member_status is not None
    assert sw.registration.registration_date == datetime.date(2024, 9, 1)
    assert sw.registration.season is not None
    # No phantom fields.
    assert not hasattr(sw.contact, "email")
    assert not hasattr(sw.contact, "address_2")


def test_d3_long_id_and_demographics() -> None:
    d3 = rec((1, "D3"), (3, "49AC52F6961843"), (17, "Reney"), (32, "S"), (36, "Y"))
    archive = parse_lines([A0, B1, C1, d0(), d3, Z0])
    sw = archive.meets[0].swimmers[0]
    assert sw.id_long == "49AC52F6961843"
    assert sw.preferred_first_name == "Reney"
    assert sw.registration is not None
    assert sw.registration.ethnicity_primary is Ethnicity.CAUCASIAN
    assert Affiliation.YMCA_YWCA in sw.registration.affiliations


def test_e0_relay_result() -> None:
    archive = parse_lines([A0, B1, C1, e0(), f0(), Z0])
    relay = archive.meets[0].relays[0]
    assert relay.relay_letter == "A"
    assert relay.event is Event.FREE_200_RELAY_SCY
    assert relay.total_age == 56
    assert relay.time is not None


def test_e0_relay_dq() -> None:
    archive = parse_lines([A0, B1, C1, e0(finals="1:45.00", finals_course="X"), f0(), Z0])
    assert archive.meets[0].relays[0].status is ResultStatus.DQ


def test_f0_relay_swims() -> None:
    archive = parse_lines([A0, B1, C1, e0(), f0(), Z0])
    relay = archive.meets[0].relays[0]
    assert len(relay.legs) == 1
    leg = relay.legs[0]
    assert leg.swimmer is not None
    assert leg.relay is relay
    assert leg.session == relay.session
    assert leg.order is RelayLegOrder.LEG_1
    assert leg.time is not None
    assert leg.takeoff_time == 29
    assert leg.event is Event.FREE_50_SCY  # individual leg event of a 200 free relay
    assert leg in leg.swimmer.swims


def test_f0_alternate_routed_and_excluded_from_swims() -> None:
    alt = f0(name="Sub, Alt", uss="ALT000000001", order_finals="A", leg_time="")
    archive = parse_lines([A0, B1, C1, e0(), alt, Z0])
    relay = archive.meets[0].relays[0]
    assert relay.legs == []
    assert len(relay.alternates) == 1
    alt_swim = relay.alternates[0]
    assert alt_swim.swimmer is not None
    assert alt_swim not in alt_swim.swimmer.swims
    assert alt_swim.swimmer.relay_swims == []


def test_f0_missing_id_keeps_leg_with_none_swimmer() -> None:
    leg = f0(uss="", id_long="")
    archive = parse_lines([A0, B1, C1, e0(), leg, Z0])
    relay = archive.meets[0].relays[0]
    assert len(relay.legs) == 1
    assert relay.legs[0].swimmer is None
    assert archive.report.warnings_for(record_type="F0", field="id_short")


def test_f0_new_swimmer_from_relay() -> None:
    leg = f0(name="New, Swimmer", uss="NEW000000001")
    archive = parse_lines([A0, B1, C1, e0(), leg, Z0])
    assert any(s.id_short == "NEW000000001" for s in archive.meets[0].swimmers)


def test_relay_per_session_and_split_routing() -> None:
    # E0 with both a prelim time (55/8 + course 63/1) and a finals time (73/8 + course 81/1).
    e0pf = rec(
        (1, "E0"),
        (3, "1"),
        (12, "A"),
        (13, "PCSCSC"),
        (21, "F"),
        (22, "200"),
        (26, "6"),
        (31, "1314"),
        (35, "56"),
        (38, "01032025"),
        (55, "1:46.00"),
        (63, "Y"),
        (73, "1:45.00"),
        (81, "Y"),
    )
    f0pf = f0(order_prelim="1", order_finals="1")
    archive = parse_lines([A0, B1, C1, e0pf, f0pf, Z0])
    relays = archive.meets[0].relays
    assert {r.session for r in relays} == {Session.PRELIMS, Session.FINALS}
    sw = next(s for s in archive.meets[0].swimmers if s.relay_swims)
    assert len(sw.relay_swims) == 2  # one RelaySwim per session swum


def test_g0_splits_after_d0() -> None:
    archive = parse_lines([A0, B1, C1, d0(), g0(), Z0])
    finals = next(s for s in archive.meets[0].individual_swims if s.session is Session.FINALS)
    assert [str(s.time) for s in finals.splits] == ["29.00", "1:00.00"]
    assert finals.splits[0].distance == 50
    assert finals.splits[1].distance == 100  # cumulative


def test_g0_splits_after_f0_on_leg_not_relay() -> None:
    gr = g0(times=("26.50",), total="1", session="F")
    archive = parse_lines([A0, B1, C1, e0(), f0(), gr, Z0])
    relay = archive.meets[0].relays[0]
    # SDIF relay splits live on the leg (RelaySwim), never on the Relay itself.
    assert relay.splits == []
    assert [str(s.time) for s in relay.legs[0].splits] == ["26.50"]


def test_g0_multi_record_ordered_by_sequence() -> None:
    g1 = g0(seq="1", total="20", split_dist="50", times=tuple(f"{i}.00" for i in range(30, 40)))
    g2 = g0(seq="2", total="20", split_dist="50", times=("1:00.00", "1:05.00"))
    archive = parse_lines([A0, B1, C1, d0(), g1, g2, Z0])
    finals = next(s for s in archive.meets[0].individual_swims if s.session is Session.FINALS)
    assert len(finals.splits) == 12
    assert finals.splits[0].distance == 50
    assert finals.splits[10].distance == 550  # 11th split in 2nd record


def test_g0_unparseable_split_kept_as_none() -> None:
    gr = g0(times=("29.00", "garbage"), total="2")
    archive = parse_lines([A0, B1, C1, d0(), gr, Z0])
    finals = next(s for s in archive.meets[0].individual_swims if s.session is Session.FINALS)
    assert finals.splits[0].time is not None
    assert finals.splits[1].time is None
    assert archive.report.warnings_for(record_type="G0", field="split_time")


def test_z0_count_mismatch() -> None:
    z0_bad = rec((1, "Z0"), (3, "1"), (12, "02"), (58, "999"))
    archive = parse_lines([A0, B1, C1, d0(), z0_bad])
    from tunas import IssueKind

    assert archive.report.warnings_for(kind=IssueKind.COUNT_MISMATCH)
    assert archive.report.fields_recovered == 0  # COUNT_MISMATCH excluded


def test_unknown_record_type() -> None:
    j0 = rec((1, "J0"), (12, "qualifying time"))
    archive = parse_lines([A0, B1, j0, C1, d0(), Z0])
    from tunas import IssueKind

    assert archive.report.warnings_for(kind=IssueKind.UNKNOWN_RECORD)
    assert len(archive.meets[0].swimmers) == 1  # parse continues
