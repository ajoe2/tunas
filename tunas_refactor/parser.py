"""
Parser for tunas application. Handle reading data and creating underlying data
structure for higher level application code.
"""

import datetime
import enum
import os

import database
import util
from database import swim, sdif, stime


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

        # Ignore entries without an id
        if len(swimmer_short_id_str) != 12:
            return

        # Parse full name
        if full_name_str[-1].isupper() and full_name_str[-2] == " ":
            middle_initial = full_name_str[-1]
            full_name_str = full_name_str[:-2].strip()
        else:
            middle_initial = None
        last_name, first_name = full_name_str.split(",")
        last_name = last_name.strip()
        first_name = first_name.strip()

        # Standardize first name capitalization
        first_name_components = first_name.split(" ")
        first_name = ""
        for c in first_name_components:
            c = c.lower()
            c = c[0].upper() + c[1:]
            first_name = first_name + c + " "
        first_name = first_name[:-1]

        # Standardize last name capitalization
        last_name_components = last_name.split(" ")
        last_name = ""
        for c in last_name_components:
            if c != "":
                c = c.lower()
                c = c[0].upper() + c[1:]
                last_name = last_name + c + " "
        last_name = last_name[:-1]

        # Parse sex, id, and age_class
        swimmer_sex = sdif.Sex(swimmer_sex_str)
        usa_id_short = swimmer_short_id_str
        age_class = age_class_str

        # Parse birthday
        if b_day_str and b_month_str and b_year_str:
            birthday = datetime.date(int(b_year_str), int(b_month_str), int(b_day_str))
        elif util.is_old_id(usa_id_short):
            b_month = int(usa_id_short[:2])
            b_day = int(usa_id_short[2:4])
            if int(usa_id_short[4:6]) > datetime.date.today().year % 100:
                b_year = int("19" + usa_id_short[4:6])
            else:
                b_year = int("20" + usa_id_short[4:6])
            try:
                birthday = datetime.date(b_year, b_month, b_day)
            except ValueError:
                birthday = None
        else:
            birthday = None

        # Parse rest of data
        attach_status = sdif.AttachStatus(attach_code_str)
        event_sex = sdif.Sex(event_sex_str)
        event_distance = int(event_distance_str)
        event_stroke = sdif.Stroke(event_stroke_str)
        event_number = event_number_str
        event_date = datetime.date(
            int(event_year_str), int(event_month_str), int(event_day_str)
        )
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
        if prelim_time_str == "" or prelim_time_str in ["NT", "NS", "DNF", "DQ", "SCR"]:
            prelim_time = None
            prelim_course = None
            prelim_heat = None
            prelim_lane = None
        else:
            prelim_time = database.create_time_from_str(prelim_time_str)
            prelim_course = sdif.Course(util.standardize_course(prelim_course_str))
            prelim_heat = int(prelim_heat_str)
            prelim_lane = int(prelim_lane_str)
        if swim_off_time_str == "" or swim_off_time_str in [
            "NT",
            "NS",
            "DNF",
            "DQ",
            "SCR",
        ]:
            swim_off_time = None
            swim_off_course = None
            swim_off_heat = None
            swim_off_lane = None
        else:
            swim_off_time = database.create_time_from_str(swim_off_time_str)
            swim_off_course = sdif.Course(util.standardize_course(swim_off_course_str))
            swim_off_heat = None
            swim_off_lane = None
        if finals_time_str == "" or finals_time_str in ["NT", "NS", "DNF", "DQ", "SCR"]:
            finals_time = None
            finals_course = None
            finals_heat = None
            finals_lane = None
        else:
            finals_time = database.create_time_from_str(finals_time_str)
            finals_course = sdif.Course(util.standardize_course(finals_course_str))
            finals_heat = int(finals_heat_str)
            finals_lane = int(finals_lane_str)
        if prelim_place_str == "":
            prelim_place = None
        else:
            prelim_place = int(prelim_place_str)
        if finals_place_str == "":
            finals_place = None
        else:
            finals_place = int(finals_place_str)
        if points_scored_str == "":
            points_scored = None
        else:
            points_scored = float(points_scored_str)

        # At this point, birthday will be None if it is missing and the record has
        # the new usa swimming id format

        # If we can't figure out the birthday, look for swimmer using new id and age class

        # If birthday exists, search for swimmer using name and birthday

        # Once we look for the swimmer, either create it or update attributes

    def process_z0(self, line: str) -> None:
        self.current_meet = None
        self.current_club = None
        self.current_swimmer = None
