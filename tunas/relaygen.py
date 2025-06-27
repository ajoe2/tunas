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


def get_relay_leg_events(
    relay_event: database.dutil.Event,
) -> list[database.dutil.Event]:
    """
    Return leg events for a given relay event.
    """
    is_free_relay = relay_event.get_stroke() == database.sdif.Stroke.FREESTYLE_RELAY
    is_medley_relay = relay_event.get_stroke() == database.sdif.Stroke.MEDLEY_RELAY
    assert is_free_relay or is_medley_relay

    leg_dist = relay_event.get_distance() // 4
    course = relay_event.get_course()
    leg_strokes = FREESTYLE_RELAY_STROKES if is_free_relay else MEDLEY_RELAY_STROKES
    leg_events = [
        database.dutil.Event((leg_dist, strk, course)) for strk in leg_strokes
    ]
    return leg_events


def get_relay_time(
    relay: list[database.swim.Swimmer],
    event: database.dutil.Event,
) -> database.stime.Time:
    """
    Calculate total relay time.
    """
    assert len(relay) == 4

    leg_events = get_relay_leg_events(event)
    total_time = database.stime.Time(0, 0, 0)
    for i in range(4):
        swimmer = relay[i]
        best_mr = swimmer.get_best_meet_result(leg_events[i])
        assert best_mr is not None  # Every swimmer should have a valid time.
        total_time += best_mr.get_final_time()
    return total_time


class RelayGenerator:
    """
    Generate optimal relay assignments and maintain settings.
    """

    def __init__(
        self,
        db: database.Database,
        club: database.swim.Club,
        relay_date: datetime.date = datetime.date.today(),
        num_relays: int = 2,
        sex: database.sdif.Sex = database.sdif.Sex.FEMALE,
        course: database.sdif.Course = database.sdif.Course.LCM,
        age_range: tuple[int, int] = (1, 10),
    ) -> None:
        self.set_database(db)
        self.set_club(club)
        self.set_relay_date(relay_date)
        self.set_num_relays(num_relays)
        self.set_sex(sex)
        self.set_course(course)
        self.set_age_range(age_range)
        self.set_excluded_swimmers(set())

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

    def set_excluded_swimmers(
        self, excluded_swimmers: set[database.swim.Swimmer]
    ) -> None:
        assert type(excluded_swimmers) == set
        for s in excluded_swimmers:
            assert type(s) == database.swim.Swimmer
        self.excluded_swimmers = excluded_swimmers

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

    def get_excluded_swimmers(self) -> set[database.swim.Swimmer]:
        return self.excluded_swimmers

    def exclude_swimmer(self, swimmer: database.swim.Swimmer):
        """
        Exclude swimmer from generated relays. If swimmer was already
        excluded, this does nothing.
        """
        assert type(swimmer) == database.swim.Swimmer
        self.excluded_swimmers.add(swimmer)

    def include_swimmer(self, swimmer: database.swim.Swimmer):
        """
        Include swimmer in generated relays. If swimmer was not originally
        excluded, this raises an error.
        """
        assert type(swimmer) == database.swim.Swimmer
        self.excluded_swimmers.remove(swimmer)

    def generate_relays(
        self, event: database.dutil.Event
    ) -> list[list[database.swim.Swimmer]]:
        """
        Generate relays for given event.
        """
        is_free_relay = event.get_stroke() == database.sdif.Stroke.FREESTYLE_RELAY
        is_medley_relay = event.get_stroke() == database.sdif.Stroke.MEDLEY_RELAY
        assert is_free_relay or is_medley_relay

        # Get leg information, min/max age, and eligible swimmers
        leg_events = get_relay_leg_events(event)
        min_age, max_age = self.get_age_range()
        eligible_swimmers = self.get_club().get_swimmers()

        # Find valid swimmers for each leg
        best_le1: list[tuple[database.swim.Swimmer, database.stime.Time]] = []
        best_le2: list[tuple[database.swim.Swimmer, database.stime.Time]] = []
        best_le3: list[tuple[database.swim.Swimmer, database.stime.Time]] = []
        best_le4: list[tuple[database.swim.Swimmer, database.stime.Time]] = []

        for swimmer in eligible_swimmers:
            # Continue if swimmer is wrong sex or should be excluded
            relay_sex = self.get_sex()
            if relay_sex != database.sdif.Sex.MIXED and swimmer.get_sex() != relay_sex:
                continue
            if swimmer in self.get_excluded_swimmers():
                continue

            # Get swimmer min/max age.
            s_min_age, s_max_age = swimmer.get_age_range(self.get_relay_date())

            # If swimmer is the right age and has a meet result for the given leg
            # event, add them to the list of eligible swimmers.
            if not s_min_age > max_age and not s_max_age < min_age:
                le1, le2, le3, le4 = leg_events
                best_le1_mr = swimmer.get_best_meet_result(le1)
                best_le2_mr = swimmer.get_best_meet_result(le2)
                best_le3_mr = swimmer.get_best_meet_result(le3)
                best_le4_mr = swimmer.get_best_meet_result(le4)
                if best_le1_mr is not None:
                    best_le1.append((swimmer, best_le1_mr.get_final_time()))
                if best_le2_mr is not None:
                    best_le2.append((swimmer, best_le2_mr.get_final_time()))
                if best_le3_mr is not None:
                    best_le3.append((swimmer, best_le3_mr.get_final_time()))
                if best_le4_mr is not None:
                    best_le4.append((swimmer, best_le4_mr.get_final_time()))

        # Sort each relay leg by fastest swimmers
        best_le1.sort(key=lambda x: x[1])
        best_le2.sort(key=lambda x: x[1])
        best_le3.sort(key=lambda x: x[1])
        best_le4.sort(key=lambda x: x[1])

        # Generate optimal relays
        generated_relays = []
        remaining_relays = self.get_num_relays()
        while remaining_relays > 0:
            # Check if we have enough swimmers
            empty_le1 = len(best_le1) == 0
            empty_le2 = len(best_le2) == 0
            empty_le3 = len(best_le3) == 0
            empty_le4 = len(best_le4) == 0
            if empty_le1 or empty_le2 or empty_le3 or empty_le4:
                generated_relays.append([])
                remaining_relays -= 1
                continue

            # If relay is mixed, find the top 2 swimmers for each sex.
            # Otherwise, just take the top 4 for each leg. 
            if relay_sex == database.sdif.Sex.MIXED:
                top_four_l1 = []
                num_male, num_female = 0, 0
                for swimmer, time in best_le1:
                    if len(top_four_l1) == 4:
                        break
                    swimmer_sex = swimmer.get_sex()
                    if swimmer_sex == database.sdif.Sex.MALE and num_male < 2:
                        num_male += 1
                        top_four_l1.append((swimmer, time))
                    if swimmer_sex == database.sdif.Sex.FEMALE and num_female < 2:
                        num_female += 1
                        top_four_l1.append((swimmer, time))
                print(top_four_l1)
                top_four_l2 = []
                num_male, num_female = 0, 0
                for swimmer, time in best_le2:
                    if len(top_four_l2) == 4:
                        break
                    swimmer_sex = swimmer.get_sex()
                    if swimmer_sex == database.sdif.Sex.MALE and num_male < 2:
                        num_male += 1
                        top_four_l2.append((swimmer, time))
                    if swimmer_sex == database.sdif.Sex.FEMALE and num_female < 2:
                        num_female += 1
                        top_four_l2.append((swimmer, time))
                print(top_four_l2)
                top_four_l3 = []
                num_male, num_female = 0, 0
                for swimmer, time in best_le3:
                    if len(top_four_l3) == 4:
                        break
                    swimmer_sex = swimmer.get_sex()
                    if swimmer_sex == database.sdif.Sex.MALE and num_male < 2:
                        num_male += 1
                        top_four_l3.append((swimmer, time))
                    if swimmer_sex == database.sdif.Sex.FEMALE and num_female < 2:
                        num_female += 1
                        top_four_l3.append((swimmer, time))
                print(top_four_l3)
                top_four_l4 = []
                num_male, num_female = 0, 0
                for swimmer, time in best_le4:
                    if len(top_four_l4) == 4:
                        break
                    swimmer_sex = swimmer.get_sex()
                    if swimmer_sex == database.sdif.Sex.MALE and num_male < 2:
                        num_male += 1
                        top_four_l4.append((swimmer, time))
                    if swimmer_sex == database.sdif.Sex.FEMALE and num_female < 2:
                        num_female += 1
                        top_four_l4.append((swimmer, time))
                print(top_four_l4)
            else:
                top_four_l1 = best_le1[:4]
                top_four_l2 = best_le2[:4]
                top_four_l3 = best_le3[:4]
                top_four_l4 = best_le4[:4]

            # Find best combination of 4 unique swimmers
            best_combination = []
            for candidate_combination in itertools.product(
                top_four_l1,
                top_four_l2,
                top_four_l3,
                top_four_l4,
            ):
                candidate_swimmers = [pair[0] for pair in candidate_combination]
                if len(set(candidate_swimmers)) != 4:
                    continue
                if relay_sex == database.sdif.Sex.MIXED:
                    # Only consider relays with 2 males and 2 females.
                    num_male, num_female = 0, 0
                    for swimmer, time in candidate_combination:
                        if swimmer.get_sex() == database.sdif.Sex.MALE:
                            num_male += 1
                        else:
                            num_female += 1
                    if not (num_male == 2 and num_female == 2):
                        continue
                if best_combination == []:
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

            if best_combination == []:
                generated_relays.append([])
                remaining_relays -= 1
                continue

            # Remove swimmers from list of available swimmers
            new_relay = [pair[0] for pair in best_combination]
            best_le1 = list(filter(lambda x: x[0] not in new_relay, best_le1))
            best_le2 = list(filter(lambda x: x[0] not in new_relay, best_le2))
            best_le3 = list(filter(lambda x: x[0] not in new_relay, best_le3))
            best_le4 = list(filter(lambda x: x[0] not in new_relay, best_le4))

            # Add new relay to generated relays
            generated_relays.append(new_relay)
            remaining_relays -= 1

        return generated_relays
