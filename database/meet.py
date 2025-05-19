"""
Defines the Meet and MeetResult classes. Defines associated classes
IndividualMeetResult, RelayMeetResult, RelayLeg which inherit
from MeetResult.
"""

from __future__ import annotations  # Enable future annotations
import datetime

import util.sdif as sdif
import util.time as time


class Meet():
    """
    Defines basic meet attributes and associated helper methods (getter/setter).
    Used to manage meet result entries.

    TODO
    """

    def __init__(
        self,
        organization: sdif.Organization,
        name: str,
    ) -> None:
        self.set_organization(organization)
        self.set_name(name)
        self.set_meet_results([])

    def set_organization(self, organization: sdif.Organization) -> None:
        assert type(organization) == sdif.Organization
        self.organization = organization

    def set_name(self, name: str) -> None:
        assert type(name) == str and len(name) > 0
        self.name = name

    def set_meet_results(self, meet_results: list[MeetResult]) -> None:
        assert type(meet_results) == list
        new_results = []
        for mr in meet_results:
            assert type(mr) == MeetResult
            new_results.append(mr)
        self.meet_results = new_results

    def set_address_one(self, address_one: str) -> None:
        if address_one != None:
            assert type(address_one) == str
        self.address_one = address_one

    def set_address_two(self, address_two: str) -> None:
        if address_two != None:
            assert type(address_two) == str
        self.address_two = address_two

    def set_city(self, city: str) -> None:
        assert type(city) == str
        self.city = city

    def set_state(self, state: sdif.State) -> None:
        assert type(state) == sdif.State
        self.state = state

    def set_postal_code(self, postal_code: str) -> None:
        assert type(postal_code) == str
        self.postal_code = postal_code

    def set_country(self, country: sdif.Country) -> None:
        assert type(country) == sdif.Country
        self.country = country

    def set_meet_type(self, meet_type: sdif.MeetType) -> None:
        assert type(meet_type) == sdif.MeetType
        self.meet_type = meet_type

    def set_start_date(self, start_date: datetime.date) -> None:
        assert type(start_date) == datetime.date
        self.start_date = start_date

    def set_end_date(self, end_date: datetime.date) -> None:
        assert type(end_date) == datetime.date
        self.end_date = end_date

    def set_altitude(self, altitude: int) -> None:
        assert type(altitude) == int
        assert altitude >= 0
        self.altitude = altitude

    def set_course(self, course: sdif.Course) -> None:
        assert type(course) == sdif.Course
        self.course = course

    def get_organization(self) -> sdif.Organization:
        return self.organization

    def get_name(self) -> str:
        return self.name

    def get_meet_results(self) -> list[MeetResult]:
        return self.meet_results

    def get_address_one(self) -> str:
        return self.address_one

    def get_address_two(self) -> str:
        return self.address_two

    def get_city(self) -> str:
        return self.city

    def get_state(self) -> sdif.State:
        return self.state

    def get_postal_code(self) -> str:
        return self.postal_code
    
    def get_country(self) -> sdif.Country:
        return self.country
    
    def get_meet_type(self) -> sdif.MeetType:
        return self.meet_type
    
    def get_start_date(self) -> datetime.date:
        return self.start_date
    
    def get_end_date(self) -> datetime.date:
        return self.end_date
    
    def get_altitude(self) -> int:
        return self.altitude
    
    def get_course(self) -> sdif.Course:
        return self.course

    def add_meet_result(self, meet_result: MeetResult):
        assert type(meet_result) == MeetResult
        self.meet_results.append(meet_result)


class MeetResult:
    """
    Defines basic meet result attributes and associated helper methods (getter/setter).
    """

    def __init__(
        self,
        meet: Meet,
        organization: sdif.Organization,
        team_code: str,
        lsc: sdif.LSC,
        session: sdif.Session,
        date_of_swim: datetime.date,
        event: sdif.Event,
        event_min_age: int,
        event_max_age: int,
        event_number: str,
        event_sex: sdif.Sex,
        heat: int,
        lane: int,
        final_time: time.Time,
        rank: int | None = None,
        points: float | None = None,
        seed_time: time.Time | None = None,
        seed_course: sdif.Course | None = None,
        event_min_time_class: sdif.EventTimeClass | None = None,
        event_max_time_class: sdif.EventTimeClass | None = None,
    ) -> None:
        # Mandatory fields
        self.set_meet(meet)
        self.set_organization(organization)
        self.set_team_code(team_code)
        self.set_lsc(lsc)
        self.set_session(session)
        self.set_date_of_swim(date_of_swim)
        self.set_event(event)
        self.set_event_min_age(event_min_age)
        self.set_event_max_age(event_max_age)
        self.set_event_number(event_number)
        self.set_event_sex(event_sex)
        self.set_heat(heat)
        self.set_lane(lane)
        self.set_final_time(final_time)

        # Optional fields (may not be present in the data)
        self.set_rank(rank)
        self.set_points(points)
        self.set_seed_time(seed_time)
        self.set_seed_course(seed_course)
        self.set_event_min_time_class(event_min_time_class)
        self.set_event_max_time_class(event_max_time_class)

    def set_meet(self, meet: Meet) -> None:
        assert type(meet) == Meet
        self.meet = meet

    def set_organization(self, organization: sdif.Organization) -> None:
        assert type(organization) == sdif.Organization
        self.organization = organization

    def set_team_code(self, team_code: str) -> None:
        if team_code != None:
            assert type(team_code) == str
            assert team_code.isupper()
            assert len(team_code) <= 4 and len(team_code) > 0
        self.team_code = team_code

    def set_lsc(self, lsc: sdif.LSC) -> None:
        if lsc != None:
            assert type(lsc) == sdif.LSC
        self.lsc = lsc

    def set_session(self, session: sdif.Session) -> None:
        assert type(session) == sdif.Session
        self.session = session

    def set_date_of_swim(self, date_of_swim: datetime.date) -> None:
        assert type(date_of_swim) == datetime.date
        self.date_of_swim = date_of_swim

    def set_event(self, event: sdif.Event) -> None:
        assert type(event) == sdif.Event
        self.event = event

    def set_event_min_age(self, min_age: int) -> None:
        """
        Set the event minimum age. If no minimum age exists, min_age
        should be set to 0. See SDIF AGE Code 025 for more details on
        the encoding scheme.
        """
        assert type(min_age) == int
        self.event_min_age = min_age

    def set_event_max_age(self, max_age: int) -> None:
        """
        Set the event maximum age. If no maximum age exists, max_age
        should be set to 1000. See SDIF AGE Code 025 for more details on
        the encoding scheme.
        """
        assert type(max_age) == int
        self.event_max_age = max_age

    def set_event_number(self, event_number: str) -> None:
        """
        Event numbers can contain nonnumeric values. Thus, event
        numbers are stored as strings, and processing is left to
        higher layers of code.
        """
        assert type(event_number) == str and " " not in event_number
        self.event_number = event_number

    def set_event_sex(self, event_sex: sdif.Sex) -> None:
        assert type(event_sex) == sdif.Sex
        self.event_sex = event_sex

    def set_heat(self, heat: int) -> None:
        assert type(heat) == int
        assert heat >= 0 and heat <= 99
        self.heat = heat

    def set_lane(self, lane: int) -> None:
        assert type(lane) == int
        assert lane >= 0 and lane <= 99
        self.lane = lane

    def set_final_time(self, final_time: time.Time) -> None:
        assert type(final_time) == time.Time
        self.final_time = final_time

    def set_rank(self, rank: int | None) -> None:
        if rank != None:
            assert type(rank) == int
            assert rank > 0
        self.rank = rank

    def set_points(self, points: float | None) -> None:
        if points != None:
            assert type(points) == float
            assert points >= 0
        self.points = points

    def set_seed_time(self, seed_time: time.Time | None) -> None:
        if seed_time != None:
            assert type(seed_time) == time.Time
        self.seed_time = seed_time

    def set_seed_course(self, seed_course: sdif.Course | None) -> None:
        if seed_course != None:
            assert type(seed_course) == sdif.Course
        self.seed_course = seed_course

    def set_event_min_time_class(
        self, event_min_time_class: sdif.EventTimeClass | None
    ) -> None:
        if event_min_time_class != None:
            assert type(event_min_time_class) == sdif.EventTimeClass
            assert event_min_time_class != sdif.EventTimeClass.NO_UPPER_LIMIT
        self.event_min_time_class = event_min_time_class

    def set_event_max_time_class(
        self, event_max_time_class: sdif.EventTimeClass | None
    ) -> None:
        if event_max_time_class != None:
            assert type(event_max_time_class) == sdif.EventTimeClass
            assert event_max_time_class != sdif.EventTimeClass.NO_LOWER_LIMIT
        self.event_max_time_class = event_max_time_class

    def get_meet(self) -> Meet:
        return self.meet

    def get_organization(self) -> sdif.Organization:
        return self.organization

    def get_team_code(self) -> str:
        return self.team_code

    def get_lsc(self) -> sdif.LSC:
        return self.lsc

    def get_session(self) -> sdif.Session:
        return self.session

    def get_date_of_swim(self) -> datetime.date:
        return self.date_of_swim

    def get_event(self) -> sdif.Event:
        return self.event

    def get_event_min_age(self) -> int:
        return self.event_min_age

    def get_event_max_age(self) -> int:
        return self.event_max_age

    def get_event_number(self) -> str:
        return self.event_number

    def get_event_sex(self) -> sdif.Sex:
        return self.event_sex

    def get_heat(self) -> int:
        return self.heat

    def get_lane(self) -> int:
        return self.lane

    def get_final_time(self) -> time.Time:
        return self.final_time

    def get_rank(self) -> int | None:
        return self.rank

    def get_points(self) -> float | None:
        return self.points

    def get_seed_time(self) -> time.Time | None:
        return self.seed_time

    def get_seed_course(self) -> sdif.Course | None:
        return self.seed_course

    def get_event_min_time_class(self) -> sdif.EventTimeClass | None:
        return self.event_min_time_class

    def get_event_max_time_class(self) -> sdif.EventTimeClass | None:
        return self.event_max_time_class
