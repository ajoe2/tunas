"""USA Swimming motivational time standards (B through AAAA), bundled offline."""

from __future__ import annotations

import functools
import importlib.resources
import json
from enum import IntEnum

from tunas.enums import Sex
from tunas.event import Event
from tunas.exceptions import StandardsError
from tunas.time import Time

__all__ = ["TimeStandard", "qualifies_for", "all_qualified", "standard_time"]

_DATA_FILE = "standards-2025-2028.json"


class TimeStandard(IntEnum):
    """USA Swimming motivational standards, ordered slowest (B) to fastest (AAAA)."""

    B = 1
    BB = 2
    A = 3
    AA = 4
    AAA = 5
    AAAA = 6

    def display(self) -> str:
        return self.name


def _age_group(age: int) -> str:
    if age <= 10:
        return "10_U"
    if age <= 12:
        return "11_12"
    if age <= 14:
        return "13_14"
    if age <= 16:
        return "15_16"
    return "17_18"


@functools.cache
def _load_index() -> dict[tuple[str, str, str, str], int]:
    """Load the bundled JSON into ``{(standard, age_group, sex, event): centiseconds}``."""
    try:
        raw = (
            importlib.resources.files("tunas._data")
            .joinpath(_DATA_FILE)
            .read_text(encoding="utf-8")
        )
        data = json.loads(raw)
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        raise StandardsError(f"could not load bundled standards: {exc}") from exc

    index: dict[tuple[str, str, str, str], int] = {}
    for row in data["standards"]:
        key = (row["standard"], row["age_group"], row["sex"], row["event"])
        if key in index:
            raise StandardsError(f"duplicate standard row: {key}")
        index[key] = int(row["cutoff_centiseconds"])
    return index


def _check_sex(sex: Sex) -> None:
    if sex is Sex.MIXED:
        raise ValueError("time standards are defined for MALE/FEMALE only, not MIXED")


def qualifies_for(time: Time, event: Event, age: int, sex: Sex) -> TimeStandard | None:
    """The fastest standard ``time`` achieves for the event/age/sex, or ``None``."""
    _check_sex(sex)
    index = _load_index()
    age_group = _age_group(age)
    best: TimeStandard | None = None
    for standard in TimeStandard:
        cutoff = index.get((standard.name, age_group, sex.value, event.name))
        if cutoff is not None and time.centiseconds <= cutoff:
            best = standard
    return best


def all_qualified(time: Time, event: Event, age: int, sex: Sex) -> list[TimeStandard]:
    """Every standard ``time`` qualifies for, ordered slowest first."""
    _check_sex(sex)
    index = _load_index()
    age_group = _age_group(age)
    return [
        standard
        for standard in TimeStandard
        if (cutoff := index.get((standard.name, age_group, sex.value, event.name))) is not None
        and time.centiseconds <= cutoff
    ]


def standard_time(standard: TimeStandard, event: Event, age: int, sex: Sex) -> Time | None:
    """The cutoff time required to achieve ``standard``, or ``None`` if undefined."""
    _check_sex(sex)
    index = _load_index()
    cutoff = index.get((standard.name, _age_group(age), sex.value, event.name))
    return Time(cutoff) if cutoff is not None else None
