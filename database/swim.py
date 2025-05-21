"""
Data structures for representing swimming objects (club, swimmer, meet, etc.).
"""

from __future__ import annotations
import datetime

from .util import sdif, stime


class Club:
    """
    Represents a swim club.
    """

    def __init__(
        self,
        organization: sdif.Organization,
        team_code: str,
        lsc: sdif.LSC,
        full_name: str,
        abbreviated_name: str | None = None,
        address_one: str | None = None,
        city: str | None = None,
        state: sdif.State | None = None,
        postal_code: str | None = None,
        country: sdif.Country | None = None,
        region: sdif.Region | None = None,
        swimmers: list[Swimmer] = [],
        meets: list[Meet] = [],
        meet_results: list[MeetResult] = []
    ) -> None:
        pass


class Swimmer:
    """
    Represents a swimmer.
    """

    def __init__(
        self,
        first_name: str,
        last_name: str,
        sex: sdif.Sex,
        usa_id_short: str,
        club: Club,
        middle_initial: str | None = None,
        preferred_first_name: str | None = None,
        birthday: datetime.date | None = None,
        usa_id_long: str | None = None,
        citizenship: sdif.Country | None = None,
        meets: list[Meet] = list(),
        meet_results: list[MeetResult] = list(),
    ) -> None:
        # Mandatory fields
        self.set_first_name(first_name)
        self.set_last_name(last_name)
        self.set_sex(sex)
        self.set_usa_id_short(usa_id_short)
        self.set_club(club)

        # Optional fields
        self.set_middle_initial(middle_initial)
        self.set_preferred_first_name(preferred_first_name)
        self.set_birthday(birthday)
        self.set_usa_id_long(usa_id_long)
        self.set_citizenship(citizenship)
        self.set_meets(meets)
        self.set_meet_results(meet_results)

    def set_first_name(self, first_name: str) -> None:
        assert type(first_name) == str
        assert first_name != ""
        self.first_name = first_name

    def set_last_name(self, last_name: str) -> None:
        assert type(last_name) == str
        assert last_name != ""
        self.last_name = last_name

    def set_sex(self, sex: sdif.Sex) -> None:
        assert type(sex) == sdif.Sex
        self.sex = sex

    def set_usa_id_short(self, usa_id_short: str) -> None:
        assert type(usa_id_short) == str
        assert len(usa_id_short) == 12
        self.usa_id_short = usa_id_short

    def set_club(self, club: Club) -> None:
        """
        Sets swimmer's club to the most recent associated club seen in the data.
        """
        assert type(club) == Club
        self.club = club

    def set_middle_initial(self, middle_initial: str | None) -> None:
        if middle_initial != None:
            assert type(middle_initial) == str
            assert len(middle_initial) == 1
        self.middle_initial = middle_initial

    def set_preferred_first_name(self, preferred_first_name: str | None) -> None:
        if preferred_first_name != None:
            assert type(preferred_first_name) == str
            assert len(preferred_first_name) > 0
        self.preferred_first_name = preferred_first_name

    def set_birthday(self, birthday: datetime.date | None) -> None:
        """
        Prior to Jan 2025, all records contained swimmer's birthdays. However, now
        they are excluded. If birthday is None, it can be estimated by looking at the
        history of recorded age classes and the associated dates.
        """
        if birthday != None:
            assert type(birthday) == datetime.date
        self.birthday = birthday

    def set_usa_id_long(self, usa_id_long: str | None) -> None:
        if usa_id_long != None:
            assert type(usa_id_long) == str
            assert len(usa_id_long) == 14
        self.usa_id_long = usa_id_long

    def set_citizenship(self, citizenship: sdif.Country | None) -> None:
        if citizenship != None:
            assert type(citizenship) == sdif.Country
        self.citizenship = citizenship

    def set_meets(self, meets: list[Meet]) -> None:
        assert type(meets) == list
        for m in meets:
            assert type(m) == Meet
        self.meets = meets

    def set_meet_results(self, meet_results: list[MeetResult]) -> None:
        assert type(meet_results) == list
        for mr in meet_results:
            assert isinstance(mr, MeetResult)
        self.meet_results = meet_results

    def get_first_name(self) -> str:
        return self.first_name

    def get_last_name(self) -> str:
        return self.last_name

    def get_sex(self) -> sdif.Sex:
        return self.sex

    def get_usa_id_short(self) -> str:
        return self.usa_id_short

    def get_club(self) -> Club:
        return self.club

    def get_middle_initial(self) -> str | None:
        return self.middle_initial

    def get_preferred_first_name(self) -> str | None:
        return self.preferred_first_name

    def get_birthday(self) -> datetime.date | None:
        return self.birthday

    def get_usa_id_long(self) -> str | None:
        return self.usa_id_long

    def get_citizenship(self) -> sdif.Country | None:
        return self.citizenship

    def get_meets(self) -> list[Meet]:
        return self.meets

    def get_meet_results(self) -> list[MeetResult]:
        return self.meet_results

    def add_meet(self, meet: Meet) -> None:
        assert type(meet) == Meet
        self.meets.append(meet)

    def add_meet_result(self, meet_result: MeetResult) -> None:
        assert isinstance(meet_result, MeetResult)
        self.meet_results.append(meet_result)


class Meet:
    """
    Represents a swim meet. Has access to all meet result records for the associated
    swim meet.
    """

    def __init__(
        self,
        organization: sdif.Organization,
        name: str,
        meet_type: sdif.MeetType,
        city: str,
        state: sdif.State,
        address_one: str,
        start_date: datetime.date,
        end_date: datetime.date,
        address_two: str | None = None,
        postal_code: str | None = None,
        country: sdif.Country | None = None,
        course: sdif.Course | None = None,
        altitude: int | None = None,
        meet_results: list[MeetResult] = list(),
    ) -> None:
        # Mandatory fields
        self.set_organization(organization)
        self.set_name(name)
        self.set_meet_type(meet_type)
        self.set_city(city)
        self.set_state(state)
        self.set_address_one(address_one)
        self.set_start_date(start_date)
        self.set_end_date(end_date)

        # Optional fields (may not be present in the data)
        self.set_address_two(address_two)
        self.set_postal_code(postal_code)
        self.set_country(country)
        self.set_course(course)
        self.set_altitude(altitude)
        self.set_meet_results(meet_results)

    def set_organization(self, organization: sdif.Organization) -> None:
        assert type(organization) == sdif.Organization
        self.organization = organization

    def set_name(self, name: str) -> None:
        assert type(name) == str and len(name) > 0
        self.name = name

    def set_meet_type(self, meet_type: sdif.MeetType) -> None:
        assert type(meet_type) == sdif.MeetType
        self.meet_type = meet_type

    def set_city(self, city: str) -> None:
        assert type(city) == str
        self.city = city

    def set_state(self, state: sdif.State) -> None:
        assert type(state) == sdif.State
        self.state = state

    def set_address_one(self, address_one: str) -> None:
        assert type(address_one) == str
        self.address_one = address_one

    def set_start_date(self, start_date: datetime.date) -> None:
        assert type(start_date) == datetime.date
        self.start_date = start_date

    def set_end_date(self, end_date: datetime.date) -> None:
        assert type(end_date) == datetime.date
        self.end_date = end_date

    def set_address_two(self, address_two: str | None) -> None:
        if address_two != None:
            assert type(address_two) == str
        self.address_two = address_two

    def set_postal_code(self, postal_code: str | None) -> None:
        assert type(postal_code) == str
        self.postal_code = postal_code

    def set_country(self, country: sdif.Country | None) -> None:
        assert type(country) == sdif.Country
        self.country = country

    def set_course(self, course: sdif.Course | None) -> None:
        assert type(course) == sdif.Course
        self.course = course

    def set_altitude(self, altitude: int | None) -> None:
        assert type(altitude) == int
        assert altitude >= 0
        self.altitude = altitude

    def set_meet_results(self, meet_results: list[MeetResult]) -> None:
        assert type(meet_results) == list
        new_results = []
        for mr in meet_results:
            assert type(mr) == MeetResult
            new_results.append(mr)
        self.meet_results = new_results

    def get_organization(self) -> sdif.Organization:
        return self.organization

    def get_name(self) -> str:
        return self.name

    def get_meet_type(self) -> sdif.MeetType:
        return self.meet_type

    def get_city(self) -> str:
        return self.city

    def get_state(self) -> sdif.State:
        return self.state

    def get_address_one(self) -> str:
        return self.address_one

    def get_start_date(self) -> datetime.date:
        return self.start_date

    def get_end_date(self) -> datetime.date:
        return self.end_date

    def get_address_two(self) -> str | None:
        return self.address_two

    def get_postal_code(self) -> str | None:
        return self.postal_code

    def get_country(self) -> sdif.Country | None:
        return self.country

    def get_course(self) -> sdif.Course | None:
        return self.course

    def get_altitude(self) -> int | None:
        return self.altitude

    def get_meet_results(self) -> list[MeetResult]:
        return self.meet_results

    def add_meet_result(self, meet_result: MeetResult):
        assert type(meet_result) == MeetResult
        self.meet_results.append(meet_result)


class MeetResult:
    """
    Base class for swim meet results. Defines basic information such as event time
    and heat/lane assignments.
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
        final_time: stime.Time,
        rank: int | None = None,
        points: float | None = None,
        seed_time: stime.Time | None = None,
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
        Set the event minimum age. If no minimum age exists, min_age should be set to 0.
        See SDIF AGE Code 025 for more details on the encoding scheme.
        """
        assert type(min_age) == int
        self.event_min_age = min_age

    def set_event_max_age(self, max_age: int) -> None:
        """
        Set the event maximum age. If no maximum age exists, max_age should be set to
        1000. See SDIF AGE Code 025 for more details on the encoding scheme.
        """
        assert type(max_age) == int
        self.event_max_age = max_age

    def set_event_number(self, event_number: str) -> None:
        """
        Event numbers can contain nonnumeric values. Thus, event numbers are stored as
        strings, and processing is left to higher layers of code.
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

    def set_final_time(self, final_time: stime.Time) -> None:
        assert type(final_time) == stime.Time
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

    def set_seed_time(self, seed_time: stime.Time | None) -> None:
        if seed_time != None:
            assert type(seed_time) == stime.Time
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

    def get_final_time(self) -> stime.Time:
        return self.final_time

    def get_rank(self) -> int | None:
        return self.rank

    def get_points(self) -> float | None:
        return self.points

    def get_seed_time(self) -> stime.Time | None:
        return self.seed_time

    def get_seed_course(self) -> sdif.Course | None:
        return self.seed_course

    def get_event_min_time_class(self) -> sdif.EventTimeClass | None:
        return self.event_min_time_class

    def get_event_max_time_class(self) -> sdif.EventTimeClass | None:
        return self.event_max_time_class


class IndividualMeetResult(MeetResult):
    """
    Represents one individual meet result. Inherits from MeetResult, which provides
    event information. Provides new methods for swimmer information such as first/last
    name and splits.
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
        final_time: stime.Time,
        swimmer_first_name: str,
        swimmer_last_name: str,
        swimmer_sex: sdif.Sex,
        swimmer_usa_id_short: str,
        swimmer_attach_status: sdif.AttachStatus,
        rank: int | None = None,
        points: float | None = None,
        seed_time: stime.Time | None = None,
        seed_course: sdif.Course | None = None,
        event_min_time_class: sdif.EventTimeClass | None = None,
        event_max_time_class: sdif.EventTimeClass | None = None,
        swimmer_middle_initial: str | None = None,
        swimmer_age_class: str | None = None,
        swimmer_birthday: datetime.date | None = None,
        swimmer_usa_id_long: str | None = None,
        swimmer_citizenship: sdif.Country | None = None,
        splits: dict[int, stime.Time] = dict(),
    ) -> None:
        super().__init__(
            meet,
            organization,
            team_code,
            lsc,
            session,
            date_of_swim,
            event,
            event_min_age,
            event_max_age,
            event_number,
            event_sex,
            heat,
            lane,
            final_time,
            rank,
            points,
            seed_time,
            seed_course,
            event_min_time_class,
            event_max_time_class,
        )
        # New mandatory attributes (TODO)
        self.set_swimmer_first_name(swimmer_first_name)
        self.set_swimmer_last_name(swimmer_last_name)
        self.set_swimmer_sex(swimmer_sex)
        self.set_swimmer_attach_status(swimmer_attach_status)

        # New optional attributes (TODO)
        self.set_swimmer_middle_initial(swimmer_middle_initial)
        self.set_swimmer_age_class(swimmer_age_class)
        self.set_swimmer_birthday(swimmer_birthday)
        self.set_swimmer_usa_id_short(swimmer_usa_id_short)
        self.set_swimmer_usa_id_long(swimmer_usa_id_long)
        self.set_swimmer_citizenship(swimmer_citizenship)
        self.set_splits(splits)

    def set_swimmer_first_name(self, swimmer_first_name: str) -> None:
        assert type(swimmer_first_name) == str
        assert swimmer_first_name != ""
        self.swimmer_first_name = swimmer_first_name

    def set_swimmer_last_name(self, swimmer_last_name: str) -> None:
        assert type(swimmer_last_name) == str
        assert swimmer_last_name != ""
        self.swimmer_last_name = swimmer_last_name

    def set_swimmer_sex(self, swimmer_sex: sdif.Sex) -> None:
        assert type(swimmer_sex) == sdif.Sex
        self.swimmer_sex = swimmer_sex

    def set_swimmer_usa_id_short(self, swimmer_usa_id_short: str):
        assert type(swimmer_usa_id_short) == str
        assert len(swimmer_usa_id_short) == 12
        self.swimmer_usa_id_short = swimmer_usa_id_short

    def set_swimmer_attach_status(
        self, swimmer_attach_status: sdif.AttachStatus
    ) -> None:
        assert type(swimmer_attach_status) == sdif.AttachStatus
        self.swimmer_attach_status = swimmer_attach_status

    def set_swimmer_middle_initial(self, swimmer_middle_initial: str | None) -> None:
        if swimmer_middle_initial != None:
            assert type(swimmer_middle_initial) == str
            assert len(swimmer_middle_initial) == 1
            assert swimmer_middle_initial.isupper()

        self.swimmer_middle_initial = swimmer_middle_initial

    def set_swimmer_age_class(self, swimmer_age_class: str | None) -> None:
        """
        Set the swimmer's age class. Age class should be a string consisting of an age
        (ex. 19) or a classification (ex. Jr).
        """
        if swimmer_age_class != None:
            try:
                age = int(swimmer_age_class)
                assert age >= 0 and age < 100
            except:
                assert age in ["Fr", "So", "Jr", "Sr"]
        self.swimmer_age_class = swimmer_age_class

    def set_swimmer_birthday(self, swimmer_birthday: datetime.date | None) -> None:
        """
        Prior to Jan 2025, all records contained swimmer's birthdays. However, now
        they are excluded. If birthday is None, it can be estimated by looking at the
        history of recorded age classes and the associated dates.
        """
        if swimmer_birthday != None:
            assert type(swimmer_birthday) == datetime.date
        self.swimmer_birthday = swimmer_birthday

    def set_swimmer_usa_id_long(self, swimmer_usa_id_long: str | None) -> None:
        if swimmer_usa_id_long != None:
            assert type(swimmer_usa_id_long) == str
            assert len(swimmer_usa_id_long) == 14
        self.swimmer_usa_id_long = swimmer_usa_id_long

    def set_swimmer_citizenship(self, swimmer_citizenship: sdif.Country | None) -> None:
        if swimmer_citizenship != None:
            assert type(swimmer_citizenship) == sdif.Country
        self.swimmer_citizenship = swimmer_citizenship

    def set_splits(self, splits: dict[int, stime.Time]) -> None:
        assert type(splits) == dict
        for dist in splits:
            assert type(dist) == int
            assert type(splits[dist]) == stime.Time
        self.splits = splits

    def get_swimmer_first_name(self) -> str:
        return self.swimmer_first_name

    def get_swimmer_last_name(self) -> str:
        return self.swimmer_last_name

    def get_swimmer_sex(self) -> sdif.Sex:
        return self.swimmer_sex

    def get_swimmer_usa_id_short(self) -> str:
        return self.swimmer_usa_id_short

    def get_swimmer_attach_status(self) -> sdif.AttachStatus:
        return self.swimmer_attach_status

    def get_swimmer_middle_initial(self) -> str | None:
        return self.swimmer_middle_initial

    def get_swimmer_age_class(self) -> str | None:
        return self.swimmer_age_class

    def get_swimmer_birthday(self) -> datetime.date | None:
        return self.swimmer_birthday

    def get_swimmer_usa_id_long(self) -> str | None:
        return self.swimmer_usa_id_long

    def get_swimmer_citizenship(self) -> sdif.Country | None:
        return self.swimmer_citizenship

    def get_splits(self) -> dict[int, stime.Time]:
        return self.splits
