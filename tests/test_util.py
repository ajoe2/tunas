"""
Test file for util.py
"""

from tunas import util


def test_is_old_id():
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

    first_6 = "Ty"
    middle_6 = "W"
    last_6 = "Lee"
    id6 = "011873TY**LEE*"

    assert util.is_old_id(first_1, last_1, middle_1, id1) == True
    assert util.is_old_id(first_2, last_2, middle_2, id2) == True
    assert util.is_old_id(first_3, last_3, middle_3, id3) == True
    assert util.is_old_id(first_4, last_4, middle_4, id4) == True
    assert util.is_old_id(first_5, last_5, middle_5, id5) == False
    assert util.is_old_id(first_6, last_6, middle_6, id6) == True


def test_parse_full_name():
    full_name_1 = "Jr, Billy Bob J"
    full_name_2 = "SwImMEr, tOTally R"

    first_1, middle_1, last_1 = util.parse_full_name(full_name_1)
    first_2, middle_2, last_2 = util.parse_full_name(full_name_2)

    assert (first_1, middle_1, last_1) == ("Billy Bob", "J", "Jr")
    assert (first_2, middle_2, last_2) == ("Totally", "R", "Swimmer")


def test_standardize_course():
    course1 = "S"
    course2 = "Y"
    course3 = "L"
    course4 = "1"
    course5 = "2"
    course6 = "3"
    course7 = "x"

    assert util.standardize_course(course1) == '1'
    assert util.standardize_course(course2) == '2'
    assert util.standardize_course(course3) == '3'
    assert util.standardize_course(course4) == '1'
    assert util.standardize_course(course5) == '2'
    assert util.standardize_course(course6) == '3'

    try:
        util.standardize_course(course7)
        assert False
    except:
        assert True
