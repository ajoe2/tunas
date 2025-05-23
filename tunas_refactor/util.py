"""
Utility functions for tunas application.
"""


def is_old_id(id: str) -> bool:
    try:
        if "*" in id:
            return True
        month = int(id[:2])
        day = int(id[2:4])
        year = int(id[4:6])
        assert month >= 1 and month <= 12
        assert day >= 1 and day <= 32
        return True
    except:
        return False
