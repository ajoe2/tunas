"""
Backend data structures for tunas application.
"""

from . import stime, swim, sdif, dutil
from typing import Optional
import datetime


def create_time_from_str(time_str: str) -> stime.Time:
    """
    Create and return a time object corresponding to time_str which should be in
    mm:ss.hh format.
    """
    minute_str, second_str, hundredth_str = "0", "0", "0"
    minute, second, hundredth = 0, 0, 0

    # Parse string
    first_split = time_str.split(":")
    if len(first_split) == 2:
        minute_str = first_split[0]
    next_split = first_split[-1].split(".")
    if len(next_split) != 2:
        raise Exception(f"Invalid time string: '{time_str}'")
    second_str = next_split[0]
    hundredth_str = next_split[1]
    try:
        minute = int(minute_str)
        second = int(second_str)
        hundredth = int(hundredth_str)
    except:
        raise Exception(f"Invalid time string: '{time_str}'")

    return stime.Time(minute, second, hundredth)


class Database:
    """
    Stores information loaded from data files. Has access to all clubs, swimmers,
    meets, and meet_results.
    """

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

    def find_swimmer_with_short_id(self, short_id: str) -> swim.Swimmer | None:
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
        meet_start_date: datetime.date,
        age_class: str,
    ) -> Optional[swim.Swimmer]:
        old_id = sdif.get_old_id(first_name, middle_initial, last_name, birthday)
        for swimmer in self.get_swimmers():
            swimmer_birthday = swimmer.get_birthday()
            if swimmer_birthday != birthday:
                continue
            swimmer_first_name = swimmer.get_first_name()
            swimmer_last_name = swimmer.get_last_name()
            swimmer_middle_initial = swimmer.get_middle_initial()
            if swimmer_birthday is not None:
                # Find swimmer by generating old ids and comparing hamming distance
                swimmer_id = sdif.get_old_id(
                    swimmer_first_name,
                    swimmer_middle_initial,
                    swimmer_last_name,
                    swimmer_birthday,
                )
                if dutil.hamming_distance(swimmer_id, old_id) <= 1:
                    return swimmer
            else:
                # Find swimmers with the same name and age
                if not age_class.isnumeric():
                    return None
                if (
                    swimmer_first_name == first_name
                    and swimmer_last_name == last_name
                    and swimmer_middle_initial == middle_initial
                    and int(age_class) >= swimmer.get_age_range(meet_start_date)[0]
                    and int(age_class) <= swimmer.get_age_range(meet_start_date)[1]
                ):
                    return swimmer
        return None
