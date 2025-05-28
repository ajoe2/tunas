"""
Entry point for tunas application.
"""

import parser
import database

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
DATABASE: database.Database


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
            print(f"Invalid input: '{user_input}'")
            print(f"Please try again!")
            pass
    print()
    return True


def main():
    """
    Run Tunas application.
    """
    print()
    print(TUNAS_LOGO)
    DATABASE = parser.read_cl2("/Users/ajoe/code/tunas/data/meetData")
    print(
        "Finished processing files!\n"
        + "-------------------------------------------------------------"
    )
    running = True
    while running:
        running = print_menu_and_process_input()
    print("Program exited!")


if __name__ == "__main__":
    main()
