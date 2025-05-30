"""
Core logic for relay generation.
"""

import datetime

import database

type relay = list[database.swim.Swimmer]


class RelayGenerator:
    """
    Generates optimal relays based on current settings.
    """

    def __init__(
        self,
        db: database.Database,
        club: database.swim.Club,
        relay_date: datetime.date = datetime.date.today(),
        num_relays: int = 2,
        sex: database.sdif.Sex = database.sdif.Sex.FEMALE,
        course: database.sdif.Course = database.sdif.Course.SCY,
        age_range: tuple[int, int] = (7, 10),
    ) -> None:
        self.set_database(db)
        self.set_club(club)
        self.set_relay_date(relay_date)
        self.set_num_relays(num_relays)
        self.set_sex(sex)
        self.set_course(course)
        self.set_age_range(age_range)

    def set_database(self, db: database.Database) -> None:
        self.db = db

    def set_club(self, club: database.swim.Club) -> None:
        self.club = club

    def set_relay_date(self, relay_date: datetime.date) -> None:
        self.relay_date = relay_date

    def set_num_relays(self, num_relays: int) -> None:
        self.num_relays = num_relays

    def set_sex(self, sex: database.sdif.Sex) -> None:
        self.sex = sex

    def set_course(self, course: database.sdif.Course) -> None:
        self.course = course

    def set_age_range(self, age_range: tuple[int, int]) -> None:
        assert type(age_range) == tuple
        assert len(age_range) == 2
        assert age_range[1] > age_range[0]
        self.age_range = age_range

    def get_database(self) -> database.Database:
        return self.db

    def get_club(self) -> database.swim.Club:
        return self.club

    def get_relay_date(self) -> datetime.date:
        return self.relay_date

    def get_num_relays(self) -> int:
        return self.num_relays

    def get_sex(self) -> database.sdif.Sex:
        return self.sex

    def get_course(self) -> database.sdif.Course:
        return self.course

    def get_age_range(self) -> tuple[int, int]:
        return self.age_range

    def generate_relays(self, event: database.sdif.Event) -> list[relay]:
        """
        Generate relays based on the current settings.
        """
        if event.get_stroke() == database.sdif.Stroke.FREESTYLE_RELAY:
            return self.generate_free_relays(event)
        else:
            return []

    def generate_free_relays(self, event: database.sdif.Event) -> list[relay]:
        assert event.get_stroke() == database.sdif.Stroke.FREESTYLE_RELAY

        leg_distance = event.get_distance() // 4
        leg_stroke = database.sdif.Stroke.FREESTYLE
        leg_course = event.get_course()
        leg_event = database.sdif.Event((leg_distance, leg_stroke, leg_course))

        # Construct list of valid swimmers for relay generation
        best_results: list[tuple[database.swim.Swimmer, database.stime.Time]]
        best_results = []
        for swimmer in self.get_club().get_swimmers():
            # Only consider swimmers with the right sex
            if swimmer.get_sex() != self.get_sex():
                continue

            # Check if swimmer is the right age. Because birthdays might not exist,
            # we consider anyone who might be the right age.
            min_age, max_age = swimmer.get_age_range(self.get_relay_date())
            if (min_age >= self.age_range[0] and min_age <= self.age_range[1]) or (
                max_age >= self.age_range[0] and max_age <= self.age_range[1]
            ):
                best_meet_result = swimmer.get_best_meet_result(leg_event)
                if best_meet_result is not None:
                    best_results.append((swimmer, best_meet_result.get_final_time()))
        best_results.sort(key=lambda x: x[1])

        # Generate relays
        relays: list[list[database.swim.Swimmer]]
        relays = []
        relays_to_generate = self.num_relays

        while relays_to_generate > 0:
            relay = []
            if len(best_results) >= 4:
                for i in range(4):
                    relay.append(best_results[i][0])
                best_results = best_results[4:]

            relays.append(relay)
            relays_to_generate -= 1

        return relays
