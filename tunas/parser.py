"""
Parser for tunas application. Handle reading data and creating underlying data
structure for higher level application code.
"""

import os
import datetime

import database
import util


def read_cl2(file_path: str) -> database.Database:
    """
    Return database object containing data from all cl2 files in file_path.
    """
    db = database.Database()
    processor = Cl2Processor(db)

    # Get cl2 file paths
    paths = []
    for root, _, files in os.walk(file_path):
        for f in files:
            if f.endswith(".cl2"):
                full_file_path = os.path.join(root, f)
                paths.append(full_file_path)

    # Load cl2 files into database
    print("Loading files...")
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
        """
        Load data from file specified at path into self.db.
        """
        assert os.path.isfile(path)
        assert path.endswith(".cl2")

        with open(path, encoding="utf-8", errors="replace") as file:
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
                        self.process_d3(line)
                    case "E0":
                        pass
                    case "F0":
                        pass
                    case "G0":
                        pass
                    case "Z0":
                        self.process_z0(line)

    def process_b1(self, line: str) -> None:
        """
        Process B1 line in cl2 file.
        """
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

        # Parse start date and end date
        start_date_year = int(start_date_str[4:])
        start_date_month = int(start_date_str[:2])
        start_date_day = int(start_date_str[2:4])
        end_date_year = int(end_date_str[4:])
        end_date_month = int(end_date_str[:2])
        end_date_day = int(end_date_str[2:4])

        # Parse data
        organization = database.sdif.Organization(org_code_str)
        name = name_str
        city = city_str
        address_one = address_one_str
        start_date = datetime.date(start_date_year, start_date_month, start_date_day)
        end_date = datetime.date(end_date_year, end_date_month, end_date_day)
        if address_two_str != "":
            address_two = address_two_str
        else:
            address_two = None
        if state_str != "":
            state = database.sdif.State(state_str)
        else:
            state = None
        if postal_code_str != "":
            postal_code = postal_code_str
        else:
            postal_code = None
        if country_code_str != "":
            country = database.sdif.Country(country_code_str)
        else:
            country = None
        if course_code_str != "":
            standardized_course = util.standardize_course(course_code_str)
            course = database.sdif.Course(standardized_course)
        else:
            course = None
        if altitude_str != "":
            altitude = int(altitude_str)
        else:
            altitude = None
        if meet_type_str != "":
            meet_type = database.sdif.MeetType(meet_type_str)
        else:
            meet_type = None

        # Create meet object
        new_meet = database.swim.Meet(
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
        """
        Process C1 line in cl2 file.
        """
        assert self.current_meet is not None

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
            if lsc_code_str == "UN" or team_code_str.upper() == "UN":
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

        # Parse string data
        organization = database.sdif.Organization(org_code_str)
        full_name = full_name_str
        team_code = team_code_str
        if lsc_code_str in database.sdif.LSC:
            lsc = database.sdif.LSC(lsc_code_str)
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
        if state_str != "" and state_str in database.sdif.State:
            state = database.sdif.State(state_str)
        else:
            state = None
        if postal_code_str != "":
            postal_code = postal_code_str
        else:
            postal_code = None
        if country_code_str != "" and country_code_str in database.sdif.Country:
            country = database.sdif.Country(country_code_str)
        else:
            country = None
        if region_str != "":
            region = database.sdif.Region(region_str)
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
            club = database.swim.Club(
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
            # We need to add the club to the database if we create it
            self.db.add_club(club)

        # Add club to current meet and set current_club to club
        club.add_meet(self.current_meet)
        self.current_club = club

    def process_d0(self, line: str) -> None:
        """
        Process D0 line in cl2 file.
        """
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

        # Ignore invalid entries
        invalid_short_id = len(swimmer_short_id_str) != 12
        invalid_stroke = event_stroke_str not in database.sdif.Stroke
        if invalid_short_id or invalid_stroke:
            self.current_swimmer = None
            return

        # Ignore entries with invalid stroke
        if event_stroke_str not in database.sdif.Stroke:
            self.current_swimmer = None
            return

        # Parse full name, sex, id, and age_class
        first_name, middle_initial, last_name = util.parse_full_name(full_name_str)
        swimmer_sex = database.sdif.Sex(swimmer_sex_str)
        usa_id_short = swimmer_short_id_str
        age_class = age_class_str

        # Check to see if the usa_id_short is in the new id format
        is_new_id = not util.is_old_id(
            first_name, last_name, middle_initial, usa_id_short
        )

        # Parse birthday
        if b_day_str and b_month_str and b_year_str:
            # If the birthday is in the data, we just read it.
            birthday = datetime.date(int(b_year_str), int(b_month_str), int(b_day_str))
        elif util.is_old_id(first_name, last_name, middle_initial, usa_id_short):
            # If the swimmer has an old id, we can reverse engineer the birthday.
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
        organization = database.sdif.Organization(org_code_str)
        attach_status = database.sdif.AttachStatus(attach_code_str)
        event_sex = database.sdif.Sex(event_sex_str)
        event_distance = int(event_distance_str)
        event_stroke = database.sdif.Stroke(event_stroke_str)
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
        if citizen_code_str == "" or citizen_code_str not in database.sdif.Country:
            citizen_code = None
        else:
            citizen_code = database.sdif.Country(citizen_code_str)
        if seed_time_str == "":
            seed_time = None
            seed_course = None
        else:
            seed_time = database.stime.create_time_from_str(seed_time_str)
            seed_course = database.sdif.Course(util.standardize_course(seed_course_str))
        if prelim_time_str == "" or prelim_time_str in ignored_results:
            prelim_time = None
            prelim_course = None
            prelim_heat = None
            prelim_lane = None
        else:
            prelim_time = database.stime.create_time_from_str(prelim_time_str)
            prelim_course = database.sdif.Course(
                util.standardize_course(prelim_course_str)
            )
            prelim_heat = int(prelim_heat_str)
            prelim_lane = int(prelim_lane_str)
        if swim_off_time_str == "" or swim_off_time_str in ignored_results:
            swim_off_time = None
            swim_off_course = None
            swim_off_heat = None
            swim_off_lane = None
        else:
            swim_off_time = database.stime.create_time_from_str(swim_off_time_str)
            swim_off_course = database.sdif.Course(
                util.standardize_course(swim_off_course_str)
            )
            swim_off_heat = None
            swim_off_lane = None
        if finals_time_str == "" or finals_time_str in ignored_results:
            finals_time = None
            finals_course = None
            finals_heat = None
            finals_lane = None
        else:
            finals_time = database.stime.create_time_from_str(finals_time_str)
            finals_course = database.sdif.Course(
                util.standardize_course(finals_course_str)
            )
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

        # Before searching for the corresponding swimmer, we check if the
        # most recent swimmer is what we are looking for. This improves performance
        # because we don't have to iterate over the pool of swimmers for
        # every entry, which has O(n) runtime.
        need_to_find_swimmer = (
            self.current_swimmer is None
            or self.current_swimmer.get_usa_id_short() != usa_id_short
        )
        if need_to_find_swimmer:
            self.current_swimmer = None  # Reset current swimmer to None
            found_in_club = False

            # If the swimmer has a birthday, we search using the name and birthday.
            if birthday is not None:
                # Search for swimmer in current club
                if self.current_club is not None:
                    self.current_swimmer = self.current_club.find_swimmer_with_birthday(
                        first_name,
                        middle_initial,
                        last_name,
                        birthday,
                    )
                if self.current_swimmer is not None:
                    found_in_club = True
                else:
                    found_in_club = False

                # If we didn't find the swimmer in the club, look through the database.
                if not found_in_club:
                    self.current_swimmer = self.db.find_swimmer_with_birthday(
                        first_name,
                        middle_initial,
                        last_name,
                        birthday,
                    )

            # If we don't find the swimmer using their birthday (either doesn't exit
            # or didn't have a birthday in the data entry), then we need to search
            # using the usa swimming id.
            if self.current_swimmer is None:
                # Search for swimmer in current club
                if self.current_club is not None:
                    self.current_swimmer = self.current_club.find_swimmer_with_short_id(
                        usa_id_short
                    )
                if self.current_swimmer is not None:
                    found_in_club = True
                else:
                    found_in_club = False

                # If we didn't find the swimmer in the current_club, look in the database
                if not found_in_club:
                    self.current_swimmer = self.db.find_swimmer_with_short_id(
                        usa_id_short
                    )

            # If we still didn't find the swimmer, then we need to create it.
            if self.current_swimmer is None:
                # Only set the short id if it is in the new id format.
                if is_new_id:
                    short_id = usa_id_short
                else:
                    short_id = None

                # Create swimmer
                created_swimmer = True
                self.current_swimmer = database.swim.Swimmer(
                    first_name,
                    last_name,
                    swimmer_sex,
                    short_id,
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
                    self.current_club.add_swimmer(self.current_swimmer)
            else:
                created_swimmer = False

            # Check current_swimmer has been set properly
            assert self.current_swimmer is not None

            # If we only found the swimmer in the database, move swimmer to current club
            if (
                self.current_club is not None
                and not found_in_club
                and not created_swimmer
            ):
                # Update swimmer club if it is the newest data entry
                date_most_recent_swim = self.current_swimmer.get_date_most_recent_swim()
                if date_most_recent_swim == None or date_most_recent_swim < event_date:
                    self.current_swimmer.update_club(self.current_club)

        assert self.current_swimmer is not None

        # Update swimmer attributes
        if self.current_swimmer.get_usa_id_short() == None and is_new_id:
            self.current_swimmer.set_usa_id_short(usa_id_short)
        if self.current_swimmer.get_middle_initial() == None and middle_initial != None:
            self.current_swimmer.set_middle_initial(middle_initial)
        if self.current_swimmer.get_birthday() == None and birthday != None:
            self.current_swimmer.set_birthday(birthday)
        if self.current_swimmer.get_citizenship() == None and citizen_code != None:
            self.current_swimmer.set_citizenship(citizen_code)

        # Add prelim result to the current swimmer
        if prelim_time is not None:
            event = database.dutil.Event((event_distance, event_stroke, prelim_course))
            mr = database.swim.IndividualMeetResult(
                self.current_meet,
                organization,
                team_code,
                lsc,
                database.sdif.Session.PRELIMS,
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
            event = database.dutil.Event(
                (event_distance, event_stroke, swim_off_course)
            )
            mr = database.swim.IndividualMeetResult(
                self.current_meet,
                organization,
                team_code,
                lsc,
                database.sdif.Session.SWIM_OFFS,
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
                event = database.dutil.Event(
                    (event_distance, event_stroke, finals_course)
                )
            except:
                pass
            else:
                mr = database.swim.IndividualMeetResult(
                    self.current_meet,
                    organization,
                    team_code,
                    lsc,
                    database.sdif.Session.FINALS,
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

    def process_d3(self, line: str) -> None:
        """
        Process D3 line in cl2 file.
        """
        # If there was an error reading the d0 line, return.
        if self.current_swimmer is None:
            return

        full_id = line[2:16].strip()
        preferred_first_name = line[16:31].strip()
        curr_long_id = self.current_swimmer.get_usa_id_long()
        curr_preferred_name = self.current_swimmer.get_preferred_first_name()

        # Update full id if applicable
        if len(full_id) == 14:
            old_id = util.is_old_id(
                self.current_swimmer.get_first_name(),
                self.current_swimmer.get_last_name(),
                self.current_swimmer.get_middle_initial(),
                full_id,
            )
            if not old_id and curr_long_id is None:
                self.current_swimmer.set_usa_id_long(full_id)

        # Update preferred first name if applicable
        if len(preferred_first_name) > 0 and curr_preferred_name is None:
            self.current_swimmer.set_preferred_first_name(preferred_first_name)

    def process_z0(self, line: str) -> None:
        """
        Process Z0 line in cl2 file.
        """
        self.current_meet = None
        self.current_club = None
        self.current_swimmer = None
