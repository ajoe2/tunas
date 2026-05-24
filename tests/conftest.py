"""Shared test helpers: a fixed-width SDIF record builder and common records."""

from __future__ import annotations

import io
from collections.abc import Iterator

import pytest

from tunas import Meet, ParseReport
from tunas.parser import read_cl2
from tunas.standards import _load_index

RECORD_WIDTH = 160


def rec(*fields: tuple[int, str]) -> str:
    """Build a 160-char SDIF line by placing ``(start_1indexed, text)`` fields."""
    buf = [" "] * RECORD_WIDTH
    for start, text in fields:
        for i, ch in enumerate(text):
            buf[start - 1 + i] = ch
    return "".join(buf)


def parse_lines(lines: list[str], *, strict: bool = False) -> tuple[list[Meet], ParseReport]:
    """Parse a list of record lines from an in-memory stream."""
    return read_cl2(io.StringIO("\n".join(lines) + "\n"), strict=strict)


# -- Reusable building blocks -------------------------------------------------

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
    fields = [(1, "D0"), (3, "1"), (12, name), (56, birth), (64, age_class), (66, sex), (81, date)]
    if uss:
        fields.append((40, uss))
    if esex:
        fields.append((67, esex))
    if dist:
        fields.append((68, dist))
    if stroke:
        fields.append((72, stroke))
    if eage:
        fields.append((77, eage))
    if seed:
        fields.append((89, seed))
    if seed_course:
        fields.append((97, seed_course))
    if prelim:
        fields.append((98, prelim))
    if prelim_course:
        fields.append((106, prelim_course))
    if finals:
        fields.append((116, finals))
    if finals_course:
        fields.append((124, finals_course))
    if finals_place:
        fields.append((136, finals_place))
    return rec(*fields)


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
    fields = [
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
    ]
    if uss:
        fields.append((51, uss))
    if id_long:
        fields.append((93, id_long))
    return rec(*fields)


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
    fields = [
        (1, "G0"),
        (3, "1"),
        (44, uss),
        (56, seq),
        (57, total),
        (59, split_dist),
        (63, split_type),
    ]
    for i, t in enumerate(times):
        fields.append((64 + i * 8, t))
    if session:
        fields.append((144, session))
    return rec(*fields)


@pytest.fixture(autouse=True)
def _clear_standards_cache() -> Iterator[None]:
    """Keep the lazily-loaded standards index isolated between tests."""
    _load_index.cache_clear()
    yield
    _load_index.cache_clear()
