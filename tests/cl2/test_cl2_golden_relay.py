"""Golden file: ``aaa_league_championship.cl2`` (relays, prelims+finals, D3 long IDs).

The expected JSON is built by the independent decoder ``tests/data/build_expected_aaa.py``.
"""

from __future__ import annotations

import functools
import json

import pytest
from conftest import DATA_DIR as DATA
from conftest import enum_name, report_summary

from tunas import IndividualSwim, Meet, RelaySwim, read_cl2
from tunas.parser import ParseReport

CL2 = DATA / "aaa_league_championship.cl2"
EXPECTED = json.loads((DATA / "aaa_league_championship.expected.json").read_text())


def _split(sp: object) -> dict:
    return {
        "distance": sp.distance,  # type: ignore[attr-defined]
        "time": str(sp.time) if sp.time is not None else None,  # type: ignore[attr-defined]
        "split_type": sp.split_type.name,  # type: ignore[attr-defined]
    }


def _swim_entry(swim: IndividualSwim | RelaySwim) -> dict:
    if isinstance(swim, IndividualSwim):
        return {
            "is_relay_leg": False,
            "event": swim.event.name,
            "event_sex": swim.event_sex.name,
            "event_min_age": swim.event_min_age,
            "event_max_age": swim.event_max_age,
            "session": swim.session.name,
            "status": swim.status.name,
            "time": str(swim.time) if swim.time is not None else None,
            "rank": swim.rank,
            "seed_time": str(swim.seed_time) if swim.seed_time is not None else None,
            "splits": [_split(s) for s in swim.splits],
        }
    return {
        "is_relay_leg": True,
        "session": swim.session.name,
        "leg_event": swim.event.name if swim.event is not None else None,
        "order": swim.order.name if swim.order is not None else None,
    }


def _swimmer_id(sw: object) -> str:
    return sw.id_short or sw.id_long or ""  # type: ignore[attr-defined]


def _actual_state(meets: list[Meet], report: ParseReport) -> dict:
    assert len(meets) == 1
    meet = meets[0]

    swimmers = []
    for sw in sorted(meet.swimmers, key=lambda s: (s.id_short or "", s.id_long or "")):
        swimmers.append(
            {
                "id_short": sw.id_short,
                "id_long": sw.id_long,
                "first_name": sw.first_name,
                "last_name": sw.last_name,
                "middle_initial": sw.middle_initial,
                "preferred_first_name": sw.preferred_first_name,
                "sex": sw.sex.name,
                "birthday": sw.birthday.isoformat() if sw.birthday else None,
                "citizenship": enum_name(sw.citizenship),
                "club_team_code": sw.club.team_code if sw.club else None,
                "swims": [_swim_entry(s) for s in sw.swims],
            }
        )

    relays = []
    for relay in meet.relays:
        relays.append(
            {
                "club_team_code": relay.club.team_code if relay.club else None,
                "relay_letter": relay.relay_letter,
                "event": relay.event.name,
                "event_sex": relay.event_sex.name,
                "event_min_age": relay.event_min_age,
                "event_max_age": relay.event_max_age,
                "session": relay.session.name,
                "status": relay.status.name,
                "time": str(relay.time) if relay.time is not None else None,
                "rank": relay.rank,
                "total_age": relay.total_age,
                "date": relay.date.isoformat() if relay.date else None,
                "splits": [_split(s) for s in relay.splits],
                "legs": [_leg(leg) for leg in relay.legs],
                "alternates": [_leg(leg) for leg in relay.alternates],
            }
        )

    sf = meet.source_file
    assert sf is not None
    return {
        "file": CL2.name,
        **report_summary(report),
        "meet": {
            "organization": meet.organization.name,
            "name": meet.name,
            "start_date": meet.start_date.isoformat(),
            "end_date": meet.end_date.isoformat() if meet.end_date else None,
            "city": meet.city,
            "state": enum_name(meet.state),
            "postal_code": meet.postal_code,
            "country": enum_name(meet.country),
            "course": enum_name(meet.course),
            "altitude": meet.altitude,
            "meet_type": enum_name(meet.meet_type),
        },
        "source_file": {
            "file_type": enum_name(sf.file_type),
            "sdif_version": sf.sdif_version,
            "software_name": sf.software_name,
            "software_version": sf.software_version,
            "contact_name": sf.contact_name,
            "contact_phone": sf.contact_phone,
            "created": sf.created.isoformat() if sf.created else None,
            "submitted_by_lsc": enum_name(sf.submitted_by_lsc),
            "notes": sf.notes,
        },
        "clubs": [
            {
                "team_code": c.team_code,
                "lsc": enum_name(c.lsc),
                "full_name": c.full_name,
                "country": enum_name(c.country),
                "swimmer_count": len(c.swimmers),
                "individual_count": len(c.individual_swims),
                "relay_count": len(c.relays),
            }
            for c in sorted(meet.clubs, key=lambda c: c.team_code)
        ],
        "swimmers": swimmers,
        "relays": relays,
        "_split_breakdown": EXPECTED["_split_breakdown"],  # not re-derived; checked separately
    }


def _leg(leg: RelaySwim) -> dict:
    return {
        "order": leg.order.name if leg.order is not None else None,
        "leg_event": leg.event.name if leg.event is not None else None,
        "swimmer_id": _swimmer_id(leg.swimmer) if leg.swimmer is not None else None,
        "time": str(leg.time) if leg.time is not None else None,
        "takeoff_time": leg.takeoff_time,
        "course": enum_name(leg.course),
    }


@functools.cache
def _actual() -> dict:
    archive = next(iter(read_cl2(str(CL2))))
    return _actual_state(archive.meets, archive.report)


@pytest.mark.parametrize("section", EXPECTED)
def test_section_matches(section: str) -> None:
    assert _actual()[section] == EXPECTED[section]


def test_no_extra_sections() -> None:
    assert _actual().keys() == EXPECTED.keys()


def test_relay_split_breakdown() -> None:
    meets = next(iter(read_cl2(str(CL2)))).meets
    relay_splits = sum(len(relay.splits) for relay in meets[0].relays)
    indiv_splits = sum(len(s.splits) for s in meets[0].individual_swims)
    assert {"individual": indiv_splits, "relay": relay_splits} == EXPECTED["_split_breakdown"]
    # Per-leg derived splits partition the relay row's marks exactly.
    for relay in meets[0].relays:
        derived = sum(len(leg.splits) for leg in relay.legs)
        assert derived == len(relay.splits), f"{relay.club} {relay.relay_letter} {relay.event.name}"
