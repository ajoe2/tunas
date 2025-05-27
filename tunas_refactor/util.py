"""
Utility functions for tunas application.
"""


def is_old_id(id: str) -> bool:
    if "*" in id:
        return True
    if not id[:6].isnumeric() or not id[6:].isalpha():
        return False
    month = int(id[:2])
    day = int(id[2:4])
    if month >= 1 and month <= 12 and day >= 1 and day <= 32:
        return True
    return False

def standardize_course(course_str: str) -> str:
    """
    Standardize course data in D0 entry.
    """
    alpha_to_num_course = {"S": "1", "Y": "2", "L": "3"}
    if course_str in alpha_to_num_course.keys():
        course_str = alpha_to_num_course[course_str]
    return course_str