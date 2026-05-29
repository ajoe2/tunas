"""Build the ground-truth JSON for ``reno_walk_on_meet.cl2`` (golden-file test).

This is an INDEPENDENT reference decoder: it reads the SDIF v3 columns directly
and does NOT import ``tunas``. The committed ``reno_walk_on_meet.expected.json``
was produced by this script and then hand-verified against the raw records; the
test (`cl2/test_cl2_golden_meet.py`) compares the real `tunas` parse against that static
JSON, so a parser regression makes the test fail.

Re-generate with:  uv run python tests/data/build_expected.py
"""

from __future__ import annotations

import datetime
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "reno_walk_on_meet.cl2"
OUT = HERE / "reno_walk_on_meet.expected.json"

# --- explicit code -> enum-name maps (only the codes this file uses) --------- #
_STROKE = {"1": "FREE", "2": "BACK", "3": "BREAST", "4": "FLY", "5": "IM"}
_COURSE = {"1": "SCM", "S": "SCM", "2": "SCY", "Y": "SCY", "3": "LCM", "L": "LCM"}
_SEX = {"M": "MALE", "F": "FEMALE", "X": "MIXED"}
_ORG = {"1": "USS"}
_STATE = {"NV": "NEVADA"}
_COUNTRY = {"USA": "UNITED_STATES"}
_LSC = {"PC": "PACIFIC", "SN": "SIERRA_NEVADA"}
_FILETYPE = {"02": "MEET_RESULTS"}


def fld(line: str, start: int, length: int) -> str:
    return line[start - 1 : start - 1 + length].strip()


def parse_date(raw: str) -> str | None:
    raw = raw.strip()
    if len(raw) != 8 or not raw.isdigit():
        return None
    mm, dd, yyyy = int(raw[0:2]), int(raw[2:4]), int(raw[4:8])
    return datetime.date(yyyy, mm, dd).isoformat()


def time_str(raw: str) -> str | None:
    """Canonical ``[M:]SS.HH`` string (matches ``str(tunas.Time)``), or None."""
    raw = raw.strip()
    if not raw or "." not in raw:
        return None
    minutes = 0
    sec_part = raw
    if ":" in raw:
        m, sec_part = raw.split(":", 1)
        minutes = int(m)
    sec, frac = sec_part.split(".")
    cs = minutes * 6000 + int(sec) * 100 + int((frac + "00")[:2])
    mm, ss, hh = cs // 6000, (cs // 100) % 60, cs % 100
    return f"{mm}:{ss:02d}.{hh:02d}" if mm else f"{ss}.{hh:02d}"


def event_name(dist: str, stroke: str, course_name: str) -> str:
    return f"{_STROKE[stroke]}_{int(dist)}_{course_name}"


def parse_name(raw: str) -> tuple[str, str, str | None]:
    text = raw.strip()
    last, rest = text.split(",", 1)
    tokens = rest.split()
    if not tokens:
        return last.strip(), "", None
    # A trailing single-letter (optionally dotted) token is the middle initial;
    # a trailing whole word is part of a compound first name, not an initial.
    tail = tokens[-1]
    is_initial = (
        len(tail) == 1
        and tail.isalpha()
        or (len(tail) == 2 and tail[1] == "." and tail[0].isalpha())
    )
    if len(tokens) > 1 and is_initial:
        return last.strip(), " ".join(tokens[:-1]), tail[0]
    return last.strip(), " ".join(tokens), None


def build() -> dict:
    lines = SRC.read_text(encoding="cp1252").splitlines()

    meet: dict = {}
    source_file: dict = {}
    clubs: dict[str, dict] = {}  # team_code -> club
    swimmers: dict[str, dict] = {}  # id_short -> swimmer
    swim_order: list[str] = []  # swimmer ids in first-seen order

    current_club: dict | None = None
    unattached = False
    current_swimmer: dict | None = None
    current_swim: dict | None = None

    warnings: Counter[tuple] = Counter()
    splits_parsed = 0

    for line in lines:
        t = line[:2]

        if t == "A0":
            source_file = {
                "file_type": _FILETYPE.get(fld(line, 12, 2)),
                "sdif_version": fld(line, 4, 8) or None,
                "software_name": fld(line, 44, 20) or None,
                "software_version": fld(line, 64, 10) or None,
                "contact_name": fld(line, 74, 20) or None,
                "contact_phone": fld(line, 94, 12) or None,
                "created": parse_date(fld(line, 106, 8)),
                "submitted_by_lsc": _LSC.get(fld(line, 156, 2)) if fld(line, 156, 2) else None,
                "notes": None,  # filled from Z0
            }

        elif t == "B1":
            course = _COURSE.get(fld(line, 150, 1)) if fld(line, 150, 1) else None
            mtype = fld(line, 121, 1)
            if not mtype:
                warnings[("B1", "meet_type", "MISSING", "RECOVERED")] += 1
            meet = {
                "organization": _ORG.get(fld(line, 3, 1), "USS"),
                "name": fld(line, 12, 30),
                "start_date": parse_date(fld(line, 122, 8)),
                "end_date": parse_date(fld(line, 130, 8)),
                "city": fld(line, 86, 20) or None,
                "state": _STATE.get(fld(line, 106, 2)),
                "postal_code": fld(line, 108, 10) or None,
                "country": _COUNTRY.get(fld(line, 118, 3)),
                "course": course,
                "altitude": int(fld(line, 138, 4)) if fld(line, 138, 4).isdigit() else None,
                "meet_type": None,
            }

        elif t == "C1":
            base = line[11:17]  # 12/6
            lsc_code, team_part = base[0:2].strip(), base[2:].strip()
            full = (lsc_code + team_part).strip()
            name = fld(line, 18, 30)
            if team_part.upper() == "UN" or "UNATTACHED" in name.upper():
                unattached = True
                current_club = None
            else:
                unattached = False
                if full not in clubs:
                    clubs[full] = {
                        "team_code": full,
                        "lsc": _LSC.get(lsc_code),
                        "full_name": name or None,
                        "swimmer_ids": [],
                        "result_count": 0,
                    }
                current_club = clubs[full]

        elif t == "D0":
            id_short = fld(line, 40, 12)
            last, first, middle = parse_name(line[11:39])  # 12/28
            sex = _SEX[fld(line, 66, 1)]
            citizen = fld(line, 53, 3)
            citizenship = _COUNTRY.get(citizen) if citizen else None
            if not fld(line, 56, 8):  # birth date blank
                warnings[("D0", "birthday", "MISSING", "RECOVERED")] += 1

            course_name = _COURSE[fld(line, 124, 1)]  # finals course (the only one used)
            event = event_name(fld(line, 68, 4), fld(line, 72, 1), course_name)
            esex = _SEX[fld(line, 67, 1)]
            eage = fld(line, 77, 4)
            emin = int(eage[0:2]) if eage[0:2].isdigit() else None
            emax = int(eage[2:4]) if eage[2:4].isdigit() else None

            club_code = (
                None if unattached else (current_club["team_code"] if current_club else None)
            )

            # register/merge swimmer (group on id_short)
            sw = swimmers.get(id_short)
            if sw is None:
                sw = {
                    "id_short": id_short,
                    "id_long": None,
                    "first_name": first,
                    "last_name": last,
                    "middle_initial": middle,
                    "preferred_first_name": None,
                    "sex": sex,
                    "birthday": None,
                    "citizenship": citizenship,
                    "club_team_code": club_code,
                    "swims": [],
                }
                swimmers[id_short] = sw
                swim_order.append(id_short)
                if club_code is not None:
                    clubs[club_code]["swimmer_ids"].append(id_short)
            elif sw["citizenship"] is None and citizenship is not None:
                sw["citizenship"] = citizenship  # first non-None wins

            swim = {
                "event": event,
                "event_sex": esex,
                "event_min_age": emin,
                "event_max_age": emax,
                "session": "FINALS",
                "status": "OK",
                "time": time_str(fld(line, 116, 8)),  # finals time
                "rank": (
                    int(fld(line, 136, 3))
                    if fld(line, 136, 3).lstrip("-").isdigit() and int(fld(line, 136, 3)) > 0
                    else None
                ),
                "seed_time": time_str(fld(line, 89, 8)),
                "splits": [],
            }
            sw["swims"].append(swim)
            if club_code is not None:
                clubs[club_code]["result_count"] += 1
            current_swimmer = sw
            current_swim = swim

        elif t == "D3":
            if current_swimmer is not None:
                id_long = fld(line, 3, 14)
                if id_long and current_swimmer["id_long"] is None:
                    current_swimmer["id_long"] = id_long
                pref = fld(line, 17, 15)
                if pref:
                    current_swimmer["preferred_first_name"] = pref

        elif t == "G0":
            if current_swim is None:
                continue
            seq = int(fld(line, 56, 1))
            inc = int(fld(line, 59, 4))
            stype = "CUMULATIVE" if fld(line, 63, 1) == "C" else "INTERVAL"
            base = (max(seq, 1) - 1) * 10
            for j in range(10):
                raw = fld(line, 64 + j * 8, 8)
                if not raw:
                    continue  # skip an empty slot; keep later recorded splits
                ts = time_str(raw)
                current_swim["splits"].append(
                    {"distance": inc * (base + j + 1), "time": ts, "split_type": stype}
                )
                splits_parsed += 1

        elif t == "Z0":
            note = fld(line, 14, 30)
            if note:
                source_file["notes"] = note
            # Z0 record-count cross-check (B/C/D/E/F/G + meets)
            actual = Counter(ln[0] for ln in lines)
            declared = {
                "B": (44, 3),
                "C": (50, 4),
                "D": (58, 6),
                "E": (70, 5),
                "F": (75, 6),
                "G": (81, 6),
            }
            for letter, (s, n) in declared.items():
                raw = fld(line, s, n)
                if raw.isdigit() and int(raw) != actual.get(letter, 0):
                    warnings[("Z0", f"{letter} records", "COUNT_MISMATCH", "RECOVERED")] += 1
            meets_declared = fld(line, 47, 3)
            if meets_declared.isdigit() and int(meets_declared) != 1:
                warnings[("Z0", "meets", "COUNT_MISMATCH", "RECOVERED")] += 1

    individual_swims = sum(len(s["swims"]) for s in swimmers.values())
    fields_recovered = sum(
        c for (rt, fdn, kind, sev), c in warnings.items() if kind != "COUNT_MISMATCH"
    )

    return {
        "file": SRC.name,
        "report": {
            "files_read": 1,
            "meets_parsed": 1,
            "swimmers_parsed": len(swimmers),
            "individual_swims_parsed": individual_swims,
            "relays_parsed": 0,
            "splits_parsed": splits_parsed,
            "records_skipped": 0,
            "fields_recovered": fields_recovered,
        },
        "warnings": sorted(
            [
                {"record_type": rt, "field": f, "kind": k, "severity": s, "count": c}
                for (rt, f, k, s), c in warnings.items()
            ],
            key=lambda w: (w["record_type"], w["field"] or ""),
        ),
        "meet": meet,
        "source_file": source_file,
        "clubs": [
            {
                "team_code": c["team_code"],
                "lsc": c["lsc"],
                "full_name": c["full_name"],
                "swimmer_count": len(c["swimmer_ids"]),
                "result_count": c["result_count"],
            }
            for c in sorted(clubs.values(), key=lambda c: c["team_code"])
        ],
        "swimmers": [
            {k: v for k, v in swimmers[i].items() if k != "swims"} | {"swims": swimmers[i]["swims"]}
            for i in sorted(swim_order)
        ],
    }


if __name__ == "__main__":
    data = build()
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    r = data["report"]
    print(f"wrote {OUT.name}")
    print(
        f"  swimmers={r['swimmers_parsed']} swims={r['individual_swims_parsed']} "
        f"splits={r['splits_parsed']} clubs={len(data['clubs'])} warnings={len(data['warnings'])}"
    )
