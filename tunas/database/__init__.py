"""
Database backend for tunas application.
"""

from . import swim, dutil, timestandard, sdif, stime
from typing import Optional
import datetime


class Database:
    """
    Stores information loaded from meet result data files.
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
        self.time_standard_info = timestandard.TimeStandardInfo()

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
        """
        Find swimmer in database who has id equal to short_id. Short id should
        be in the new usa swimming id format.
        """
        assert len(short_id) == 12
        for s in self.get_swimmers():
            if s.get_usa_id_short() == short_id:
                return s

    def find_swimmer_with_long_id(self, long_id: str) -> swim.Swimmer | None:
        """
        Find swimmer in database who has id equal to short_id. Short id should
        be in the new usa swimming id format.
        """
        assert len(long_id) == 14
        for s in self.get_swimmers():
            if s.get_usa_id_long() == long_id:
                return s

    def find_swimmer_with_birthday(
        self,
        first_name: str,
        middle_initial: Optional[str],
        last_name: str,
        birthday: datetime.date,
    ) -> Optional[swim.Swimmer]:
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

    def find_club(self, club_code: str) -> Optional[swim.Club]:
        assert type(club_code) == str and len(club_code) <= 4
        for c in self.get_clubs():
            if c.get_team_code() == club_code:
                return c
        return None
