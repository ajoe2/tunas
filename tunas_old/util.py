"""
Helper methods and constants. Includes a custom time class, 
functions for processing input, and meet result constants.
"""


class Time():
    """
    Custom time representation for swim meet results.
    """
    def __init__(self, minute=0, second=0, hundredth=0):
        """
        Create a time oject. There are two ways to create a time object:
        1) Input minute, second, and hundredth
        2) Input a time_str. Must be in m:ss.hh or m:ss:hh* format.

        Keyword arguments:
        minute -- the minutes component (default 0)
        second -- the seconds component (default 0)
        hundredth -- the hundredths component (default 0)
        time_str -- time string
        """
        self.set_minute(minute)
        self.set_second(second)
        self.set_hundredth(hundredth)
    
    def __str__(self) -> str:
        """
        Return string representation of time object. Return empty
        string if time is equal to 0.

        >>> t = Time(1, 15, 23)
        >>> print(t)
        1:15.23
        >>> t2 = Time(0, 32, 10)
        >>> print(t2)
        32.10
        >>> t3 = Time(0, 0, 0)
        >>> str(t3) == ""
        True
        """
        if (self.get_hundredth() == 0 
            and self.get_minute() == 0 
            and self.get_second() == 0):
            return ""
        m = str(self.get_minute())
        s = str(self.get_second()).zfill(2)
        h = str(self.get_hundredth()).zfill(2)
        if m == '0':
            return f"{s}.{h}"
        else:
            return f"{m}:{s}.{h}"
        
    def __repr__(self) -> str:
        """
        Return representation of time object.

        >>> t = Time(1, 15, 23)
        >>> t
        Time(1, 15, 23)
        >>> t2 = Time(0, 32, 10)
        >>> t2
        Time(0, 32, 10)
        """
        return f"Time({self.minute}, {self.second}, {self.hundredth})"
    
    def __gt__(self, other_time) -> bool:
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
        # Compare hundredths
        if self.get_hundredth() > other_time.get_hundredth():
            return True
        if self.get_hundredth() < other_time.get_hundredth():
            return False
        # Self must equal other_time so return false
        return False
    
    def __lt__(self, other_time) -> bool:
        """
        Return true if self is a shorter time than other_time.

        Keyword arguments:
        other_time -- Time object that is being compared against
        """
        return other_time > self
    
    def __eq__(self, other_time) -> bool:
        """
        Return true if self is equal to other_time.

        Keyword arguments:
        other_time -- Time object that is being compared against
        """
        return self.get_minute() == other_time.get_minute() \
           and self.get_second() == other_time.get_second() \
           and self.get_hundredth() == other_time.get_hundredth()
    
    def __ge__(self, other_time) -> bool:
        """
        Return true if self is a greater than or equal time to 
        other_time.

        Keyword arguments:
        other_time -- Time object that is being compared against
        """
        return self > other_time or self == other_time

    def __le__(self, other_time) -> bool:
        """
        Return true if self is a less than or equal time to 
        other_time.

        Keyword arguments:
        other_time -- Time object that is being compared against
        """
        return other_time >= self

    def __add__(self, other_time):
        """
        Return the sum of self and other_time.

        Keyword arguments:
        other_time -- Time object that is being added to self.
        """
        hundredth = self.hundredth + other_time.get_hundredth()
        second = self.second + other_time.get_second()
        minute = self.minute + other_time.get_minute()
        if hundredth >= 100:
            hundredth = hundredth % 100
            second += 1
        if second >= 60:
            second = second % 60
            minute += 1
        return Time(minute, second, hundredth)

    def __sub__(self, other_time):
        """
        Return self minus other_time.

        Keyword arguments:
        other_time -- Time object that is being subtracted from self.
        """
        if other_time > self:
            return
        hundredth = self.get_hundredth()
        second = self.get_second()
        minute = self.get_minute
        t_hundredth = other_time.get_hundredth()
        t_second = other_time.get_second()
        t_minute = other_time.get_minute()
        if hundredth < t_hundredth:
            second = second - 1
            hundredth = hundredth + 100
        hundredth = hundredth - t_hundredth
        if second < t_second:
            minute = minute - 1
            second = second + 60
        second = second - t_second
        minute = minute - t_minute
        return Time(minute, second, hundredth)
    
    def set_minute(self, m: int):
        """
        Verify and set self.minute attribute
        """
        assert type(m) == int, f"Minute should be an integer: {m}"
        assert 0 <= m and m < 60, f"Invalid minute: {m}"
        self.minute = m

    def set_second(self, s: int):
        """
        Verify and set self.second attribute
        """
        assert type(s) == int, f"Seconds should be an integer: {s}"
        assert 0 <= s and s < 60, f"Invalid seconds: {s}"
        self.second = s

    def set_hundredth(self, h: int):
        """
        Verify and set self.hundredth attribute
        """
        assert type(h) == int, f"Hundredths should be an integer: {h}"
        assert 0 <= h and h < 100, f"Invalid hundredths: {h}"
        self.hundredth = h
    
    def get_minute(self) -> int:
        """
        Return self.minute attribute.
        """
        return self.minute

    def get_second(self) -> int:
        """
        Return self.second attribute.
        """
        return self.second
    
    def get_hundredth(self) -> int:
        """
        Return self.hundredth attribute.
        """
        return self.hundredth
    

def create_time_from_str(time_str: str) -> Time:
    """
    Return time object corresponding to time_str. Input string
    should be in mm:ss.hh format.

    Keyword arguments:
    time_str -- time string.
    """
    minute_str, second_str, hundredth_str = "0", "0", "0"
    minute, second, hundredth = 0, 0, 0

    # Parse string
    first_split = time_str.split(":")
    if (len(first_split) == 2):
        minute_str = first_split[0]
    next_split = first_split[-1].split(".")
    if len(next_split) != 2:
        raise Exception(f"Invalid input: '{time_str}'. " + \
                        f"Should be in 'mm:ss.hh' format.")
    second_str = next_split[0]
    hundredth_str = next_split[1]
    try:
        minute = int(minute_str)
        second = int(second_str)
        hundredth = int(hundredth_str)
    except:
        raise Exception(f"Invalid input: '{time_str}'. " + \
                        f"Time is not a valid time.")
    
    return Time(minute, second, hundredth)

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

