"""
User interface logic for tunas application.
"""

import os

import parser
import database
import relaygen

# Useful paths
TUNAS_DIRECTORY_PATH = os.path.dirname(os.path.realpath(__file__))
MEET_DATA_PATH = os.path.join(os.path.dirname(TUNAS_DIRECTORY_PATH), "data", "meetData")

# Global database and session information
DATABASE: database.Database
RELAY_GENERATOR: relaygen.RelayGenerator

# String constants
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
RELAY_MENU = (
    "1) Settings\n"
    + "2) 4 x 50 Free\n"
    + "3) 4 x 50 Medley\n"
    + "4) 4 x 100 Free\n"
    + "5) 4 x 100 Medley\n"
    + "6) 4 x 200 Free\n"
    + "7) Exclude swimmer\n"
    + "8) Include swimmer\n"
    + "Back (b/B)\n"
)
RELAY_SETTINGS_MENU = (
    "1) Club\n"
    + "2) Age range\n"
    + "3) Sex\n"
    + "4) Course\n"
    + "5) Date\n"
    + "6) Num relays\n"
    + "Back (b/B)\n"
)
LINE_BREAK = "-------------------------------------------------------------\n"
FINISHED_LOADING = "Finished processing files!"
PROGRAM_EXIT = "Program exited!"


def run_tunas_application():
    """
    Main logic for tunas application.
    """
    print()
    print(TUNAS_LOGO)
    load_data()
    print(FINISHED_LOADING)
    print(LINE_BREAK)
    running = True
    while running:
        running = print_menu_and_process_input()
    print(PROGRAM_EXIT)


def load_data():
    """
    Create and set global database variable.
    """
    global DATABASE
    global RELAY_GENERATOR

    # Load database
    DATABASE = parser.read_cl2(MEET_DATA_PATH)

    # Load relay generator. Default club is SCSC.
    default = "SCSC"
    default_club = DATABASE.find_club(default)
    assert default_club is not None  # SCSC should exist
    RELAY_GENERATOR = relaygen.RelayGenerator(DATABASE, default_club)


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
            print()
            run_relay_mode()
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
    try:
        swimmer = DATABASE.find_swimmer_with_long_id(id)
        assert swimmer is not None
    except:
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


def run_relay_mode():
    """
    Relay mode main loop.
    """
    while True:
        print(RELAY_MENU)
        selection = input("Selection > ")
        match selection:
            case "1":
                print()
                run_relay_settings()
            case "2":
                dist = 200
                stroke = database.sdif.Stroke.FREESTYLE_RELAY
                course = RELAY_GENERATOR.get_course()
                event = database.sdif.Event((dist, stroke, course))

                relays = RELAY_GENERATOR.generate_relays(event)
                print()
                display_relays(relays, event)
            case "3":
                dist = 200
                stroke = database.sdif.Stroke.MEDLEY_RELAY
                course = RELAY_GENERATOR.get_course()
                event = database.sdif.Event((dist, stroke, course))

                relays = RELAY_GENERATOR.generate_relays(event)
                print()
                display_relays(relays, event)
            case "4":
                dist = 400
                stroke = database.sdif.Stroke.FREESTYLE_RELAY
                course = RELAY_GENERATOR.get_course()
                event = database.sdif.Event((dist, stroke, course))

                relays = RELAY_GENERATOR.generate_relays(event)
                print()
                display_relays(relays, event)
            case "5":
                dist = 400
                stroke = database.sdif.Stroke.MEDLEY_RELAY
                course = RELAY_GENERATOR.get_course()
                event = database.sdif.Event((dist, stroke, course))

                relays = RELAY_GENERATOR.generate_relays(event)
                print()
                display_relays(relays, event)
            case "6":
                dist = 800
                stroke = database.sdif.Stroke.FREESTYLE_RELAY
                course = RELAY_GENERATOR.get_course()
                event = database.sdif.Event((dist, stroke, course))

                relays = RELAY_GENERATOR.generate_relays(event)
                print()
                display_relays(relays, event)
            case "7":
                print()
                print("Not implemented yet!")
                print()
            case "8":
                print()
                print("Not implemented yet!")
                print()
            case "b" | "B":
                break
            case _:
                print("Invalid selection!")


def run_relay_settings():
    while True:
        cur_club = RELAY_GENERATOR.get_club()
        cur_min_age, cur_max_age = RELAY_GENERATOR.get_age_range()
        cur_sex = RELAY_GENERATOR.get_sex()
        cur_course = RELAY_GENERATOR.get_course()
        cur_date = RELAY_GENERATOR.get_relay_date()
        cur_num_relays = RELAY_GENERATOR.get_num_relays()
        query_settings = (
            f"Query settings:\n"
            + f" * {"Club:":<12} {cur_club.get_lsc()}-{cur_club.get_team_code()}\n"
            + f" * {"Age range:":<12} {cur_min_age}-{cur_max_age}\n"
            + f" * {"Sex:":<12} {cur_sex.get_name()}\n"
            + f" * {"Course:":<12} {cur_course}\n"
            + f" * {"Date::":<12} {cur_date}\n"
            + f" * {"Num relays:":<12} {cur_num_relays}\n"
        )

        print(query_settings)
        print(RELAY_SETTINGS_MENU)
        selection = input("Selection > ")
        match selection:
            case "1":
                pass
            case "2":
                pass
            case "3":
                selection = input("\n1) Female\n2) Male\n\nSelection > ")
                if not (selection == "1" or selection == "2"):
                    print("Invalid selection!")
                    print()
                    continue
                if selection == "1":
                    new_sex = database.sdif.Sex.FEMALE
                else:
                    new_sex = database.sdif.Sex.MALE
                RELAY_GENERATOR.set_sex(new_sex)
                print(f"Success! New sex set to: {new_sex.get_name()}")
                print()
            case "4":
                pass
            case "5":
                pass
            case "6":
                new_num = input("Number of relays > ")
                try:
                    new_num = int(new_num)
                    assert new_num > 0
                except:
                    print(
                        f"Invalid selection! Make sure the number of relays is an "
                        + f"integer greater than zero."
                    )
                    print()
                    continue
                RELAY_GENERATOR.set_num_relays(new_num)
                print(f"Success! Number of relays set to: {new_num}")
                print()
            case "b" | "B":
                print()
                break
            case _:
                print("Invalid selection!")
                print()


def display_statistics():
    print("Statistics:")
    print(f"Number of clubs: {len(DATABASE.get_clubs())}")
    print(f"Number of swimmers: {len(DATABASE.get_swimmers())}")
    print(f"Number of meets: {len(DATABASE.get_meets())}")
    print(f"Number of meet results: {len(DATABASE.get_meet_results())}")


def display_relays(
    relays: list[list[database.swim.Swimmer]], event: database.sdif.Event
):
    leg_dist = event.get_distance() // 4
    if event.get_stroke() == database.sdif.Stroke.FREESTYLE_RELAY:
        relay_type = "Free"
        strokes = ["Free", "Free", "Free", "Free"]
    else:
        relay_type = "Medley"
        strokes = ["Back", "Breast", "Fly", "Free"]
    course = event.get_course()

    curr_relay_letter = "A"
    for relay in relays:
        print(f"4x{leg_dist} {relay_type} {course} Relay: '{curr_relay_letter}'")
        if relay == []:
            print("Not enough swimmers!")
        else:
            for i in range(4):
                stroke = strokes[i]
                swimmer = relay[i]
                print(f"{stroke:<6} {swimmer.get_full_name()}")
        print()
        curr_relay_letter = chr(ord(curr_relay_letter) + 1)


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
    event = mr.get_event()
    final_time = mr.get_final_time()
    age_class = mr.get_swimmer_age_class()
    meet_name = mr.get_meet().get_name()
    swim_date = mr.get_date_of_swim()
    session = mr.get_session()

    if age_class == None:
        age_class = ""

    # Calculate full code
    lsc_code = mr.get_lsc()
    team_code = mr.get_team_code()
    if team_code == None:
        team_code = ""
    if lsc_code == None:
        lsc_code = ""
    else:
        lsc_code = lsc_code.value
    full_code = f"{lsc_code:>2}-{team_code:<4}"

    print(
        f"{event}  {str(final_time):<8}  {session}  {age_class:<2}  {meet_name:<30}  "
        + f"{full_code:<7}  {swim_date}"
    )
