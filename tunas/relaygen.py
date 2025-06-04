"""
Core logic for relay generation.
"""

import datetime
import itertools

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
            return self.generate_medley_relays(event)

    def generate_free_relays(self, event: database.sdif.Event) -> list[relay]:
        assert event.get_stroke() == database.sdif.Stroke.FREESTYLE_RELAY

        leg_distance = event.get_distance() // 4
        leg_stroke = database.sdif.Stroke.FREESTYLE
        leg_course = event.get_course()
        leg_event = database.sdif.Event((leg_distance, leg_stroke, leg_course))

        # Construct list of valid swimmers for relay generation
        best_results: list[tuple[database.swim.Swimmer, database.stime.Time]] = []
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

    def generate_medley_relays(self, event: database.sdif.Event) -> list[relay]:
        """
        Generate medley relays. TODO: if this is fast, can combine with the free relay logic.
        """
        assert event.get_stroke() == database.sdif.Stroke.MEDLEY_RELAY
        leg_distance = event.get_distance() // 4
        leg_strokes = [
            database.sdif.Stroke.BACKSTROKE,
            database.sdif.Stroke.BREASTSTROKE,
            database.sdif.Stroke.BUTTERFLY,
            database.sdif.Stroke.FREESTYLE,
        ]
        leg_course = event.get_course()
        leg_events = [
            database.sdif.Event((leg_distance, stroke, leg_course))
            for stroke in leg_strokes
        ]

        # Compile fastest swimmers for each leg event
        best_results_back: list[tuple[database.swim.Swimmer, database.stime.Time]] = []
        best_results_breast: list[tuple[database.swim.Swimmer, database.stime.Time]] = (
            []
        )
        best_results_fly: list[tuple[database.swim.Swimmer, database.stime.Time]] = []
        best_results_free: list[tuple[database.swim.Swimmer, database.stime.Time]] = []

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
                back_result = swimmer.get_best_meet_result(leg_events[0])
                if back_result is not None:
                    best_results_back.append((swimmer, back_result.get_final_time()))
                breast_result = swimmer.get_best_meet_result(leg_events[1])
                if breast_result is not None:
                    best_results_breast.append(
                        (swimmer, breast_result.get_final_time())
                    )
                fly_result = swimmer.get_best_meet_result(leg_events[2])
                if fly_result is not None:
                    best_results_fly.append((swimmer, fly_result.get_final_time()))
                free_result = swimmer.get_best_meet_result(leg_events[3])
                if free_result is not None:
                    best_results_free.append((swimmer, free_result.get_final_time()))

        # Sort lists by fastest results
        best_results_back.sort(key=lambda x: x[1])
        best_results_breast.sort(key=lambda x: x[1])
        best_results_fly.sort(key=lambda x: x[1])
        best_results_free.sort(key=lambda x: x[1])

        relays = []
        num_relays = self.get_num_relays()
        while num_relays > 0:
            # If we can't generate a relay, return.
            if (
                len(best_results_free) == 0
                or len(best_results_breast) == 0
                or len(best_results_back) == 0
                or len(best_results_fly) == 0
            ):
                break

            # Compile top 4 fastest swimmers for each event
            top_four_back = best_results_back[:4]
            top_four_breast = best_results_breast[:4]
            top_four_fly = best_results_fly[:4]
            top_four_free = best_results_free[:4]

            best_relay = []
            for relay in itertools.product(top_four_back, top_four_breast, top_four_fly, top_four_free):
                if len(set([r[0] for r in relay])) < 4:
                    continue
                elif best_relay == []:
                    best_relay = relay
                else:
                    best_time = database.stime.Time()
                    for r in best_relay:
                        best_time = best_time + r[1]

                    curr_time = database.stime.Time()
                    for r in relay:
                        curr_time = curr_time + r[1]
                    
                    if curr_time < best_time:
                        best_relay = relay
            
            assert len(best_relay) == 4
            best_relay = [r[0] for r in best_relay]

            best_results_back = list(filter(lambda r: r[0] not in best_relay, best_results_back))
            best_results_breast = list(filter(lambda r: r[0] not in best_relay, best_results_breast))
            best_results_fly = list(filter(lambda r: r[0] not in best_relay, best_results_fly))
            best_results_free = list(filter(lambda r: r[0] not in best_relay, best_results_free))

            relays.append(best_relay)
            num_relays -= 1

        return relays
