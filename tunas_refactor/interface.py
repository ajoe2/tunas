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
    + "Version: 1.0.0\n"
)
MAIN_MENU = (
    "1) Swimmer information\n"
    + "2) Time standards\n"
    + "3) Club information\n"
    + "4) Relay mode\n"
    + "Quit (q/Q)\n"
)
LINE_BREAK = "-------------------------------------------------------------"


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
        case "q" | "Q":
            return False
        case _:
            print(f"Invalid input: '{user_input}'\n" + "Please try again!")
            pass
    print()
    return True
