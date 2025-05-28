"""
Contains custom time class used to represent swimming times.
"""

from __future__ import annotations  # Enable future annotations
from typing import Optional


def create_time_from_str(time_str: str) -> Time:
    """
    Create and return a time object corresponding to time_str which should be in
    mm:ss.hh format.
    """
    minute_str, second_str, hundredth_str = "0", "0", "0"
    minute, second, hundredth = 0, 0, 0

    # Parse string
    first_split = time_str.split(":")
    if len(first_split) == 2:
        minute_str = first_split[0]
    next_split = first_split[-1].split(".")
    if len(next_split) != 2:
        raise Exception(f"Invalid time string: '{time_str}'")
    second_str = next_split[0]
    hundredth_str = next_split[1]
    try:
        minute = int(minute_str)
        second = int(second_str)
        hundredth = int(hundredth_str)
    except:
        raise Exception(f"Invalid time string: '{time_str}'")

    return Time(minute, second, hundredth)


class Time:
    """
    Custom time representation for swim meet results.
    """

    def __init__(
        self,
        minute=0,
        second=0,
        hundredth=0,
    ) -> None:
        """
        Create a time oject. There are two ways to create a time object:
        1) Input minute, second, and hundredth
        2) Input a time_str. Must be in m:ss.hh or m:ss:hh* format.

        Keyword arguments:
        minute -- the minutes component (default 0)
        second -- the seconds component (default 0)
        hundredth -- the hundredths component (default 0)
        time_str -- time string
        """
        self.set_minute(minute)
        self.set_second(second)
        self.set_hundredth(hundredth)

    def __str__(self) -> str:
        """
        Return string representation of time object. Return empty
        string if time is equal to 0.

        >>> t = Time(1, 15, 23)
        >>> print(t)
        1:15.23
        >>> t2 = Time(0, 32, 10)
        >>> print(t2)
        32.10
        >>> t3 = Time(0, 0, 0)
        >>> str(t3) == ""
        True
        """
        if (
            self.get_hundredth() == 0
            and self.get_minute() == 0
            and self.get_second() == 0
        ):
            return ""
        m = str(self.get_minute())
        s = str(self.get_second()).zfill(2)
        h = str(self.get_hundredth()).zfill(2)
        if m == "0":
            return f"{s}.{h}"
        else:
            return f"{m}:{s}.{h}"

    def __repr__(self) -> str:
        """
        Return representation of time object.

        >>> t = Time(1, 15, 23)
        >>> t
        Time(1, 15, 23)
        >>> t2 = Time(0, 32, 10)
        >>> t2
        Time(0, 32, 10)
        """
        return f"Time({self.minute}, {self.second}, {self.hundredth})"

    def __gt__(self, other_time: Optional[Time]) -> bool:
        """
        Return true if self is a longer time than other_time.

        Keyword arguments:
        other_time -- Time object that is being compared against
        """
        if other_time is None:
            return False

        # Compare minutes
        if self.get_minute() > other_time.get_minute():
            return True
        if self.get_minute() < other_time.get_minute():
            return False
        # Compare seconds
        if self.get_second() > other_time.get_second():
            return True
        if self.get_second() < other_time.get_second():
            return False
        # Compare hundredths
        if self.get_hundredth() > other_time.get_hundredth():
            return True
        if self.get_hundredth() < other_time.get_hundredth():
            return False
        # Self must equal other_time so return false
        return False

    def __lt__(self, other_time: Optional[Time]) -> bool:
        """
        Return true if self is a shorter time than other_time.

        Keyword arguments:
        other_time -- Time object that is being compared against
        """
        return other_time > self

    def __eq__(self, other_time: Optional[Time]) -> bool:
        """
        Return true if self is equal to other_time.

        Keyword arguments:
        other_time -- Time object that is being compared against
        """
        if other_time is None:
            return False
        return (
            self.get_minute() == other_time.get_minute()
            and self.get_second() == other_time.get_second()
            and self.get_hundredth() == other_time.get_hundredth()
        )

    def __ge__(self, other_time: Time) -> bool:
        """
        Return true if self is a greater than or equal time to
        other_time.

        Keyword arguments:
        other_time -- Time object that is being compared against
        """
        return self > other_time or self == other_time

    def __le__(self, other_time: Time) -> bool:
        """
        Return true if self is a less than or equal time to
        other_time.

        Keyword arguments:
        other_time -- Time object that is being compared against
        """
        return other_time >= self

    def __add__(self, other_time: Time) -> Time:
        """
        Return the sum of self and other_time.

        Keyword arguments:
        other_time -- Time object that is being added to self.
        """
        hundredth = self.hundredth + other_time.get_hundredth()
        second = self.second + other_time.get_second()
        minute = self.minute + other_time.get_minute()
        if hundredth >= 100:
            hundredth = hundredth % 100
            second += 1
        if second >= 60:
            second = second % 60
            minute += 1
        return Time(minute, second, hundredth)

    def __sub__(self, other_time: Time) -> Time:
        """
        Return self minus other_time.

        Keyword arguments:
        other_time -- Time object that is being subtracted from self.
        """
        if other_time > self:
            raise Exception("Cannot subtract larger valued time")
        hundredth = self.get_hundredth()
        second = self.get_second()
        minute = self.get_minute()
        t_hundredth = other_time.get_hundredth()
        t_second = other_time.get_second()
        t_minute = other_time.get_minute()
        if hundredth < t_hundredth:
            second = second - 1
            hundredth = hundredth + 100
        hundredth = hundredth - t_hundredth
        if second < t_second:
            minute = minute - 1
            second = second + 60
        second = second - t_second
        minute = minute - t_minute
        return Time(minute, second, hundredth)

    def set_minute(self, m: int) -> None:
        """
        Verify and set self.minute attribute
        """
        assert type(m) == int, f"Minute should be an integer: {m}"
        assert 0 <= m and m < 60, f"Invalid minute: {m}"
        self.minute = m

    def set_second(self, s: int) -> None:
        """
        Verify and set self.second attribute
        """
        assert type(s) == int, f"Seconds should be an integer: {s}"
        assert 0 <= s and s < 60, f"Invalid seconds: {s}"
        self.second = s

    def set_hundredth(self, h: int) -> None:
        """
        Verify and set self.hundredth attribute
        """
        assert type(h) == int, f"Hundredths should be an integer: {h}"
        assert 0 <= h and h < 100, f"Invalid hundredths: {h}"
        self.hundredth = h

    def get_minute(self) -> int:
        """
        Return self.minute attribute.
        """
        return self.minute

    def get_second(self) -> int:
        """
        Return self.second attribute.
        """
        return self.second

    def get_hundredth(self) -> int:
        """
        Return self.hundredth attribute.
        """
        return self.hundredth
