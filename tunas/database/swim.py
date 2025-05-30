"""
Data structures for representing swimming objects (club, swimmer, meet, meet result).
"""

from __future__ import annotations
from typing import Optional
import datetime

from . import dutil, stime, sdif


class Club:
    """
    Swim club representation.
    """

    def __init__(
        self,
        organization: sdif.Organization,
        team_code: str,
        lsc: Optional[sdif.LSC],
        full_name: str,
        abbreviated_name: Optional[str] = None,
        address_one: Optional[str] = None,
        address_two: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[sdif.State] = None,
        postal_code: Optional[str] = None,
        country: Optional[sdif.Country] = None,
        region: Optional[sdif.Region] = None,
        swimmers: Optional[list[Swimmer]] = None,
        meets: Optional[list[Meet]] = None,
        meet_results: Optional[list[MeetResult]] = None,
    ) -> None:
        # Mandatory fields
        self.set_organization(organization)
        self.set_team_code(team_code)
        self.set_lsc(lsc)
        self.set_full_name(full_name)

        # Optional fields
        self.set_abbreviated_name(abbreviated_name)
        self.set_address_one(address_one)
        self.set_address_two(address_two)
        self.set_city(city)
        self.set_state(state)
        self.set_postal_code(postal_code)
        self.set_country(country)
        self.set_region(region)

        # Internal
        self.set_swimmers(swimmers)
        self.set_meets(meets)
        self.set_meet_results(meet_results)

    def set_organization(self, organization: sdif.Organization) -> None:
        assert type(organization) == sdif.Organization
        self.organization = organization

    def set_team_code(self, team_code: str) -> None:
        if team_code != None:
            assert type(team_code) == str
            assert team_code.isupper()
            assert len(team_code) <= 6 and len(team_code) > 0
        self.team_code = team_code

    def set_lsc(self, lsc: Optional[sdif.LSC]) -> None:
        if lsc != None:
            assert type(lsc) == sdif.LSC
        self.lsc = lsc

    def set_full_name(self, full_name: str) -> None:
        assert type(full_name) == str
        assert len(full_name) > 0
        self.full_name = full_name

    def set_abbreviated_name(self, abbreviated_name: Optional[str]) -> None:
        if abbreviated_name != None:
            assert type(abbreviated_name) == str
            assert len(abbreviated_name) > 0
        self.abbreviated_name = abbreviated_name

    def set_address_one(self, address_one: Optional[str]) -> None:
        if address_one != None:
            assert type(address_one) == str
            assert len(address_one) > 0
        self.address_one = address_one

    def set_address_two(self, address_two: Optional[str]) -> None:
        if address_two != None:
            assert type(address_two) == str
            assert len(address_two) > 0
        self.address_two = address_two

    def set_city(self, city: Optional[str]) -> None:
        if city != None:
            assert type(city) == str
            assert len(city) > 0
        self.city = city

    def set_state(self, state: Optional[sdif.State]) -> None:
        if state != None:
            assert type(state) == sdif.State
        self.state = state

    def set_postal_code(self, postal_code: Optional[str]) -> None:
        if postal_code != None:
            assert type(postal_code) == str
            assert len(postal_code) > 0
        self.postal_code = postal_code

    def set_country(self, country: Optional[sdif.Country]) -> None:
        if country != None:
            assert type(country) == sdif.Country
        self.country = country

    def set_region(self, region: Optional[sdif.Region]) -> None:
        if region != None:
            assert type(region) == sdif.Region
        self.region = region

    def set_swimmers(self, swimmers: Optional[list[Swimmer]]) -> None:
        if swimmers == None:
            self.swimmers = []
            return
        assert type(swimmers) == list
        for s in swimmers:
            assert type(s) == Swimmer
        self.swimmers = swimmers

    def set_meets(self, meets: Optional[list[Meet]]) -> None:
        if meets == None:
            self.meets = []
            return
        assert type(meets) == list
        for m in meets:
            assert type(m) == Meet
        self.meets = meets

    def set_meet_results(self, meet_results: Optional[list[MeetResult]]) -> None:
        if meet_results == None:
            self.meet_results = []
            return
        assert type(meet_results) == list
        for mr in meet_results:
            assert isinstance(mr, MeetResult)
        self.meet_results = meet_results

    def get_organization(self) -> sdif.Organization:
        return self.organization

    def get_team_code(self) -> str:
        return self.team_code

    def get_lsc(self) -> Optional[sdif.LSC]:
        return self.lsc

    def get_full_name(self) -> str:
        return self.full_name

    def get_abbreviated_name(self) -> Optional[str]:
        return self.abbreviated_name

    def get_address_one(self) -> Optional[str]:
        return self.address_one

    def get_address_two(self) -> Optional[str]:
        return self.address_two

    def get_city(self) -> Optional[str]:
        return self.city

    def get_state(self) -> Optional[sdif.State]:
        return self.state

    def get_postal_code(self) -> Optional[str]:
        return self.postal_code

    def get_country(self) -> Optional[sdif.Country]:
        return self.country

    def get_region(self) -> Optional[sdif.Region]:
        return self.region

    def get_swimmers(self) -> list[Swimmer]:
        return self.swimmers

    def get_meets(self) -> list[Meet]:
        return self.meets

    def get_meet_results(self) -> list[MeetResult]:
        return self.meet_results

    def add_swimmer(self, swimmer: Swimmer) -> None:
        assert type(swimmer) == Swimmer
        self.swimmers.append(swimmer)

    def add_meet(self, meet: Meet) -> None:
        assert type(meet) == Meet
        self.meets.append(meet)

    def add_meet_result(self, meet_result: MeetResult) -> None:
        assert isinstance(meet_result, MeetResult)
        self.meet_results.append(meet_result)

    def find_swimmer_with_short_id(self, short_id: str) -> Optional[Swimmer]:
        assert len(short_id) == 12
        for s in self.get_swimmers():
            if s.get_usa_id_short() == short_id:
                return s

    def find_swimmer_with_birthday(
        self,
        first_name: str,
        middle_initial: Optional[str],
        last_name: str,
        birthday: datetime.date,
    ) -> Optional[Swimmer]:
        old_id = dutil.generate_old_id(first_name, middle_initial, last_name, birthday)
        for swimmer in self.get_swimmers():
            swimmer_birthday = swimmer.get_birthday()
            if swimmer_birthday is None or swimmer_birthday != birthday:
                continue
            swimmer_first_name = swimmer.get_first_name()
            swimmer_last_name = swimmer.get_last_name()
            swimmer_middle_initial = swimmer.get_middle_initial()

            # Find swimmer by generating old ids and comparing hamming distance
            swimmer_id = dutil.generate_old_id(
                swimmer_first_name,
                swimmer_middle_initial,
                swimmer_last_name,
                swimmer_birthday,
            )
            if dutil.hamming_distance(swimmer_id, old_id) <= 1:
                return swimmer
        return None


class Swimmer:
    """
    Swimmer representation.
    """

    def __init__(
        self,
        first_name: str,
        last_name: str,
        sex: sdif.Sex,
        usa_id_short: Optional[str],
        club: Optional[Club],
        middle_initial: Optional[str] = None,
        preferred_first_name: Optional[str] = None,
        birthday: Optional[datetime.date] = None,
        usa_id_long: Optional[str] = None,
        citizenship: Optional[sdif.Country] = None,
        meets: Optional[list[Meet]] = None,
        meet_results: Optional[list[IndividualMeetResult]] = None,
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

        # Internal
        self.set_meets(meets)
        self.set_meet_results(meet_results)
        self.date_most_recent_swim = None

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

    def set_usa_id_short(self, usa_id_short: Optional[str]) -> None:
        if usa_id_short is not None:
            assert type(usa_id_short) == str
            assert len(usa_id_short) == 12
        self.usa_id_short = usa_id_short

    def set_club(self, club: Optional[Club]) -> None:
        """
        Sets swimmer's club to the most recent associated club seen in the data.
        """
        if club != None:
            assert type(club) == Club
        self.club = club

    def set_middle_initial(self, middle_initial: Optional[str]) -> None:
        if middle_initial != None:
            assert type(middle_initial) == str
            assert len(middle_initial) == 1
        self.middle_initial = middle_initial

    def set_preferred_first_name(self, preferred_first_name: Optional[str]) -> None:
        if preferred_first_name != None:
            assert type(preferred_first_name) == str
            assert len(preferred_first_name) > 0
        self.preferred_first_name = preferred_first_name

    def set_birthday(self, birthday: Optional[datetime.date]) -> None:
        """
        Prior to Jan 2025, all records contained swimmer's birthdays. However, now
        they are excluded. If birthday is None, it can be estimated by looking at the
        history of recorded age classes and the associated dates.
        """
        if birthday != None:
            assert type(birthday) == datetime.date
        self.birthday = birthday

    def set_usa_id_long(self, usa_id_long: Optional[str]) -> None:
        if usa_id_long != None:
            assert type(usa_id_long) == str
            assert len(usa_id_long) == 14
        self.usa_id_long = usa_id_long

    def set_citizenship(self, citizenship: Optional[sdif.Country]) -> None:
        if citizenship != None:
            assert type(citizenship) == sdif.Country
        self.citizenship = citizenship

    def set_meets(self, meets: Optional[list[Meet]]) -> None:
        if meets == None:
            self.meets = []
            return
        assert type(meets) == list
        for m in meets:
            assert type(m) == Meet
        self.meets = meets

    def set_meet_results(
        self, meet_results: Optional[list[IndividualMeetResult]]
    ) -> None:
        if meet_results == None:
            self.meet_results = []
            return
        assert type(meet_results) == list
        for mr in meet_results:
            assert isinstance(mr, IndividualMeetResult)
        for mr in meet_results:
            if (
                self.date_most_recent_swim == None
                or mr.get_date_of_swim() > self.date_most_recent_swim
            ):
                self.date_most_recent_swim = mr.get_date_of_swim()
        self.meet_results = meet_results

    def get_first_name(self) -> str:
        return self.first_name

    def get_last_name(self) -> str:
        return self.last_name

    def get_full_name(self) -> str:
        if self.middle_initial != None:
            return f"{self.first_name} {self.middle_initial} {self.last_name}"
        else:
            return f"{self.first_name} {self.last_name}"

    def get_sex(self) -> sdif.Sex:
        return self.sex

    def get_usa_id_short(self) -> Optional[str]:
        return self.usa_id_short

    def get_club(self) -> Optional[Club]:
        return self.club

    def get_middle_initial(self) -> Optional[str]:
        return self.middle_initial

    def get_preferred_first_name(self) -> Optional[str]:
        return self.preferred_first_name

    def get_birthday(self) -> Optional[datetime.date]:
        return self.birthday

    def get_usa_id_long(self) -> Optional[str]:
        return self.usa_id_long

    def get_citizenship(self) -> Optional[sdif.Country]:
        return self.citizenship

    def get_meets(self) -> list[Meet]:
        return self.meets

    def get_meet_results(self) -> list[IndividualMeetResult]:
        return self.meet_results

    def get_date_most_recent_swim(self) -> Optional[datetime.date]:
        return self.date_most_recent_swim

    def add_meet(self, meet: Meet) -> None:
        assert type(meet) == Meet
        self.meets.append(meet)

    def add_meet_result(self, meet_result: IndividualMeetResult) -> None:
        assert isinstance(meet_result, IndividualMeetResult)
        if (
            self.date_most_recent_swim == None
            or meet_result.get_date_of_swim() > self.date_most_recent_swim
        ):
            self.date_most_recent_swim = meet_result.get_date_of_swim()
        self.meet_results.append(meet_result)

    def get_age_range(self, on_date: datetime.date) -> tuple[int, int]:
        """
        Return age range for the given swimmer.
        """
        min_age: int
        max_age: int

        birthday_range = self.get_birthday_range()
        if birthday_range != None:
            # Calculate min and max age
            birthday_min, birthday_max = birthday_range
            max_age = dutil.calculate_age(birthday_min, on_date)
            min_age = dutil.calculate_age(birthday_max, on_date)
        else:
            # Set min and max age to defaults
            min_age, max_age = 1, 99

        assert max_age >= min_age
        return (min_age, max_age)

    def get_birthday_range(self) -> Optional[tuple[datetime.date, datetime.date]]:
        # If the swimmer has a birthday, then the range is just the birthday.
        birthday = self.get_birthday()
        if birthday is not None:
            return birthday, birthday

        # Find numerical age records
        age_records = []
        for mr in self.get_meet_results():
            meet_start_date = mr.get_meet().get_start_date()
            swimmer_age_class = mr.get_swimmer_age_class()
            if swimmer_age_class != None and swimmer_age_class.isnumeric():
                age_records.append((meet_start_date, int(swimmer_age_class)))

        # We can't guess the birthday without age records
        if len(age_records) == 0:
            return None

        # Set birthday min and birthday max
        birthday_min = datetime.date(
            age_records[0][0].year - age_records[0][1] - 1,
            age_records[0][0].month,
            age_records[0][0].day,
        ) + datetime.timedelta(days=1)
        birthday_max = datetime.date(
            age_records[0][0].year - age_records[0][1],
            age_records[0][0].month,
            age_records[0][0].day,
        )

        # Iterating through records and refine min/max birthday
        for record in age_records:
            record_date, record_age = record
            record_year, record_month, record_day = (
                record_date.year,
                record_date.month,
                record_date.day,
            )
            min = datetime.date(
                record_year - record_age - 1, record_month, record_day
            ) + datetime.timedelta(days=1)
            max = datetime.date(record_year - record_age, record_month, record_day)

            if min > birthday_min:
                birthday_min = min
            if max < birthday_max:
                birthday_max = max

        return birthday_min, birthday_max

    def update_club(self, new_club: Club):
        assert type(new_club) == Club
        current_club = self.get_club()
        if current_club == None:
            self.set_club(new_club)
            new_club.add_swimmer(self)
        else:
            current_club.get_swimmers().remove(self)
            new_club.add_swimmer(self)
            self.set_club(new_club)

    def get_best_meet_result(self, event: sdif.Event) -> Optional[IndividualMeetResult]:
        """
        Return meet result with fastest time for event
        """
        valid_results: list[IndividualMeetResult]
        valid_results = []
        for mr in self.get_meet_results():
            if mr.get_event() == event:
                valid_results.append(mr)
        if len(valid_results) == 0:
            return None
        else:
            return min(valid_results, key=lambda mr: mr.get_final_time())


class Meet:
    """
    Represents a swim meet. Has access to all meet result records for the associated
    swim meet.
    """

    def __init__(
        self,
        organization: sdif.Organization,
        name: str,
        city: str,
        address_one: str,
        start_date: datetime.date,
        end_date: datetime.date,
        state: Optional[sdif.State] = None,
        address_two: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[sdif.Country] = None,
        course: Optional[sdif.Course] = None,
        altitude: Optional[int] = None,
        meet_type: Optional[sdif.MeetType] = None,
        meet_results: Optional[list[MeetResult]] = None,
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

        # Internal
        self.set_meet_results(meet_results)

    def set_organization(self, organization: sdif.Organization) -> None:
        assert type(organization) == sdif.Organization
        self.organization = organization

    def set_name(self, name: str) -> None:
        assert type(name) == str and len(name) > 0
        self.name = name

    def set_meet_type(self, meet_type: Optional[sdif.MeetType]) -> None:
        if meet_type != None:
            assert type(meet_type) == sdif.MeetType
        self.meet_type = meet_type

    def set_city(self, city: str) -> None:
        assert type(city) == str
        self.city = city

    def set_state(self, state: Optional[sdif.State]) -> None:
        if state != None:
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

    def set_address_two(self, address_two: Optional[str]) -> None:
        if address_two != None:
            assert type(address_two) == str
        self.address_two = address_two

    def set_postal_code(self, postal_code: Optional[str]) -> None:
        if postal_code != None:
            assert type(postal_code) == str
            self.postal_code = postal_code

    def set_country(self, country: Optional[sdif.Country]) -> None:
        if country != None:
            assert type(country) == sdif.Country
        self.country = country

    def set_course(self, course: Optional[sdif.Course]) -> None:
        if course != None:
            assert type(course) == sdif.Course
        self.course = course

    def set_altitude(self, altitude: Optional[int]) -> None:
        if altitude != None:
            assert type(altitude) == int
            assert altitude >= 0
        self.altitude = altitude

    def set_meet_results(self, meet_results: Optional[list[MeetResult]]) -> None:
        if meet_results == None:
            meet_results = []
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

    def get_meet_type(self) -> Optional[sdif.MeetType]:
        return self.meet_type

    def get_city(self) -> str:
        return self.city

    def get_state(self) -> Optional[sdif.State]:
        return self.state

    def get_address_one(self) -> str:
        return self.address_one

    def get_start_date(self) -> datetime.date:
        return self.start_date

    def get_end_date(self) -> datetime.date:
        return self.end_date

    def get_address_two(self) -> Optional[str]:
        return self.address_two

    def get_postal_code(self) -> Optional[str]:
        return self.postal_code

    def get_country(self) -> Optional[sdif.Country]:
        return self.country

    def get_course(self) -> Optional[sdif.Course]:
        return self.course

    def get_altitude(self) -> Optional[int]:
        return self.altitude

    def get_meet_results(self) -> list[MeetResult]:
        return self.meet_results

    def add_meet_result(self, meet_result: MeetResult):
        assert isinstance(meet_result, MeetResult)
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
        team_code: Optional[str],
        lsc: Optional[sdif.LSC],
        session: sdif.Session,
        date_of_swim: datetime.date,
        event: sdif.Event,
        event_min_age: int,
        event_max_age: int,
        event_number: str,
        event_sex: sdif.Sex,
        heat: Optional[int],
        lane: Optional[int],
        final_time: stime.Time,
        rank: Optional[int] = None,
        points: Optional[float] = None,
        seed_time: Optional[stime.Time] = None,
        seed_course: Optional[sdif.Course] = None,
        event_min_time_class: Optional[sdif.EventTimeClass] = None,
        event_max_time_class: Optional[sdif.EventTimeClass] = None,
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

    def set_team_code(self, team_code: Optional[str]) -> None:
        if team_code != None:
            assert type(team_code) == str
            assert team_code.isupper()
            assert len(team_code) <= 4 and len(team_code) > 0
        self.team_code = team_code

    def set_lsc(self, lsc: Optional[sdif.LSC]) -> None:
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

    def set_heat(self, heat: Optional[int]) -> None:
        if heat != None:
            assert type(heat) == int
            assert heat >= 0 and heat <= 99
        self.heat = heat

    def set_lane(self, lane: Optional[int]) -> None:
        if lane != None:
            assert type(lane) == int
            assert lane >= 0 and lane <= 99
        self.lane = lane

    def set_final_time(self, final_time: stime.Time) -> None:
        assert type(final_time) == stime.Time
        self.final_time = final_time

    def set_rank(self, rank: Optional[int]) -> None:
        if rank != None:
            assert type(rank) == int
            assert rank > 0
        self.rank = rank

    def set_points(self, points: Optional[float]) -> None:
        if points != None:
            assert type(points) == float
            assert points >= 0
        self.points = points

    def set_seed_time(self, seed_time: Optional[stime.Time]) -> None:
        if seed_time != None:
            assert type(seed_time) == stime.Time
        self.seed_time = seed_time

    def set_seed_course(self, seed_course: Optional[sdif.Course]) -> None:
        if seed_course != None:
            assert type(seed_course) == sdif.Course
        self.seed_course = seed_course

    def set_event_min_time_class(
        self, event_min_time_class: Optional[sdif.EventTimeClass]
    ) -> None:
        if event_min_time_class != None:
            assert type(event_min_time_class) == sdif.EventTimeClass
            assert event_min_time_class != sdif.EventTimeClass.NO_UPPER_LIMIT
        self.event_min_time_class = event_min_time_class

    def set_event_max_time_class(
        self, event_max_time_class: Optional[sdif.EventTimeClass]
    ) -> None:
        if event_max_time_class != None:
            assert type(event_max_time_class) == sdif.EventTimeClass
            assert event_max_time_class != sdif.EventTimeClass.NO_LOWER_LIMIT
        self.event_max_time_class = event_max_time_class

    def get_meet(self) -> Meet:
        return self.meet

    def get_organization(self) -> sdif.Organization:
        return self.organization

    def get_team_code(self) -> Optional[str]:
        return self.team_code

    def get_lsc(self) -> Optional[sdif.LSC]:
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

    def get_heat(self) -> Optional[int]:
        return self.heat

    def get_lane(self) -> Optional[int]:
        return self.lane

    def get_final_time(self) -> stime.Time:
        return self.final_time

    def get_rank(self) -> Optional[int]:
        return self.rank

    def get_points(self) -> Optional[float]:
        return self.points

    def get_seed_time(self) -> Optional[stime.Time]:
        return self.seed_time

    def get_seed_course(self) -> Optional[sdif.Course]:
        return self.seed_course

    def get_event_min_time_class(self) -> Optional[sdif.EventTimeClass]:
        return self.event_min_time_class

    def get_event_max_time_class(self) -> Optional[sdif.EventTimeClass]:
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
        team_code: Optional[str],
        lsc: Optional[sdif.LSC],
        session: sdif.Session,
        date_of_swim: datetime.date,
        event: sdif.Event,
        event_min_age: int,
        event_max_age: int,
        event_number: str,
        event_sex: sdif.Sex,
        heat: Optional[int],
        lane: Optional[int],
        final_time: stime.Time,
        swimmer_first_name: str,
        swimmer_last_name: str,
        swimmer_sex: sdif.Sex,
        swimmer_usa_id_short: str,
        swimmer_attach_status: sdif.AttachStatus,
        rank: Optional[int] = None,
        points: Optional[float] = None,
        seed_time: Optional[stime.Time] = None,
        seed_course: Optional[sdif.Course] = None,
        event_min_time_class: Optional[sdif.EventTimeClass] = None,
        event_max_time_class: Optional[sdif.EventTimeClass] = None,
        swimmer_middle_initial: Optional[str] = None,
        swimmer_age_class: Optional[str] = None,
        swimmer_birthday: Optional[datetime.date] = None,
        swimmer_usa_id_long: Optional[str] = None,
        swimmer_citizenship: Optional[sdif.Country] = None,
        splits: Optional[dict[int, stime.Time]] = None,
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

    def set_swimmer_middle_initial(self, swimmer_middle_initial: Optional[str]) -> None:
        if swimmer_middle_initial != None:
            assert type(swimmer_middle_initial) == str
            assert len(swimmer_middle_initial) == 1
            assert swimmer_middle_initial.isupper()

        self.swimmer_middle_initial = swimmer_middle_initial

    def set_swimmer_age_class(self, swimmer_age_class: Optional[str]) -> None:
        """
        Set the swimmer's age class. Age class should be a string consisting of an age
        (ex. 19) or a classification (ex. Jr).
        """
        if swimmer_age_class != None:
            if swimmer_age_class.isnumeric():
                age = int(swimmer_age_class)
                if age < 4 or age > 99:
                    swimmer_age_class = "NA"  # Corrupt entry
            else:
                assert swimmer_age_class.upper() in [
                    "FR",
                    "SO",
                    "JR",
                    "SR",
                ], swimmer_age_class
        self.swimmer_age_class = swimmer_age_class

    def set_swimmer_birthday(self, swimmer_birthday: Optional[datetime.date]) -> None:
        """
        Prior to Jan 2025, all records contained swimmer's birthdays. However, now
        they are excluded. If birthday is None, it can be estimated by looking at the
        history of recorded age classes and the associated dates.
        """
        if swimmer_birthday != None:
            assert type(swimmer_birthday) == datetime.date
        self.swimmer_birthday = swimmer_birthday

    def set_swimmer_usa_id_long(self, swimmer_usa_id_long: Optional[str]) -> None:
        if swimmer_usa_id_long != None:
            assert type(swimmer_usa_id_long) == str
            assert len(swimmer_usa_id_long) == 14
        self.swimmer_usa_id_long = swimmer_usa_id_long

    def set_swimmer_citizenship(
        self, swimmer_citizenship: Optional[sdif.Country]
    ) -> None:
        if swimmer_citizenship != None:
            assert type(swimmer_citizenship) == sdif.Country
        self.swimmer_citizenship = swimmer_citizenship

    def set_splits(self, splits: Optional[dict[int, stime.Time]]) -> None:
        if splits == None:
            splits = dict()
        assert type(splits) == dict, splits
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

    def get_swimmer_middle_initial(self) -> Optional[str]:
        return self.swimmer_middle_initial

    def get_swimmer_age_class(self) -> Optional[str]:
        return self.swimmer_age_class

    def get_swimmer_birthday(self) -> Optional[datetime.date]:
        return self.swimmer_birthday

    def get_swimmer_usa_id_long(self) -> Optional[str]:
        return self.swimmer_usa_id_long

    def get_swimmer_citizenship(self) -> Optional[sdif.Country]:
        return self.swimmer_citizenship

    def get_splits(self) -> dict[int, stime.Time]:
        return self.splits
