"""
Utility class for database
"""

import datetime
from typing import Optional


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
