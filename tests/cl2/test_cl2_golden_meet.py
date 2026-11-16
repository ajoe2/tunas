"""Golden file: ``reno_walk_on_meet.cl2`` vs. its hand-verified expected JSON.

The JSON is built by the independent decoder ``tests/data/build_expected.py``.
"""

from __future__ import annotations

import functools
import json

import pytest
from conftest import DATA_DIR as DATA
from conftest import enum_name, report_summary

from tunas import IndividualSwim, Meet, read_cl2
from tunas.parser import ParseReport

CL2 = DATA / "reno_walk_on_meet.cl2"
EXPECTED = json.loads((DATA / "reno_walk_on_meet.expected.json").read_text())


def _actual_state(meets: list[Meet], report: ParseReport) -> dict:
    assert len(meets) == 1
    meet = meets[0]

    swimmers = []
    for sw in sorted(meet.swimmers, key=lambda s: s.id_short or s.id_long or ""):
        swims = []
        for swim in sw.swims:
            assert isinstance(swim, IndividualSwim)  # this file has no relays
            swims.append(
                {
                    "event": swim.event.name,
                    "event_sex": swim.event_sex.name,
                    "event_min_age": swim.event_min_age,
                    "event_max_age": swim.event_max_age,
                    "session": swim.session.name,
                    "status": swim.status.name,
                    "time": str(swim.time) if swim.time is not None else None,
                    "rank": swim.rank,
                    "seed_time": str(swim.seed_time) if swim.seed_time is not None else None,
                    "splits": [
                        {
                            "distance": sp.distance,
                            "time": str(sp.time) if sp.time is not None else None,
                            "split_type": sp.split_type.name,
                        }
                        for sp in swim.splits
                    ],
                }
            )
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
                "swims": swims,
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
                "swimmer_count": len(c.swimmers),
                "result_count": len(c.results),
            }
            for c in sorted(meet.clubs, key=lambda c: c.team_code)
        ],
        "swimmers": swimmers,
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
