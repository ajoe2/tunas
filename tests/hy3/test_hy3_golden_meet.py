"""Golden file: ``pasa_distance_intersquad.hy3`` vs. its hand-verified expected JSON.

Covers A1/B1/B2, E1/E2/G1/H1 and F1/F2/F3, including a course-less relay result
that is skipped, orphaning its F3. Expected JSON: ``tests/data/build_expected_hy3.py``.
"""

from __future__ import annotations

import functools
import json

import pytest
from conftest import DATA_DIR as DATA
from conftest import enum_name, report_summary

from tunas import IndividualSwim, Meet, read_hy3
from tunas.parser import ParseReport

HY3 = DATA / "pasa_distance_intersquad.hy3"
EXPECTED = json.loads((DATA / "pasa_distance_intersquad.expected.json").read_text())


def _swim(swim: IndividualSwim) -> dict:
    return {
        "event": swim.event.name,
        "event_sex": swim.event_sex.name,
        "event_min_age": swim.event_min_age,
        "event_max_age": swim.event_max_age,
        "event_number": swim.event_number,
        "session": swim.session.name,
        "status": swim.status.name,
        "time": str(swim.time) if swim.time is not None else None,
        "rank": swim.rank,
        "seed_time": str(swim.seed_time) if swim.seed_time is not None else None,
        "converted_seed_time": (
            str(swim.converted_seed_time) if swim.converted_seed_time is not None else None
        ),
        "dq_code": swim.dq_code,
        "dq_reason": swim.dq_reason,
        "swimmer_age_class": swim.swimmer_age_class,
        "splits": [
            {"distance": sp.distance, "time": str(sp.time) if sp.time is not None else None}
            for sp in swim.splits
        ],
    }


def _actual_state(meets: list[Meet], report: ParseReport) -> dict:
    assert len(meets) == 1
    meet = meets[0]

    swimmers = [
        {
            "sex": sw.sex.name,
            "last_name": sw.last_name,
            "first_name": sw.first_name,
            "preferred_first_name": sw.preferred_first_name,
            "middle_initial": sw.middle_initial,
            "id_short": sw.id_short,
            "birthday": sw.birthday.isoformat() if sw.birthday else None,
            "club_team_code": sw.club.team_code if sw.club else None,
            "swims": [_swim(s) for s in sw.individual_swims],
        }
        for sw in meet.swimmers
    ]

    relays = [
        {
            "event": r.event.name,
            "event_sex": r.event_sex.name,
            "event_min_age": r.event_min_age,
            "event_max_age": r.event_max_age,
            "event_number": r.event_number,
            "relay_letter": r.relay_letter,
            "session": r.session.name,
            "status": r.status.name,
            "time": str(r.time) if r.time is not None else None,
            "rank": r.rank,
            "dq_code": r.dq_code,
            "dq_reason": r.dq_reason,
            "splits": [
                {"distance": sp.distance, "time": str(sp.time) if sp.time is not None else None}
                for sp in r.splits
            ],
            "legs": [
                {
                    "order": leg.order.name,
                    "swimmer_id_short": leg.swimmer.id_short if leg.swimmer else None,
                }
                for leg in r.legs
            ],
        }
        for r in meet.relays
    ]

    sf = meet.source_file
    assert sf is not None
    return {
        "file": HY3.name,
        **report_summary(report),
        "meet": {
            "name": meet.name,
            "venue": meet.venue,
            "start_date": meet.start_date.isoformat(),
            "end_date": meet.end_date.isoformat() if meet.end_date else None,
            "age_up_date": meet.age_up_date.isoformat() if meet.age_up_date else None,
            "altitude": meet.altitude,
            "course": enum_name(meet.course),
            "sanction_number": meet.sanction_number,
        },
        "source_file": {
            "hy3_file_type": enum_name(sf.hy3_file_type),
            "software_name": sf.software_name,
            "created": sf.created.isoformat() if sf.created else None,
            "created_time": sf.created_time.isoformat() if sf.created_time else None,
            "licensee": sf.licensee,
        },
        "clubs": [
            {
                "team_code": c.team_code,
                "lsc": enum_name(c.lsc),
                "full_name": c.full_name,
                "email": c.email,
                "swimmer_count": len(c.swimmers),
                "result_count": len(c.results),
            }
            for c in meet.clubs
        ],
        "swimmers": swimmers,
        "relays": relays,
    }


@functools.cache
def _actual() -> dict:
    archive = next(iter(read_hy3(str(HY3))))
    return _actual_state(archive.meets, archive.report)


@pytest.mark.parametrize("section", EXPECTED)
def test_section_matches(section: str) -> None:
    assert _actual()[section] == EXPECTED[section]


def test_no_extra_sections() -> None:
    assert _actual().keys() == EXPECTED.keys()
