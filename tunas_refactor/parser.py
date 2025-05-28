"""
Parser for tunas application. Handle reading data and creating underlying data
structure for higher level application code.
"""

import datetime
import os

import database
import util
from database import swim, sdif


def read_cl2(file_path: str) -> database.Database:
    """
    Return database object containing data from all cl2 files in file_path.
    """
    db = database.Database()
    processor = Cl2Processor(db)

    # Find cl2 files
    paths = []
    for root, dirs, files in os.walk(file_path):
        for f in files:
            if f.endswith(".cl2"):
                full_file_path = os.path.join(root, f)
                paths.append(full_file_path)

    # Load cl2 files into database
    files_read = 0
    for p in paths:
        processor.read_file(p)
        files_read += 1
        print(f"Files read: {files_read}", end="\r")
    print()

    return db


class Cl2Processor:
    def __init__(self, db: database.Database):
        self.db = db
        self.meet = None
        self.current_club = None
        self.current_swimmer = None

    def read_file(self, path: str):
        with open(path, "r") as file:
            for line in file:
                header = line[:2]
                match header:
                    case "A0":
                        pass
                    case "B1":
                        self.process_b1(line)
                    case "B2":
                        pass
                    case "C1":
                        self.process_c1(line)
                    case "C2":
                        pass
                    case "D0":
                        self.process_d0(line)
                    case "D1":
                        pass
                    case "D2":
                        pass
                    case "D3":
                        pass
                    case "E0":
                        pass
                    case "F0":
                        pass
                    case "G0":
                        pass
                    case "Z0":
                        self.process_z0(line)

    def process_b1(self, line: str) -> None:
        # Parse line
        org_code_str = line[2].strip()
        name_str = line[11:41].strip()
        address_one_str = line[41:63].strip()
        address_two_str = line[63:85].strip()
        city_str = line[85:105].strip()
        state_str = line[105:107].strip()
        postal_code_str = line[107:117].strip()
        country_code_str = line[117:120].strip()
        meet_type_str = line[120:121].strip()
        start_date_str = line[121:129].strip()
        end_date_str = line[129:137].strip()
        altitude_str = line[137:141].strip()
        course_code_str = line[149].strip()

        # Convert mandatory line components to internal type
        organization = sdif.Organization(org_code_str)
        name = name_str
        city = city_str
        address_one = address_one_str
        start_date = datetime.date(
            int(start_date_str[4:]),
            int(start_date_str[:2]),
            int(start_date_str[2:4]),
        )
        end_date = datetime.date(
            int(end_date_str[4:]),
            int(end_date_str[:2]),
            int(end_date_str[2:4]),
        )

        # Convert optional line components to internal type
        if address_two_str != "":
            address_two = address_two_str
        else:
            address_two = None
        if state_str != "":
            state = sdif.State(state_str)
        else:
            state = None
        if postal_code_str != "":
            postal_code = postal_code_str
        else:
            postal_code = None
        if country_code_str != "":
            country = sdif.Country(country_code_str)
        else:
            country = None
        if course_code_str != "":
            course = sdif.Course(util.standardize_course(course_code_str))
        else:
            course = None
        if altitude_str != "":
            altitude = int(altitude_str)
        else:
            altitude = None
        if meet_type_str != "":
            meet_type = sdif.MeetType(meet_type_str)
        else:
            meet_type = None

        # Create meet object
        new_meet = swim.Meet(
            organization,
            name,
            city,
            address_one,
            start_date,
            end_date,
            state,
            address_two,
            postal_code,
            country,
            course,
            altitude,
            meet_type,
        )
        self.current_meet = new_meet
        self.db.add_meet(new_meet)

    def process_c1(self, line: str) -> None:
        org_code_str = line[2].strip()
        lsc_code_str = line[11:13].strip()
        team_code_str = line[13:17].strip()
        full_name_str = line[17:47].strip()
        abbreviated_name_str = line[47:63].strip()
        address_one_str = line[63:85].strip()
        address_two_str = line[85:107].strip()
        city_str = line[107:127].strip()
        state_str = line[127:129].strip()
        postal_code_str = line[129:139].strip()
        country_code_str = line[139:142].strip()
        region_str = line[142].strip()

        def is_unattached() -> bool:
            """
            Return true if line is an unattached club.
            """
            if lsc_code_str == "UN":
                return True
            if "unattached" in full_name_str.lower():
                return True
            if "UN" in team_code_str.upper() and (
                "unat" in full_name_str.lower() or "unnat" in full_name_str.lower()
            ):
                return True
            return False

        # If unattached, set current club to None
        if is_unattached():
            self.current_club = None
            return

        # Convert string data to internal types
        organization = sdif.Organization(org_code_str)
        full_name = full_name_str
        team_code = team_code_str
        if lsc_code_str in sdif.LSC:
            lsc = sdif.LSC(lsc_code_str)
        else:
            lsc = None
        if abbreviated_name_str != "":
            abbreviated_name = abbreviated_name_str
        else:
            abbreviated_name = None
        if address_one_str != "":
            address_one = address_one_str
        else:
            address_one = None
        if address_two_str != "":
            address_two = address_two_str
        else:
            address_two = None
        if city_str != "":
            city = city_str
        else:
            city = None
        if state_str != "" and state_str in sdif.State:
            state = sdif.State(state_str)
        else:
            state = None
        if postal_code_str != "":
            postal_code = postal_code_str
        else:
            postal_code = None
        if country_code_str != "" and country_code_str in sdif.Country:
            country = sdif.Country(country_code_str)
        else:
            country = None
        if region_str != "":
            region = sdif.Region(region_str)
        else:
            region = None

        # Check for existing club object
        club_exists = False
        for c in self.db.get_clubs():
            if c.get_team_code() == team_code and c.get_lsc() == lsc:
                club_exists = True
                club = c
                break

        # If club exists, update abbributes. Otherwise, create new club.
        if club_exists:
            if club.get_lsc() == None:
                club.set_lsc(lsc)
            if club.get_abbreviated_name() == None:
                club.set_abbreviated_name(abbreviated_name)
            if club.get_address_one() == None:
                club.set_address_one(address_one)
            if club.get_address_two() == None:
                club.set_address_two(address_two)
            if club.get_city() == None:
                club.set_city(city)
            if club.get_state() == None:
                club.set_state(state)
            if club.get_postal_code() == None:
                club.set_postal_code(postal_code)
            if club.get_country() == None:
                club.set_country(country)
            if club.get_region() == None:
                club.set_region(region)
        else:
            club = swim.Club(
                organization,
                team_code,
                lsc,
                full_name,
                abbreviated_name,
                address_one,
                address_two,
                city,
                state,
                postal_code,
                country,
                region,
            )
            self.db.add_club(club)

        # Set current club to the club we just created/found
        self.current_club = club

    def process_d0(self, line: str) -> None:
        assert self.current_meet is not None

        ignored_results = ["NT", "NS", "DNF", "DQ", "SCR"]

        org_code_str = line[2].strip()
        full_name_str = line[11:39].strip()
        swimmer_short_id_str = line[39:51].strip()
        attach_code_str = line[51].strip()
        citizen_code_str = line[52:55].strip()
        b_month_str = line[55:57].strip()
        b_day_str = line[57:59].strip()
        b_year_str = line[59:63].strip()
        age_class_str = line[63:65].strip()
        swimmer_sex_str = line[65].strip()
        event_sex_str = line[66].strip()
        event_distance_str = line[67:71].strip()
        event_stroke_str = line[71].strip()
        event_number_str = line[72:76].strip()
        event_age_code_str = line[76:80].strip()
        event_month_str = line[80:82].strip()
        event_day_str = line[82:84].strip()
        event_year_str = line[84:88].strip()
        seed_time_str = line[88:96].strip()
        seed_course_str = line[96].strip()
        prelim_time_str = line[97:105].strip()
        prelim_course_str = line[105].strip()
        swim_off_time_str = line[106:114].strip()
        swim_off_course_str = line[114].strip()
        finals_time_str = line[115:123].strip()
        finals_course_str = line[123].strip()
        prelim_heat_str = line[124:126].strip()
        prelim_lane_str = line[126:128].strip()
        finals_heat_str = line[128:130].strip()
        finals_lane_str = line[130:132].strip()
        prelim_place_str = line[132:135].strip()
        finals_place_str = line[135:138].strip()
        points_scored_str = line[138:142].strip()

        # Ignore entries without a valid id
        if len(swimmer_short_id_str) != 12:
            return

        # Parse full name
        if full_name_str[-1].isupper() and full_name_str[-2] == " ":
            middle_initial = full_name_str[-1]
            full_name_str = full_name_str[:-2].strip()
        else:
            middle_initial = None
        last_name, first_name = full_name_str.split(",")
        last_name, first_name = last_name.strip(), first_name.strip()
        last_name, first_name = util.title_case(last_name), util.title_case(first_name)

        # Parse sex, id, and age_class
        swimmer_sex = sdif.Sex(swimmer_sex_str)
        usa_id_short = swimmer_short_id_str
        age_class = age_class_str

        # Parse birthday
        if b_day_str and b_month_str and b_year_str:
            # If the birthday is in the data, we just read it.
            birthday = datetime.date(int(b_year_str), int(b_month_str), int(b_day_str))
        elif util.is_old_id(first_name, last_name, middle_initial, usa_id_short):
            # If there is no birthday, but the swimmer has an old id, then we can
            # reverse engineer the birthday.
            b_month = int(usa_id_short[:2])
            b_day = int(usa_id_short[2:4])
            if int(usa_id_short[4:6]) > datetime.date.today().year % 100:
                b_year = int("19" + usa_id_short[4:6])
            else:
                b_year = int("20" + usa_id_short[4:6])
            birthday = datetime.date(b_year, b_month, b_day)

            # We can also get the middle initial from the old id
            if middle_initial == None and usa_id_short[9] != "*":
                middle_initial = usa_id_short[9]
        else:
            # There is no way to retrieve the birthday
            birthday = None

        # Parse rest of data
        organization = sdif.Organization(org_code_str)
        attach_status = sdif.AttachStatus(attach_code_str)
        event_sex = sdif.Sex(event_sex_str)
        event_distance = int(event_distance_str)
        event_stroke = sdif.Stroke(event_stroke_str)
        event_number = event_number_str
        event_year = int(event_year_str)
        event_month = int(event_month_str)
        event_day = int(event_day_str)
        event_date = datetime.date(event_year, event_month, event_day)
        if self.current_club == None:
            team_code = None
            lsc = None
        else:
            team_code = self.current_club.get_team_code()
            lsc = self.current_club.get_lsc()
        if event_age_code_str[0:2] == "UN":
            event_min_age = 0
        else:
            event_min_age = int(event_age_code_str[0:2])
        if event_age_code_str[2:4] == "OV":
            event_max_age = 1000
        else:
            event_max_age = int(event_age_code_str[2:4])
        if citizen_code_str == "":
            citizen_code = None
        else:
            citizen_code = sdif.Country(citizen_code_str)
        if seed_time_str == "":
            seed_time = None
            seed_course = None
        else:
            seed_time = database.create_time_from_str(seed_time_str)
            seed_course = sdif.Course(util.standardize_course(seed_course_str))
        if prelim_time_str == "" or prelim_time_str in ignored_results:
            prelim_time = None
            prelim_course = None
            prelim_heat = None
            prelim_lane = None
        else:
            prelim_time = database.create_time_from_str(prelim_time_str)
            prelim_course = sdif.Course(util.standardize_course(prelim_course_str))
            prelim_heat = int(prelim_heat_str)
            prelim_lane = int(prelim_lane_str)
        if swim_off_time_str == "" or swim_off_time_str in ignored_results:
            swim_off_time = None
            swim_off_course = None
            swim_off_heat = None
            swim_off_lane = None
        else:
            swim_off_time = database.create_time_from_str(swim_off_time_str)
            swim_off_course = sdif.Course(util.standardize_course(swim_off_course_str))
            swim_off_heat = None
            swim_off_lane = None
        if finals_time_str == "" or finals_time_str in ignored_results:
            finals_time = None
            finals_course = None
            finals_heat = None
            finals_lane = None
        else:
            finals_time = database.create_time_from_str(finals_time_str)
            finals_course = sdif.Course(util.standardize_course(finals_course_str))
            finals_heat = int(finals_heat_str)
            finals_lane = int(finals_lane_str)
        if prelim_place_str == "" or int(prelim_place_str) <= 0:
            prelim_place = None
        else:
            prelim_place = int(prelim_place_str)
        if finals_place_str == "" or int(finals_place_str) <= 0:
            finals_place = None
        else:
            finals_place = int(finals_place_str)
        if points_scored_str == "":
            points_scored = None
        else:
            points_scored = float(points_scored_str)

        # Search for swimmer if swimmer is different from current_swimmer
        different_current_swimmer = (
            self.current_swimmer is None
            or self.current_swimmer.get_usa_id_short() != usa_id_short
        )
        if different_current_swimmer:
            swimmer_found_in_club = False

            # Search for swimmer in current club
            if self.current_club is not None:
                self.current_swimmer = self.current_club.find_swimmer_with_short_id(
                    usa_id_short
                )
                if self.current_swimmer is not None:
                    swimmer_found_in_club = True
                else:
                    swimmer_found_in_club = False

            # If we didn't find the swimmer in the current_club, look in the database
            if not swimmer_found_in_club:
                self.current_swimmer = self.db.find_swimmer_with_short_id(usa_id_short)

            # Create swimmer if not found
            found_swimmer = self.current_swimmer is not None
            if not found_swimmer:
                self.current_swimmer = swim.Swimmer(
                    first_name,
                    last_name,
                    swimmer_sex,
                    usa_id_short,
                    self.current_club,
                    middle_initial,
                    None,  # Preferred first name is not contained in d0
                    birthday,
                    None,  # USA ID long is not contained in d0
                    citizen_code,
                )

                # Add swimmer to database and current club
                self.db.add_swimmer(self.current_swimmer)
                if self.current_club is not None:
                    self.current_club.get_swimmers().append(self.current_swimmer)

            # Check current_swimmer has been set properly
            assert self.current_swimmer is not None

            # If we only found the swimmer in the database, add to current club (if applicable)
            if found_swimmer and not swimmer_found_in_club:
                if self.current_club is None:
                    pass  # Swimmer is unattached so we don't need to modify the club
                elif self.current_swimmer.get_club() is None:
                    # If the swimmer doesn't have a club, set it to the current club
                    self.current_swimmer.set_club(self.current_club)
                else:
                    # If the swimmer has a club, we need to modify it if it is outdated (TODO)
                    pass

        assert self.current_swimmer is not None  # For type checker

        # Add prelim result to the current swimmer
        if prelim_time is not None:
            event = sdif.Event((event_distance, event_stroke, prelim_course))
            mr = swim.IndividualMeetResult(
                self.current_meet,
                organization,
                team_code,
                lsc,
                sdif.Session.PRELIMS,
                event_date,
                event,
                event_min_age,
                event_max_age,
                event_number,
                event_sex,
                prelim_heat,
                prelim_lane,
                prelim_time,
                first_name,
                last_name,
                swimmer_sex,
                usa_id_short,
                attach_status,
                prelim_place,
                None,
                seed_time,
                seed_course,
                None,
                None,
                middle_initial,
                age_class,
                birthday,
                None,
                citizen_code,
            )
            self.current_swimmer.add_meet_result(mr)
            self.current_meet.add_meet_result(mr)
            self.db.add_meet_result(mr)
            if self.current_club != None:
                self.current_club.add_meet_result(mr)

        # Add swim off result to current swimmer
        if swim_off_time is not None:
            event = sdif.Event((event_distance, event_stroke, swim_off_course))
            mr = swim.IndividualMeetResult(
                self.current_meet,
                organization,
                team_code,
                lsc,
                sdif.Session.SWIM_OFFS,
                event_date,
                event,
                event_min_age,
                event_max_age,
                event_number,
                event_sex,
                swim_off_heat,
                swim_off_lane,
                swim_off_time,
                first_name,
                last_name,
                swimmer_sex,
                usa_id_short,
                attach_status,
                None,
                None,
                seed_time,
                seed_course,
                None,
                None,
                middle_initial,
                age_class,
                birthday,
                None,
                citizen_code,
            )
            self.current_swimmer.add_meet_result(mr)
            self.db.add_meet_result(mr)
            self.current_meet.add_meet_result(mr)
            if self.current_club is not None:
                self.current_club.add_meet_result(mr)

        # Add finals time to swimmer object
        if finals_time is not None:
            try:
                event = sdif.Event((event_distance, event_stroke, finals_course))
            except:
                pass
            else:
                mr = swim.IndividualMeetResult(
                    self.current_meet,
                    organization,
                    team_code,
                    lsc,
                    sdif.Session.FINALS,
                    event_date,
                    event,
                    event_min_age,
                    event_max_age,
                    event_number,
                    event_sex,
                    finals_heat,
                    finals_lane,
                    finals_time,
                    first_name,
                    last_name,
                    swimmer_sex,
                    usa_id_short,
                    attach_status,
                    finals_place,
                    points_scored,
                    seed_time,
                    seed_course,
                    None,
                    None,
                    middle_initial,
                    age_class,
                    birthday,
                    None,
                    citizen_code,
                )
                self.current_swimmer.add_meet_result(mr)
                self.current_meet.add_meet_result(mr)
                self.db.add_meet_result(mr)
                if self.current_club != None:
                    self.current_club.add_meet_result(mr)

    def process_z0(self, line: str) -> None:
        self.current_meet = None
        self.current_club = None
        self.current_swimmer = None
