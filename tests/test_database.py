"""
Tests for database package
"""

import database
import database.swim as swim
import database.sdif as sdif
import datetime


def test_database_basic():
    d = database.Database()
    assert d.get_clubs() == []
    assert d.get_meet_results() == []
    assert d.get_meets() == []
    assert d.get_swimmers() == []


def test_swimmer_basic():
    c = swim.Club(
        sdif.Organization.USA_SWIMMING,
        "SCSC",
        sdif.LSC.PACIFIC,
        "Santa Clara Swim Club",
    )
    s = swim.Swimmer(
        "John",
        "Doe",
        sdif.Sex.FEMALE,
        "GM2SP90AS920",
        c,
        "L",
        "Johnny",
        datetime.date.today(),
    )
    assert s.get_first_name() == "John"
    assert s.get_last_name() == "Doe"
    assert s.get_sex() == sdif.Sex.FEMALE
    assert s.get_usa_id_short() == "GM2SP90AS920"
    assert s.get_club() == c
