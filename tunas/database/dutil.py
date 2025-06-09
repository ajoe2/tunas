"""
Utility class for database
"""

from __future__ import annotations
from typing import Optional
import datetime
import enum

from . import sdif


class Event(enum.Enum):
    """
    Swim event. Each event is represented by a distance, stroke,
    and course.
    """

    # Individual events
    FREE_25_SCY = (25, sdif.Stroke.FREESTYLE, sdif.Course.SCY)
    FREE_50_SCY = (50, sdif.Stroke.FREESTYLE, sdif.Course.SCY)
    FREE_100_SCY = (100, sdif.Stroke.FREESTYLE, sdif.Course.SCY)
    FREE_200_SCY = (200, sdif.Stroke.FREESTYLE, sdif.Course.SCY)
    FREE_400_SCY = (400, sdif.Stroke.FREESTYLE, sdif.Course.SCY)
    FREE_500_SCY = (500, sdif.Stroke.FREESTYLE, sdif.Course.SCY)
    FREE_800_SCY = (800, sdif.Stroke.FREESTYLE, sdif.Course.SCY)
    FREE_1000_SCY = (1000, sdif.Stroke.FREESTYLE, sdif.Course.SCY)
    FREE_1650_SCY = (1650, sdif.Stroke.FREESTYLE, sdif.Course.SCY)
    BACK_25_SCY = (25, sdif.Stroke.BACKSTROKE, sdif.Course.SCY)
    BACK_50_SCY = (50, sdif.Stroke.BACKSTROKE, sdif.Course.SCY)
    BACK_100_SCY = (100, sdif.Stroke.BACKSTROKE, sdif.Course.SCY)
    BACK_200_SCY = (200, sdif.Stroke.BACKSTROKE, sdif.Course.SCY)
    BREAST_25_SCY = (25, sdif.Stroke.BREASTSTROKE, sdif.Course.SCY)
    BREAST_50_SCY = (50, sdif.Stroke.BREASTSTROKE, sdif.Course.SCY)
    BREAST_100_SCY = (100, sdif.Stroke.BREASTSTROKE, sdif.Course.SCY)
    BREAST_200_SCY = (200, sdif.Stroke.BREASTSTROKE, sdif.Course.SCY)
    FLY_25_SCY = (25, sdif.Stroke.BUTTERFLY, sdif.Course.SCY)
    FLY_50_SCY = (50, sdif.Stroke.BUTTERFLY, sdif.Course.SCY)
    FLY_100_SCY = (100, sdif.Stroke.BUTTERFLY, sdif.Course.SCY)
    FLY_200_SCY = (200, sdif.Stroke.BUTTERFLY, sdif.Course.SCY)
    IM_100_SCY = (100, sdif.Stroke.INDIVIDUAL_MEDLEY, sdif.Course.SCY)
    IM_200_SCY = (200, sdif.Stroke.INDIVIDUAL_MEDLEY, sdif.Course.SCY)
    IM_400_SCY = (400, sdif.Stroke.INDIVIDUAL_MEDLEY, sdif.Course.SCY)
    FREE_25_SCM = (25, sdif.Stroke.FREESTYLE, sdif.Course.SCM)
    FREE_50_SCM = (50, sdif.Stroke.FREESTYLE, sdif.Course.SCM)
    FREE_100_SCM = (100, sdif.Stroke.FREESTYLE, sdif.Course.SCM)
    FREE_200_SCM = (200, sdif.Stroke.FREESTYLE, sdif.Course.SCM)
    FREE_400_SCM = (400, sdif.Stroke.FREESTYLE, sdif.Course.SCM)
    FREE_800_SCM = (800, sdif.Stroke.FREESTYLE, sdif.Course.SCM)
    FREE_1500_SCM = (1500, sdif.Stroke.FREESTYLE, sdif.Course.SCM)
    BACK_25_SCM = (25, sdif.Stroke.BACKSTROKE, sdif.Course.SCM)
    BACK_50_SCM = (50, sdif.Stroke.BACKSTROKE, sdif.Course.SCM)
    BACK_100_SCM = (100, sdif.Stroke.BACKSTROKE, sdif.Course.SCM)
    BACK_200_SCM = (200, sdif.Stroke.BACKSTROKE, sdif.Course.SCM)
    BREAST_25_SCM = (25, sdif.Stroke.BREASTSTROKE, sdif.Course.SCM)
    BREAST_50_SCM = (50, sdif.Stroke.BREASTSTROKE, sdif.Course.SCM)
    BREAST_100_SCM = (100, sdif.Stroke.BREASTSTROKE, sdif.Course.SCM)
    BREAST_200_SCM = (200, sdif.Stroke.BREASTSTROKE, sdif.Course.SCM)
    FLY_25_SCM = (25, sdif.Stroke.BUTTERFLY, sdif.Course.SCM)
    FLY_50_SCM = (50, sdif.Stroke.BUTTERFLY, sdif.Course.SCM)
    FLY_100_SCM = (100, sdif.Stroke.BUTTERFLY, sdif.Course.SCM)
    FLY_200_SCM = (200, sdif.Stroke.BUTTERFLY, sdif.Course.SCM)
    IM_100_SCM = (100, sdif.Stroke.INDIVIDUAL_MEDLEY, sdif.Course.SCM)
    IM_200_SCM = (200, sdif.Stroke.INDIVIDUAL_MEDLEY, sdif.Course.SCM)
    IM_400_SCM = (400, sdif.Stroke.INDIVIDUAL_MEDLEY, sdif.Course.SCM)
    FREE_50_LCM = (50, sdif.Stroke.FREESTYLE, sdif.Course.LCM)
    FREE_100_LCM = (100, sdif.Stroke.FREESTYLE, sdif.Course.LCM)
    FREE_200_LCM = (200, sdif.Stroke.FREESTYLE, sdif.Course.LCM)
    FREE_400_LCM = (400, sdif.Stroke.FREESTYLE, sdif.Course.LCM)
    FREE_800_LCM = (800, sdif.Stroke.FREESTYLE, sdif.Course.LCM)
    FREE_1500_LCM = (1500, sdif.Stroke.FREESTYLE, sdif.Course.LCM)
    BACK_50_LCM = (50, sdif.Stroke.BACKSTROKE, sdif.Course.LCM)
    BACK_100_LCM = (100, sdif.Stroke.BACKSTROKE, sdif.Course.LCM)
    BACK_200_LCM = (200, sdif.Stroke.BACKSTROKE, sdif.Course.LCM)
    BREAST_50_LCM = (50, sdif.Stroke.BREASTSTROKE, sdif.Course.LCM)
    BREAST_100_LCM = (100, sdif.Stroke.BREASTSTROKE, sdif.Course.LCM)
    BREAST_200_LCM = (200, sdif.Stroke.BREASTSTROKE, sdif.Course.LCM)
    FLY_50_LCM = (50, sdif.Stroke.BUTTERFLY, sdif.Course.LCM)
    FLY_100_LCM = (100, sdif.Stroke.BUTTERFLY, sdif.Course.LCM)
    FLY_200_LCM = (200, sdif.Stroke.BUTTERFLY, sdif.Course.LCM)
    IM_200_LCM = (200, sdif.Stroke.INDIVIDUAL_MEDLEY, sdif.Course.LCM)
    IM_400_LCM = (400, sdif.Stroke.INDIVIDUAL_MEDLEY, sdif.Course.LCM)

    # Relay events
    FREE_200_RELAY_SCY = (200, sdif.Stroke.FREESTYLE_RELAY, sdif.Course.SCY)
    FREE_400_RELAY_SCY = (400, sdif.Stroke.FREESTYLE_RELAY, sdif.Course.SCY)
    FREE_800_RELAY_SCY = (800, sdif.Stroke.FREESTYLE_RELAY, sdif.Course.SCY)
    MEDLEY_200_RELAY_SCY = (200, sdif.Stroke.MEDLEY_RELAY, sdif.Course.SCY)
    MEDLEY_400_RELAY_SCY = (400, sdif.Stroke.MEDLEY_RELAY, sdif.Course.SCY)
    FREE_200_RELAY_SCM = (200, sdif.Stroke.FREESTYLE_RELAY, sdif.Course.SCM)
    FREE_400_RELAY_SCM = (400, sdif.Stroke.FREESTYLE_RELAY, sdif.Course.SCM)
    FREE_800_RELAY_SCM = (800, sdif.Stroke.FREESTYLE_RELAY, sdif.Course.SCM)
    MEDLEY_200_RELAY_SCM = (200, sdif.Stroke.MEDLEY_RELAY, sdif.Course.SCM)
    MEDLEY_400_RELAY_SCM = (400, sdif.Stroke.MEDLEY_RELAY, sdif.Course.SCM)
    FREE_200_RELAY_LCM = (200, sdif.Stroke.FREESTYLE_RELAY, sdif.Course.LCM)
    FREE_400_RELAY_LCM = (400, sdif.Stroke.FREESTYLE_RELAY, sdif.Course.LCM)
    FREE_800_RELAY_LCM = (800, sdif.Stroke.FREESTYLE_RELAY, sdif.Course.LCM)
    MEDLEY_200_RELAY_LCM = (200, sdif.Stroke.MEDLEY_RELAY, sdif.Course.LCM)
    MEDLEY_400_RELAY_LCM = (400, sdif.Stroke.MEDLEY_RELAY, sdif.Course.LCM)

    def __str__(self) -> str:
        event_basic = f"{self.get_distance()} {self.get_stroke()}"
        return f"{event_basic: <10}  {self.get_course()}"

    def __eq__(self, value: Event) -> bool:
        return self.name == value.name

    def __lt__(self, value: Event) -> bool:
        self_index = list(Event.__members__).index(self.name)
        value_index = list(Event.__members__).index(value.name)
        return self_index < value_index

    def __gt__(self, value: Event) -> bool:
        return value < self

    def get_distance(self) -> int:
        """
        Return distance of event.
        """
        return self.value[0]

    def get_stroke(self) -> sdif.Stroke:
        """
        Return stroke of event.
        """
        return self.value[1]

    def get_course(self) -> sdif.Course:
        """
        Return course of event.
        """
        return self.value[2]


class AgeGroup(enum.Enum):
    """
    Represent an age group. Every age group corresponds to an age range.
    """

    _8_U = range(9)
    _10_U = range(11)
    _9_10 = range(9, 11)
    _11_12 = range(11, 13)
    _13_14 = range(13, 15)
    _15_16 = range(15, 17)
    _17_18 = range(17, 19)
    _18_U = range(19)
    _19_O = range(19, 100)
    SENIOR = range(15, 100)

    # Single age groups
    _11 = range(11, 12)
    _12 = range(12, 13)
    _13 = range(13, 14)
    _14 = range(14, 15)

    def __contains__(self: AgeGroup, value: object) -> bool:
        return value in self.value


def calculate_age(birthday: datetime.date, on_date: datetime.date):
    """
    Calculate age on_date for given birthday.
    """
    return (
        on_date.year
        - birthday.year
        - ((on_date.month, on_date.day) < (birthday.month, birthday.day))
    )


def hamming_distance(str1: str, str2: str) -> int:
    """
    Calculate hamming distance between two strings.
    """
    diffs = abs(len(str1) - len(str2))
    for i in range(min(len(str1), len(str2))):
        if str1[i] != str2[i]:
            diffs += 1
    return diffs


def generate_old_id(
    first_name: str,
    middle_initial: Optional[str],
    last_name: str,
    birthday: datetime.date,
) -> str:
    """
    Generate old id using first name, last name, middle initial, and birthday.

    From the documentation:
    'The USSNUM format consists of: date of birth + first 3 letters
    of legal first name + middle initial + first 4 letters of last
    name. In the event that there is no middle initial or not enough
    letters in the first or last name to fill the field, an asterisk
    will be used. Special characters are removed.
    Examples: Catherine A. Durance = 011553CATADURA
        Cy V. Young          = 091879CY*VYOUN
        Thomas Chu           = 020981THO*CHU*
        Ty Lee               = 011873TY**LEE*
        Dave T. O'Neil       = 030367DAVTONEI'
    """
    month = str(birthday.month).zfill(2)
    day = str(birthday.day).zfill(2)
    year = str(birthday.year)[-2:]

    first = (first_name.upper() + "**")[:3]
    last = (last_name.upper() + "***")[:4]
    if middle_initial == None:
        middle_initial = "*"

    old_id = month + day + year + first + middle_initial + last
    assert len(old_id) == 14
    return old_id
