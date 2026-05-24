"""The :class:`Time` value type — a swim time stored with centisecond precision."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Time"]


@dataclass(order=True, frozen=True, slots=True)
class Time:
    """An immutable, hashable swim time.

    Stored internally as a single non-negative ``centiseconds`` integer (an
    unbounded ``int``, so open-water marathon times are safe). Faster times
    compare *less than* slower times.
    """

    centiseconds: int

    def __post_init__(self) -> None:
        if self.centiseconds < 0:
            raise ValueError(f"Time cannot be negative: {self.centiseconds}")

    @classmethod
    def parse(cls, s: str) -> Time:
        """Parse a ``[MM:]SS.HH`` swim-time string.

        Whitespace is stripped. Empty or malformed strings raise ``ValueError``.

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
        return self.centiseconds // 6000

    @property
    def second(self) -> int:
        return (self.centiseconds // 100) % 60

    @property
    def hundredth(self) -> int:
        return self.centiseconds % 100

    @property
    def total_seconds(self) -> float:
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
