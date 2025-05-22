"""
Tests for database package
"""

import datetime

import database
from database import swim, sdif, stime


def test_database_basic():
    db = database.Database()
    assert db.get_clubs() == []
    assert db.get_meet_results() == []
    assert db.get_meets() == []
    assert db.get_swimmers() == []

    # Create club
    club = swim.Club(
        sdif.Organization.USA_SWIMMING,
        "SCSC",
        sdif.LSC.PACIFIC,
        "Santa Clara Swim Club",
        "Santa",
        "123 Test Drive",
        "456 Test Drive",
        "Santa Clara",
        sdif.State.CALIFORNIA,
        "99999",
        sdif.Country.UNITED_STATES,
        sdif.Region.REGION_1,
    )

    # Test club has correct attributes
    assert club.get_organization() == sdif.Organization.USA_SWIMMING
    assert club.get_team_code() == "SCSC"
    assert club.get_full_name() == "Santa Clara Swim Club"
    assert club.get_abbreviated_name() == "Santa"
    assert club.get_address_one() == "123 Test Drive"
    assert club.get_address_two() == "456 Test Drive"
    assert club.get_city() == "Santa Clara"
    assert club.get_state() == sdif.State.CALIFORNIA
    assert club.get_postal_code() == "99999"
    assert club.get_country() == sdif.Country.UNITED_STATES
    assert club.get_region() == sdif.Region.REGION_1

    # Create Swimmer
    swimmer = swim.Swimmer(
        "John",
        "Doe",
        sdif.Sex.FEMALE,
        "GM2SP90AS920",
        club,
        "A",
        "Johnny",
        datetime.date(2000, 1, 1),
        "GM2SP90AS920AA",
        sdif.Country.UNITED_STATES,
    )

    # Create Meet
    meet = swim.Meet(
        sdif.Organization.USA_SWIMMING,
        "Swim Meet Classic",
        sdif.MeetType.ZONE,
        "Rome",
        sdif.State.CALIFORNIA,
        "999 Cool Road",
        datetime.date(2025, 1, 14),
        datetime.date(2025, 1, 15),
        None,
        None,
        sdif.Country.ARGENTINA,
        sdif.Course.LCM,
        None,
    )

    # Create Meet Result
    meet_result = swim.MeetResult(
        meet,
        sdif.Organization.USA_SWIMMING,
        "SCSC",
        sdif.LSC.PACIFIC,
        sdif.Session.FINALS,
        datetime.date.today(),
        sdif.Event.FREE_1000_SCY,
        0,
        1000,
        "14",
        sdif.Sex.MALE,
        1,
        4,
        stime.Time(8, 0, 0),
        None,
        None,
        None,
        None,
        None,
        None,
    )

    # Add object pointers
    meet.add_meet_result(meet_result)
    swimmer.add_meet(meet)
    swimmer.add_meet_result(meet_result)
    club.add_meet(meet)
    club.add_meet_result(meet_result)
    club.add_swimmer(swimmer)

    # Test that meet_result, meet, and swimmer got added correctly
    assert len(meet.get_meet_results()) == 1
    assert meet.get_meet_results()[0] == meet_result
    assert len(swimmer.get_meets()) == 1
    assert swimmer.get_meets()[0] == meet
    assert len(swimmer.get_meet_results()) == 1
    assert swimmer.get_meet_results()[0] == meet_result
    assert len(club.get_swimmers()) == 1
    assert club.get_swimmers()[0] == swimmer
    assert len(club.get_meets()) == 1
    assert club.get_meets()[0] == meet
    assert len(club.get_meet_results()) == 1
    assert club.get_meet_results()[0] == meet_result


def test_create_time_from_string_basic1():
    t_str = "1:52.65"
    t = database.create_time_from_str(t_str)
    assert t == stime.Time(1, 52, 65)


def test_create_time_from_string_error1():
    try:
        t_str = "]fw*Ds1"  # Garbage
        t = database.create_time_from_str(t_str)
        success = True
    except:
        success = False
    assert not success


def test_create_time_from_string_error2():
    try:
        t_str = "1:99.99"  # Invalid minutes
        t = database.create_time_from_str(t_str)
        success = True
    except:
        success = False
    assert not success


def test_create_time_from_string_error3():
    try:
        t_str = "1:59.999"  # Invalid hundredths
        t = database.create_time_from_str(t_str)
        success = True
    except:
        success = False
    assert not success
