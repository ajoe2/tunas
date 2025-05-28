"""
Utility class for database
"""


def hamming_distance(str1: str, str2: str) -> int:
    assert len(str1) == len(str2)

    diffs = 0
    for i in range(len(str1)):
        if str1[i] != str2[i]:
            diffs += 1
    return diffs
