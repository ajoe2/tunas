"""
Parser for tunas application. Handle reading data and creating underlying data
structure for higher level application code.
"""

import datetime
import enum
import os

import database
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
    for p in paths:
        processor.read_file(p)

    return db


class Cl2Processor:
    def __init__(self, db: database.Database):
        self.db = db
        self.meet = None
        self.current_club = None

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
                        pass
                    case "C2":
                        pass
                    case "D0":
                        pass
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
        # Unused: line[3:11].strip()
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
        # Unused: line[141:149].strip()
        course_code_str = line[149].strip()
        # Unused: line[150:160].strip()

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
            alpha_to_num_course = {"S": "1", "Y": "2", "L": "3"}
            if course_code_str in alpha_to_num_course.keys():
                course_code_str = alpha_to_num_course[course_code_str]
            course = sdif.Course(course_code_str)
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

    def process_z0(self, line: str) -> None:
        self.current_meet = None
        self.current_club = None
