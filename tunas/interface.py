"""
User interface logic for tunas application.
"""

import os

import parser
import database
import relaygen

# Paths
TUNAS_DIRECTORY_PATH = os.path.dirname(os.path.realpath(__file__))
MEET_DATA_PATH = os.path.dirname(TUNAS_DIRECTORY_PATH) + "/data/meetData"

# Global database and relay generator
DATABASE: database.Database
RELAY_GENERATOR: relaygen.RelayGenerator

# String constatns
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
    id = input("Enter swimmer id > ")
    swimmer = DATABASE.find_swimmer_with_long_id(id)
    if swimmer == None:
        print("Swimmer not found!")
    else:
        print(f"Swimmer found! Displaying time history for {swimmer.get_full_name()}")
        print()
        meet_results = swimmer.get_meet_results()
        meet_results.sort(key=lambda mr: (mr.get_event(), mr.get_date_of_swim()))
        for mr in meet_results:
            display_ind_meet_result_info(mr)


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
        print(f"Could not find club with club code {code}")
    else:
        print("Club found! Displaying swimmers...")
        print()
        swimmers = club.get_swimmers()

        # Remove swimmers without a birthday range
        for swimmer in swimmers:
            if swimmer.get_birthday_range() == None:
                swimmers.remove(swimmer)
        # Sort swimmer by birthday
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


def display_swimmer_information(swimmer: database.swim.Swimmer):
    # Calculate full name
    full_name = swimmer.get_full_name()

    # Calculate birthday
    b_range = swimmer.get_birthday_range()
    if b_range == None:
        b_range = f"-----------------------"
    elif b_range[0] == b_range[1]:
        b_range = f"{b_range[0]}"
    else:
        b_range = f"{b_range[0]} - {b_range[1]}"

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
    full_code = f"{lsc_code:<2}-{club_code:<4}"

    print(f"{full_name:<27}  {long_id:<14}  {full_code}  {b_range:<25}")


def display_ind_meet_result_info(mr: database.swim.IndividualMeetResult):
    if mr.get_team_code() != None and mr.get_lsc() != None:
        full_code = f"{str(mr.get_lsc())}-{mr.get_team_code()}"
    elif mr.get_team_code() != None and mr.get_lsc() == None:
        full_code = f"   {mr.get_team_code()}"
    elif mr.get_team_code() == None and mr.get_lsc() != None:
        full_code = f"{mr.get_lsc()}     "
    else:
        full_code = ""
    print(
        f"{mr.get_event()}  {str(mr.get_final_time()):<8}  "
        + f"{str(mr.get_swimmer_age_class()):<2}  "
        + f"{mr.get_meet().get_name():<30}  {full_code:<7}  {mr.get_date_of_swim()}"
    )
