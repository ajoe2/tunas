"""Build the ground-truth JSON for ``aaa_league_championship.cl2`` (relay golden file).

Like ``build_expected.py`` (the individual-events golden file), this is an
INDEPENDENT reference decoder that reads the SDIF v3 columns directly and does
NOT import ``tunas``. It additionally covers the relay path that the smaller
``reno`` file lacks: prelim+finals individual swims with per-session split
routing, E0 relays, F0 relay legs (leg event, leg splits), and blank-``id_short``
swimmers resolved from a later ``D3`` long ID.

The committed ``aaa_league_championship.expected.json`` was produced here and
cross-checked against the raw records; ``test_golden_relay.py`` compares the real
``tunas`` parse against it.

Re-generate with:  uv run python tests/data/build_expected_aaa.py
"""

from __future__ import annotations

import datetime
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "aaa_league_championship.cl2"
OUT = HERE / "aaa_league_championship.expected.json"

_STROKE = {"1": "FREE", "2": "BACK", "3": "BREAST", "4": "FLY", "5": "IM"}
_RELAY_STROKE = {"6": "FREE", "7": "MEDLEY"}
_MEDLEY_LEGS = {1: "BACK", 2: "BREAST", 3: "FLY", 4: "FREE"}
_COURSE = {"1": "SCM", "S": "SCM", "2": "SCY", "Y": "SCY", "3": "LCM", "L": "LCM"}
_SEX = {"M": "MALE", "F": "FEMALE", "X": "MIXED"}
_ORG = {
    "1": "USS",
    "2": "MASTERS",
    "3": "NCAA",
    "4": "NCAA_DIV_I",
    "5": "NCAA_DIV_II",
    "6": "NCAA_DIV_III",
    "7": "YMCA",
    "8": "FINA",
    "9": "HIGH_SCHOOL",
}
_TIME_CODES = {"NT", "NS", "DNF", "DQ", "SCR"}
# Geo codes this file uses; team codes are non-standard "R5xxxx" -> lsc None.
_STATE = {"CA": "CALIFORNIA"}
_COUNTRY = {"USA": "UNITED_STATES"}
_LSC: dict[str, str] = {}
_FILETYPE = {"02": "MEET_RESULTS"}


def fld(line: str, s: int, n: int) -> str:
    return line[s - 1 : s - 1 + n].strip()


def parse_date(raw: str) -> str | None:
    raw = raw.strip()
    if len(raw) != 8 or not raw.isdigit():
        return None
    return datetime.date(int(raw[4:8]), int(raw[0:2]), int(raw[2:4])).isoformat()


def time_str(raw: str) -> str | None:
    raw = raw.strip()
    if not raw or "." not in raw:
        return None
    minutes, sec_part = 0, raw
    if ":" in raw:
        m, sec_part = raw.split(":", 1)
        minutes = int(m)
    sec, frac = sec_part.split(".")
    cs = minutes * 6000 + int(sec) * 100 + int((frac + "00")[:2])
    mm, ss, hh = cs // 6000, (cs // 100) % 60, cs % 100
    return f"{mm}:{ss:02d}.{hh:02d}" if mm else f"{ss}.{hh:02d}"


def time_outcome(raw: str, course_byte: str) -> tuple[str, str | None]:
    """(status, time) for a session time field + its course byte."""
    v = raw.strip()
    if v.upper() in _TIME_CODES:
        return v.upper(), None
    if course_byte.strip().upper() == "X":
        return "DQ", time_str(raw)
    return "OK", time_str(raw)


def ages(raw: str) -> tuple[int | None, int | None]:
    lo, hi = raw[0:2].strip().upper(), raw[2:4].strip().upper()
    return (int(lo) if lo.isdigit() else None, int(hi) if hi.isdigit() else None)


def parse_name(raw: str) -> tuple[str, str, str | None]:
    last, rest = raw.strip().split(",", 1)
    tokens = rest.split()
    first = tokens[0] if tokens else ""
    middle = tokens[1][0] if len(tokens) > 1 and tokens[1] else None
    return last.strip(), first, middle


def event_course(line: str, positions: list[int], default: str | None) -> str | None:
    for p in positions:
        tag = _COURSE.get(fld(line, p, 1))
        if tag:
            return tag
    return default


def leg_event(relay_dist: int, relay_stroke: str, course: str, order: int) -> str:
    leg_dist = relay_dist // 4
    stroke = _MEDLEY_LEGS[order] if relay_stroke == "7" else "FREE"  # 7 = medley relay
    return f"{stroke}_{leg_dist}_{course}"


def build() -> dict:  # noqa: C901 - a faithful single-pass decoder
    lines = SRC.read_text(encoding="cp1252").splitlines()
    meet: dict = {}
    source_file: dict = {}
    clubs: dict[str, dict] = {}
    swimmers: dict[int, dict] = {}  # keyed by id() of the swimmer dict
    by_id: dict[str, dict] = {}  # keyed by member id_short / id_long
    order: list[int] = []
    relays: list[dict] = []
    warnings: Counter[tuple] = Counter()
    counts = Counter()

    current_club: dict | None = None
    unattached = False
    current_swimmer: dict | None = None
    current_swims: list[dict] = []
    pending: dict | None = None  # {"swimmer":.., "swims":[..], "club":..}
    current_relays: dict[str, dict] = {}
    current_legs: dict[str, dict] = {}
    last_leaf: str | None = None
    meet_course: str | None = None

    def register(sw: dict, swims: list[dict], club: dict | None) -> dict:
        keys = [k for k in (sw["id_short"], sw["id_long"]) if k]
        target = next((by_id[k] for k in keys if k in by_id), None)
        if target is None:
            target = sw
            swimmers[id(sw)] = sw
            order.append(id(sw))
            counts["swimmers"] += 1
            if club is not None:
                club["swimmer_ids"].append(id(sw))
        else:
            for attr in (
                "id_short",
                "id_long",
                "middle_initial",
                "preferred_first_name",
                "birthday",
                "citizenship",
                "club_team_code",
            ):
                if target.get(attr) is None and sw.get(attr) is not None:
                    target[attr] = sw[attr]
        for k in keys:
            by_id.setdefault(k, target)
        for s in swims:
            target["swims"].append(s)
            counts["individual_swims"] += 1
            if club is not None:
                club["individual_count"] += 1
        return target

    def commit_pending() -> None:
        nonlocal pending
        if pending is None:
            return
        p, pending = pending, None
        sw = p["swimmer"]
        if sw["id_short"] is None and sw["id_long"] is None:
            # No identity: discard the record (and any splits a trailing G0 counted).
            counts["splits"] -= sum(len(s["splits"]) for s in p["swims"])
            warnings[("D0", "id_short", "MISSING", "SKIPPED")] += 1
            counts["records_skipped"] += 1
        else:
            register(sw, p["swims"], p["club"])

    for line in lines:
        t = line[:2]
        if t in ("D0", "C1", "E0", "F0", "Z0", "B1", "A0"):
            commit_pending()

        if t == "A0":
            source_file = {
                "file_type": _FILETYPE.get(fld(line, 12, 2)),
                "sdif_version": fld(line, 4, 8) or None,
                "software_name": fld(line, 44, 20) or None,
                "software_version": fld(line, 64, 10) or None,
                "contact_name": fld(line, 74, 20) or None,
                "contact_phone": fld(line, 94, 12) or None,
                "created": parse_date(fld(line, 106, 8)),
                "submitted_by_lsc": _LSC.get(fld(line, 156, 2)) or None,
                "notes": None,
            }

        elif t == "B1":
            meet_course = _COURSE.get(fld(line, 150, 1)) or None
            if not fld(line, 121, 1):
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
                "course": meet_course,
                "altitude": int(fld(line, 138, 4)) if fld(line, 138, 4).isdigit() else None,
                "meet_type": None,
            }

        elif t == "C1":
            base = line[11:17]
            lsc_code, team_part = base[0:2].strip(), base[2:].strip()
            full = (lsc_code + team_part).strip()
            name = fld(line, 18, 30)
            if team_part.upper() == "UN" or "UNATTACHED" in name.upper():
                unattached, current_club = True, None
            elif full in clubs:
                unattached, current_club = False, clubs[full]  # repeated C1 reuses the club
            else:
                unattached = False
                country_raw = fld(line, 140, 3)
                country = _COUNTRY.get(country_raw)
                if country_raw and country is None:
                    warnings[("C1", "country", "UNKNOWN_CODE", "RECOVERED")] += 1
                clubs[full] = {
                    "team_code": full,
                    "lsc": _LSC.get(lsc_code),
                    "full_name": name or None,
                    "country": country,
                    "swimmer_ids": [],
                    "individual_count": 0,
                    "relay_count": 0,
                }
                current_club = clubs[full]

        elif t == "D0":
            id_short = fld(line, 40, 12) or None
            last, first, middle = parse_name(line[11:39])
            sex = _SEX[fld(line, 66, 1)]
            citizen = fld(line, 53, 3)
            citizenship = _COUNTRY.get(citizen) if citizen else None
            if not fld(line, 56, 8):
                warnings[("D0", "birthday", "MISSING", "RECOVERED")] += 1
            esex_raw, dist_raw, stroke_raw, eage_raw = (
                fld(line, 67, 1),
                fld(line, 68, 4),
                fld(line, 72, 1),
                fld(line, 77, 4),
            )
            present = bool(esex_raw or dist_raw or stroke_raw or eage_raw)
            club_code = (
                None if unattached else (current_club["team_code"] if current_club else None)
            )

            swims: list[dict] = []
            if present:
                course = event_course(line, [124, 106, 115, 97], meet_course)
                event = (
                    f"{_STROKE[stroke_raw]}_{int(dist_raw)}_{course}"
                    if stroke_raw in _STROKE and dist_raw.isdigit() and course
                    else None
                )
                if event is None:
                    warnings[("D0", "event", "UNKNOWN_CODE", "SKIPPED")] += 1
                    counts["records_skipped"] += 1
                    current_swimmer, current_swims, last_leaf = None, [], None
                    continue
                emin, emax = ages(eage_raw)
                seed = time_str(fld(line, 89, 8))
                shared = {
                    "event": event,
                    "event_sex": _SEX[esex_raw],
                    "event_min_age": emin,
                    "event_max_age": emax,
                    "seed_time": seed,
                }
                specs = [
                    ("PRELIMS", 98, 106, 133),
                    ("SWIM_OFFS", 107, 115, None),
                    ("FINALS", 116, 124, 136),
                ]
                for session, tpos, cpos, ppos in specs:
                    raw = fld(line, tpos, 8)
                    if not raw:
                        continue
                    status, ts = time_outcome(line[tpos - 1 : tpos - 1 + 8], fld(line, cpos, 1))
                    rank = None
                    if ppos is not None:
                        praw = fld(line, ppos, 3)
                        if praw.lstrip("-").isdigit() and int(praw) > 0:
                            rank = int(praw)
                    swims.append(
                        {
                            "is_relay_leg": False,
                            "session": session,
                            "status": status,
                            "time": ts,
                            "rank": rank,
                            "splits": [],
                            **shared,
                        }
                    )

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
            if id_short:
                current_swimmer = register(sw, swims, current_club if not unattached else None)
            else:
                pending = {
                    "swimmer": sw,
                    "swims": swims,
                    "club": current_club if not unattached else None,
                }
                current_swimmer = sw
            current_swims = swims
            last_leaf = "individual"

        elif t == "D3":
            if current_swimmer is not None:
                id_long = fld(line, 3, 14) or None
                pref = fld(line, 17, 15) or None
                if id_long and current_swimmer["id_long"] is None:
                    current_swimmer["id_long"] = id_long
                if pref:
                    current_swimmer["preferred_first_name"] = pref
                if (
                    pending is not None
                    and pending["swimmer"] is current_swimmer
                    and current_swimmer["id_long"] is not None
                ):
                    current_swimmer = register(
                        pending["swimmer"], pending["swims"], pending["club"]
                    )
                    pending = None

        elif t == "E0":
            letter = fld(line, 12, 1)
            esex = _SEX[fld(line, 21, 1)]
            dist_raw, stroke_raw = fld(line, 22, 4), fld(line, 26, 1)
            course = event_course(line, [81, 63, 72, 54], meet_course)
            relay_event = (
                f"{_RELAY_STROKE[stroke_raw]}_{int(dist_raw)}_RELAY_{course}"
                if stroke_raw in _RELAY_STROKE and dist_raw.isdigit() and course
                else None
            )
            emin, emax = ages(fld(line, 31, 4))
            tage = int(fld(line, 35, 3)) if fld(line, 35, 3).lstrip("-").isdigit() else None
            date = parse_date(fld(line, 38, 8))
            club_code = (
                None if unattached else (current_club["team_code"] if current_club else None)
            )
            current_relays = {}
            current_legs = {}
            if relay_event is None:
                warnings[("E0", "event", "UNKNOWN_CODE", "SKIPPED")] += 1
                counts["records_skipped"] += 1
                last_leaf = None
                continue
            specs = [("PRELIMS", 55, 63, 90), ("SWIM_OFFS", 64, 72, None), ("FINALS", 73, 81, 93)]
            for session, tpos, cpos, ppos in specs:
                raw = fld(line, tpos, 8)
                if not raw:
                    continue
                status, ts = time_outcome(line[tpos - 1 : tpos - 1 + 8], fld(line, cpos, 1))
                rank = None
                if ppos is not None:
                    praw = fld(line, ppos, 3)
                    if praw.lstrip("-").isdigit() and int(praw) > 0:
                        rank = int(praw)
                relay = {
                    "club_team_code": club_code,
                    "relay_letter": letter,
                    "event": relay_event,
                    "event_sex": esex,
                    "event_min_age": emin,
                    "event_max_age": emax,
                    "session": session,
                    "status": status,
                    "time": ts,
                    "rank": rank,
                    "total_age": tage,
                    "date": date,
                    "_dist": int(dist_raw),
                    "_stroke": stroke_raw,
                    "_course": course,
                    "legs": [],
                    "alternates": [],
                }
                relays.append(relay)
                current_relays[session] = relay
                counts["relays"] += 1
                if club_code is not None:
                    clubs[club_code]["relay_count"] += 1
            last_leaf = "relay"

        elif t == "F0":
            if not current_relays:
                warnings[("F0", None, "ORPHANED", "SKIPPED")] += 1
                counts["records_skipped"] += 1
                continue
            id_short = fld(line, 51, 12) or None
            id_long = fld(line, 93, 14) or None
            last, first, middle = parse_name(line[22:50])
            sex = _SEX[fld(line, 76, 1)]
            citizen = fld(line, 63, 3)
            citizenship = _COUNTRY.get(citizen) if citizen else None
            if not fld(line, 66, 8):
                warnings[("F0", "birthday", "MISSING", "RECOVERED")] += 1
            club_code = (
                None if unattached else (current_club["team_code"] if current_club else None)
            )

            leg_swimmer: dict | None = None
            if id_short or id_long:
                keys = [k for k in (id_short, id_long) if k]
                leg_swimmer = next((by_id[k] for k in keys if k in by_id), None)
                if leg_swimmer is None:
                    leg_swimmer = {
                        "id_short": id_short,
                        "id_long": id_long,
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
                    swimmers[id(leg_swimmer)] = leg_swimmer
                    order.append(id(leg_swimmer))
                    counts["swimmers"] += 1
                    for k in keys:
                        by_id[k] = leg_swimmer
                    if club_code is not None and not unattached and current_club is not None:
                        current_club["swimmer_ids"].append(id(leg_swimmer))
            else:
                warnings[("F0", "id_short", "MISSING", "RECOVERED")] += 1

            leg_time = time_str(fld(line, 80, 8))
            leg_course = _COURSE.get(fld(line, 88, 1))
            tk = fld(line, 89, 4)
            takeoff = round(float(tk) * 100) if tk.replace(".", "", 1).isdigit() else None
            sid = (leg_swimmer["id_short"] or leg_swimmer["id_long"]) if leg_swimmer else None

            created: dict[str, dict] = {}
            for session, opos in [("PRELIMS", 77), ("SWIM_OFFS", 78), ("FINALS", 79)]:
                o = fld(line, opos, 1)
                if not o or o == "0":
                    continue
                relay = current_relays.get(session)
                if relay is None:
                    continue
                leg_evt = (
                    None
                    if o == "A" and relay["_stroke"] == "7"
                    else leg_event(
                        relay["_dist"],
                        relay["_stroke"],
                        relay["_course"],
                        1 if o == "A" else int(o),
                    )
                )
                leg = {
                    "order": "ALTERNATE" if o == "A" else f"LEG_{o}",
                    "leg_event": leg_evt,
                    "swimmer_id": sid,
                    "time": None,
                    "takeoff_time": None,
                    "course": None,
                    "splits": [],
                }
                if o == "A":
                    relay["alternates"].append(leg)
                else:
                    relay["legs"].append(leg)
                    if leg_swimmer is not None:
                        leg_swimmer["swims"].append(
                            {
                                "is_relay_leg": True,
                                "session": session,
                                "leg_event": leg_evt,
                                "order": leg["order"],
                                "splits": leg["splits"],
                            }
                        )
                created[session] = leg
            if created:
                target = created.get("FINALS") or next(iter(created.values()))
                target["time"] = leg_time
                target["course"] = leg_course
                target["takeoff_time"] = takeoff
            current_legs = created
            current_swimmer = leg_swimmer
            last_leaf = "relay"

        elif t == "G0":
            seq = int(fld(line, 56, 1)) if fld(line, 56, 1).lstrip("-").isdigit() else 0
            if seq < 1:
                if fld(line, 56, 1).lstrip("-").isdigit():
                    warnings[("G0", "sequence_number", "MALFORMED", "RECOVERED")] += 1
                seq = 1
            inc = int(fld(line, 59, 4))
            stype = "CUMULATIVE" if fld(line, 63, 1) == "C" else "INTERVAL"
            scode = {"P": "PRELIMS", "F": "FINALS", "S": "SWIM_OFFS"}.get(fld(line, 144, 1))
            target_splits = None
            if last_leaf == "relay" and current_legs:
                leg = (
                    (current_legs.get(scode) if scode else None)
                    or current_legs.get("FINALS")
                    or next(iter(current_legs.values()))
                )
                target_splits = leg["splits"]
            elif last_leaf == "individual" and current_swims:
                match = next((s for s in current_swims if scode and s["session"] == scode), None)
                target_splits = (match or current_swims[0])["splits"]
            if target_splits is None:
                warnings[("G0", None, "ORPHANED", "SKIPPED")] += 1
                counts["records_skipped"] += 1
                continue
            base = (seq - 1) * 10
            for j in range(10):
                raw = fld(line, 64 + j * 8, 8)
                if not raw:
                    continue
                target_splits.append(
                    {
                        "distance": inc * (base + j + 1),
                        "time": time_str(raw),
                        "split_type": stype,
                    }
                )
                counts["splits"] += 1

        elif t == "Z0":
            note = fld(line, 14, 30)
            if note:
                source_file["notes"] = note
            actual = Counter(ln[0] for ln in lines)
            for letter, (s, n) in {
                "B": (44, 3),
                "C": (50, 4),
                "D": (58, 6),
                "E": (70, 5),
                "F": (75, 6),
                "G": (81, 6),
            }.items():
                raw = fld(line, s, n)
                if raw.isdigit() and int(raw) != actual.get(letter, 0):
                    warnings[("Z0", f"{letter} records", "COUNT_MISMATCH", "RECOVERED")] += 1
            md = fld(line, 47, 3)
            if md.isdigit() and int(md) != 1:
                warnings[("Z0", "meets", "COUNT_MISMATCH", "RECOVERED")] += 1

    commit_pending()  # flush any trailing pending record

    fields_recovered = sum(
        c for (rt, f, k, s), c in warnings.items() if s == "RECOVERED" and k != "COUNT_MISMATCH"
    )
    relay_splits = sum(len(leg["splits"]) for r in relays for leg in r["legs"] + r["alternates"])
    indiv_splits = counts["splits"] - relay_splits

    def render_swimmer(sw: dict) -> dict:
        out = {k: v for k, v in sw.items() if k != "swims"}
        out["swims"] = sw["swims"]
        return out

    return {
        "file": SRC.name,
        "report": {
            "files_read": 1,
            "meets_parsed": 1,
            "swimmers_parsed": counts["swimmers"],
            "individual_swims_parsed": counts["individual_swims"],
            "relays_parsed": counts["relays"],
            "splits_parsed": counts["splits"],
            "records_skipped": counts["records_skipped"],
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
                "country": c["country"],
                "swimmer_count": len(c["swimmer_ids"]),
                "individual_count": c["individual_count"],
                "relay_count": c["relay_count"],
            }
            for c in sorted(clubs.values(), key=lambda c: c["team_code"])
        ],
        "swimmers": [
            render_swimmer(swimmers[k])
            for k in sorted(
                order, key=lambda k: (swimmers[k]["id_short"] or "", swimmers[k]["id_long"] or "")
            )
        ],
        "relays": [{k: v for k, v in r.items() if not k.startswith("_")} for r in relays],
        "_split_breakdown": {"individual": indiv_splits, "relay": relay_splits},
    }


if __name__ == "__main__":
    data = build()
    OUT.write_text(json.dumps(data, indent=1) + "\n")
    r = data["report"]
    sb = data["_split_breakdown"]
    print(f"wrote {OUT.name}")
    print(
        f"  swimmers={r['swimmers_parsed']} indiv={r['individual_swims_parsed']} "
        f"relays={r['relays_parsed']} skipped={r['records_skipped']} "
        f"clubs={len(data['clubs'])} warnings={len(data['warnings'])}"
    )
    print(f"  splits={r['splits_parsed']} (individual {sb['individual']} / relay {sb['relay']})")
