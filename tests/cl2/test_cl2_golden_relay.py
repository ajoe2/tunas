"""Golden-file test #2: a real relay meet vs. a hand-verified ground truth.

``tests/data/aaa_league_championship.cl2`` is a real Pacific Swimming high-school
league championship (committed with the tests). Unlike the individual-events
golden file (``reno_walk_on_meet``), it exercises the relay path and per-session
swims: prelim+finals individual swims with split routing by session, E0 relays,
F0 relay legs (leg event), whole-relay cumulative splits on the relay row, and
blank-``id_short`` swimmers resolved from a later ``D3`` long ID.

``aaa_league_championship.expected.json`` is its complete expected parsed state,
built by the independent decoder ``tests/data/build_expected_aaa.py`` (which does
not import ``tunas``) and cross-checked against the raw records. This test parses
the file with ``tunas`` and asserts the full result matches.
"""

from __future__ import annotations

import json
from collections import Counter
from enum import Enum

from conftest import DATA_DIR as DATA

from tunas import IndividualSwim, Meet, RelaySwim, read_cl2
from tunas.parser import ParseReport

CL2 = DATA / "aaa_league_championship.cl2"
EXPECTED = json.loads((DATA / "aaa_league_championship.expected.json").read_text())


def _name(value: Enum | None) -> str | None:
    return value.name if value is not None else None


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

    warning_counts: Counter[tuple[str | None, str | None, str, str]] = Counter()
    for w in report.warnings:
        warning_counts[(w.record_type, w.field, w.kind.name, w.severity.name)] += 1

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
                "citizenship": _name(sw.citizenship),
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
                "country": _name(c.country),
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
        "course": _name(leg.course),
    }


def _actual() -> dict:
    archive = next(iter(read_cl2(str(CL2))))  # a single file -> a single archive
    return _actual_state(archive.meets, archive.report)


# --------------------------------------------------------------------------- #
# Section-by-section comparison
# --------------------------------------------------------------------------- #


def test_report_counts() -> None:
    assert _actual()["report"] == EXPECTED["report"]


def test_warning_summary() -> None:
    assert _actual()["warnings"] == EXPECTED["warnings"]


def test_meet_and_source_file() -> None:
    actual = _actual()
    assert actual["meet"] == EXPECTED["meet"]
    assert actual["source_file"] == EXPECTED["source_file"]


def test_clubs() -> None:
    assert _actual()["clubs"] == EXPECTED["clubs"]


def test_relay_split_breakdown() -> None:
    meets = next(iter(read_cl2(str(CL2)))).meets
    # Parsed splits: whole-relay cumulative marks live on the relay row.
    relay_splits = sum(len(relay.splits) for relay in meets[0].relays)
    indiv_splits = sum(len(s.splits) for s in meets[0].individual_swims)
    assert {"individual": indiv_splits, "relay": relay_splits} == EXPECTED["_split_breakdown"]
    # Each leg derives its own splits from the row; every row mark belongs to
    # exactly one leg, so the per-leg derived splits partition the row exactly.
    for relay in meets[0].relays:
        derived = sum(len(leg.splits) for leg in relay.legs)
        assert derived == len(relay.splits), f"{relay.club} {relay.relay_letter} {relay.event.name}"


def test_swimmer_roster_matches() -> None:
    actual = {(s["id_short"], s["id_long"]) for s in _actual()["swimmers"]}
    expected = {(s["id_short"], s["id_long"]) for s in EXPECTED["swimmers"]}
    assert actual == expected


def test_each_swimmer_full_detail() -> None:
    actual = {_key(s): s for s in _actual()["swimmers"]}
    expected = {_key(s): s for s in EXPECTED["swimmers"]}
    assert set(actual) == set(expected)
    for sid, exp in expected.items():
        assert actual[sid] == exp, f"mismatch for swimmer {sid} ({exp['last_name']})"


def test_each_relay_full_detail() -> None:
    actual, expected = _actual()["relays"], EXPECTED["relays"]
    assert len(actual) == len(expected)
    for i, (a, e) in enumerate(zip(actual, expected, strict=True)):
        assert a == e, f"mismatch for relay #{i} ({e['club_team_code']} {e['relay_letter']})"


def test_entire_state_matches() -> None:
    assert _actual() == EXPECTED


def _key(sw: dict) -> tuple[str | None, str | None]:
    return (sw["id_short"], sw["id_long"])
