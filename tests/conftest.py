"""Shared test helpers: fixed-width SDIF / Hy-Tek record builders and common records."""

from __future__ import annotations

import io
from collections.abc import Iterator
from pathlib import Path

import pytest

from tunas import MeetArchive
from tunas._parser.checksum import hy3_checksum
from tunas.parser import read_cl2, read_hy3
from tunas.standards import _load_index

RECORD_WIDTH = 160

# Committed golden-file fixtures (`.cl2`/`.hy3` + their `.expected.json`), resolved
# here so tests reference them independent of which subfolder they live in.
DATA_DIR = Path(__file__).resolve().parent / "data"


def rec(*fields: tuple[int, str]) -> str:
    """Build a 160-char SDIF line by placing ``(start_1indexed, text)`` fields."""
    buf = [" "] * RECORD_WIDTH
    for start, text in fields:
        for i, ch in enumerate(text):
            buf[start - 1 + i] = ch
    return "".join(buf)


def parse_lines(lines: list[str], *, strict: bool = False) -> MeetArchive:
    """Parse record lines from an in-memory stream into its single MeetArchive.

    A stream is one source, so the reader yields exactly one archive — this returns
    it directly, the way a caller of a single source would consume the iterator.
    """
    return next(iter(read_cl2(io.StringIO("\n".join(lines) + "\n"), strict=strict)))


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


# --------------------------------------------------------------------------- #
# Hy-Tek `.hy3` builders (130-char records: 128 data columns + a 2-digit checksum)
# --------------------------------------------------------------------------- #


def hy3_rec(*fields: tuple[int, str]) -> str:
    """Build a valid 130-char `.hy3` line, placing ``(start_1indexed, text)`` fields.

    The trailing 2-digit checksum is computed over the data body so the line
    passes :func:`tunas._parser.checksum.checksum_matches`.
    """
    buf = [" "] * 128
    for start, text in fields:
        for i, ch in enumerate(text):
            buf[start - 1 + i] = ch
    body = "".join(buf)
    return body + hy3_checksum(body.encode("cp1252"))


def parse_hy3_lines(lines: list[str], *, strict: bool = False) -> MeetArchive:
    """Parse `.hy3` record lines from an in-memory stream into its single MeetArchive."""
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
    citizen: str = "",
) -> str:
    fields = [
        (1, "D1"),
        (3, sex),
        (4, number.rjust(5)),
        (9, last),
        (29, first),
        (49, preferred),
        (70, member),
        (89, birth),
        (98, age.rjust(2)),
    ]
    if middle:
        fields.append((69, middle))
    if citizen:
        fields.append((113, citizen))
    return hy3_rec(*fields)


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
) -> str:
    return hy3_rec(
        (1, "E1"),
        (4, number.rjust(5)),
        (15, event_sex),
        (16, dist.rjust(6)),
        (22, stroke),
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
    fields = [
        (1, "E2"),
        (3, rnd),
        (5, time.rjust(7)),
        (12, course),
        (22, heat.rjust(2)),
        (25, lane.rjust(2)),
        (31, place.rjust(3)),
        (88, date),
    ]
    if status:
        fields.append((13, status))
    if dqcode:
        fields.append((14, dqcode))
    for col, w in ((38, watch1), (46, watch2), (54, watch3)):
        if w:
            fields.append((col, w.rjust(7)))
    return hy3_rec(*fields)


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
    fields = [
        (1, "F2"),
        (3, rnd),
        (6, time.rjust(6)),
        (12, course),
        (22, heat.rjust(2)),
        (25, lane.rjust(2)),
        (31, place.rjust(3)),
        (103, date),
    ]
    if status:
        fields.append((13, status))
    if dqcode:
        fields.append((14, dqcode))
    return hy3_rec(*fields)


def f3_slot(sex: str, number: str, last5: str, rnd: str, leg: str) -> str:
    """Build one 13-char F3 athlete slot."""
    return sex + number.rjust(5) + last5.ljust(5) + rnd + leg


def f3(*slots: str) -> str:
    """Build an F3 record from up to 8 :func:`f3_slot` strings."""
    fields = [(1, "F3")]
    for i, slot in enumerate(slots):
        fields.append((3 + i * 13, slot))
    return hy3_rec(*fields)


def g1_block(rnd: str, counter: int, time: str) -> str:
    """Build one 11-char G1 split block (round + distance counter + cumulative time)."""
    return rnd + str(counter).rjust(2) + time.rjust(8)


def g1(*blocks: str) -> str:
    """Build a G1 splits record from up to 11 :func:`g1_block` strings."""
    fields = [(1, "G1")]
    for i, block in enumerate(blocks):
        fields.append((3 + i * 11, block))
    return hy3_rec(*fields)


def h1(*, code: str = "3D", text: str = "Scissors kick") -> str:
    return hy3_rec((1, "H1"), (3, code), (5, text))


@pytest.fixture(autouse=True)
def _clear_standards_cache() -> Iterator[None]:
    """Keep the lazily-loaded standards index isolated between tests."""
    _load_index.cache_clear()
    yield
    _load_index.cache_clear()
