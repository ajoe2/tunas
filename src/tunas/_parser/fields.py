"""Fixed-width field extraction for SDIF records."""

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
    """A padded SDIF line sliced by 1-indexed start/length."""

    __slots__ = ("line", "line_no", "source", "type")

    def __init__(self, line: str, line_no: int, source: str) -> None:
        self.line = line
        self.line_no = line_no
        self.source = source
        self.type = line[0:2]

    def raw(self, start: int, length: int) -> str:
        """Raw unstripped slice for a 1-indexed start/length field."""
        return self.line[start - 1 : start - 1 + length]

    def text(self, start: int, length: int) -> str | None:
        """Stripped ALPHA field, or None if blank."""
        return self.raw(start, length).strip() or None


def course_value(raw: str) -> tuple[str, Course | None]:
    """Parse and resolve a course value from a raw fixed-width string.

    Args:
        raw: The raw fixed-width string containing a course code.

    Returns:
        A tuple of `(status, course)` where `status` is one of:
        - `"ok"`: Successfully parsed; `course` is a `Course` enum.
        - `"blank"`: The field was blank or whitespace-only; `course` is `None`.
        - `"dq"`: A disqualified course sentinel `"X"`; `course` is `None`.
        - `"unknown"`: An invalid or unrecognized course code; `course` is `None`.
    """
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
    """Parse and resolve a swim time or non-time status from a raw fixed-width string.

    Args:
        raw: The raw fixed-width string containing a time or non-time code.

    Returns:
        A tuple of `(status, value)` where `status` is one of:
        - `"time"`: Successfully parsed; `value` is a `Time` instance.
        - `"status"`: Recognized non-time outcome (e.g. `"NS"`, `"DQ"`); `value` is a `ResultStatus`.
        - `"blank"`: The field was blank; `value` is `None`.
        - `"bad"`: An unparseable or invalid time string; `value` is `None`.
    """
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
    """Parse a date string formatted as `MMDDYYYY` into a date object.

    Args:
        raw: The raw 8-character fixed-width string.

    Returns:
        A tuple of `(status, date)` where `status` is one of:
        - `"date"`: Successfully parsed; `date` is a `datetime.date`.
        - `"blank"`: The field was blank; `date` is `None`.
        - `"bad"`: Malformed date format or an invalid date (e.g. 13th month); `date` is `None`.
    """
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
    """Parse an integer value from a raw fixed-width string.

    Args:
        raw: The raw fixed-width string.

    Returns:
        A tuple of `(status, value)` where `status` is one of:
        - `"int"`: Successfully parsed; `value` is an `int`.
        - `"blank"`: The field was blank; `value` is `None`.
        - `"bad"`: Non-numeric or otherwise unparseable string; `value` is `None`.
    """
    v = raw.strip()
    if not v:
        return "blank", None
    try:
        return "int", int(v)
    except ValueError:
        return "bad", None


def decimal_value(raw: str) -> tuple[str, float | None]:
    """Parse a decimal/float value from a raw fixed-width string.

    Args:
        raw: The raw fixed-width string.

    Returns:
        A tuple of `(status, value)` where `status` is one of:
        - `"dec"`: Successfully parsed; `value` is a `float`.
        - `"blank"`: The field was blank; `value` is `None`.
        - `"bad"`: Unparseable non-numeric float string; `value` is `None`.
    """
    v = raw.strip()
    if not v:
        return "blank", None
    try:
        return "dec", float(v)
    except ValueError:
        return "bad", None


def code_value[E: StrEnum](raw: str, enum_cls: type[E]) -> tuple[str, E | None]:
    """Resolve a raw code-table string into a specific StrEnum class member.

    Args:
        raw: The raw fixed-width string.
        enum_cls: The specific StrEnum subclass to resolve into.

    Returns:
        A tuple of `(status, enum_member)` where `status` is one of:
        - `"ok"`: Code successfully matched; `enum_member` is a member of `enum_cls`.
        - `"blank"`: The field was blank; `enum_member` is `None`.
        - `"unknown"`: Code is not a valid member of `enum_cls`; `enum_member` is `None`.
    """
    v = raw.strip()
    if not v:
        return "blank", None
    try:
        return "ok", enum_cls(v)
    except ValueError:
        return "unknown", None


def event_age_value(raw: str) -> tuple[str, int | None, int | None]:
    """Parse a 4-byte EVENT AGE Code 025 field into minimum and maximum age bounds.

    Open-ended bounds represented by sentinels (e.g. `'UN'` for under or `'OV'` for over)
    map to `None` to indicate no lower/upper limit.

    Args:
        raw: The raw 4-character fixed-width string.

    Returns:
        A tuple of `(status, min_age, max_age)` where `status` is one of:
        - `"ok"`: Parsing succeeded; `min_age` and `max_age` are bounds (each `int` or `None`).
        - `"blank"`: The field was blank; bounds are both `None`.
        - `"bad"`: The field contained malformed or unrecognized characters; bounds are both `None`.
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
