"""
Tests for database package
"""

import datetime
import pytest

from tunas import database


def test_database_basic():
    db = database.Database()
    assert db.get_clubs() == []
    assert db.get_meet_results() == []
    assert db.get_meets() == []
    assert db.get_swimmers() == []

    # Create club
    club = database.swim.Club(
        database.sdif.Organization.USA_SWIMMING,
        "SCSC",
        database.sdif.LSC.PACIFIC,
        "Santa Clara Swim Club",
        "Santa",
        "123 Test Drive",
        "456 Test Drive",
        "Santa Clara",
        database.sdif.State.CALIFORNIA,
        "99999",
        database.sdif.Country.UNITED_STATES,
        database.sdif.Region.REGION_1,
    )

    # Test club has correct attributes
    assert club.get_organization() == database.sdif.Organization.USA_SWIMMING
    assert club.get_team_code() == "SCSC"
    assert club.get_full_name() == "Santa Clara Swim Club"
    assert club.get_abbreviated_name() == "Santa"
    assert club.get_address_one() == "123 Test Drive"
    assert club.get_address_two() == "456 Test Drive"
    assert club.get_city() == "Santa Clara"
    assert club.get_state() == database.sdif.State.CALIFORNIA
    assert club.get_postal_code() == "99999"
    assert club.get_country() == database.sdif.Country.UNITED_STATES
    assert club.get_region() == database.sdif.Region.REGION_1

    # Create Swimmer
    swimmer = database.swim.Swimmer(
        "John",
        "Doe",
        database.sdif.Sex.FEMALE,
        "GM2SP90AS920",
        club,
        "A",
        "Johnny",
        None,
        "GM2SP90AS920AA",
        database.sdif.Country.UNITED_STATES,
    )

    # Create Meet
    meet = database.swim.Meet(
        database.sdif.Organization.USA_SWIMMING,
        "Swim Meet Classic",
        "Rome",
        "999 Cool Road",
        datetime.date.today(),
        datetime.date.today() + datetime.timedelta(days=1),
    )

    # Create Meet Result
    meet_result = database.swim.IndividualMeetResult(
        meet,
        database.sdif.Organization.USA_SWIMMING,
        "SCSC",
        database.sdif.LSC.PACIFIC,
        database.sdif.Session.FINALS,
        datetime.date.today(),
        database.dutil.Event.FREE_1000_SCY,
        0,
        1000,
        "14",
        database.sdif.Sex.MALE,
        1,
        4,
        database.stime.Time(8, 0, 0),
        "John",
        "Doe",
        database.sdif.Sex.FEMALE,
        "GM2SP90AS920",
        database.sdif.AttachStatus.ATTACHED,
        swimmer_age_class="14",
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
    print(datetime.date.today() + datetime.timedelta(days=364))
    assert swimmer.get_age_range(
        datetime.date.today() + datetime.timedelta(days=366)
    ) == (15, 16)


class TestTime:
    """
    Time tests in stime.py.
    """

    def test_time_basic(self):
        t1 = database.stime.Time(2, 0, 0)
        t2 = database.stime.Time(1, 30, 94)
        t3 = database.stime.Time(0, 32, 1)

        assert t1 > t2
        assert not t1 < t2
        assert not t1 == t2

        assert str(t1) == "2:00.00"
        assert str(t2) == "1:30.94"
        assert str(t3) == "32.01"

        t4 = t1 - t2
        assert t4 == database.stime.Time(0, 29, 6)

        t5 = t1 + t2
        assert t5 == database.stime.Time(3, 30, 94)

    def test_create_time_from_string_basic1(self):
        t_str = "1:52.65"
        t = database.stime.create_time_from_str(t_str)
        assert t == database.stime.Time(1, 52, 65)

    def test_create_time_from_string_error1(self):
        with pytest.raises(Exception):
            t_str = "]fw*Ds1"  # Garbage
            database.stime.create_time_from_str(t_str)

    def test_create_time_from_string_error2(self):
        with pytest.raises(Exception):
            t_str = "1:99.99"  # Invalid minutes
            database.stime.create_time_from_str(t_str)

    def test_create_time_from_string_error3(self):
        with pytest.raises(Exception):
            t_str = "1:59.999"  # Invalid hundredths
            database.stime.create_time_from_str(t_str)


class TestUtil:
    """
    Utility tests in dutil.py.
    """

    def test_event_basic(self):
        e1 = database.dutil.Event.BACK_100_LCM
        assert e1.get_course() == database.sdif.Course.LCM
        assert e1.get_distance() == 100
        assert e1.get_stroke() == database.sdif.Stroke.BACKSTROKE

    def test_calculate_age_basic(self):
        birthday1 = datetime.date(2010, 1, 1)
        on_date1 = datetime.date(2025, 8, 14)
        assert database.dutil.calculate_age(birthday1, on_date1) == 15

        birthday2 = datetime.date(2010, 2, 4)
        on_date2 = datetime.date(2025, 2, 3)
        assert database.dutil.calculate_age(birthday2, on_date2) == 14

        birthday3 = datetime.date(2010, 2, 4)
        on_date3 = datetime.date(2025, 2, 4)
        assert database.dutil.calculate_age(birthday3, on_date3) == 15
