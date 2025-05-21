"""
Backend data structures for tunas application.
"""

from . import stime, swim


def create_time_from_str(time_str: str) -> stime.Time:
    """
    Create and return a time object corresponding to time_str. time_str
    should be in mm:ss.hh format.
    """
    minute_str, second_str, hundredth_str = "0", "0", "0"
    minute, second, hundredth = 0, 0, 0

    # Parse string
    first_split = time_str.split(":")
    if len(first_split) == 2:
        minute_str = first_split[0]
    next_split = first_split[-1].split(".")
    if len(next_split) != 2:
        raise Exception(f"Invalid input: '{time_str}'. Should be in 'mm:ss.hh' format.")
    second_str = next_split[0]
    hundredth_str = next_split[1]
    try:
        minute = int(minute_str)
        second = int(second_str)
        hundredth = int(hundredth_str)
    except:
        raise Exception(f"Invalid input: '{time_str}'. Time is not a valid time.")

    return stime.Time(minute, second, hundredth)


class Database:
    def __init__(
        self,
        clubs: list[swim.Club] = [],
        swimmers: list[swim.Swimmer] = [],
        meets: list[swim.Meet] = [],
        meet_results: list[swim.MeetResult] = [],
    ) -> None:
        self.set_clubs(clubs)
        self.set_swimmers(swimmers)
        self.set_meets(meets)
        self.set_meet_results(meet_results)

    def get_clubs(self) -> list[swim.Club]:
        return self.clubs

    def get_swimmers(self) -> list[swim.Swimmer]:
        return self.swimmers

    def get_meets(self) -> list[swim.Meet]:
        return self.meets

    def get_meet_results(self) -> list[swim.MeetResult]:
        return self.meet_results

    def set_clubs(self, clubs: list[swim.Club]) -> None:
        assert type(clubs) == list
        for c in clubs:
            assert type(c) == swim.Club
        self.clubs = clubs

    def set_swimmers(self, swimmers: list[swim.Swimmer]) -> None:
        assert type(swimmers) == list
        for s in swimmers:
            assert type(s) == swim.Swimmer
        self.swimmers = swimmers

    def set_meets(self, meets: list[swim.Meet]) -> None:
        assert type(meets) == list
        for m in meets:
            assert type(m) == swim.Meet
        self.meets = meets

    def set_meet_results(self, meet_results: list[swim.MeetResult]) -> None:
        assert type(meet_results) == list
        for mr in meet_results:
            assert isinstance(mr, swim.MeetResult)
        self.meet_results = meet_results

    def add_club(self, club: swim.Club) -> None:
        assert type(club) == swim.Club
        self.clubs.append(club)

    def add_swimmer(self, swimmer: swim.Swimmer) -> None:
        assert type(swimmer) == swim.Swimmer
        self.swimmers.append(swimmer)

    def add_meet(self, meet: swim.Meet) -> None:
        assert type(meet) == swim.Meet
        self.meets.append(meet)

    def add_meet_result(self, meet_result: swim.MeetResult) -> None:
        assert isinstance(meet_result, swim.MeetResult)
        self.meet_results.append(meet_result)
