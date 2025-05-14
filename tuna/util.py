

class Time():
    """
    Represent time as (minute, second, hundreths) tuple. 
    """
    def __init__(self, minute=0, second=0, hundreth=0, time_str=None):
        """
        Create time oject.

        Keyword arguments:
        minute -- the minutes component (default 0)
        second -- the seconds component (default 0)
        hundreth -- the hundreths component (default 0)
        time_str -- alternate way of initializing Time object. Must be in
                    format m:ss.hh or m:ss:hh*.
        """
        if time_str and time_str != '0':
            if time_str[-1] == '*':
                time_str = time_str[:-1]
            seperated = time_str.split(":")
            if len(seperated) == 2:
                minute = int(seperated[0])
            second, hundreth = seperated[-1].split(".")
            second, hundreth = int(second), int(hundreth)
        self.minute = minute
        self.second = second
        self.hundreth = hundreth
    
    def __str__(self):
        """
        Return string representation of the time object.
        """
        if (self.get_hundreth() == 0 
            and self.get_minute() == 0 
            and self.get_second() == 0):
            return "  -  "
        m = str(self.get_minute())
        s = str(self.get_second()).zfill(2)
        h = str(self.get_hundreth()).zfill(2)
        if m == '0':
            return f"{s}.{h}"
        else:
            return f"{m}:{s}.{h}"
    
    def __gt__(self, other_time):
        """
        Return true if self is a longer time than other_time.

        Keyword arguments:
        other_time -- Time object that is being compared against
        """
        # Compare minutes
        if self.get_minute() > other_time.get_minute():
            return True
        if self.get_minute() < other_time.get_minute():
            return False
        # Compare seconds
        if self.get_second() > other_time.get_second():
            return True
        if self.get_second() < other_time.get_second():
            return False
        # Compare hundreths
        if self.get_hundreth() > other_time.get_hundreth():
            return True
        if self.get_hundreth() < other_time.get_hundreth():
            return False
        # Self must equal other_time so return false
        return False
    
    def __lt__(self, other_time):
        """
        Return true if self is a shorter time than other_time.

        Keyword arguments:
        other_time -- Time object that is being compared against
        """
        return other_time > self
    
    def __eq__(self, other_time):
        """
        Return true if self is equal to other_time.

        Keyword arguments:
        other_time -- Time object that is being compared against
        """
        return self.get_minute() == other_time.get_minute() \
           and self.get_second() == other_time.get_second() \
           and self.get_hundreth() == other_time.get_hundreth()
    
    def __ge__(self, other_time):
        return self > other_time or self == other_time

    def __le__(self, other_time):
        return other_time >= self

    def __add__(self, other_time):
        """
        Return the sum of self and other_time.

        Keyword arguments:
        other_time -- Time object that is being added to self.
        """
        hundreth = self.hundreth + other_time.get_hundreth()
        second = self.second + other_time.get_second()
        minute = self.minute + other_time.get_minute()
        if hundreth >= 100:
            hundreth = hundreth % 100
            second += 1
        if second >= 60:
            second = second % 60
            minute += 1
        return Time(minute, second, hundreth)

    def __sub__(self, other_time):
        """
        Return the difference of self and other_time.

        Keyword arguments:
        other_time -- Time object that is being subtracted from self.
        """
        if other_time > self:
            return
        hundreth = self.get_hundreth()
        second = self.get_second()
        minute = self.get_minute
        t_hundreth = other_time.get_hundreth()
        t_second = other_time.get_second()
        t_minute = other_time.get_minute()
        if hundreth < t_hundreth:
            second = second - 1
            hundreth = hundreth + 100
        hundreth = hundreth - t_hundreth
        if second < t_second:
            minute = minute - 1
            second = second + 60
        second = second - t_second
        minute = minute - t_minute
        return Time(minute, second, hundreth)
    
    def get_minute(self):
        """
        Return self.minute attribute of time instance.
        """
        return self.minute

    def get_second(self):
        """
        Return self.second attribute of time instance.
        """
        return self.second
    
    def get_hundreth(self):
        """
        Return self.hundreth attribute of time instance.
        """
        return self.hundreth


class Util():
    """
    Utility class for constants and methods.
    """
    distances = [25, 50, 100, 200, 400, 500, 800, 1000, 1500, 1650]
    strokes = [1, 2, 3, 4, 5]
    courses = ['S', 'Y', 'L']
    valid_events = [(25, 1, 'Y'), (50, 1, 'Y'), (100, 1, 'Y'), (200, 1, 'Y'),
                    (400, 1, 'Y'), (500, 1, 'Y'), (800, 1, 'Y'), (1000, 1, 'Y'), 
                    (1650, 1, 'Y'),
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
    sessions = [1, 2, 3]
    stroke_to_str = {1: "Free", 2: "Back", 3: "Breast", 4: "Fly", 5: "IM"}
    stroke_to_str_short = {1: "FR", 2: "BK", 3: "BR", 4: "FL", 5: "IM"}
    course_to_str = {'Y': "SCY", 'S': "SCM", 'L': "LCM"}
    session_to_str = {1: "Prelims", 2: "Swim-off", 3: "Finals"}
    age_group_to_min_max = {'10&u': (0, 10),
                            '11-12': (11, 12),
                            '13-14': (13, 14),
                            '15-16': (15, 16),
                            '17-18': (17, 18),
                            'senior': (13, 100)}
    sex_code = ['F', 'M']
    gender_to_str = {'F': 'Female',
                     'M': 'Male'}
    
    
    def standardize_course(course: str | int) -> str:
        """
        Standardize course to string format.

        Keyword arguments:
        course -- course specified in D0 line 
        """
        if course == 'S' or course == 1:
            return 'S'
        if course == 'Y' or course == 2:
            return  'Y'
        if course == 'L' or course == 3:
            return 'L'
        return course
    
    def create_time(time_str: str) -> Time:
        """
        Convert time_str to Time object.

        Keyword arguments:
        time_str -- time string specified in D0 line
        """
        invalid_results = ["DQ", "NS", "DNF", "SCR"]
        if not time_str.strip() or time_str.strip() in invalid_results:
            return
        minutes = time_str[0:2]
        if not minutes.strip():
            minutes = 0
        else:
            minutes = int(minutes)
        seconds = int(time_str[3:5])
        hundreths = int(time_str[6:8])
        return Time(minutes, seconds, hundreths)
    
