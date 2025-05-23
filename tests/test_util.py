"""
Test file for util.py
"""

from tunas_refactor import util


def test_id_checker():
    id1 = "091879CY*VYO"
    id2 = "020981THO*CH"
    id3 = "011873TY**LEE*"
    id4 = "030367DAVTONEI"
    id5 = "ASD03SD991SDFA"
    assert util.is_old_id(id1) == True
    assert util.is_old_id(id2) == True
    assert util.is_old_id(id3) == True
    assert util.is_old_id(id4) == True
    assert util.is_old_id(id5) == False
