"""Shared test helpers: fixed-width SDIF / Hy-Tek record builders and common records."""

from __future__ import annotations

import io
from collections import Counter
from collections.abc import Iterator
from enum import Enum
from pathlib import Path

import pytest

from tunas import MeetArchive, ParseReport
from tunas._parser.checksum import hy3_checksum
from tunas.parser import read_cl2, read_hy3
from tunas.standards import _load_index

DATA_DIR = Path(__file__).resolve().parent / "data"


def _place(width: int, fields: tuple[tuple[int, str], ...]) -> str:
    buf = [" "] * width
    for start, text in fields:
        buf[start - 1 : start - 1 + len(text)] = text
    return "".join(buf)


def rec(*fields: tuple[int, str]) -> str:
    """Build a 160-char SDIF line by placing ``(start_1indexed, text)`` fields."""
    return _place(160, fields)


def parse_lines(lines: list[str], *, strict: bool = False) -> MeetArchive:
    """Parse SDIF lines into the single MeetArchive an in-memory stream yields."""
    return next(iter(read_cl2(io.StringIO("\n".join(lines) + "\n"), strict=strict)))


A0 = rec(
    (1, "A0"),
    (3, "1"),
    (4, "V3"),
    (12, "02"),
    (44, "Hy-Tek"),
    (64, "8.0"),
    (74, "Jane Admin"),
    (94, "5551234567"),
    (106, "07012024"),
    (156, "PC"),
)

B1 = rec(
    (1, "B1"),
    (3, "1"),
    (12, "Winter Champs"),
    (86, "Santa Clara"),
    (106, "CA"),
    (121, "3"),
    (122, "01012025"),
    (130, "01032025"),
    (150, "2"),
)

C1 = rec(
    (1, "C1"), (3, "1"), (12, "PCSCSC"), (18, "Santa Clara Swim Club"), (48, "SCSC"), (143, "1")
)

Z0 = rec((1, "Z0"), (3, "1"), (12, "02"), (14, "Build OK"))


def d0(
    *,
    uss: str = "49AC52F69618",
    name: str = "Zhong, Irene Q",
    sex: str = "F",
    birth: str = "12242010",
    age_class: str = "14",
    esex: str = "F",
    dist: str = "100",
    stroke: str = "1",
    eage: str = "1314",
    date: str = "01022025",
    seed: str = "1:02.00",
    seed_course: str = "Y",
    prelim: str = "",
    prelim_course: str = "",
    finals: str = "1:00.00",
    finals_course: str = "Y",
    finals_place: str = "1",
) -> str:
    return rec(
        (1, "D0"),
        (3, "1"),
        (12, name),
        (56, birth),
        (64, age_class),
        (66, sex),
        (81, date),
        (40, uss),
        (67, esex),
        (68, dist),
        (72, stroke),
        (77, eage),
        (89, seed),
        (97, seed_course),
        (98, prelim),
        (106, prelim_course),
        (116, finals),
        (124, finals_course),
        (136, finals_place),
    )


def e0(
    *,
    letter: str = "A",
    team: str = "PCSCSC",
    esex: str = "F",
    dist: str = "200",
    stroke: str = "6",
    eage: str = "1314",
    total_age: str = "56",
    date: str = "01032025",
    seed: str = "",
    seed_course: str = "",
    finals: str = "1:45.00",
    finals_course: str = "Y",
) -> str:
    return rec(
        (1, "E0"),
        (3, "1"),
        (12, letter),
        (13, team),
        (21, esex),
        (22, dist),
        (26, stroke),
        (31, eage),
        (35, total_age),
        (38, date),
        (46, seed),
        (54, seed_course),
        (73, finals),
        (81, finals_course),
    )


def f0(
    *,
    team: str = "PCSCSC",
    letter: str = "A",
    name: str = "Zhong, Irene Q",
    uss: str = "49AC52F69618",
    id_long: str = "",
    birth: str = "12242010",
    sex: str = "F",
    order_prelim: str = "0",
    order_swimoff: str = "0",
    order_finals: str = "1",
    leg_time: str = "26.50",
    leg_course: str = "Y",
    takeoff: str = "0.29",
) -> str:
    return rec(
        (1, "F0"),
        (3, "1"),
        (16, team),
        (22, letter),
        (23, name),
        (66, birth),
        (76, sex),
        (77, order_prelim),
        (78, order_swimoff),
        (79, order_finals),
        (80, leg_time),
        (88, leg_course),
        (89, takeoff),
        (51, uss),
        (93, id_long),
    )


def g0(
    *,
    uss: str = "49AC52F69618",
    seq: str = "1",
    total: str = "2",
    split_dist: str = "50",
    split_type: str = "C",
    times: tuple[str, ...] = ("29.00", "1:00.00"),
    session: str = "F",
) -> str:
    return rec(
        (1, "G0"),
        (3, "1"),
        (44, uss),
        (56, seq),
        (57, total),
        (59, split_dist),
        (63, split_type),
        *((64 + i * 8, t) for i, t in enumerate(times)),
        (144, session),
    )


# -- Hy-Tek `.hy3` builders (128 data columns + a 2-digit checksum) ----------


def hy3_rec(*fields: tuple[int, str]) -> str:
    """Build a 130-char `.hy3` line with a valid trailing checksum."""
    body = _place(128, fields)
    return body + hy3_checksum(body.encode("cp1252"))


def parse_hy3_lines(lines: list[str], *, strict: bool = False) -> MeetArchive:
    """Parse `.hy3` lines into the single MeetArchive an in-memory stream yields."""
    return next(iter(read_hy3(io.StringIO("\n".join(lines) + "\n"), strict=strict)))


A1 = hy3_rec(
    (1, "A1"),
    (3, "07"),
    (5, "Results From MM to TM"),
    (30, "Hy-Tek, Ltd"),
    (45, "MM5 7.0Gb"),
    (59, "05012021"),
    (68, "6:52 AM"),
    (76, "Pacific Swimming"),
)

B1_HY3 = hy3_rec(
    (1, "B1"),
    (3, "Winter Distance Classic"),
    (48, "Rinconada Pool"),
    (93, "05012021"),
    (101, "05022021"),
    (109, "05012021"),
    (117, "  12"),
)

B2_HY3 = hy3_rec((1, "B2"), (99, "Y"), (109, "21-042"))

C1_HY3 = hy3_rec((1, "C1"), (3, "PASA"), (8, "Palo Alto Stanford Aquatics"), (54, "PC"))


def d1(
    *,
    sex: str = "F",
    number: str = "1",
    last: str = "Cadena",
    first: str = "Maggie",
    preferred: str = "Maggie",
    middle: str = "",
    member: str = "9F58190E90084A",
    birth: str = "07242014",
    age: str = "9",
    grade: str = "",
    citizen: str = "",
) -> str:
    return hy3_rec(
        (1, "D1"),
        (3, sex),
        (4, number.rjust(5)),
        (9, last),
        (29, first),
        (49, preferred),
        (70, member),
        (89, birth),
        (98, age.rjust(2)),
        (100, grade),
        (69, middle),
        (113, citizen),
    )


def e1(
    *,
    number: str = "1",
    event_sex: str = "G",
    dist: str = "100",
    stroke: str = "A",
    conv_seed: str = "0.00",
    conv_course: str = "Y",
    seed: str = "62.50",
    seed_course: str = "Y",
    event_number: str = "",
) -> str:
    return hy3_rec(
        (1, "E1"),
        (4, number.rjust(5)),
        (15, event_sex),
        (16, dist.rjust(6)),
        (22, stroke),
        (39, event_number.rjust(4)),
        (44, conv_seed.rjust(7)),
        (51, conv_course),
        (53, seed.rjust(7)),
        (60, seed_course),
    )


def e2(
    *,
    rnd: str = "F",
    time: str = "61.64",
    course: str = "Y",
    status: str = "",
    dqcode: str = "",
    heat: str = "4",
    lane: str = "7",
    place: str = "3",
    watch1: str = "",
    watch2: str = "",
    watch3: str = "",
    date: str = "05012021",
) -> str:
    return hy3_rec(
        (1, "E2"),
        (3, rnd),
        (5, time.rjust(7)),
        (12, course),
        (22, heat.rjust(2)),
        (25, lane.rjust(2)),
        (31, place.rjust(3)),
        (88, date),
        (13, status),
        (14, dqcode),
        (38, watch1.rjust(7)),
        (46, watch2.rjust(7)),
        (54, watch3.rjust(7)),
    )


def f1(
    *,
    letter: str = "A",
    event_sex: str = "X",
    dist: str = "200",
    stroke: str = "A",
    seed: str = "105.95",
    seed_course: str = "Y",
) -> str:
    return hy3_rec(
        (1, "F1"),
        (3, "PASA"),
        (8, letter),
        (15, event_sex),
        (19, dist.rjust(3)),
        (22, stroke),
        (53, seed.rjust(7)),
        (60, seed_course),
    )


def f2(
    *,
    rnd: str = "F",
    time: str = "125.69",
    course: str = "Y",
    status: str = "",
    dqcode: str = "",
    heat: str = "1",
    lane: str = "4",
    place: str = "1",
    date: str = "05012021",
) -> str:
    return hy3_rec(
        (1, "F2"),
        (3, rnd),
        (6, time.rjust(6)),
        (12, course),
        (22, heat.rjust(2)),
        (25, lane.rjust(2)),
        (31, place.rjust(3)),
        (103, date),
        (13, status),
        (14, dqcode),
    )


def f3_slot(sex: str, number: str, last5: str, rnd: str, leg: str) -> str:
    """Build one 13-char F3 athlete slot."""
    return sex + number.rjust(5) + last5.ljust(5) + rnd + leg


def f3(*slots: str) -> str:
    """Build an F3 record from up to 8 :func:`f3_slot` strings."""
    return hy3_rec((1, "F3"), *((3 + i * 13, s) for i, s in enumerate(slots)))


def g1_block(rnd: str, counter: int, time: str) -> str:
    """Build one 11-char G1 split block (round + distance counter + cumulative time)."""
    return rnd + str(counter).rjust(2) + time.rjust(8)


def g1(*blocks: str) -> str:
    """Build a G1 splits record from up to 11 :func:`g1_block` strings."""
    return hy3_rec((1, "G1"), *((3 + i * 11, b) for i, b in enumerate(blocks)))


def h1(*, code: str = "3D", text: str = "Scissors kick") -> str:
    return hy3_rec((1, "H1"), (3, code), (5, text))


# -- Golden-file rendering shared by the expected-JSON tests -----------------


def enum_name(value: Enum | None) -> str | None:
    return value.name if value is not None else None


def report_summary(report: ParseReport) -> dict[str, object]:
    """Render a report's counts and grouped warnings in the expected-JSON shape."""
    counts: Counter[tuple[str | None, str | None, str, str]] = Counter(
        (w.record_type, w.field, w.kind.name, w.severity.name) for w in report.warnings
    )
    return {
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
            (
                {"record_type": rt, "field": f, "kind": k, "severity": sev, "count": c}
                for (rt, f, k, sev), c in counts.items()
            ),
            key=lambda w: (w["record_type"] or "", w["field"] or ""),
        ),
    }


@pytest.fixture(autouse=True)
def _clear_standards_cache() -> Iterator[None]:
    """Keep the lazily-loaded standards index isolated between tests."""
    _load_index.cache_clear()
    yield
    _load_index.cache_clear()
