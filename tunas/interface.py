"""
Handles user interface for tunas application.
"""

import database
import parser
import os

# Calculate data path
TUNAS_DIRECTORY_PATH = os.path.dirname(os.path.realpath(__file__))
MEET_DATA_PATH = os.path.dirname(TUNAS_DIRECTORY_PATH) + "/data/meetData"

# Global database data structure
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
            pass
        case "4":
            pass
        case "5":
            print()
            print("Database statistics:")
            print(f"Number of clubs: {len(DATABASE.get_clubs())}")
            print(f"Number of swimmers: {len(DATABASE.get_swimmers())}")
            print(f"Number of meets: {len(DATABASE.get_meets())}")
            print(f"Number of meet results: {len(DATABASE.get_meet_results())}")
            swimmers = DATABASE.get_clubs()[0].get_swimmers()
            swimmers.sort(key=lambda s: s.get_first_name() + s.get_last_name())
            for swimmer in swimmers:
                if swimmer.get_middle_initial() == None:
                    m = ""
                else:
                    m = swimmer.get_middle_initial()
                print(f"{swimmer.first_name:<20} {m:<1} {swimmer.last_name:<20} {str(swimmer.birthday):<10} {swimmer.usa_id_short:<12}")
        case "q" | "Q":
            return False
        case _:
            print(f"Invalid input: '{user_input}'\n" + "Please try again!")
            pass
    print()
    return True
