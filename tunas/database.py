from datetime import date

from util import *
from timestandard import *

class MeetResult():
    """
    Meet result.
    """

    def __init__(self, first_name: str, last_name: str, short_id: str,
                 birthday: date, age_class: str, sex: str,
                 date: date, session: int, course: str, time: Time, 
                 swimmer, event, meet, database, type="ind"):
        """
        Create meet result object instance.

        Keyword arguments:
        first_name -- swimmer's first name
        last_name -- swimmer's last name
        short_id -- swimmer's id (shortened due to cl2 format)
        birthday -- swimmer's birthday
        age_class -- swimmer's age class
        sex -- swimmer's sex
        date -- date of swim
        session -- session type
        course -- course of meet result
        time -- time of meet result
        swimmer -- associated swimmer object
        event -- associated event object
        meet -- associated meet
        type -- type of swim
        """
        self.first_name = first_name
        self.last_name = last_name
        self.short_id = short_id
        self.birthday = birthday
        self.age_class = age_class
        self.sex = sex
        self.date = date
        self.session = session
        self.course = course
        self.time = time
        self.swimmer = swimmer
        self.event = event
        self.meet = meet
        self.type = type
        self.db = database
    
    def __str__(self) -> str:
        """
        Return string representation of meet result.
        """
        time_standard = self.db.get_highest_standard(self.time, self.sex, 
                                                     self.swimmer.get_age(date.today()),
                                                     self.event.stroke,
                                                     self.event.dist, self.course)
        if not time_standard:
            time_standard = ""
        else:
            time_standard = f"[{time_standard}]"
        return f"{str(self.event) : <10} {self.course : <3}" + \
               f"{str(self.time) : >8}  {self.age_class : >2}  " + \
               f"{self.meet.get_name() : <30}  {str(self.date): <10} " + \
               f"{time_standard: <6}"
    
    def get_date(self) -> date:
        return self.date
    
    def get_time(self) -> Time:
        """
        Return time of meet_result.
        """
        return self.time
    
    def get_meet(self):
        return self.meet


class Meet():
    """
    Meet.
    """

    def __init__(self):
        """
        Create meet object instance.
        """
        self.name = ""
        self.meet_results = []
    
    def get_name(self) -> str:
        """
        Return self.name.
        """
        return self.name

    def get_meet_results(self) -> list[MeetResult]:
        """
        Return self.meet_results.
        """
        return self.meet_results

    def set_name(self, name: str):
        """
        Set self.name to name.

        Keyword arguments:
        name -- new meet name
        """
        self.name = name

    def add_meet_result(self, meet_result: MeetResult):
        """
        Add meet_result to self.

        Keyword arguments:
        meet_result -- new meet result
        """
        self.get_meet_results().append(meet_result)


class Event():
    valid_events = [(25, 1, 'Y'), (50, 1, 'Y'), (100, 1, 'Y'), (200, 1, 'Y'), 
                    (500, 1, 'Y'), (1000, 1, 'Y'), (1650, 1, 'Y'),
                    (25, 2, 'Y'), (50, 2, 'Y'), (100, 2, 'Y'), (200, 2, 'Y'),
                    (25, 3, 'Y'), (50, 3, 'Y'), (100, 3, 'Y'), (200, 3, 'Y'),
                    (25, 4, 'Y'), (50, 4, 'Y'), (100, 4, 'Y'), (200, 4, 'Y'),
                    (100, 5, 'Y'), (200, 5, 'Y'), (400, 5, 'Y'),
                    (25, 1, 'S'), (50, 1, 'S'), (100, 1, 'S'), (200, 1, 'S'), 
                    (400, 1, 'S'), (800, 1, 'S'), (1500, 1, 'S'),
                    (25, 2, 'S'), (50, 2, 'S'), (100, 2, 'S'), (200, 2, 'S'),
                    (25, 3, 'S'), (50, 3, 'S'), (100, 3, 'S'), (200, 3, 'S'),
                    (25, 4, 'S'), (50, 4, 'S'), (100, 4, 'S'), (200, 4, 'S'),
                    (100, 5, 'S'), (200, 5, 'S'), (400, 5, 'S'),
                    (50, 1, 'L'), (100, 1, 'L'), (200, 1, 'L'), (400, 1, 'L'), 
                    (800, 1, 'L'), (1500, 1, 'L'),
                    (50, 2, 'L'), (100, 2, 'L'), (200, 2, 'L'),
                    (50, 3, 'L'), (100, 3, 'L'), (200, 3, 'L'),
                    (50, 4, 'L'), (100, 4, 'L'), (200, 4, 'L'),
                    (200, 5, 'L'), (400, 5, 'L')]
    def __init__(self, stroke: int, dist: int, course: str, swimmer):
        """
        Create event object instance.
        """
        self.stroke = stroke
        self.dist = dist
        self.course = course
        self.meet_results = []

    def __str__(self) -> str:
        """
        Return string representation of event.
        """
        return f"{self.dist} {Util.stroke_to_str[self.stroke]}"
    
    def add_meet_result(self, meet_result: MeetResult):
        """
        Add meet_result to self.meet_results and sort by date.
        """
        self.meet_results.append(meet_result)
        self.meet_results.sort(reverse=False, 
                               key=lambda result: result.get_date())

    def get_meet_results(self) -> list[MeetResult]:
        """
        Return meet_results.
        """
        return self.meet_results


class Swimmer():
    def __init__(self, id: str, first_name: str, last_name: str, sex: str,
                 club, birthday: date, date_most_recent_swim: date):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.sex = sex
        self.club = club
        self.birthday = birthday
        self.date_most_recent_swim = date_most_recent_swim
        self.events = self.create_events()
        self.fake_id = self.create_fake_id()
    
    def __str__(self):
        full_name = self.first_name + " " + self.last_name
        return f"{full_name: <28}  {self.id: <14}  " + \
               f"{self.club.get_code(): <6}  " + \
               f"{self.get_age(date.today()): <2}  {str(self.birthday): <20}"
    
    def create_events(self) -> dict[tuple, Event]:
        """
        Create nested map structure for event objects.
        """
        events = {}
        for event in Event.valid_events:
            dist = event[0]
            stroke = event[1]
            course = event[2]
            events[event] = Event(stroke, dist, course, self)             
        return events
    
    def create_fake_id(self) -> str:
        """
        Create self.fake_id for self.
        """
        month = str(self.birthday.month).zfill(2)
        day = str(self.birthday.day).zfill(2)
        year = str(self.birthday.year)[-2:]
        first = (self.first_name.upper() + "***")[:4]
        last = (self.last_name.upper() + "***")[:4]

        fake_id = month + day + year + first + last
        return fake_id
    
    def get_id(self) -> str:
        """
        Return self.id.
        """
        return self.id
    
    def get_first_name(self) -> str:
        """
        Return self.name.
        """
        return self.first_name
    
    def get_last_name(self) -> str:
        """
        Return self.last_name.
        """
        return self.last_name
    
    def get_sex(self) -> str:
        """
        Return self.sex.
        """
        return self.sex
    
    def get_club(self):
        """
        Return self.club.
        """
        return self.club
    
    def get_birthday(self) -> date:
        """
        Return self.birthday.
        """
        return self.birthday
    
    def get_date_most_recent_swim(self) -> date:
        """
        Return self.date_most_recent_swim.
        """
        return self.date_most_recent_swim
    
    def get_events(self) -> dict[tuple, Event]:
        """
        Return self.events.
        """
        return self.events
    
    def get_fake_id(self) -> str:
        """
        Return self.fake_id.
        """
        return self.fake_id
    
    def get_full_name(self) -> str:
        """
        Return swimmer's full name ({Last name}, {First name}).
        """
        return f"{self.last_name}, {self.first_name}"
    
    def get_event(self, course: str, stroke: int, distance: int) -> Event:
        """
        Return corresponding event object.

        Keyword arguments:
        course - event course
        stroke - event stroke
        distance - event distance
        """
        invalid_str = f"Invalid event: ({distance} {stroke} {course})."
        assert (distance, stroke, course) in Event.valid_events, invalid_str
        return self.events[(distance, stroke, course)]
    
    def get_age(self, on_date: date) -> int:
        """
        Return age of swimmer on date on_date.
        """
        if on_date < self.birthday:
            return
        date_y, date_m, date_d = on_date.year, on_date.month, on_date.day
        self_y, self_m, self_d = self.birthday.year, self.birthday.month, self.birthday.day
        if date_m > self_m:
            return date_y - self_y
        elif date_m == self_m and date_d >= self_d:
            return date_y - self_y
        else:
            return date_y - self_y - 1
            
    def get_best_meet_result(self, distance: int, stroke: int, course: str) -> MeetResult:
        """
        Get best meet_result for corresponding event.

        Keyword arguments:
        distance -- event distance
        stroke -- event stroke
        course -- event course
        """
        results = self.get_event(course, stroke, distance).get_meet_results()
        best_meet_result = None
        for meet_result in results:
            if not best_meet_result or meet_result.get_time() < best_meet_result.get_time():
                best_meet_result = meet_result
        return best_meet_result
    
    def get_time_history(self) -> list[MeetResult]:
        """
        Return a list of swimmer's entire time history sorted by event 
        followed by date.
        """
        history = []
        for d, s, c in Event.valid_events:
            history = history + self.get_event(c, s, d).get_meet_results()
        return history

    def get_best_time(self, distance: int, stroke: int, course: str) -> Time:
        """
        Return swimmer's best time for corresponding event.

        Keyword arguments:
        distance -- event distance
        stroke -- event stroke
        course -- event course
        """
        best_meet_result = self.get_best_meet_result(distance, stroke, course)
        if best_meet_result:
            return best_meet_result.get_time()
    
    def update_club(self, new_club):
        """
        Update self.club to new_club.
        """
        self.club.remove_swimmer(self)
        self.club = new_club
        new_club.add_swimmer(self)

    def update_id(self, new_id: str):
        self.id = new_id

    def add_meet_result(self, meet_result: MeetResult, stroke: int, distance: int, course: str):
        """
        Add meet_result to event history.
        """
        event = self.get_event(course, stroke, distance)
        event.add_meet_result(meet_result)


class Club():
    def __init__(self, code: str, name: str, lsc):
        """
        Create club instance.

        Keyword arguments:
        code -- club code
        name -- club name
        lsc -- LSC that points to club instance
        """
        self.code = code
        self.name = name
        self.swimmers = []
        self.lsc = lsc
    
    def __str__(self) -> str:
        """
        Return string representation of club instance.
        """
        return f"{self.name}, {self.code}"
    
    def get_code(self) -> str:
        """
        Return club code.
        """
        return self.code
    
    def get_swimmers(self) -> list[Swimmer]:
        return self.swimmers
    
    def get_swimmer(self, swimmer_id: str) -> Swimmer:
        """
        Return swimmer with id swimmer_id or None if not found.
        """
        for swimmer in self.swimmers:
            if swimmer.id == swimmer_id:
                return swimmer
            
    def get_swimmer_with_fake_id(self, fake_id: str) -> Swimmer:
        """
        Return swimmer with id fake_id or None if not found.
        """
        for swimmer in self.swimmers:
            if swimmer.fake_id == fake_id:
                return swimmer
    
    def add_swimmer(self, swimmer: Swimmer):
        """
        Add swimmer to self.swimmers.
        """
        self.swimmers.append(swimmer)

    def remove_swimmer(self, swimmer: Swimmer):
        """
        Remove swimmer from self.swimmers.
        """
        if swimmer in self.swimmers:
            self.swimmers.remove(swimmer)


class LSC():
    """
    Class representing a LSC in USA Swimming.
    """
    id_to_name = {"AD": "Adirondack", "AK": "Alaska",
                  "AM": "Allegheny Mountain", "AR": "Arkansas",
                  "AZ": "Arizona", "BD": "Border", 
                  "CA": "Southern California", "CC": "Central California",
                  "CO": "Colorado", "CT": "Connecticut",
                  "FG": "Florida Gold Coast", "FL": "Florida", 
                  "GA": "Georgia", "GU": "Gulf", "HI": "Hawaii",
                  "IA": "Iowa", "IE": "Inland Empire",
                  "IL": "Illinois", "IN": "Indiana",
                  "KY": "Kentucky", "LA": "Louisiana",
                  "LE": "Lake Erie", "MA": "Middle Atlantic",
                  "MD": "Maryland", "ME": "Maine",
                  "MI": "Michigan", "MN": "Minnesota",
                  "MR": "Metropolitan", "MS": "Mississippi",
                  "MT": "Montana", "MV": "Missouri Valley",
                  "MW": "Midwestern", "NC": "North Carolina",
                  "ND": "North Dakota", "NE": "New England",
                  "NI": "Niagara", "NJ": "New Jersey",
                  "NM": "New Mexico", "NT": "North Texas",
                  "OH": "Ohio", "OK": "Oklahoma",
                  "OR": "Oregon", "OZ": "Ozark",
                  "PC": "Pacific", "PN": "Pacific Northwest",
                  "PV": "Potomac Valley", "SC": "South Carolina",
                  "SD": "South Dakota", "SE": "Southeastern",
                  "SI": "San Diego Imperial", "SN": "Sierra Nevada",
                  "SR": "Snake River", "ST": "South Texas",
                  "UT": "Utah", "VA": "Virginia",
                  "WI": "Wisconsin", "WT": "West Texas",
                  "WV": "West Virginia", "WY": "Wyoming",
                  "UN": "Unattached"
                  }

    def __init__(self, id: str):
        """
        Create lsc object instance.
        """
        self.id = id
        self.clubs = []
        try:
            self.set_name(id)
        except:
            self.name = "Undefined"
        
    def __str__(self) -> str:
        """
        Return string representation of lsc object.
        """
        return f"{self.name} Swimming"
    
    def set_name(self, id: str):
        """
        Set self.name to id.
        """
        assert id in LSC.id_to_name.keys(), f"Invalid id: {id}"
        self.name = LSC.id_to_name[id]
    
    def get_name(self) -> str:
        """
        Return self.name.
        """
        return self.name
    
    def get_clubs(self) -> list[Club]:
        """
        Return self.clubs.
        """
        return self.clubs

    def add_club(self, club: Club):
        """
        Add club to self.clubs.
        """
        self.clubs.append(club)

    def find_club(self, club_code: str) -> Club:
        """
        Return club with code club_code or None if not found.
        """
        for club in self.get_clubs():
            if club.get_code() == club_code:
                return club


class Database():
    """
    Class storing all meet result data.

    Attributes:
    self.lscs - list of lscs in USA Swimming
    self.clubs - list of clubs in USA Swimming
    self.swimmers - list of swimmers in USA Swimming
    self.meets - list of meets in USA Swimming

    Methods:
    
    """

    def __init__(self):
        """
        Create database instance.
        """
        self.lscs = []
        self.clubs = []
        self.swimmers = []
        self.meets = []
        self.meet_results = []
        self.ts = TimeStandard()

    def add_lsc(self, lsc: LSC):
        """
        Add lsc object to self.lscs.
        """
        self.lscs.append(lsc)

    def add_club(self, club: Club):
        """
        Add club object to self.clubs.
        """
        self.clubs.append(club)
    
    def add_swimmer(self, swimmer: Swimmer):
        """
        Add swimmer object to self.swimmers.
        """
        self.swimmers.append(swimmer)
    
    def add_meet(self, meet: Meet):
        """
        Add meet object to self.meets.
        """
        self.meets.append(meet)

    def add_meet_result(self, meet_result: MeetResult):
        """
        Add meet result to self.meet_results.
        """
        self.meet_results.append(meet_result)

    def get_lscs(self) -> list[LSC]:
        return self.lscs
    
    def get_clubs(self) -> list[Club]:
        return self.clubs

    def get_swimmers(self) -> list[Swimmer]:
        return self.swimmers

    def get_meets(self) -> list[Meet]:
        return self.meets
    
    def get_meet_results(self) -> list[MeetResult]:
        return self.meet_results
    
    def find_lsc(self, id: str) -> LSC:
        """
        Find and return LSC object with lsc.id == id. If lsc does not exist, 
        create and return new lsc object.

        Keyword arguments:
        id -- lsc id
        """
        for lsc in self.lscs:
            if lsc.id == id:
                return lsc
        # If lsc does not exist
        new_lsc = LSC(id)
        self.lscs.append(new_lsc)
        return new_lsc

    def find_club(self, club_code: str) -> Club:
        """
        Return club with code club_code or None if not found.
        """
        lsc = self.find_lsc(club_code[:2])
        return lsc.find_club(club_code)
    
    def find_swimmer(self, swimmer_id: str, club=None, club_code=None) -> Swimmer:
        """
        Return swimmer with id swimmer_id or None if not found.
        """
        swimmer = None
        if club:
            swimmer = club.get_swimmer(swimmer_id)
        elif club_code:
            club = self.find_club(club_code)
            swimmer = club.get_swimmer(swimmer_id)
        if not swimmer:
            for s in self.swimmers:
                if s.id == swimmer_id:
                    swimmer = s
                    break
        return swimmer
    
    def find_swimmer_with_fake_id(self, fake_swimmer_id: str, club: Club=None) -> Swimmer:
        """
        Return swimmer with fake_id == fake_swimmer_id or None if not found.
        """
        swimmer = None
        if club:
            swimmer = club.get_swimmer_with_fake_id(fake_swimmer_id)
        if not swimmer:
            for s in self.swimmers:
                if s.fake_id == fake_swimmer_id:
                    swimmer = s
                    break
        return swimmer
    
    def get_time_standard_df(self, standard: str, 
                             age_group: str) -> pd.DataFrame:
        return self.ts.get_time_standards(standard, age_group)

    def get_highest_standard(self, time: Time, sex: str, age: int, stroke: int, 
                             distance: int, course: str, relay=False) -> str:
        return self.ts.get_highest_standard(time, sex, age, stroke, distance, 
                                    course, relay)
    
    def get_qualified_standards(self, swimmer: Swimmer):
        sex = swimmer.get_sex()
        age = swimmer.get_age(date.today())
        qualified = set()
        for event in Event.valid_events:
            dist = event[0]
            stroke = event[1]
            course = event[2]
            best_result = swimmer.get_best_meet_result(dist, stroke, course)
            if best_result:
                best_time = best_result.get_time()
                qual_standards = self.ts.get_qualified_standards(best_time, 
                                                                 sex, age, 
                                                                 stroke, dist,
                                                                 course)
                for standard in qual_standards:
                    qualified.add(standard)
        return [standard for standard in TimeStandard.standards
                if standard in qualified]

