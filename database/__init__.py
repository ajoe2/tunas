"""
Backend data structures for tunas application.
"""

from . import swim
from .util import sdif, stime


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

    def add_swimmer(self, swimmer: swim.Swimmer)-> None:
        assert type(swimmer) == swim.Swimmer
        self.swimmers.append(swimmer)

    def add_meet(self, meet: swim.Meet) -> None:
        assert type(meet) == swim.Meet
        self.meets.append(meet)

    def add_meet_result(self, meet_result: swim.MeetResult) -> None:
        assert isinstance(meet_result, swim.MeetResult)
        self.meet_results.append(meet_result)
