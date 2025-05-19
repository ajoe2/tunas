"""
Helper methods and constants. Includes a custom time class,
functions for processing input, and meet result constants.
"""

from __future__ import annotations
from enum import Enum


class Organization(Enum):
    """
    All organizations defined under the USA Swimming Interchange
    Format (ORG Code 001).
    """

    USA_SWIMMING = 1
    MASTERS = 2
    NCAA = 3
    NCAA_DIV_I = 4
    NCAA_DIV_II = 5
    NCAA_DIV_III = 6
    YMCA = 7
    FINA = 8
    HIGH_SCHOOL = 9


class LSC(Enum):
    """
    List of all LSCs. Follows convention used in USA Swimming
    Interchange Format (LSC Code 002).
    """

    ADIRONDACK = "AD"
    ALASKA = "AK"
    ALLEGHENY_MOUNTAIN = "AM"
    ARKANSAS = "AR"
    ARIZONA = "AZ"
    BORDER = "BD"
    SOUTHERN_CALIFORNIA = "CA"
    CENTRAL_CALIFORNIA = "CC"
    COLORADO = "CO"
    CONNECTICUT = "CT"
    FLORIDA_GOLD_COAST = "FG"
    FLORIDA = "FL"
    GEORGIA = "GA"
    GULF = "GU"
    HAWAII = "HI"
    IOWA = "IA"
    INLAND_EMPIRE = "IE"
    ILLINOIS = "IL"
    INDIANA = "IN"
    KENTUCKY = "KY"
    LOUISIANA = "LA"
    LAKE_ERIE = "LE"
    MIDDLE_ATLANTIC = "MA"
    MARYLAND = "MD"
    MAINE = "ME"
    MICHIGAN = "MI"
    MINNESOTA = "MN"
    METROPOLITAN = "MR"
    MISSISSIPPI = "MS"
    MONTANA = "MT"
    MISSOURI_VALLEY = "MV"
    MIDWESTERN = "MW"
    NORTH_CAROLINA = "NC"
    NORTH_DAKOTA = "ND"
    NEW_ENGLAND = "NE"
    NIAGARA = "NI"
    NEW_JERSEY = "NJ"
    NEW_MEXICO = "NM"
    NORTH_TEXAS = "NT"
    OHIO = "OH"
    OKLAHOMA = "OK"
    OREGON = "OR"
    OZARK = "OZ"
    PACIFIC = "PC"
    PACIFIC_NORTHWEST = "PN"
    POTOMAC_VALLEY = "PV"
    SOUTH_CAROLINA = "SC"
    SOUTH_DAKOTA = "SD"
    SOUTHEASTERN = "SE"
    SAN_DIEGO_IMPERIAL = "SI"
    SIERRA_NEVADA = "SN"
    SNAKE_RIVER = "SR"
    SOUTH_TEXAS = "ST"
    UTAH = "UT"
    VIRGINIA = "VA"
    WISCONSIN = "WI"
    WEST_TEXAS = "WT"
    WEST_VIRGINIA = "WV"
    WYOMING = "WY"


class Stroke(Enum):
    """
    Valid strokes. Follows convention used in USA Swimming
    Interchange Format (STROKE Code 012).
    """

    FREESTYLE = 1
    BACKSTROKE = 2
    BREASTSTROKE = 3
    BUTTERFLY = 4
    INDIVIDUAL_MEDLEY = 5
    FREESTYLE_RELAY = 6
    MEDLEY_RELAY = 7

    def __str__(self) -> str:
        match self:
            case Stroke.FREESTYLE:
                return "Free"
            case Stroke.BACKSTROKE:
                return "Back"
            case Stroke.BREASTSTROKE:
                return "Breast"
            case Stroke.BUTTERFLY:
                return "Fly"
            case Stroke.INDIVIDUAL_MEDLEY:
                return "IM"
            case Stroke.FREESTYLE_RELAY:
                return "Free Relay"
            case Stroke.MEDLEY_RELAY:
                return "Medley Relay"

    def short(self) -> str:
        """
        Short string representation of stroke.
        """
        match self:
            case Stroke.FREESTYLE:
                return "FR"
            case Stroke.BACKSTROKE:
                return "BK"
            case Stroke.BREASTSTROKE:
                return "BR"
            case Stroke.BUTTERFLY:
                return "FL"
            case Stroke.INDIVIDUAL_MEDLEY:
                return "IM"
            case Stroke.FREESTYLE_RELAY:
                return "FR-R"
            case Stroke.MEDLEY_RELAY:
                return "IM-R"


class Session(Enum):
    """
    Swim meet sessions. Follows convention used in USA Swimming
    Interchange Format (PRELIMS/FINALS Code 019).
    """

    PRELIMS = "P"
    FINALS = "F"
    SWIM_OFFS = "S"

    def __str__(self) -> str:
        return self.value


class Course(Enum):
    """
    Event course. The USA Swimming Interchange Format represents
    courses in two ways (COURSE Code 013). Here, we use the integer
    representation as the default and the character representation
    as the shortened string.
    """

    SCM = 1
    SCY = 2
    LCM = 3

    def __str__(self) -> str:
        return self.name

    def short(self) -> str:
        """
        Short string representation of course.
        """
        match self:
            case Course.SCM:
                return "S"
            case Course.SCY:
                return "Y"
            case Course.LCM:
                return "L"


class Sex(Enum):
    """
    Swimmer sex. Follows convention used in USA Swimming
    Interchange Format (SEX Code 010 and EVENT SEX Code 011).
    """

    MALE = "M"
    FEMALE = "F"
    MIXED = "X"

    def __str__(self) -> str:
        return self.value


class AgeGroup(Enum):
    """
    Swimmer age group. Each age group is represented by a min and
    max age.
    """

    AG_10_u = (0, 10)
    AG_11_12 = (11, 12)
    AG_13_14 = (13, 14)
    AG_15_16 = (15, 16)
    AG_17_18 = (17, 18)
    AG_SENIOR = (13, 1000)

    def __str__(self) -> str:
        match self:
            case AgeGroup.AG_10_u:
                return "10&u"
            case AgeGroup.AG_SENIOR:
                return "senior"
            case _:
                return f"{self.get_min_age()}-{self.get_max_age()}"

    def get_min_age(self) -> int:
        return self.value[0]

    def get_max_age(self) -> int:
        return self.value[1]


class Event(Enum):
    """
    Swim event. Each event is represented by a distance, stroke,
    and course.
    """

    FREE_25_SCY = (25, Stroke.FREESTYLE, Course.SCY)
    FREE_50_SCY = (50, Stroke.FREESTYLE, Course.SCY)
    FREE_100_SCY = (100, Stroke.FREESTYLE, Course.SCY)
    FREE_200_SCY = (200, Stroke.FREESTYLE, Course.SCY)
    FREE_400_SCY = (400, Stroke.FREESTYLE, Course.SCY)
    FREE_500_SCY = (500, Stroke.FREESTYLE, Course.SCY)
    FREE_800_SCY = (800, Stroke.FREESTYLE, Course.SCY)
    FREE_1000_SCY = (1000, Stroke.FREESTYLE, Course.SCY)
    FREE_1650_SCY = (1650, Stroke.FREESTYLE, Course.SCY)
    BACK_25_SCY = (25, Stroke.BACKSTROKE, Course.SCY)
    BACK_50_SCY = (50, Stroke.BACKSTROKE, Course.SCY)
    BACK_100_SCY = (100, Stroke.BACKSTROKE, Course.SCY)
    BACK_200_SCY = (200, Stroke.BACKSTROKE, Course.SCY)
    BREAST_25_SCY = (25, Stroke.BREASTSTROKE, Course.SCY)
    BREAST_50_SCY = (50, Stroke.BREASTSTROKE, Course.SCY)
    BREAST_100_SCY = (100, Stroke.BREASTSTROKE, Course.SCY)
    BREAST_200_SCY = (200, Stroke.BREASTSTROKE, Course.SCY)
    FLY_25_SCY = (25, Stroke.BUTTERFLY, Course.SCY)
    FLY_50_SCY = (50, Stroke.BUTTERFLY, Course.SCY)
    FLY_100_SCY = (100, Stroke.BUTTERFLY, Course.SCY)
    FLY_200_SCY = (200, Stroke.BUTTERFLY, Course.SCY)
    IM_100_SCY = (100, Stroke.INDIVIDUAL_MEDLEY, Course.SCY)
    IM_200_SCY = (200, Stroke.INDIVIDUAL_MEDLEY, Course.SCY)
    IM_400_SCY = (400, Stroke.INDIVIDUAL_MEDLEY, Course.SCY)
    FREE_25_SCM = (25, Stroke.FREESTYLE, Course.SCM)
    FREE_50_SCM = (50, Stroke.FREESTYLE, Course.SCM)
    FREE_100_SCM = (100, Stroke.FREESTYLE, Course.SCM)
    FREE_200_SCM = (200, Stroke.FREESTYLE, Course.SCM)
    FREE_400_SCM = (400, Stroke.FREESTYLE, Course.SCM)
    FREE_800_SCM = (800, Stroke.FREESTYLE, Course.SCM)
    FREE_1500_SCM = (1500, Stroke.FREESTYLE, Course.SCM)
    BACK_25_SCM = (25, Stroke.BACKSTROKE, Course.SCM)
    BACK_50_SCM = (50, Stroke.BACKSTROKE, Course.SCM)
    BACK_100_SCM = (100, Stroke.BACKSTROKE, Course.SCM)
    BACK_200_SCM = (200, Stroke.BACKSTROKE, Course.SCM)
    BREAST_25_SCM = (25, Stroke.BREASTSTROKE, Course.SCM)
    BREAST_50_SCM = (50, Stroke.BREASTSTROKE, Course.SCM)
    BREAST_100_SCM = (100, Stroke.BREASTSTROKE, Course.SCM)
    BREAST_200_SCM = (200, Stroke.BREASTSTROKE, Course.SCM)
    FLY_25_SCM = (25, Stroke.BUTTERFLY, Course.SCM)
    FLY_50_SCM = (50, Stroke.BUTTERFLY, Course.SCM)
    FLY_100_SCM = (100, Stroke.BUTTERFLY, Course.SCM)
    FLY_200_SCM = (200, Stroke.BUTTERFLY, Course.SCM)
    IM_100_SCM = (100, Stroke.INDIVIDUAL_MEDLEY, Course.SCM)
    IM_200_SCM = (200, Stroke.INDIVIDUAL_MEDLEY, Course.SCM)
    IM_400_SCM = (400, Stroke.INDIVIDUAL_MEDLEY, Course.SCM)
    FREE_50_LCM = (50, Stroke.FREESTYLE, Course.LCM)
    FREE_100_LCM = (100, Stroke.FREESTYLE, Course.LCM)
    FREE_200_LCM = (200, Stroke.FREESTYLE, Course.LCM)
    FREE_400_LCM = (400, Stroke.FREESTYLE, Course.LCM)
    FREE_800_LCM = (800, Stroke.FREESTYLE, Course.LCM)
    FREE_1500_LCM = (1500, Stroke.FREESTYLE, Course.LCM)
    BACK_50_LCM = (50, Stroke.BACKSTROKE, Course.LCM)
    BACK_100_LCM = (100, Stroke.BACKSTROKE, Course.LCM)
    BACK_200_LCM = (200, Stroke.BACKSTROKE, Course.LCM)
    BREAST_50_LCM = (50, Stroke.BREASTSTROKE, Course.LCM)
    BREAST_100_LCM = (100, Stroke.BREASTSTROKE, Course.LCM)
    BREAST_200_LCM = (200, Stroke.BREASTSTROKE, Course.LCM)
    FLY_50_LCM = (50, Stroke.BUTTERFLY, Course.LCM)
    FLY_100_LCM = (100, Stroke.BUTTERFLY, Course.LCM)
    FLY_200_LCM = (200, Stroke.BUTTERFLY, Course.LCM)
    IM_200_LCM = (200, Stroke.INDIVIDUAL_MEDLEY, Course.LCM)
    IM_400_LCM = (400, Stroke.INDIVIDUAL_MEDLEY, Course.LCM)

    def __str__(self) -> str:
        event_basic = f"{self.get_distance()} {self.get_stroke()}"
        return f"{event_basic: <10} {self.get_course()}"

    def get_distance(self) -> int:
        """
        Return distance of event.
        """
        return self.value[0]

    def get_stroke(self) -> Stroke:
        """
        Return stroke of event.
        """
        return self.value[1]

    def get_course(self) -> Course:
        """
        Return course of event.
        """
        return self.value[2]


class EventTimeClass(Enum):
    """
    Event time class. Follows convention used in the USA Swimming
    Interchange Format (EVENT TIME CLASS Code 014)
    """

    NO_LOWER_LIMIT = "U"
    NO_UPPER_LIMIT = "O"
    NOVICE = "1"
    B_STANDARD = "2"
    BB_STANDARD = "P"
    A_STANDARD = "3"
    AA_STANDARD = "4"
    AAA_STANDARD = "5"
    AAAA_STANDARD = "6"
    JUNIOR_STANDARD = "J"
    SENIOR_STANDARD = "S"


class State(Enum):
    """
    State encoding. Follows USPS state abbreviations.
    """

    ALABAMA = "AL"
    ALASKA = "AK"
    ARIZONA = "AZ"
    ARKANSAS = "AR"
    CALIFORNIA = "CA"
    COLORADO = "CO"
    CONNECTICUT = "CT"
    DELAWARE = "DE"
    DISTRICT_OF_COLUMBIA = "DC"
    FLORIDA = "FL"
    GEORGIA = "GA"
    HAWAII = "HI"
    IDAHO = "ID"
    ILLINOIS = "IL"
    INDIANA = "IN"
    IOWA = "IA"
    KANSAS = "KS"
    KENTUCKY = "KY"
    LOUISIANA = "LA"
    MAINE = "ME"
    MARYLAND = "MD"
    MASSACHUSETTS = "MA"
    MICHIGAN = "MI"
    MINNESOTA = "MN"
    MISSISSIPPI = "MS"
    MISSOURI = "MO"
    MONTANA = "MT"
    NEBRASKA = "NE"
    NEVADA = "NV"
    NEW_HAMPSHIRE = "NH"
    NEW_JERSEY = "NJ"
    NEW_MEXICO = "NM"
    NEW_YORK = "NY"
    NORTH_CAROLINA = "NC"
    NORTH_DAKOTA = "ND"
    OHIO = "OH"
    OKLAHOMA = "OK"
    OREGON = "OR"
    PENNSYLVANIA = "PA"
    PUERTO_RICO = "PR"
    RHODE_ISLAND = "RI"
    SOUTH_CAROLINA = "SC"
    SOUTH_DAKOTA  = "SD"
    TENNESSEE = "TN"
    TEXAS = "TX"
    UTAH = "UT"
    VERMONT = "VT"
    VIRGINIA = "VA"
    WASHINGTON = "WA"
    WEST_VIRGINIA = "WV"
    WISCONSIN = "WI"
    WYOMING = "WY"

    
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

    def __gt__(self, other_time: Time) -> bool:
        """
        Return true if self is a longer time than other_time.

        Keyword arguments:
        other_time -- Time object that is being compared against
        """
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

    def __lt__(self, other_time: Time) -> bool:
        """
        Return true if self is a shorter time than other_time.

        Keyword arguments:
        other_time -- Time object that is being compared against
        """
        return other_time > self

    def __eq__(self, other_time: Time) -> bool:
        """
        Return true if self is equal to other_time.

        Keyword arguments:
        other_time -- Time object that is being compared against
        """
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


def create_time_from_str(time_str: str) -> Time:
    """
    Return time object corresponding to time_str. Input string
    should be in mm:ss.hh format.

    Keyword arguments:
    time_str -- time string.
    """
    minute_str, second_str, hundredth_str = "0", "0", "0"
    minute, second, hundredth = 0, 0, 0

    # Parse string
    first_split = time_str.split(":")
    if len(first_split) == 2:
        minute_str = first_split[0]
    next_split = first_split[-1].split(".")
    if len(next_split) != 2:
        raise Exception(
            f"Invalid input: '{time_str}'. " + f"Should be in 'mm:ss.hh' format."
        )
    second_str = next_split[0]
    hundredth_str = next_split[1]
    try:
        minute = int(minute_str)
        second = int(second_str)
        hundredth = int(hundredth_str)
    except:
        raise Exception(f"Invalid input: '{time_str}'. " + f"Time is not a valid time.")

    return Time(minute, second, hundredth)
