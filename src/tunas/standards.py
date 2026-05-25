"""USA Swimming motivational time standards (B through AAAA) bundled offline."""

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
    """USA Swimming motivational standards ordered slowest (B) to fastest (AAAA)."""

    B = 1
    BB = 2
    A = 3
    AA = 4
    AAA = 5
    AAAA = 6

    def display(self) -> str:
        """Human-readable standard name (e.g., "AAAA")."""
        return self.name


# Single-year age groups as (inclusive upper bound, label) ordered youngest first.
_AGE_GROUPS: tuple[tuple[int, str], ...] = (
    (10, "10_U"),
    (12, "11_12"),
    (14, "13_14"),
    (16, "15_16"),
)
_OLDEST_AGE_GROUP = "17_18"


def _age_group(age: int) -> str:
    for upper, label in _AGE_GROUPS:
        if age <= upper:
            return label
    return _OLDEST_AGE_GROUP


@functools.cache
def _load_index() -> dict[tuple[str, str, str, str], int]:
    """Load bundled JSON into `{(standard, age_group, sex, event): centiseconds}` dict."""
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


def _cutoff(standard: TimeStandard, event: Event, age: int, sex: Sex) -> int | None:
    """Cutoff in centiseconds for one (standard, event, age, sex), or ``None``."""
    return _load_index().get((standard.name, _age_group(age), sex.value, event.name))


def qualifies_for(time: Time, event: Event, age: int, sex: Sex) -> TimeStandard | None:
    """Determine the fastest USA Swimming motivational standard achieved for the given event,
    age, and sex.

    Uses a youngest-first lookup for the swimmer's age group (10 & Under, 11-12, 13-14, 15-16,
    17-18).

    Args:
        time: The swimmer's time.
        event: The event.
        age: The swimmer's age in years.
        sex: The swimmer's sex (must be MALE or FEMALE).

    Returns:
        The fastest achieved `TimeStandard` (from slowest B to fastest AAAA), or `None`
        if the time does not qualify for any motivational standard.

    Raises:
        ValueError: If `sex` is `Sex.MIXED`.
    """
    _check_sex(sex)
    best: TimeStandard | None = None
    for standard in TimeStandard:
        cutoff = _cutoff(standard, event, age, sex)
        if cutoff is not None and time.centiseconds <= cutoff:
            best = standard
    return best


def all_qualified(time: Time, event: Event, age: int, sex: Sex) -> list[TimeStandard]:
    """Retrieve all USA Swimming motivational standards qualified for by the given time.

    Args:
        time: The swimmer's time.
        event: The event.
        age: The swimmer's age in years.
        sex: The swimmer's sex (must be MALE or FEMALE).

    Returns:
        A list of all qualified `TimeStandard` values, ordered from slowest (B) to fastest (AAAA).

    Raises:
        ValueError: If `sex` is `Sex.MIXED`.
    """
    _check_sex(sex)
    return [
        standard
        for standard in TimeStandard
        if (cutoff := _cutoff(standard, event, age, sex)) is not None
        and time.centiseconds <= cutoff
    ]


def standard_time(standard: TimeStandard, event: Event, age: int, sex: Sex) -> Time | None:
    """Get the cutoff time required to achieve a specific motivational standard.

    Args:
        standard: The target motivational standard.
        event: The event.
        age: The swimmer's age in years.
        sex: The swimmer's sex (must be MALE or FEMALE).

    Returns:
        The cutoff `Time` required to achieve the standard, or `None` if the standard
        is undefined for the event/age/sex combination.

    Raises:
        ValueError: If `sex` is `Sex.MIXED`.
    """
    _check_sex(sex)
    cutoff = _cutoff(standard, event, age, sex)
    return Time(cutoff) if cutoff is not None else None
