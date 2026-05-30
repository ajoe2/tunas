"""Build the ground-truth JSON for ``pasa_distance_intersquad.hy3`` (golden-file test).

This is an INDEPENDENT reference decoder for the Hy-Tek `.hy3` format: it reads
the documented columns directly and does NOT import ``tunas``. The committed
``pasa_distance_intersquad.expected.json`` was produced by this script and
cross-checked against the raw records; ``hy3/test_hy3_golden_meet.py`` compares the
real ``read_hy3`` parse against that static JSON, so a parser regression fails the test.

Re-generate with:  uv run python tests/data/build_expected_hy3.py
"""

from __future__ import annotations

import datetime
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "pasa_distance_intersquad.hy3"
OUT = HERE / "pasa_distance_intersquad.expected.json"

# --- code -> enum-name maps -------------------------------------------------- #
_STROKE = {"A": "FREE", "B": "BACK", "C": "BREAST", "D": "FLY", "E": "IM"}
_RELAY_STROKE = {"A": "FREE", "E": "MEDLEY"}
_COURSE = {"Y": "SCY", "L": "LCM", "S": "SCM"}
_EVENT_SEX = {"W": "FEMALE", "G": "FEMALE", "M": "MALE", "B": "MALE", "X": "MIXED"}
_SEX = {"M": "MALE", "F": "FEMALE", "X": "MIXED"}
_STATUS = {
    "": ("OK", True),
    "Q": ("DQ", True),
    "D": ("DNF", False),
    "F": ("NS", False),
    "R": ("SCR", False),
    "S": ("EXHIBITION", True),
}
_FILETYPE = {"07": "MEET_RESULTS", "04": "MERGED_RESULTS", "17": "CLUB_TIMES_EXPORT"}
_LSC = {"PC": "PACIFIC"}
_LEG_ORDER = {"1": "LEG_1", "2": "LEG_2", "3": "LEG_3", "4": "LEG_4"}


def fld(line: str, start: int, length: int) -> str:
    return line[start - 1 : start - 1 + length].strip()


def parse_date(raw: str) -> str | None:
    raw = raw.strip()
    if len(raw) != 8 or not raw.isdigit():
        return None
    mm, dd, yyyy = int(raw[0:2]), int(raw[2:4]), int(raw[4:8])
    return datetime.date(yyyy, mm, dd).isoformat()


def cs(raw: str) -> int | None | str:
    """Hy-Tek decimal-seconds -> centiseconds; None for blank/`0.00`, "BAD" if malformed."""
    raw = raw.strip()
    if not raw:
        return None
    if "." not in raw:
        return "BAD"
    sec, frac = raw.split(".", 1)
    if not (sec.isdigit() and frac.isdigit()):
        return "BAD"
    val = int(sec) * 100 + int((frac + "00")[:2])
    return val or None


def time_str(raw: str) -> str | None:
    val = cs(raw)
    if not isinstance(val, int):
        return None
    mm, ss, hh = val // 6000, (val // 100) % 60, val % 100
    return f"{mm}:{ss:02d}.{hh:02d}" if mm else f"{ss}.{hh:02d}"


def int_or_none(raw: str) -> int | None:
    raw = raw.strip()
    return int(raw) if raw.lstrip("-").isdigit() else None


def event_age(raw: str, open_sentinel: int) -> int | None:
    """E1/F1 age bound; open-ended sentinel (0 low / 109 high) -> None."""
    val = int_or_none(raw)
    return None if val is None or val == open_sentinel else val


def event_name(dist: str, stroke_name: str, course: str, relay: bool) -> str | None:
    d = int_or_none(dist)
    if d is None or stroke_name is None or course is None:
        return None
    return f"{stroke_name}_{d}_RELAY_{course}" if relay else f"{stroke_name}_{d}_{course}"


def build() -> dict:  # noqa: C901 — mirrors the parser's record state machine
    lines = SRC.read_text(encoding="cp1252").splitlines()

    meet: dict = {}
    source_file: dict = {}
    club: dict | None = None
    clubs: list[dict] = []
    swimmers: dict[str, dict] = {}  # athlete number -> swimmer
    swim_order: list[str] = []

    pending_entry: dict | None = None
    pending_relay: dict | None = None
    current_age: str | None = None
    current_swim: dict | None = None
    current_relay: dict | None = None
    last_leaf: str | None = None

    warnings: Counter[tuple] = Counter()
    splits_parsed = 0
    relays: list[dict] = []

    for line in lines:
        t = line[:2]

        if t == "A1":
            source_file = {
                "hy3_file_type": _FILETYPE.get(fld(line, 3, 2)),
                "software_name": fld(line, 45, 14) or None,
                "created": parse_date(fld(line, 59, 8)),
                "created_time": _time_of_day(fld(line, 68, 8)),
                "licensee": fld(line, 76, 53) or None,
            }

        elif t == "B1":
            meet = {
                "name": fld(line, 3, 45),
                "venue": fld(line, 48, 45) or None,
                "start_date": parse_date(fld(line, 93, 8)),
                "end_date": parse_date(fld(line, 101, 8)),
                "age_up_date": parse_date(fld(line, 109, 8)),
                "altitude": int_or_none(fld(line, 117, 4)),
                "course": None,
                "sanction_number": None,
            }

        elif t == "B2":
            course = _COURSE.get(fld(line, 99, 1))
            if course:
                meet["course"] = course
            sanction = fld(line, 109, 8)
            if sanction:
                meet["sanction_number"] = sanction

        elif t == "C1":
            abbrev, name = fld(line, 3, 5), fld(line, 8, 30)
            lsc_raw = fld(line, 54, 2)
            # Prefix the LSC code to match read_cl2 / read_hy3 (e.g. "PCPASA").
            team_code = (lsc_raw + abbrev) if lsc_raw else abbrev
            club = {
                "team_code": team_code,
                "lsc": _LSC.get(lsc_raw),
                "full_name": name or None,
                "email": None,
                "swimmer_ids": [],
                "result_count": 0,
            }
            clubs.append(club)

        elif t == "C3":
            if club is not None:
                club["email"] = fld(line, 93, 30) or None

        elif t == "D1":
            number = fld(line, 4, 5)
            if not fld(line, 89, 8):
                warnings[("D1", "birthday", "MISSING", "RECOVERED")] += 1
            # Cols 70-83 hold the 14-char SWIMS member ID (-> id_long); id_short is its
            # 12-char prefix, matching the SDIF reader's distinct 12-char USS# field.
            member = fld(line, 70, 14)
            sw = {
                "athlete_number": number,
                "sex": _SEX[fld(line, 3, 1)],
                "last_name": fld(line, 9, 20),
                "first_name": fld(line, 29, 20),
                "preferred_first_name": fld(line, 49, 20) or None,
                "middle_initial": fld(line, 69, 1) or None,
                "id_short": member[:12] if member else None,
                "birthday": parse_date(fld(line, 89, 8)),
                "club_team_code": club["team_code"] if club else None,
                "swims": [],
            }
            swimmers[number] = sw
            swim_order.append(number)
            if club is not None:
                club["swimmer_ids"].append(number)
            # cl2 packs a single "age or class" code; .hy3 separates Age (cols 98-99)
            # from Grade/Class (cols 100-101). Prefer a real (non-zero) age, else grade.
            age = fld(line, 98, 2)
            grade = fld(line, 100, 2)
            current_age = age if (age and age.lstrip("0")) else (grade or None)
            current_swim = current_relay = None
            last_leaf = None

        elif t == "E1":
            number = fld(line, 4, 5)
            pending_entry = {
                "swimmer": swimmers.get(number),
                "event_sex": _EVENT_SEX.get(fld(line, 15, 1)),
                "dist": fld(line, 16, 6),
                "stroke": _STROKE.get(fld(line, 22, 1)),
                "event_min_age": event_age(fld(line, 23, 3), 0),
                "event_max_age": event_age(fld(line, 26, 3), 109),
                "event_number": fld(line, 39, 4) or None,
                "seed_time": time_str(fld(line, 53, 7)),
                "converted_seed_time": time_str(fld(line, 44, 7)),
            }

        elif t == "E2":
            entry, pending_entry = pending_entry, None
            if entry is None or entry["swimmer"] is None:
                current_swim = current_relay = None
                last_leaf = None
                continue
            course = _COURSE.get(fld(line, 12, 1))
            event = event_name(entry["dist"], entry["stroke"], course, relay=False)
            if event is None or entry["event_sex"] is None:
                warnings[("E2", "event", "UNKNOWN_CODE", "SKIPPED")] += 1
                current_swim = current_relay = None
                last_leaf = None
                continue
            status, valid = _STATUS[fld(line, 13, 1)]
            swim = {
                "event": event,
                "event_sex": entry["event_sex"],
                "event_min_age": entry["event_min_age"],
                "event_max_age": entry["event_max_age"],
                "event_number": entry["event_number"],
                "session": {"P": "PRELIMS", "F": "FINALS", "S": "SWIM_OFFS"}.get(
                    fld(line, 3, 1), "FINALS"
                ),
                "status": status,
                "time": time_str(fld(line, 5, 7)) if valid else None,
                "rank": _rank(fld(line, 31, 3)),
                "seed_time": entry["seed_time"],
                "converted_seed_time": entry["converted_seed_time"],
                "dq_code": fld(line, 14, 2) or None if status == "DQ" else None,
                "dq_reason": None,
                "swimmer_age_class": current_age,
                "splits": [],
            }
            entry["swimmer"]["swims"].append(swim)
            if club is not None:
                club["result_count"] += 1
            current_swim, current_relay = swim, None
            last_leaf = "individual"

        elif t == "F1":
            pending_relay = {
                "relay_letter": fld(line, 8, 1),
                "event_sex": _EVENT_SEX.get(fld(line, 15, 1)),
                "dist": fld(line, 19, 3),
                "stroke": _RELAY_STROKE.get(fld(line, 22, 1)),
                "event_min_age": event_age(fld(line, 23, 3), 0),
                "event_max_age": event_age(fld(line, 26, 3), 109),
                "event_number": fld(line, 39, 4) or None,
                "seed_time": time_str(fld(line, 53, 7)),
                "converted_seed_time": time_str(fld(line, 44, 7)),
            }

        elif t == "F2":
            entry, pending_relay = pending_relay, None
            if entry is None:
                current_relay = current_swim = None
                last_leaf = None
                continue
            course = _COURSE.get(fld(line, 12, 1))
            event = event_name(entry["dist"], entry["stroke"], course, relay=True)
            if event is None or entry["event_sex"] is None:
                warnings[("F2", "event", "UNKNOWN_CODE", "SKIPPED")] += 1
                current_relay = current_swim = None
                last_leaf = None
                continue
            status, valid = _STATUS[fld(line, 13, 1)]
            relay = {
                "event": event,
                "event_sex": entry["event_sex"],
                "event_min_age": entry["event_min_age"],
                "event_max_age": entry["event_max_age"],
                "event_number": entry["event_number"],
                "relay_letter": entry["relay_letter"],
                "session": {"P": "PRELIMS", "F": "FINALS", "S": "SWIM_OFFS"}.get(
                    fld(line, 3, 1), "FINALS"
                ),
                "status": status,
                "time": time_str(fld(line, 6, 6)) if valid else None,
                "rank": _rank(fld(line, 31, 3)),
                "dq_code": fld(line, 14, 2) or None if status == "DQ" else None,
                "dq_reason": None,
                "splits": [],
                "legs": [],
            }
            relays.append(relay)
            if club is not None:
                club["result_count"] += 1
            current_relay, current_swim = relay, None
            last_leaf = "relay"

        elif t == "F3":
            if current_relay is None:
                warnings[("F3", None, "ORPHANED", "SKIPPED")] += 1
                continue
            for slot in range(8):
                start = 3 + slot * 13
                chunk = line[start - 1 : start - 1 + 13]
                if not chunk.strip():
                    continue
                number = chunk[1:6].strip()
                order = _LEG_ORDER.get(chunk[12:13].strip(), "ALTERNATE")
                sw = swimmers.get(number)
                current_relay["legs"].append(
                    {"order": order, "swimmer_id_short": sw["id_short"] if sw else None}
                )

        elif t == "G1":
            target = (
                current_swim["splits"]
                if last_leaf == "individual" and current_swim
                else current_relay["splits"]
                if last_leaf == "relay" and current_relay
                else None
            )
            if target is None:
                warnings[("G1", None, "ORPHANED", "SKIPPED")] += 1
                continue
            for slot in range(11):
                start = 3 + slot * 11
                block = line[start - 1 : start - 1 + 11]
                if not block.strip():
                    continue
                counter = block[1:3].strip()
                if not counter.isdigit():
                    warnings[("G1", "split_distance", "MALFORMED", "RECOVERED")] += 1
                    continue
                val = cs(block[3:11])
                if val is None:
                    continue  # blank / 0.00 placeholder
                if val == "BAD":
                    warnings[("G1", "split_time", "MALFORMED", "RECOVERED")] += 1
                    target.append({"distance": int(counter) * 25, "time": None})
                else:
                    target.append({"distance": int(counter) * 25, "time": time_str(block[3:11])})
                splits_parsed += 1

        elif t in ("H1", "H2"):
            result = (
                current_swim
                if last_leaf == "individual"
                else current_relay
                if last_leaf == "relay"
                else None
            )
            text = fld(line, 5, 48)
            if result is not None and text:
                result["dq_reason"] = (
                    f"{result['dq_reason']} {text}".strip() if result["dq_reason"] else text
                )

    swimmers_list = [swimmers[n] for n in swim_order]
    individual_swims = sum(len(s["swims"]) for s in swimmers_list)
    fields_recovered = sum(c for (rt, f, k, s), c in warnings.items() if s == "RECOVERED")
    records_skipped = sum(c for (rt, f, k, s), c in warnings.items() if s == "SKIPPED")

    return {
        "file": SRC.name,
        "report": {
            "files_read": 1,
            "meets_parsed": 1,
            "swimmers_parsed": len(swimmers_list),
            "individual_swims_parsed": individual_swims,
            "relays_parsed": len(relays),
            "splits_parsed": splits_parsed,
            "records_skipped": records_skipped,
            "fields_recovered": fields_recovered,
        },
        "warnings": sorted(
            [
                {"record_type": rt, "field": f, "kind": k, "severity": s, "count": c}
                for (rt, f, k, s), c in warnings.items()
            ],
            key=lambda w: (w["record_type"] or "", w["field"] or ""),
        ),
        "meet": meet,
        "source_file": source_file,
        "clubs": [
            {
                "team_code": c["team_code"],
                "lsc": c["lsc"],
                "full_name": c["full_name"],
                "email": c["email"],
                "swimmer_count": len(c["swimmer_ids"]),
                "result_count": c["result_count"],
            }
            for c in clubs
        ],
        "swimmers": [{k: v for k, v in s.items() if k != "athlete_number"} for s in swimmers_list],
        "relays": relays,
    }


def _time_of_day(raw: str) -> str | None:
    raw = raw.strip()
    for fmt in ("%I:%M %p", "%H:%M"):
        try:
            return datetime.datetime.strptime(raw, fmt).time().isoformat()
        except ValueError:
            continue
    return None


def _rank(raw: str) -> int | None:
    val = int_or_none(raw)
    return val if val is not None and val > 0 else None


if __name__ == "__main__":
    data = build()
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    r = data["report"]
    print(f"wrote {OUT.name}")
    print(
        f"  swimmers={r['swimmers_parsed']} swims={r['individual_swims_parsed']} "
        f"relays={r['relays_parsed']} splits={r['splits_parsed']} "
        f"skipped={r['records_skipped']} warnings={len(data['warnings'])}"
    )
