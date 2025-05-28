"""
Utility functions for tunas application.
"""

from typing import Optional


def is_old_id(
    first_name: str,
    last_name: str,
    middle_initial: Optional[str],
    usa_id: str,
) -> bool:
    # Make sure usa_id is not malformed
    assert len(usa_id) == 12 or len(usa_id) == 14

    # Check id format
    if (
        not usa_id[:6].isnumeric() or not usa_id[6:].replace("*", "").isalpha()
    ):  # Doesn't follow old id format
        return False

    month = int(usa_id[:2])
    day = int(usa_id[2:4])
    if month < 1 or month > 12 or day < 1 or day > 31:  # Impossible birthday
        return False

    # Recreate the last 8 characters of the USA swimming old ID
    while len(first_name) < 3:
        first_name = first_name + "*"
    if middle_initial == None:
        middle_initial = "*"
    while len(last_name) < 4:
        last_name = last_name + "*"
    alpha_id = usa_id[6:]
    alpha_id_construct = (
        first_name[:3].upper() + middle_initial + last_name[:4].upper()
    )[: len(alpha_id)]

    # If name portion doesn't match, return
    if hamming_distance(alpha_id, alpha_id_construct) > 2:
        return False

    return True


def standardize_course(course_str: str) -> str:
    """
    Standardize course data in D0 entry.
    """
    alpha_to_num_course = {"S": "1", "Y": "2", "L": "3"}
    if course_str in alpha_to_num_course.keys():
        course_str = alpha_to_num_course[course_str]
    return course_str


def hamming_distance(str1: str, str2: str) -> int:
    assert len(str1) == len(str2)

    diffs = 0
    for i in range(len(str1)):
        if str1[i] != str2[i]:
            diffs += 1
    return diffs


def title_case(name: str) -> str:
    """
    Convert name to title case
    """
    name_components = name.split(" ")
    name = ""
    for c in name_components:
        if c != "":
            c = c.lower()
            c = c[0].upper() + c[1:]
            name = name + c + " "
    name = name[:-1]
    return name
