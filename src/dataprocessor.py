
import os
from datetime import date

from database import *

def read_cl2(file_path: str) -> Database:
    """
    Read all cl2 files in file_path into a database object.

    Keyword arguments:
    file_path -- file path of data
    """
    db = Database()
    load_data(db, file_path, extension=".cl2")
    resolve_duplicates(db)
    return db

def load_data(database: Database, file_path: str, extension=".cl2"):
    """
    Load data from files in file_path ending with extension into 
    database object.

    Keyword arguments:
    file_path -- location of data
    database -- database to store data
    extension -- file type
    """
    if extension == ".cl2":
        fp = Cl2Processor(database)
    else:  
        raise ValueError(f"Unsupported file type: {extension}")
    file_paths = get_files(file_path, extension)
    total_files = len(file_paths)
    files_read = 0
    max_stars = 37
    for path in file_paths:
        # print("DEBUG:", file_path)
        fp.read_file(path)
        files_read += 1
        stars = int(files_read / total_files * max_stars) * "*"
        spaces = (max_stars - len(stars)) * " "
        percent = str(int(files_read / total_files * 100)) + "%"
        load_str = f"{'Files processed:': <18} {stars}{spaces}|{percent: >4}"
        print(load_str, end="\r")
    print()

def get_files(file_path: str, extension=".cl2") -> list[str]:
    """
    Return a list of file paths ending with extension in location specified 
    by file_path.

    Keyword arguments:
    file_path -- location of data
    extension -- desired file types
    """
    paths = []
    for file_or_dir in os.listdir(file_path):
        item_path = file_path + "/" + file_or_dir
        if os.path.isdir(item_path):
            paths = paths + get_files(item_path, extension)
        elif file_or_dir[-4:] == extension: 
            paths.append(item_path)
    return paths

def resolve_duplicates(database: Database):
    groups = {}
    for swimmer in database.get_swimmers():
        if swimmer.id not in groups:
            groups[swimmer.id] = [swimmer]
        else:
            groups[swimmer.id].append(swimmer)
    keys = list(groups.keys())
    for i in range(len(keys)):
        if len(groups[keys[i]]) > 1:
            merge_duplicate_swimmers(database, groups[keys[i]])

def merge_duplicate_swimmers(database: Database, swimmer_lst: list):
    best = swimmer_lst[0]
    for swimmer in swimmer_lst[1:]:
        if swimmer.date_most_recent_swim > best.date_most_recent_swim:
            best = combine_swimmers(database, best, swimmer)
        else:
            best = combine_swimmers(database, swimmer, best)

def combine_swimmers(database: Database, s1: Swimmer, s2: Swimmer) -> Swimmer:
    database.get_swimmers().remove(s1)
    s1.club.remove_swimmer(s1)
    for distance, stroke, course in Event.valid_events:
        event1 = s1.get_event(course, stroke, distance)
        event2 = s2.get_event(course, stroke, distance)
        for result in event1.get_meet_results():
            result.swimmer = s2
            event2.get_meet_results().append(result)
    return s2


class Cl2Processor():
    def __init__(self, db: Database):
        self.db = db
        self.current_club = None

    def read_file(self, file_path: str):
        file = open(file_path, "r")
        self.meet = Meet()
        for line in file:
            # print("DEBUG: ", line)
            self.process_line(line)
        self.db.add_meet(self.meet)
        file.close()

    def process_line(self, line: str):
        header = line[:2]
        match header:
            case 'A0':
                pass
            case 'B1':
                self.process_B1(line)
            case 'B2':
                pass
            case 'C1':
                self.process_C1(line)
            case 'C2':
                pass
            case 'D0':
                self.process_D0(line)
            case 'D1':
                pass
            case 'D2':
                pass
            case 'D3':
                self.process_D3(line)
            case 'E0':
                pass
            case 'F0':
                pass
            case 'G0':
                pass
    
    def process_B1(self, line: str):
        meet_name = line[11:41].strip()
        # meet_address = line[41:63].strip()
        # meet_city = line[85:105].strip()
        self.meet.set_name(meet_name)

    def process_C1(self, line: str):
        lsc_id = line[11:13].strip()
        club_code = line[11:17].strip()
        club_name = line[17:47].strip()
        if not lsc_id:
            lsc_id = "XX"
            club_code = "XXXXXX"
            club_name = "Xxxxxxxxxx"
        lsc = self.db.find_lsc(lsc_id)
        club = self.db.find_club(club_code)
        if not club:
            club = Club(club_code, club_name, lsc)
            lsc.add_club(club)
            self.db.add_club(club)
        self.current_club = club

    def process_D0(self, line: str):
        full_name = line[11:39].strip() # Full name
        swimmer_id = line[39:51].strip() # Swimmer id
        # attach_code = line[51].strip()
        # citizen_code = line[52:55].strip()
        b_month = line[55:57].strip() # Birth month
        b_day = line[57:59].strip() # Birth day
        b_year = line[59:63].strip() # Birth year
        age_class = line[63:65].strip() # Swimmer age or class (Ex. Jr or Sr)
        sex = line[65].strip() # Swimmer sex
        # event_sex = line[66].strip() # Event sex code
        event_distance = int(line[67:71].strip()) # Event distance
        event_stroke = line[71].strip() # Event stroke
        # event_number = line[72:76].strip() # Event number
        # event_age_code = line[76:80].strip() # Event age code
        event_date_month  = line[80:82].strip() # Swim month
        event_date_day = line[82:84].strip() # Swim day
        event_date_year = line[84:88].strip() # Swim year
        # seed_time = Util.create_time(line[88:96])
        # seed_course = Util.standardize_course(line[96].strip())
        prelim_time = Util.create_time(line[97:105])
        prelim_course = Util.standardize_course(line[105].strip())
        swim_off_time = Util.create_time(line[106:114])
        swim_off_course = Util.standardize_course(line[114].strip())
        finals_time = Util.create_time(line[115:123])
        finals_course = Util.standardize_course(line[123].strip())
        # prelim_heat = line[124:126].strip()
        # prelim_lane = line[126:128].strip()
        # finals_heat = line[128:130].strip()
        # finals_lane = line[130:132].strip()
        # prelims_place = line[132:135].strip()
        # finals_place = line[135:138].strip()
        # points_scored = line[138:142].strip()

        #Ignore corrupted entries
        if (not swimmer_id
            or not b_month or not b_year or not b_day
            or not event_stroke in ['1', '2', '3', '4', '5', '6', '7']
            or not event_date_day or not event_date_month 
            or not event_date_year):
            return
        event_stroke = int(event_stroke)
        last_name, first_name = full_name.split(",")
        last_name = last_name.strip()
        first_name = first_name.strip()
        fake_id = b_month + b_day + b_year[-2:] + \
                  (first_name.upper() + "***")[:4] + \
                  (last_name.upper() + "***")[:4]
        birthday = date(int(b_year), int(b_month), int(b_day))
        event_date = date(int(event_date_year), 
                          int(event_date_month), 
                          int(event_date_day))
        swimmer = self.db.find_swimmer_with_fake_id(fake_id, self.current_club)
        if not swimmer:
            swimmer = Swimmer(swimmer_id, first_name, last_name, sex, 
                                self.current_club, birthday, event_date)
            self.current_club.add_swimmer(swimmer)
            self.db.add_swimmer(swimmer)
        if event_date > swimmer.date_most_recent_swim:
            swimmer.date_most_recent_swim = event_date
            if self.current_club != swimmer.get_club():
                swimmer.update_club(self.current_club)
        # Create meet entries
        for session, time, course in [(1, prelim_time, prelim_course), 
                                      (2, swim_off_time, swim_off_course), 
                                      (3, finals_time, finals_course)]:
            if (not time or (event_distance, event_stroke, course) 
                not in Event.valid_events):
                continue
            event = swimmer.get_event(course, event_stroke, event_distance)
            meet_result = MeetResult(first_name, last_name, swimmer_id,
                                     birthday, age_class, sex, event_date, 
                                     session, course, time, swimmer, event, 
                                     self.meet, self.db)  
            self.db.add_meet_result(meet_result)
            self.meet.add_meet_result(meet_result)
            event.add_meet_result(meet_result)
        self.most_recent_swimmer = swimmer

    def process_D3(self, line: str):
        full_id = line[2:16].strip()
        # preferred_first_name = line[16:31].strip()
        self.most_recent_swimmer.update_id(full_id)

