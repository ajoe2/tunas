"""Golden-file test for ``read_hy3``: a real Hy-Tek meet vs. a hand-verified ground truth.

``tests/data/pasa_distance_intersquad.hy3`` is a real (small) Pacific Swimming meet
file committed with the tests. It exercises the full `.hy3` path: A1/B1/B2 headers,
a club, 32 athletes, individual entries+results (E1/E2) with splits (G1) and DQs
(H1), and relays (F1/F2/F3) — including one relay result with no course that is
correctly skipped, orphaning its F3.

``pasa_distance_intersquad.expected.json`` is its complete expected parsed state,
produced by the independent reference decoder ``tests/data/build_expected_hy3.py``
(which does not import ``tunas``) and cross-checked against the raw records. This
test parses the file with ``read_hy3`` and asserts the full result matches.
"""

from __future__ import annotations

import json
from collections import Counter
from enum import Enum
from pathlib import Path

from tunas import IndividualSwim, Meet, read_hy3
from tunas.parser import ParseReport

DATA = Path(__file__).resolve().parent / "data"
HY3 = DATA / "pasa_distance_intersquad.hy3"
EXPECTED = json.loads((DATA / "pasa_distance_intersquad.expected.json").read_text())


def _name(value: Enum | None) -> str | None:
    return value.name if value is not None else None


def _swim(swim: IndividualSwim) -> dict:
    return {
        "event": swim.event.name,
        "event_sex": swim.event_sex.name,
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

    warning_counts: Counter[tuple] = Counter()
    for w in report.warnings:
        warning_counts[(w.record_type, w.field, w.kind.name, w.severity.name)] += 1

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
        "report": {
            "files_read": report.files_read,
            "meets_parsed": report.meets_parsed,
            "swimmers_parsed": report.swimmers_parsed,
            "individual_swims_parsed": report.individual_swims_parsed,
            "relays_parsed": report.relays_parsed,
            "splits_parsed": report.splits_parsed,
            "records_skipped": report.records_skipped,
            "fields_recovered": report.fields_recovered,
        },
        "warnings": sorted(
            [
                {"record_type": rt, "field": f, "kind": k, "severity": s, "count": c}
                for (rt, f, k, s), c in warning_counts.items()
            ],
            key=lambda w: (w["record_type"] or "", w["field"] or ""),
        ),
        "meet": {
            "name": meet.name,
            "venue": meet.venue,
            "start_date": meet.start_date.isoformat(),
            "end_date": meet.end_date.isoformat() if meet.end_date else None,
            "age_up_date": meet.age_up_date.isoformat() if meet.age_up_date else None,
            "altitude": meet.altitude,
            "course": _name(meet.course),
            "sanction_number": meet.sanction_number,
        },
        "source_file": {
            "hy3_file_type": _name(sf.hy3_file_type),
            "software_name": sf.software_name,
            "created": sf.created.isoformat() if sf.created else None,
            "created_time": sf.created_time.isoformat() if sf.created_time else None,
            "licensee": sf.licensee,
        },
        "clubs": [
            {
                "team_code": c.team_code,
                "lsc": _name(c.lsc),
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


def _actual() -> dict:
    meets, report = read_hy3(str(HY3))
    return _actual_state(meets, report)


def test_report_counts() -> None:
    assert _actual()["report"] == EXPECTED["report"]


def test_warning_summary() -> None:
    assert _actual()["warnings"] == EXPECTED["warnings"]


def test_meet_metadata() -> None:
    assert _actual()["meet"] == EXPECTED["meet"]


def test_source_file() -> None:
    assert _actual()["source_file"] == EXPECTED["source_file"]


def test_clubs() -> None:
    assert _actual()["clubs"] == EXPECTED["clubs"]


def test_swimmers_full_detail() -> None:
    actual = _actual()["swimmers"]
    expected = EXPECTED["swimmers"]
    assert len(actual) == len(expected)
    for a, e in zip(actual, expected, strict=True):
        assert a == e, f"mismatch for swimmer {e['last_name']}, {e['first_name']}"


def test_relays_full_detail() -> None:
    assert _actual()["relays"] == EXPECTED["relays"]


def test_entire_state_matches() -> None:
    assert _actual() == EXPECTED
