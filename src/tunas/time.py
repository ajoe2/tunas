"""Immutable swim time value type with centisecond precision."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Time"]


@dataclass(order=True, frozen=True, slots=True)
class Time:
    """An immutable, hashable swim time with centisecond precision.

    Stored internally as a non-negative centiseconds integer (unbounded int).
    Faster times compare as less than slower times. String formatting uses `[M:]SS.HH`
    (e.g., "1:04.87" or "23.45"), which round-trips with `parse`. Supports addition
    and subtraction (subtraction raising ValueError if the result is negative).
    """

    centiseconds: int

    def __post_init__(self) -> None:
        if self.centiseconds < 0:
            raise ValueError(f"Time cannot be negative: {self.centiseconds}")

    @classmethod
    def parse(cls, s: str) -> Time:
        """Parse a `[MM:]SS.HH` swim-time string.

        Strips whitespace. Raises ValueError for empty or malformed strings.

        >>> Time.parse("1:23.45")
        Time(centiseconds=8345)
        """
        raw = s.strip()
        if not raw:
            raise ValueError(f"Invalid time string: {s!r}")

        parts = raw.split(":")
        if len(parts) == 1:
            minutes_str, sec_part = "0", parts[0]
        elif len(parts) == 2:
            minutes_str, sec_part = parts
        else:
            raise ValueError(f"Invalid time string: {s!r}")

        if "." not in sec_part:
            raise ValueError(f"Invalid time string: {s!r}")
        seconds_str, frac_str = sec_part.split(".", 1)

        if not (minutes_str.isdigit() and seconds_str.isdigit() and frac_str.isdigit()):
            raise ValueError(f"Invalid time string: {s!r}")

        minutes = int(minutes_str)
        seconds = int(seconds_str)
        hundredths = int((frac_str + "00")[:2])  # tolerate 1- or 2-digit fractions
        return cls(minutes * 6000 + seconds * 100 + hundredths)

    @property
    def minute(self) -> int:
        """Whole-minute component (`centiseconds // 6000`)."""
        return self.centiseconds // 6000

    @property
    def second(self) -> int:
        """Seconds within the minute (0-59)."""
        return (self.centiseconds // 100) % 60

    @property
    def hundredth(self) -> int:
        """Hundredths-of-a-second component (0-99)."""
        return self.centiseconds % 100

    @property
    def total_seconds(self) -> float:
        """The whole time expressed as seconds (`centiseconds / 100`)."""
        return self.centiseconds / 100

    def __str__(self) -> str:
        if self.minute:
            return f"{self.minute}:{self.second:02d}.{self.hundredth:02d}"
        return f"{self.second}.{self.hundredth:02d}"

    def __add__(self, other: Time) -> Time:
        if not isinstance(other, Time):
            return NotImplemented
        return Time(self.centiseconds + other.centiseconds)

    def __sub__(self, other: Time) -> Time:
        if not isinstance(other, Time):
            return NotImplemented
        result = self.centiseconds - other.centiseconds
        if result < 0:
            raise ValueError("Cannot subtract a larger Time from a smaller one")
        return Time(result)
