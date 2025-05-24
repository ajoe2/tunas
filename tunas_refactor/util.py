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