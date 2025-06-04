"""
Relay generation logic.
"""

import datetime
import itertools

import database


FREESTYLE_RELAY_STROKES = [
    database.sdif.Stroke.FREESTYLE,
    database.sdif.Stroke.FREESTYLE,
    database.sdif.Stroke.FREESTYLE,
    database.sdif.Stroke.FREESTYLE,
]
MEDLEY_RELAY_STROKES = [
    database.sdif.Stroke.BACKSTROKE,
    database.sdif.Stroke.BREASTSTROKE,
    database.sdif.Stroke.BUTTERFLY,
    database.sdif.Stroke.FREESTYLE,
]


class RelayGenerator:
    """
    Generate optimal relay assignments.
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
        assert type(db) == database.Database
        self.db = db

    def set_club(self, club: database.swim.Club) -> None:
        assert type(club) == database.swim.Club
        self.club = club

    def set_relay_date(self, relay_date: datetime.date) -> None:
        assert type(relay_date) == datetime.date
        self.relay_date = relay_date

    def set_num_relays(self, num_relays: int) -> None:
        assert type(num_relays) == int and num_relays > 0
        self.num_relays = num_relays

    def set_sex(self, sex: database.sdif.Sex) -> None:
        assert type(sex) == database.sdif.Sex
        self.sex = sex

    def set_course(self, course: database.sdif.Course) -> None:
        assert type(course) == database.sdif.Course
        self.course = course

    def set_age_range(self, age_range: tuple[int, int]) -> None:
        assert type(age_range) == tuple
        assert len(age_range) == 2
        min_age, max_age = age_range
        assert min_age <= max_age

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

    def generate_relays(
        self, event: database.sdif.Event
    ) -> list[list[database.swim.Swimmer]]:
        """
        Generate relays based on the current settings.
        """
        assert (
            event.get_stroke() == database.sdif.Stroke.FREESTYLE_RELAY
            or event.get_stroke() == database.sdif.Stroke.MEDLEY_RELAY
        )
        leg_distance: int
        leg_strokes: list[database.sdif.Stroke]
        leg_course: database.sdif.Course
        leg_events: list[database.sdif.Event]

        # Calculate individual leg events
        leg_distance = event.get_distance() // 4
        leg_course = event.get_course()
        if event.get_stroke() == database.sdif.Stroke.FREESTYLE_RELAY:
            leg_strokes = FREESTYLE_RELAY_STROKES
        else:
            leg_strokes = MEDLEY_RELAY_STROKES
        leg_events = [
            database.sdif.Event((leg_distance, leg_stroke, leg_course))
            for leg_stroke in leg_strokes
        ]

        # Find potential swimmers for each leg
        best_leg1_results: list[tuple[database.swim.Swimmer, database.stime.Time]] = []
        best_leg2_results: list[tuple[database.swim.Swimmer, database.stime.Time]] = []
        best_leg3_results: list[tuple[database.swim.Swimmer, database.stime.Time]] = []
        best_leg4_results: list[tuple[database.swim.Swimmer, database.stime.Time]] = []
        min_age, max_age = self.get_age_range()
        for swimmer in self.get_club().get_swimmers():
            if swimmer.get_sex() != self.get_sex():
                continue
            s_min_age, s_max_age = swimmer.get_age_range(self.get_relay_date())
            if not (s_min_age > max_age or s_max_age < min_age):
                le1, le2, le3, le4 = leg_events
                best_le1_mr = swimmer.get_best_meet_result(le1)
                best_le2_mr = swimmer.get_best_meet_result(le2)
                best_le3_mr = swimmer.get_best_meet_result(le3)
                best_le4_mr = swimmer.get_best_meet_result(le4)
                if best_le1_mr is not None:
                    best_leg1_results.append((swimmer, best_le1_mr.get_final_time()))
                if best_le2_mr is not None:
                    best_leg2_results.append((swimmer, best_le2_mr.get_final_time()))
                if best_le3_mr is not None:
                    best_leg3_results.append((swimmer, best_le3_mr.get_final_time()))
                if best_le4_mr is not None:
                    best_leg4_results.append((swimmer, best_le4_mr.get_final_time()))

        # Sort leg by fastest swimmers
        best_leg1_results.sort(key=lambda x: x[1])
        best_leg2_results.sort(key=lambda x: x[1])
        best_leg3_results.sort(key=lambda x: x[1])
        best_leg4_results.sort(key=lambda x: x[1])

        # Generate optimal relays
        generated_relays: list[list[database.swim.Swimmer]] = []
        remaining_relays: int = self.get_num_relays()
        while remaining_relays > 0:
            # If a leg doesn't have valid swimmers, append an empty relay
            if (
                len(best_leg1_results) == 0
                or len(best_leg2_results) == 0
                or len(best_leg3_results) == 0
                or len(best_leg4_results) == 0
            ):
                generated_relays.append([])
                remaining_relays -= 1
                continue

            # Find top four swimmers for each leg
            top_four_l1 = best_leg1_results[:4]
            top_four_l2 = best_leg2_results[:4]
            top_four_l3 = best_leg3_results[:4]
            top_four_l4 = best_leg4_results[:4]

            # Find best combination of 4 unique swimmers
            best_combination = []
            for candidate_combination in itertools.product(
                top_four_l1, top_four_l2, top_four_l3, top_four_l4
            ):
                candidate_swimmers = [pair[0] for pair in candidate_combination]
                if len(set(candidate_swimmers)) != 4:
                    continue
                elif best_combination == []:
                    best_combination = candidate_combination
                else:
                    # Calculate best_combination time
                    best_comb_time = database.stime.Time(0, 0, 0)
                    for pair in best_combination:
                        best_comb_time += pair[1]

                    # Calculate candidate_combination time
                    candidate_comb_time = database.stime.Time(0, 0, 0)
                    for pair in candidate_combination:
                        candidate_comb_time += pair[1]

                    # Update best combination if candidate has quicker time
                    if candidate_comb_time < best_comb_time:
                        best_combination = candidate_combination

            # Set new relay and remove swimmers from candidate lists
            new_relay = [pair[0] for pair in best_combination]
            best_leg1_results = list(
                filter(lambda x: x[0] not in new_relay, best_leg1_results)
            )
            best_leg2_results = list(
                filter(lambda x: x[0] not in new_relay, best_leg2_results)
            )
            best_leg3_results = list(
                filter(lambda x: x[0] not in new_relay, best_leg3_results)
            )
            best_leg4_results = list(
                filter(lambda x: x[0] not in new_relay, best_leg4_results)
            )
            generated_relays.append(new_relay)
            remaining_relays -= 1

        return generated_relays
