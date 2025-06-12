"""
Utility functions for tunas application.
"""

from typing import Optional

import database


def standardize_course(course_str: str) -> str:
    """
    Return numeric representation of course string. Course string can be
    alphabetic or numeric.
    """
    alpha_to_num_course = {"S": "1", "Y": "2", "L": "3"}
    assert (
        course_str in alpha_to_num_course.keys()
        or course_str in alpha_to_num_course.values()
    )
    if course_str in alpha_to_num_course.keys():
        course_str = alpha_to_num_course[course_str]
    return course_str


def title_case(name: str) -> str:
    """
    Convert name to title case.
    """
    assert type(name) == str
    name_components = name.split(" ")
    name = ""
    for c in name_components:
        if c != "":
            c = c.lower()
            c = c[0].upper() + c[1:]
            name += c + " "
    name = name[:-1]
    return name


def parse_full_name(full_name: str) -> tuple[str, Optional[str], str]:
    """
    Extract the first name, middle initial, and last name from full_name.
    """
    assert type(full_name) == str

    if full_name[-1].isupper() and full_name[-2] == " ":
        middle_initial = full_name[-1]
        full_name = full_name[:-2].strip()
    else:
        middle_initial = None
    last_name, first_name = full_name.split(",")
    last_name, first_name = last_name.strip(), first_name.strip()
    last_name, first_name = title_case(last_name), title_case(first_name)
    return (first_name, middle_initial, last_name)


def is_old_id(
    first_name: str,
    last_name: str,
    middle_initial: Optional[str],
    usa_id: str,
) -> bool:
    """
    Check if usa_id is in the old USA Swimming id format.
    """
    # usa_id should be 12 or 14 characters long
    assert len(usa_id) == 12 or len(usa_id) == 14

    # Check id format
    part1, part2 = usa_id[:6], usa_id[6:]
    if not part1.isnumeric() or not part2.replace("*", "").isalpha():
        return False

    # Remove special characters from first and last name
    new_first_name = ""
    for c in first_name:
        if c.isalpha():
            new_first_name += c
    first_name = new_first_name

    new_last_name = ""
    for c in last_name:
        if c.isalpha():
            new_last_name += c
    last_name = new_last_name

    # Check month and day are reasonable
    month = int(usa_id[:2])
    day = int(usa_id[2:4])
    if month < 1 or month > 12 or day < 1 or day > 31:
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

    # Compare generated ID with usa_id
    if database.dutil.hamming_distance(alpha_id, alpha_id_construct) > 2:
        return False

    return True
