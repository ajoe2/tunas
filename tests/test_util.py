"""
Test file for util.py
"""

from tunas import util


def test_id_checker():
    first_1 = "Cy"
    middle_1 = "V"
    last_1 = "Young"
    id1 = "091879CY*VYO"

    first_2 = "Thomas"
    middle_2 = None
    last_2 = "Chu"
    id2 = "020981THO*CH"

    first_3 = "Ty"
    middle_3 = None
    last_3 = "Lee"
    id3 = "011873TY**LEE*"

    first_4 = "Dave"
    middle_4 = "T"
    last_4 = "O'Neil"
    id4 = "030367DAVTONEI"

    first_5 = "Billy"
    middle_5 = "B"
    last_5 = "Joe"
    id5 = "ASD03SD991SDFA"

    assert util.is_old_id(first_1, last_1, middle_1, id1) == True
    assert util.is_old_id(first_2, last_2, middle_2, id2) == True
    assert util.is_old_id(first_3, last_3, middle_3, id3) == True
    assert util.is_old_id(first_4, last_4, middle_4, id4) == True
    assert util.is_old_id(first_5, last_5, middle_5, id5) == False
