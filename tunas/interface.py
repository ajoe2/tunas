"""
User interface logic for tunas application.
"""

import os
import datetime

import database
import parser
import relaygen

# Important paths
TUNAS_DIRECTORY_PATH = os.path.dirname(os.path.realpath(__file__))
MEET_DATA_PATH = os.path.join(os.path.dirname(TUNAS_DIRECTORY_PATH), "data", "meetData")

# Global database and session objects
DATABASE: database.Database
RELAY_GENERATOR: relaygen.RelayGenerator

# String constants
TUNAS_LOGO = (
    "#############################################################\n"
    + "##########           Tunas: Data Analysis          ##########\n"
    + "#############################################################\n"
    + "Version: 1.1.0\n"
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
    scsc = DATABASE.find_club("SCSC")
    assert scsc is not None  # SCSC should exist
    RELAY_GENERATOR = relaygen.RelayGenerator(DATABASE, scsc)


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
            print(f"Invalid selection: '{user_input}'.")
            print()
            pass
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
        meet_results.sort(
            key=lambda mr: (mr.get_event(), mr.get_date_of_swim(), mr.get_session())
        )
        for mr in meet_results:
            display_ind_meet_result_info(mr)
    print()


def run_club_mode():
    """
    Club mode main logic.
    """
    print("Club mode:")
    code = input("Enter club code (ex. SCSC) > ")
    try:
        club = DATABASE.find_club(code)
        assert club is not None
    except:
        print(f"Could not find club with club code {code}")
    else:
        print("Club found! Displaying swimmers...")
        print()

        # Sort swimmers by birthday
        swimmers = club.get_swimmers()
        swimmers.sort(key=lambda s: s.get_birthday_range()[0], reverse=True)

        # Print swimmer information
        for swimmer in club.get_swimmers():
            display_swimmer_information(swimmer)
    print()


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
                print()
                break
            case _:
                print("Invalid selection!")
                print()


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
                code = input("New club code > ")
                try:
                    new_club = DATABASE.find_club(code)
                    assert new_club is not None
                except:
                    print("Club not found!")
                    print()
                else:
                    RELAY_GENERATOR.set_club(new_club)
                    name = new_club.get_full_name()
                    if new_club.get_lsc() is not None:
                        team_code = f"{new_club.get_lsc()}-{new_club.get_team_code()}"
                    else:
                        team_code = new_club.get_team_code()
                    print(f"Success! New club set to: {name} ({team_code})")
                    print()
            case "2":
                min_age = input("New min age > ")
                max_age = input("New max age > ")
                try:
                    min_age = int(min_age)
                    max_age = int(max_age)
                    assert min_age <= max_age
                except:
                    print("Invalid selection!")
                    print()
                else:
                    RELAY_GENERATOR.set_age_range((min_age, max_age))
                    print(f"Success! Age range set to ({min_age}, {max_age})")
                    print()
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
                selection = input("\n1) SCY\n2) SCM\n3) LCM\n\nSelection > ")
                if not selection in ["1", "2", "3"]:
                    print("Invalid selection!")
                    print()
                    continue
                if selection == "1":
                    new_course = database.sdif.Course.SCY
                elif selection == "2":
                    new_course = database.sdif.Course.SCM
                else:
                    new_course = database.sdif.Course.LCM
                RELAY_GENERATOR.set_course(new_course)
                print(f"Success! New course set to: {new_course}")
                print()
            case "5":
                try:
                    new_year = int(input("Enter year > "))
                    new_month = int(input("Enter month > "))
                    new_day = int(input("Enter day > "))
                    new_date = datetime.date(new_year, new_month, new_day)
                except:
                    print("Invalid selection!")
                    print()
                else:
                    RELAY_GENERATOR.set_relay_date(new_date)
                    print(f"Success! New relay date set to: {new_date}")
                    print()
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
    print(f"Number of clubs: {len(DATABASE.get_clubs()):,}")
    print(f"Number of swimmers: {len(DATABASE.get_swimmers()):,}")
    print(f"Number of meets: {len(DATABASE.get_meets()):,}")
    print(f"Number of meet results: {len(DATABASE.get_meet_results()):,}")
    print()


def display_relays(
    relays: list[list[database.swim.Swimmer]], event: database.sdif.Event
):
    leg_dist = event.get_distance() // 4
    course = event.get_course()
    if event.get_stroke() == database.sdif.Stroke.FREESTYLE_RELAY:
        relay_stroke = database.sdif.Stroke.FREESTYLE_RELAY
        leg_strokes = relaygen.FREESTYLE_RELAY_STROKES
    else:
        relay_stroke = database.sdif.Stroke.MEDLEY_RELAY
        leg_strokes = relaygen.MEDLEY_RELAY_STROKES
    leg_events = [database.sdif.Event((leg_dist, s, course)) for s in leg_strokes]

    curr_relay_letter = "A"
    for relay in relays:
        if relay != []:
            total_time = str(relaygen.get_relay_time(relay, event))
        else:
            total_time = "-"
        print(
            f"4x{leg_dist} {relay_stroke} {course}: '{curr_relay_letter}' [{total_time}]"
        )
        if relay != []:
            for i in range(4):
                leg_event = leg_events[i]
                swimmer = relay[i]
                club = RELAY_GENERATOR.get_club()
                mr = swimmer.get_best_meet_result(leg_event)
                assert mr is not None

                # Pull data
                full_name = swimmer.get_full_name()
                usa_id = swimmer.get_usa_id_long()
                stroke = str(leg_event.get_stroke())
                meet_name = mr.get_meet().get_name()
                best_time = str(mr.get_final_time())

                # Get full club code
                if club.get_lsc() is not None:
                    full_club_code = f"{club.get_lsc()}-{club.get_team_code()}"
                else:
                    full_club_code = club.get_team_code()

                # Condense age range if possible
                age_range = swimmer.get_age_range(RELAY_GENERATOR.get_relay_date())
                if age_range[0] == age_range[1]:
                    age_range = age_range[0]

                print(
                    f" {stroke:<6}  {full_name:<20}  {age_range:<8}  {usa_id:<14}  {full_club_code:<7}  {best_time:<8}  {meet_name:<30}"
                )
        else:
            print("Not enough swimmers!")
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
