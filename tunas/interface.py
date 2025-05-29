"""
Handles user interface for tunas application.
"""

import database
from database import swim
import parser
import os
import datetime

# Data path
TUNAS_DIRECTORY_PATH = os.path.dirname(os.path.realpath(__file__))
MEET_DATA_PATH = os.path.dirname(TUNAS_DIRECTORY_PATH) + "/data/meetData"

# Global database
DATABASE: database.Database

# Global constants
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
LOADING_EXIT_MESSAGE = "Finished processing files!"
PROGRAM_EXIT_MESSAGE = "Program exited!"


def run_tunas_application():
    """
    Main logic for tunas application.
    """
    print()
    print(TUNAS_LOGO)
    load_database()
    print(LOADING_EXIT_MESSAGE)
    print(LINE_BREAK)
    running = True
    while running:
        running = print_menu_and_process_input()
    print(PROGRAM_EXIT_MESSAGE)


def load_database():
    """
    Create and set global database variable.
    """
    global DATABASE
    DATABASE = parser.read_cl2(MEET_DATA_PATH)


def print_menu_and_process_input() -> bool:
    """
    Print menu and accept user input. After accepting user input, return
    false if user wants to quit and true otherwise.
    """
    print(MAIN_MENU)
    user_input = input("Select mode > ")
    match user_input:
        case "1":
            print()
            run_swimmer_mode()
        case "2":
            pass
        case "3":
            print()
            run_club_mode()
        case "4":
            pass
        case "5":
            print()
            display_statistics()
        case "q" | "Q":
            return False
        case _:
            print(f"Invalid input: '{user_input}'\n" + "Please try again!")
            pass
    print()
    return True


def run_swimmer_mode():
    """
    Swimmer mode main logic
    """
    print("Swimmer mode:")
    code = input("Enter swimmer id > ")
    swimmer = DATABASE.find_swimmer_with_long_id(code)
    if swimmer == None:
        print("Swimmer not found!")
    else:
        print(
            f"Swimmer found! Displaying time history for "
            + f"{swimmer.get_first_name()} {swimmer.get_last_name()} ({code})"
        )
        print()
        meet_results = swimmer.get_meet_results()
        meet_results.sort(key=lambda mr: (mr.get_event(), mr.get_date_of_swim()))
        for mr in meet_results:
            print(
                f"{mr.get_event()}  {str(mr.get_final_time()):<8}  "
                + f"{str(mr.get_swimmer_age_class()):<2}  "
                + f"{mr.get_meet().get_name():<30}  {str(mr.get_lsc())}-{mr.get_team_code():<4}  {mr.get_date_of_swim()}"
            )


def run_club_mode():
    """
    Club mode main logic.
    """
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
        # Remove swimmers without a birthday range
        for swimmer in swimmers:
            if swimmer.get_birthday_range() == None:
                swimmers.remove(swimmer)

        # Sort swimmer by earliest possible birthday
        swimmers.sort(key=lambda s: s.get_birthday_range()[0], reverse=True)  # type: ignore

        # Print swimmer information
        for swimmer in club.get_swimmers():
            display_swimmer_information(swimmer)


def display_statistics():
    print("Statistics:")
    print(f"Number of clubs: {len(DATABASE.get_clubs())}")
    print(f"Number of swimmers: {len(DATABASE.get_swimmers())}")
    print(f"Number of meets: {len(DATABASE.get_meets())}")
    print(f"Number of meet results: {len(DATABASE.get_meet_results())}")


def display_swimmer_information(swimmer: swim.Swimmer):
    # Calculate full name
    first = swimmer.get_first_name()
    last = swimmer.get_last_name()
    middle = swimmer.get_middle_initial()
    if middle is None:
        full_name = f"{first} {last}"
    else:
        full_name = f"{first} {middle} {last}"

    # Calculate birthday
    b_range = swimmer.get_birthday_range()
    if b_range == None:
        b_range = f"--------------------------"
    elif b_range[0] == b_range[1]:
        b_range = f"{b_range[0]}"
    else:
        b_range = f"({b_range[0]}, {b_range[1]})"

    # Calculate id
    long_id = swimmer.get_usa_id_long()
    if long_id == None:
        long_id = f"--------------"

    # Calcate club and lsc code
    club = swimmer.get_club()
    if club is not None:
        club_code = club.get_team_code()
        lsc = club.get_lsc()
        if lsc is not None:
            lsc_code = lsc.value
        else:
            lsc_code = "--"
    else:
        club_code = "----"
        lsc_code = "--"

    print(
        f"{full_name:<27}  {long_id:<14}  {lsc_code:<2}-{club_code:<4}  {b_range:<25}"
    )
