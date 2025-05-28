"""
Handles user interface for tunas application.
"""

import database
import parser
import os
import datetime

# Data path
TUNAS_DIRECTORY_PATH = os.path.dirname(os.path.realpath(__file__))
MEET_DATA_PATH = os.path.dirname(TUNAS_DIRECTORY_PATH) + "/data/meetData"

# Global database=
DATABASE: database.Database

# Constants
TUNAS_LOGO = (
    "#############################################################\n"
    + "##########           Tunas: Data Analysis          ##########\n"
    + "#############################################################\n"
    + "Version: 1.0.1\n"
)
MAIN_MENU = (
    "1) Swimmer information\n"
    + "2) Time standards\n"
    + "3) Club information\n"
    + "4) Relay mode\n"
    + "5) Database statistics\n"
    + "Quit (q/Q)\n"
)
LINE_BREAK = "-------------------------------------------------------------\n"


def run_tunas_application():
    print()
    print(TUNAS_LOGO)
    load_database()
    print("Finished processing files!")
    print(LINE_BREAK)
    running = True
    while running:
        running = print_menu_and_process_input()
    print("Program exited!")


def load_database():
    global DATABASE
    DATABASE = parser.read_cl2(MEET_DATA_PATH)


def print_menu_and_process_input() -> bool:
    """
    Return true if success, false otherwise.
    """
    print(MAIN_MENU)
    user_input = input("Select mode > ")
    match user_input:
        case "1":
            pass
        case "2":
            pass
        case "3":
            print()
            run_club_mode()
        case "4":
            pass
        case "5":
            print()
            print("Statistics:")
            print(f"Number of clubs: {len(DATABASE.get_clubs())}")
            print(f"Number of swimmers: {len(DATABASE.get_swimmers())}")
            print(f"Number of meets: {len(DATABASE.get_meets())}")
            print(f"Number of meet results: {len(DATABASE.get_meet_results())}")
        case "q" | "Q":
            return False
        case _:
            print(f"Invalid input: '{user_input}'\n" + "Please try again!")
            pass
    print()
    return True


def run_club_mode():
    print("Club mode:")
    code = input("Enter club code (ex. SCSC) > ")
    try:
        club = DATABASE.find_club(code)
    except:
        club = None
    if club == None:
        print("Club not found!")
    else:
        print("Club found! Displaying swimmers...")
        print()
        swimmers = club.get_swimmers()
        swimmers.sort(key=lambda s: s.get_age_range(datetime.date.today())[0])
        for swimmer in club.get_swimmers():
            first = swimmer.get_first_name()
            last = swimmer.get_last_name()
            birthday = str(swimmer.get_birthday())
            if swimmer.get_middle_initial() == None:
                middle = ""
            else:
                middle = swimmer.get_middle_initial()
            print(
                f"{first:<18} {middle:<1} {last:<18} {birthday} {swimmer.get_age_range(datetime.date.today())}"
            )
