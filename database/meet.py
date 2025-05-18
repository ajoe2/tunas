"""
Define the Meet and MeetResult classes. Define associated classes 
IndividualMeetResult, RelayMeetResult, RelaySplit which inherit 
from MeetResult.
"""

from __future__ import annotations # Enable future annotations
from datetime import date

from util import Organization, LSC, Session, Event, Sex, Time, Course
from util import EventTimeClass


class Meet():
    """
    TODO
    """
    def __init__(self, organization: Organization, name: str):
        self.set_organization(organization)
        self.set_name(name)
        self.set_meet_results([])

    def set_organization(self, organization: Organization):
        assert type(organization) == Organization
        self.organization = organization

    def set_name(self, name: str):
        assert type(name) == str and len(name) > 0
        self.name = name

    def set_meet_results(self, meet_results: list[MeetResult]):
        assert type(meet_results) == list
        new_results = []
        for mr in meet_results:
            assert type(mr) == MeetResult
            new_results.append(mr)
        self.meet_results = new_results

    def set_address_one(self, address_one: str):
        if address_one != None:
            assert type(address_one) == str
        self.address_one = address_one

    def set_address_two(self, address_two: str):
        if address_two != None:
            assert type(address_two) == str
        self.address_two = address_two

    def get_organization(self) -> Organization:
        return self.organization
    
    def get_name(self) -> str:
        return self.name

    def get_meet_results(self) -> list[MeetResult]:
        return self.meet_results
    
    def get_address_one(self) -> str:
        return self.address_one
    
    def get_address_two(self) -> str:
        return self.address_two
    
    def add_meet_result(self, meet_result: MeetResult):
        assert type(meet_result) == MeetResult
        self.meet_results.append(meet_result)


class MeetResult():
    def __init__(self, meet: Meet, organization: Organization, 
                 session: Session, date_of_swim: date, event: Event,
                 event_number: int, event_sex: Sex, heat: int, 
                 lane: int, final_time: Time):
        self.set_meet(meet)
        self.set_organization(organization)
        self.set_date_of_swim(date_of_swim)
        self.set_session(session)
        self.set_event(event)
        self.set_event_number(event_number)
        self.set_event_sex(event_sex)
        self.set_heat(heat)
        self.set_lane(lane)
        self.set_final_time(final_time)

    def set_meet(self, meet: Meet):
        assert type(meet) == Meet
        self.meet = meet

    def set_organization(self, organization: Organization):
        assert type(organization) == Organization
        self.organization = organization

    def set_session(self, session: Session):
        assert type(session) == Session
        self.session = session

    def set_date_of_swim(self, date_of_swim: date):
        assert type(date_of_swim) == date
        self.date_of_swim = date_of_swim

    def set_event(self, event: Event):
        assert type(event) == Event
        self.event = event

    def set_event_sex(self, event_sex: Sex):
        assert type(event_sex) == Sex
        self.event_sex = event_sex

    def set_event_min_age(self, min_age: int):
        """
        Set the event minimum age. If no minimum age exists, min_age 
        should be set to 0.
        """
        assert min_age == None or type(min_age) == int
        self.event_min_age = min_age

    def set_event_max_age(self, max_age: int):
        """
        Set the event maximum age. If no maximum age exists, max_age 
        should be set to 1000.
        """
        assert max_age == None or type(max_age) == int
        self.event_max_age = max_age

    def set_event_number(self, event_number: str):
        """
        The event number can contain nonnumeric values. Thus, we store
        event numbers as strings and leave processing to higher layers
        of code.
        """
        assert type(event_number) == str and ' ' not in event_number
        self.event_number = event_number

    def set_event_min_time_class(self, event_min_time_class: EventTimeClass):
        if event_min_time_class != None:
            assert type(event_min_time_class) == EventTimeClass
            assert event_min_time_class != EventTimeClass.NO_UPPER_LIMIT
        self.event_min_time_class = event_min_time_class

    def set_event_max_time_class(self, event_max_time_class: EventTimeClass):
        if event_max_time_class != None:
            assert type(event_max_time_class) == EventTimeClass
            assert event_max_time_class != EventTimeClass.NO_LOWER_LIMIT
        self.event_max_time_class = event_max_time_class

    def set_heat(self, heat: int):
        assert type(heat) == int
        assert heat >= 0 and heat <= 99
        self.heat = heat

    def set_lane(self, lane: int):
        assert type(lane) == int
        assert lane >= 0 and lane <= 99
        self.lane = lane

    def set_seed_time(self, seed_time: Time):
        if seed_time != None:
            assert type(seed_time) == Time
        self.seed_time = seed_time

    def set_seed_course(self, seed_course: Course):
        if seed_course != None:
            assert type(seed_course) == Course
        self.seed_course = seed_course

    def set_team_code(self, team_code: str):
        if team_code != None:
            assert type(team_code) == str
            assert team_code.isupper()
            assert len(team_code) <= 4 and len(team_code) > 0
        self.team_code = team_code

    def set_lsc(self, lsc: LSC):
        if lsc != None:
            assert type(lsc) == LSC
        self.lsc = lsc

    def set_final_time(self, final_time: Time):
        assert type(final_time) == Time
        self.final_time = final_time

    def set_rank(self, rank: int):
        if rank != None:
            assert type(rank) == int
            assert rank > 0
        self.rank = rank

    def set_points(self, points: float):
        if points != None:
            assert type(points) == float
            assert points >= 0
        self.points = points

    def get_meet(self) -> Meet:
        return self.meet

    def get_organization(self) -> Organization:
        return self.organization

    def get_session(self) -> Session:
        return self.session
    
    def get_date_of_swim(self) -> date:
        return self.date_of_swim
    
    def get_event(self) -> Event:
        return self.event
    
    def get_event_sex(self) -> Sex:
        return self.event_sex
    
    def get_event_min_age(self) -> int:
        return self.event_min_age
    
    def get_event_max_age(self) -> int:
        return self.event_max_age
    
    def get_event_number(self) -> str:
        return self.event_number
    
    def get_event_min_time_class(self) -> EventTimeClass:
        return self.event_min_time_class
    
    def get_event_max_time_class(self) -> EventTimeClass:
        return self.event_max_time_class
    
    def get_heat(self) -> int:
        return self.heat
    
    def get_lane(self) -> int:
        return self.lane
    
    def get_seed_time(self) -> Time:
        return self.seed_time
    
    def get_seed_course(self) -> Course:
        return self.seed_course
    
    def get_team_code(self) -> str:
        return self.team_code
    
    def get_lsc(self) -> LSC:
        return self.lsc
    
    def get_final_time(self) -> Time:
        return self.final_time
    
    def get_rank(self) -> int:
        return self.rank
    
    def get_points(self) -> float:
        return self.points
