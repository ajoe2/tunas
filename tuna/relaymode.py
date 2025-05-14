
from database import *
from itertools import product
from collections import Counter


class RelayMode():
    """
    Class used in Interface for operating Relay Mode. Supports generating
    optimal relay assignments.
    """
    SETTINGS_MENU = f"Update field:\n" + \
                    f" 1) Club\n" + \
                    f" 2) Age group\n" + \
                    f" 3) Sex\n" + \
                    f" 4) Course\n" + \
                    f" 5) Date\n" + \
                    f" 6) Num relays\n" + \
                    f" Back (b/B)\n"
    RELAY_CHOICE_MENU = f"1) Settings\n" + \
                        f"2) 4 x 50 Free\n" + \
                        f"3) 4 x 50 Medley\n" + \
                        f"4) 4 x 100 Free\n" + \
                        f"5) 4 x 100 Medley\n" + \
                        f"6) 4 x 200 Free\n" + \
                        f"7) Exclude swimmer\n" + \
                        f"8) Include swimmer\n" + \
                        f"Back (b/B)\n"
    RELAY_LETTERS = ['A', 'B', 'C', 'D', 'E']

    def __init__(self, db: Database, date=date.today(), num_relays=2, sex="F", 
                 club="PCSCSC", age_group="10&u", course="L"):
        self.db = db
        self.date = date
        self.num_relays = num_relays
        self.sex = sex
        self.club = club
        self.age_group = age_group
        self.course = course
        self.min_age = float("-inf")
        self.max_age = float("inf")
        self.eligible_swimmers = []
        self.excluded_swimmers = []
        self.update_eligible_swimmers()
    
    def set_date(self, date:date):
        self.date = date

    def set_num_relays(self, num_relays: int):
        if num_relays > 5:
            print("Num relays cannot exceed 5!\n")
        else:
            self.num_relays = num_relays

    def set_sex(self, sex: str):
        self.sex = sex

    def set_club(self, club: str):
        """
        Set self.club to be club.
        """
        self.club = club
    
    def set_age_group(self, age_group: str):
        """
        Set self.age_group to age_group
        """
        self.age_group = age_group
    
    def set_course(self, course: str):
        self.course = course

    def update_eligible_swimmers(self):
        self.min_age, self.max_age = Util.age_group_to_min_max[self.age_group]
        swimmers = self.db.find_club(self.club).swimmers
        self.eligible_swimmers = [swimmer for swimmer in swimmers 
                                  if swimmer.get_age(self.date) >= self.min_age 
                                  and swimmer.get_age(self.date) <= self.max_age 
                                  and swimmer.get_sex() == self.sex 
                                  and swimmer not in self.excluded_swimmers]

    def run_relays(self):
        while True:
            print()
            print(RelayMode.RELAY_CHOICE_MENU)
            relay_type = input(f"Selection > ")
            match relay_type:
                case '1':
                    self.update_settings()
                case '2':
                    self.print_free_relays(50)
                case '3':
                    self.print_im_relays(50)
                case '4':
                    self.print_free_relays(100)
                case '5':
                    self.print_im_relays(100)
                case '6':
                    self.print_free_relays(200)
                case '7':
                    self.exclude_swimmer()
                case '8':
                    self.include_swimmer()
                case 'b' | 'b':
                    break
                case _:
                    print("Invalid selection. Please try again.")

    def display_current_settings(self):
        print(f"\nQuery settings:\n" + \
              f"{' --> Club:': <17} {self.club}\n" + \
              f"{' --> Age Group:': <17} {self.age_group}\n" + \
              f"{' --> Sex:': <17} {Util.gender_to_str[self.sex]}\n" + \
              f"{' --> Course:': <17} {Util.course_to_str[self.course]}\n" + \
              f"{' --> Date:': <17} {self.date}\n" + \
              f"{' --> Num relays:': <17} {self.num_relays}\n"
        )

    def update_settings(self):
        while True:
            self.display_current_settings()
            print(RelayMode.SETTINGS_MENU)
            selection = input("Selection > ")
            match selection:
                case '1':
                    self.update_club()
                case '2':
                    self.update_age_group()
                case '3':
                    self.update_sex()
                case '4':
                    self.update_course()
                case '5':
                    self.update_date()
                case '6':
                    self.update_num_relays()
                case 'b' | 'B':
                    break
        self.update_eligible_swimmers()

    def update_club(self):
        new_club = input("New club code > ")
        if not self.db.find_club(new_club):
            print("Invalid club code.")
        else:
            self.set_club(new_club)
            print("Club updated to:", new_club)

    def update_age_group(self):
        age_group_index = input(f"\n" + \
                                f"1) 10&u\n" + \
                                f"2) 11-12\n" + \
                                f"3) 13-14\n" + \
                                f"4) 15-16\n" + \
                                f"5) 17-18\n" + \
                                f"6) senior\n" + \
                                f"\n" + \
                                f"New age group > ")
        if age_group_index not in ['1', '2', '3', '4', '5', '6']:
            print("Invalid selection.")
            return
        age_group_index = int(age_group_index) - 1
        age_group = list(Util.age_group_to_min_max.keys())[age_group_index]
        self.set_age_group(age_group)  
        print("Age group updated to:", age_group)

    def update_sex(self):
        sex_index = input(f"\n1) Female\n2) Male\n\nNew sex > ")
        if sex_index not in ['1', '2']:
            print("Invalid selection.")
        else:
            sex_index = int(sex_index) - 1
            self.set_sex(['F', 'M'][sex_index])
            print("Sex updated to:", Util.gender_to_str[self.sex])

    def update_course(self):
        course = input(f"\n1) SCM\n2) SCY\n3) LCM\n\nNew course > ")
        if course not in ['1', '2', '3']:
            print("Invalid selection.")
        else:
            course = {'1': 'S', '2': 'Y', '3': 'L'}[course]
            self.set_course(course)
            print("Course updated to:", Util.course_to_str[course])

    def update_date(self):
        try:
            q_year = int(input("Year of relay (ex. '2025'): "))
            q_month = int(input("Month of relay (ex. '01'): "))
            q_day = int(input("Day of relay (ex. 01): "))
            relay_date = date(q_year, q_month, q_day)
        except ValueError:
            print("Invalid input. Please try again.")
        else:
            self.set_date(relay_date)
            print("Date updated to:", self.date)

    def update_num_relays(self):
        try:
            num_relays = int(input("Number of relays: "))
        except ValueError:
            print("Invalid input. Please try again.")
        else:
            if num_relays <= 5 and num_relays >= 1:
                self.set_num_relays(num_relays)
                print("Num relays updated to:", self.num_relays)
            else:
                print("Too many relays! Maximum number of relays is 5.")
    
    def fastest_swimmers(self, swimmers_lst: list[Swimmer], stroke: int, 
                         dist: int, limit: int) -> list[Swimmer]:
        valid_swimmers = [s for s in swimmers_lst
                          if s.get_best_meet_result(dist, stroke, self.course)]
        best_time = lambda s: s.get_best_time(dist, stroke, self.course)
        return sorted(valid_swimmers, key=best_time)[:limit]
    
    def print_free_relays(self, dist: int):
        relays = self.generate_free_relays(dist)
        if len(relays) < self.num_relays:
            print(f"Not enough swimmers for {self.num_relays} free relays. "
                  f"Please update settings and try again.")
            return
        for i in range(self.num_relays):
            s1, s2, s3, s4 = relays[i]
            time = self.relay_time(relays[i], dist, mode='free')
            r_time_standard = None
            if self.age_group != "senior":
                r_age = int(self.age_group[:2])
            elif self.age_group == "senior":
                r_age = 19
            r_time_standard = self.db.get_highest_standard(time, self.sex, 
                                                           r_age, 1, dist * 4, 
                                                           self.course, 
                                                           relay=True)    
            if not r_time_standard:
                r_time_standard = ""
            print(f"\n" + \
                  f"4x{dist} Freestyle Relay " + \
                  f"{Util.course_to_str[self.course]} " + \
                  f"'{RelayMode.RELAY_LETTERS[i]}' " + \
                  f"[{time}] {r_time_standard}")
            for s in [s1, s2, s3, s4]:
                best_time = s.get_best_time(dist, 1, self.course)
                best_result = s.get_best_meet_result(dist, 1, self.course)
                meet_name = best_result.get_meet().get_name()
                age = s.get_age(self.date)
                time_standard = self.db.get_highest_standard(best_time, 
                                                             s.get_sex(), 
                                                             age, 1, dist, 
                                                             self.course)
                if not time_standard:
                    time_standard = ""
                print(f" {'Free': <6}  {s.get_full_name(): <28}  " + \
                      f"{age: >2}  {s.get_id(): <12}  {self.club: <6}  " + \
                      f"{str(best_time): >7}  {time_standard: <4}  " + \
                      f"{meet_name: <30}")

    def print_im_relays(self, dist: int):
        relays = self.generate_IM_relays(dist)
        if len(relays) < self.num_relays:
            print(f"Not enough swimmers for {self.num_relays} medley relays. "
                  f"Please update settings and try again.")
            return
        for i in range(self.num_relays):
            relay = relays[i]
            time = self.relay_time(relay, dist, mode='medley')
            strokes = ['Back', 'Breast', 'Fly', 'Free']
            stroke_nums = [2, 3, 4, 1]
            time_standard = None
            if self.age_group != "senior":
                r_age = int(self.age_group[:2])
            elif self.age_group == "senior":
                r_age = 19
            time_standard = self.db.get_highest_standard(time, self.sex, 
                                                         r_age, 5, dist * 4, 
                                                         self.course, 
                                                         relay=True)
            if not time_standard:
                time_standard = ""
            print(f"\n" + \
                  f"4x{dist} Medley Relay: " + \
                  f"{Util.course_to_str[self.course]} " + \
                  f"'{RelayMode.RELAY_LETTERS[i]}' " + \
                  f"[{time}] {time_standard}")
            for s, stroke_name, stroke_num in zip(relay, strokes, stroke_nums):
                best_time = s.get_best_time(dist, stroke_num, self.course)
                result = s.get_best_meet_result(dist, stroke_num, self.course)
                meet_name = result.meet.get_name()
                age = s.get_age(self.date)
                time_standard = self.db.get_highest_standard(best_time, 
                                                             s.get_sex(), 
                                                             age, stroke_num, 
                                                             dist, self.course)
                if not time_standard:
                    time_standard = ""
                print(f" {stroke_name: <6}  {s.get_full_name(): <28}  " + \
                      f"{age: >2}  {s.id: <12}  {self.club: <6}  " + \
                      f"{str(best_time): >7}  {time_standard: <4}  " + \
                      f"{meet_name: <30}")

    def generate_free_relays(self, dist: int) -> list[list[Swimmer]]:
        top_free = self.fastest_swimmers(self.eligible_swimmers, 1, 
                                         dist, self.num_relays * 4)
        relays = []
        for _ in range(self.num_relays):
            if len(top_free) < 4:
                break
            relay = top_free[:4]
            top_free = top_free[4:]
            relays.append(relay)
        return relays
    
    def generate_IM_relays(self, dist: int) -> list[list[Swimmer]]:
        relays = []
        swimmers_lst = self.eligible_swimmers.copy()
        for _ in range(self.num_relays):
            top_back = self.fastest_swimmers(swimmers_lst, 2, dist, 4)
            top_breast = self.fastest_swimmers(swimmers_lst, 3, dist, 4)
            top_fly = self.fastest_swimmers(swimmers_lst, 4, dist, 4)
            top_free = self.fastest_swimmers(swimmers_lst, 1, dist, 4)
            if not top_back or not top_breast or not top_fly or not top_free:
                break
            best_relay = None
            for s1, s2, s3, s4 in product(top_back, top_breast, top_fly, top_free):
                relay = [s1, s2, s3, s4]
                num_unique = len(Counter(relay).keys())
                if num_unique < 4:
                    continue
                elif not best_relay:
                    best_relay = relay
                else:
                    curr = self.relay_time(relay, dist, mode="medley")
                    best = self.relay_time(best_relay, dist, mode="medley")
                    if curr < best:
                        best_relay = relay
            relays.append(best_relay)
            for j in range(4):
                swimmers_lst.remove(best_relay[j])
        return relays
    
    def relay_time(self, relay: list[Swimmer], dist: int, mode: str) -> Time:
        time = Time(0, 0, 0)
        mode_to_strokes = {"free": [1, 1, 1, 1], "medley": [2, 3, 4, 1]}
        try:
            strokes = mode_to_strokes[mode]
        except KeyError:
            pass
        else:
            for i in range(4):
                time += relay[i].get_best_time(dist, strokes[i], self.course)
        return time

    def move_swimmer(self, source: list, dest: list, id: str) -> Swimmer:
        swimmer = None
        for s in source:
            if s.id == id:
                swimmer = s
                break
        if swimmer:
            source.remove(swimmer)
            dest.append(swimmer)
        return swimmer

    def exclude_swimmer(self):
        self.print_excluded_swimmers()
        id = input("\nSwimmer id to remove (b/B for back) > ")
        if id == 'b' or id == 'B':
            return
        swimmer = self.move_swimmer(self.eligible_swimmers, self.excluded_swimmers, id)
        if not swimmer:
            print("Swimmer not found! Check id and try again.")
        else:
            print("Success! Excluded:", swimmer)

    def include_swimmer(self):
        self.print_excluded_swimmers()
        id = input("\nSwimmer id to include (b/B for back) > ")
        if id == 'b' or id == 'B':
            return
        swimmer = self.move_swimmer(self.excluded_swimmers, self.eligible_swimmers, id)
        if not swimmer:
            print("Swimmer not found! Check id and try again.")
        else:
            print("Success! Included:", swimmer)

    def print_excluded_swimmers(self):
        print("\nExcluded swimmers:")
        for swimmer in self.excluded_swimmers:
            print(" -->", swimmer)

