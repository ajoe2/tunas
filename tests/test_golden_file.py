"""Golden-file test: parse a real meet and compare to a hand-verified ground truth.

``tests/data/reno_walk_on_meet.cl2`` is a real (small) Pacific Swimming meet file
committed with the tests. ``reno_walk_on_meet.expected.json`` is its complete
expected parsed state, produced by an independent reference decoder
(``tests/data/build_expected.py``) and hand-verified against the raw SDIF records.

This test parses the file with ``tunas`` and asserts the full result — meet
metadata, source file, clubs, every swimmer, every swim, and every split, plus
report counts and the warning summary — matches the ground truth exactly.
"""

from __future__ import annotations

import json
from collections import Counter
from enum import Enum
from pathlib import Path

from tunas import IndividualSwim, Meet, read_cl2
from tunas.parser import ParseReport

DATA = Path(__file__).resolve().parent / "data"
CL2 = DATA / "reno_walk_on_meet.cl2"
EXPECTED = json.loads((DATA / "reno_walk_on_meet.expected.json").read_text())


def _name(value: Enum | None) -> str | None:
    return value.name if value is not None else None


def _actual_state(meets: list[Meet], report: ParseReport) -> dict:
    """Render the live parse into the same shape as the ground-truth JSON."""
    assert len(meets) == 1
    meet = meets[0]

    warning_counts: Counter[tuple[str | None, str | None, str, str]] = Counter()
    for w in report.warnings:
        warning_counts[(w.record_type, w.field, w.kind.name, w.severity.name)] += 1

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
                "citizenship": _name(sw.citizenship),
                "club_team_code": sw.club.team_code if sw.club else None,
                "swims": swims,
            }
        )

    sf = meet.source_file
    assert sf is not None
    return {
        "file": CL2.name,
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
            "organization": meet.organization.name,
            "name": meet.name,
            "start_date": meet.start_date.isoformat(),
            "end_date": meet.end_date.isoformat() if meet.end_date else None,
            "city": meet.city,
            "state": _name(meet.state),
            "postal_code": meet.postal_code,
            "country": _name(meet.country),
            "course": _name(meet.course),
            "altitude": meet.altitude,
            "meet_type": _name(meet.meet_type),
        },
        "source_file": {
            "file_type": _name(sf.file_type),
            "sdif_version": sf.sdif_version,
            "software_name": sf.software_name,
            "software_version": sf.software_version,
            "contact_name": sf.contact_name,
            "contact_phone": sf.contact_phone,
            "created": sf.created.isoformat() if sf.created else None,
            "submitted_by_lsc": _name(sf.submitted_by_lsc),
            "notes": sf.notes,
        },
        "clubs": [
            {
                "team_code": c.team_code,
                "lsc": _name(c.lsc),
                "full_name": c.full_name,
                "swimmer_count": len(c.swimmers),
                "result_count": len(c.results),
            }
            for c in sorted(meet.clubs, key=lambda c: c.team_code)
        ],
        "swimmers": swimmers,
    }


# --------------------------------------------------------------------------- #
# Section-by-section comparison (granular failures)
# --------------------------------------------------------------------------- #


def _actual() -> dict:
    meets, report = read_cl2(str(CL2))
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


def test_swimmer_roster_matches() -> None:
    actual = {s["id_short"]: s for s in _actual()["swimmers"]}
    expected = {s["id_short"]: s for s in EXPECTED["swimmers"]}
    assert set(actual) == set(expected)


def test_each_swimmer_full_detail() -> None:
    actual = {s["id_short"]: s for s in _actual()["swimmers"]}
    expected = {s["id_short"]: s for s in EXPECTED["swimmers"]}
    for sid, exp in expected.items():
        assert actual[sid] == exp, f"mismatch for swimmer {sid} ({exp['last_name']})"


def test_entire_state_matches() -> None:
    # Belt-and-suspenders: the whole structure in one comparison.
    assert _actual() == EXPECTED
