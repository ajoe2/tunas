"""Fixed-width field extraction for SDIF records.

``Record`` slices a padded 160-character line by 1-indexed ``start/length``.
The free functions interpret raw field text into typed values, returning a
``(tag, value)`` pair so the engine can dispose of blanks, malformed values, and
unknown codes per the M1/M2 error model.
"""

from __future__ import annotations

import datetime
from enum import StrEnum

from tunas.enums import Course, ResultStatus
from tunas.time import Time

__all__ = [
    "Record",
    "RECORD_WIDTH",
    "course_value",
    "time_value",
    "date_value",
    "int_value",
    "decimal_value",
    "code_value",
    "event_age_value",
    "DQ_COURSE",
]

RECORD_WIDTH = 160
DQ_COURSE = "X"  # COURSE Code 013 "X" = disqualified

# TIME Code 020 — outcome codes that may appear in a time field.
_TIME_CODES: dict[str, ResultStatus] = {
    "NT": ResultStatus.NT,
    "NS": ResultStatus.NS,
    "DNF": ResultStatus.DNF,
    "DQ": ResultStatus.DQ,
    "SCR": ResultStatus.SCR,
}

# COURSE Code 013 — both numeric and alphabetic forms.
_COURSE_MAP: dict[str, Course] = {
    "1": Course.SCM,
    "S": Course.SCM,
    "2": Course.SCY,
    "Y": Course.SCY,
    "3": Course.LCM,
    "L": Course.LCM,
}

# EVENT AGE Code 025 open-ended markers: "UN"der (no lower bound) / "OV"er (no upper).
_AGE_OPEN_LOW = "UN"
_AGE_OPEN_HIGH = "OV"


class Record:
    """A single padded SDIF line, sliced by 1-indexed ``start/length``."""

    __slots__ = ("line", "line_no", "source", "type")

    def __init__(self, line: str, line_no: int, source: str) -> None:
        self.line = line
        self.line_no = line_no
        self.source = source
        self.type = line[0:2]

    def raw(self, start: int, length: int) -> str:
        """Raw (unstripped) slice for a 1-indexed ``start/length`` field."""
        return self.line[start - 1 : start - 1 + length]

    def text(self, start: int, length: int) -> str | None:
        """Stripped ALPHA field, or ``None`` if blank."""
        return self.raw(start, length).strip() or None


def course_value(raw: str) -> tuple[str, Course | None]:
    """Returns ``("blank"|"ok"|"dq"|"unknown", Course|None)``."""
    v = raw.strip().upper()
    if not v:
        return "blank", None
    if v == DQ_COURSE:
        return "dq", None
    course = _COURSE_MAP.get(v)
    if course is not None:
        return "ok", course
    return "unknown", None


def time_value(raw: str) -> tuple[str, Time | ResultStatus | None]:
    """Returns ``("blank"|"time"|"status"|"bad", Time|ResultStatus|None)``."""
    v = raw.strip()
    if not v:
        return "blank", None
    status = _TIME_CODES.get(v.upper())
    if status is not None:
        return "status", status
    try:
        return "time", Time.parse(v)
    except ValueError:
        return "bad", None


def date_value(raw: str) -> tuple[str, datetime.date | None]:
    """Parse an ``MMDDYYYY`` date. Returns ``("blank"|"date"|"bad", date|None)``."""
    v = raw.strip()
    if not v:
        return "blank", None
    if len(v) != 8 or not v.isdigit():
        return "bad", None
    month, day, year = int(v[0:2]), int(v[2:4]), int(v[4:8])
    try:
        return "date", datetime.date(year, month, day)
    except ValueError:
        return "bad", None


def int_value(raw: str) -> tuple[str, int | None]:
    """Returns ``("blank"|"int"|"bad", int|None)``."""
    v = raw.strip()
    if not v:
        return "blank", None
    try:
        return "int", int(v)
    except ValueError:
        return "bad", None


def decimal_value(raw: str) -> tuple[str, float | None]:
    """Returns ``("blank"|"dec"|"bad", float|None)``."""
    v = raw.strip()
    if not v:
        return "blank", None
    try:
        return "dec", float(v)
    except ValueError:
        return "bad", None


def code_value[E: StrEnum](raw: str, enum_cls: type[E]) -> tuple[str, E | None]:
    """Resolve a code-table value. Returns ``("blank"|"ok"|"unknown", member|None)``."""
    v = raw.strip()
    if not v:
        return "blank", None
    try:
        return "ok", enum_cls(v)
    except ValueError:
        return "unknown", None


def event_age_value(raw: str) -> tuple[str, int | None, int | None]:
    """Parse EVENT AGE Code 025 (4 bytes).

    Returns ``("blank"|"ok"|"bad", min_age, max_age)``. ``"UN"``/``"OV"`` open
    ends map to ``None``.
    """
    v = raw.strip()
    if not v:
        return "blank", None, None
    field = raw[:4]
    lo_s, hi_s = field[0:2].strip().upper(), field[2:4].strip().upper()

    def one(token: str, open_marker: str) -> tuple[bool, int | None]:
        if token in (open_marker, ""):
            return True, None
        if token.isdigit():
            return True, int(token)
        return False, None

    lo_ok, lo = one(lo_s, _AGE_OPEN_LOW)
    hi_ok, hi = one(hi_s, _AGE_OPEN_HIGH)
    if not (lo_ok and hi_ok):
        return "bad", None, None
    return "ok", lo, hi
