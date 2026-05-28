"""Immutable swim time value type with centisecond precision."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Time"]


@dataclass(order=True, frozen=True, slots=True)
class Time:
    """An immutable, hashable swim time with centisecond precision.

    Stored internally as a non-negative centiseconds integer. Faster times compare
    as less than slower times (i.e. smaller values indicate faster swims). Supports
    addition and subtraction between `Time` instances.

    String formatting returns `"M:SS.HH"` if the time is at least one minute, or
    `"SS.HH"` if under a minute. The formatted string zero-pads seconds and hundredths
    but does not pad the minute component.
    """

    centiseconds: int

    def __post_init__(self) -> None:
        if self.centiseconds < 0:
            raise ValueError(f"Time cannot be negative: {self.centiseconds}")

    @classmethod
    def parse(cls, s: str) -> Time:
        """Parse a swim-time string formatted as `[MM:]SS.HH` or `[M:]SS.HH`.

        Strips leading/trailing whitespace. Tolerates 1- or 2-digit minutes and
        seconds; fractions of a second are taken to centisecond precision, with
        any extra digits rounded to the nearest hundredth (e.g. ``"1:04.875"`` ->
        ``1:04.88``).

        Args:
            s: The time string to parse (e.g., `"1:04.87"`, `"23.4"`, `"8.23"`).

        Returns:
            A new `Time` instance with the parsed centiseconds duration.

        Raises:
            ValueError: If the string is empty, lacks a decimal point, contains
                non-numeric digits, or has more than two segments separated by colons.
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
        if len(frac_str) <= 2:
            hundredths = int((frac_str + "00")[:2])  # 1- or 2-digit fraction: exact
        else:
            # Round any extra precision to the nearest hundredth; a value that
            # rounds up to 100 carries cleanly since we store total centiseconds.
            hundredths = round(int(frac_str) / 10 ** len(frac_str) * 100)
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
