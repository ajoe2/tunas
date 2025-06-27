"""
User interface logic for tunas application.
"""

import os
import datetime

import database
import parser
import relaygen

# Paths
TUNAS_DIRECTORY_PATH = os.path.dirname(os.path.realpath(__file__))
MEET_DATA_PATH = os.path.join(os.path.dirname(TUNAS_DIRECTORY_PATH), "data", "meetData")

# Global database and session objects
DATABASE: database.Database
RELAY_GENERATOR: relaygen.RelayGenerator
TIME_STANDARD_INFO: database.timestandard.TimeStandardInfo

# Startup & shutdown
TUNAS_LOGO = (
    "#############################################################\n"
    + "##########           Tunas: Data Analysis          ##########\n"
    + "#############################################################\n"
    + "Version: 1.1.0\n"
)
LINE_BREAK = "-------------------------------------------------------------\n"
FINISHED_LOADING = "Finished processing files!"
PROGRAM_EXIT = "Program exited!"

# Menu
MAIN_MENU = (
    "1) Swimmer information\n"
    + "2) Time standards\n"
    + "3) Club information\n"
    + "4) Relay mode\n"
    + "5) Database statistics\n"
    + "Quit (q/Q)\n"
)
SWIMMER_MODE_MENU = "1) Full time history\n" + "2) Best times\n" + "Back (b/B)\n"
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
TIME_STANDARD_MODE_MENU = (
    "1) Age Group Champs\n"
    + "2) Far Westerns\n"
    + "3) Sectionals\n"
    + "4) Futures\n"
    + "5) Junior Nationals\n"
    + "6) Nationals\n"
    + "7) Olympic Trials\n"
    + "Back (b/B)\n"
)
SINGLE_AGE_MENU = (
    "1) 10 & under\n" + "2) 11\n" + "3) 12\n" + "4) 13\n" + "5) 14\n" + "Back (b/B)\n"
)
COURSE_MENU = "1) SCY\n2) SCM\n3) LCM\n"
DOUBLE_AGE_MENU = (
    "1) 10 & under\n"
    + "2) 11-12\n"
    + "3) 13-14\n"
    + "4) 15-16\n"
    + "5) 17-18\n"
    + "Back (b/B)\n"
)
SENIOR_AGE_MENU = "1) 18 & under\n" + "2) 19 & over\n" + "Back (b/B)\n"
SEX_MENU = "1) Female\n" + "2) Male\n" + "3) Mixed\n" + "Back (b/B)\n"

# Other
DEFAULT_CLUB_CODE = "SCSC"


def run_tunas_application() -> None:
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


def load_data() -> None:
    """
    Create and set global database variable.
    """
    # Declare global variables
    global DATABASE
    global RELAY_GENERATOR
    global TIME_STANDARD_INFO

    # Load database
    DATABASE = parser.read_cl2(MEET_DATA_PATH)

    # Load time standard information
    TIME_STANDARD_INFO = DATABASE.get_time_standard_info()

    # Load relay generator
    scsc = DATABASE.find_club(DEFAULT_CLUB_CODE)
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
            print()
            run_time_standard_mode()
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
            display_error(f"invalid selection '{user_input}'!")
            print()
    return True


def run_swimmer_mode() -> None:
    """
    Run swimmer mode. Display swimmer mode menu and handle user input.
    """
    print("Swimmer mode:")
    while True:
        print(SWIMMER_MODE_MENU)
        selection = input("Selection > ")
        match selection:
            case "1":  # Full time history
                id = input("Enter swimmer id > ")
                try:
                    swimmer = DATABASE.find_swimmer_with_long_id(id)
                    assert swimmer is not None
                except:
                    display_error("swimmer not found!")
                else:
                    display_full_time_history(swimmer)
                print()
            case "2":  # Best times
                id = input("Enter swimmer id > ")
                try:
                    swimmer = DATABASE.find_swimmer_with_long_id(id)
                    assert swimmer is not None
                except:
                    display_error("swimmer not found!")
                else:
                    display_best_times(swimmer)
                print()
            case "b" | "B":
                print()
                break
            case _:
                display_error(f"invalid selection '{selection}'!")
                print()


def display_full_time_history(swimmer: database.swim.Swimmer) -> None:
    """
    Display full time history for swimmer sorted by event.
    """
    name = swimmer.get_full_name()
    id = swimmer.get_usa_id_long()
    club = swimmer.get_club()
    min_age, max_age = swimmer.get_age_range(datetime.date.today())
    min_birth, max_birth = swimmer.get_birthday_range()
    meet_results = swimmer.get_meet_results()

    # Handle missing information
    if id is None:
        id = "--------------"

    if club is None:
        club_code = "----"
    elif club.get_lsc() is None:
        club_code = club.get_team_code()
    else:
        club_code = f"{club.get_lsc()}-{club.get_team_code()}"

    # Calculate age_range, birth_range strings
    if min_age == max_age:
        age_range = str(min_age)
    else:
        age_range = f"({min_age}, {max_age})"

    if min_birth == max_birth:
        b_range = str(min_birth)
    else:
        b_range = f"({min_birth}, {max_birth})"

    # Sort meet results
    meet_results.sort(
        key=lambda mr: (
            mr.get_event(),
            mr.get_date_of_swim(),
            mr.get_session(),
        )
    )

    # Display swimmer information
    info_str = f"{name}  {id}  {club_code:>6}  {age_range}  {b_range}"
    print(f"Swimmer found! Displaying time history for: {info_str}")
    print()

    # Display meet results
    for mr in meet_results:
        display_ind_meet_result_info(swimmer, mr)


def display_best_times(swimmer: database.swim.Swimmer) -> None:
    """
    Display swimmer's best time for each event.
    """
    name = swimmer.get_full_name()
    id = swimmer.get_usa_id_long()
    club = swimmer.get_club()
    min_age, max_age = swimmer.get_age_range(datetime.date.today())
    min_birth, max_birth = swimmer.get_birthday_range()
    meet_results = swimmer.get_meet_results()

    # Handle missing information
    if id is None:
        id = "--------------"

    if club is None:
        club_code = "----"
    elif club.get_lsc() is None:
        club_code = club.get_team_code()
    else:
        club_code = f"{club.get_lsc()}-{club.get_team_code()}"

    # Calculate age_range, birth_range strings
    if min_age == max_age:
        age_range = str(min_age)
    else:
        age_range = f"({min_age}, {max_age})"

    if min_birth == max_birth:
        b_range = str(min_birth)
    else:
        b_range = f"({min_birth}, {max_birth})"

    # Display swimmer information
    info_str = f"{name}  {id}  {club_code:>6}  {age_range}  {b_range}"
    print(f"Swimmer found! Displaying best times for: {info_str}")
    print()

    # Display best times
    for event in database.dutil.Event:
        best_mr = swimmer.get_best_meet_result(event)
        if best_mr is not None:
            display_ind_meet_result_info(swimmer, best_mr)


def run_time_standard_mode() -> None:
    """
    Run time standard mode.
    """
    while True:
        print(TIME_STANDARD_MODE_MENU)
        selection = input("Selection > ")
        match selection:
            case "1":
                print()
                display_time_standard(database.timestandard.TimeStandard.AGC)
            case "2":
                print()
                display_time_standard(database.timestandard.TimeStandard.FW)
            case "3":
                print()
                display_time_standard(database.timestandard.TimeStandard.SECT)
            case "4":
                print()
                display_time_standard(database.timestandard.TimeStandard.FUT)
            case "5":
                print()
                display_time_standard(database.timestandard.TimeStandard.JNAT)
            case "6":
                print()
                display_time_standard(database.timestandard.TimeStandard.NAT)
            case "7":
                print()
                display_time_standard(database.timestandard.TimeStandard.OT)
            case "B" | "b":
                print()
                break
            case _:
                display_error(f"invalid input '{selection}'!")
                print()


def display_time_standard(standard: database.timestandard.TimeStandard) -> None:
    """
    For given time standard, prompt for user input and display
    corresponding dataframe.
    """
    age_groups = TIME_STANDARD_INFO.get_age_groups(standard)

    # Determine menu type
    menu = f"{standard} options:\n"
    if age_groups == database.timestandard.SINGLE_AGE_GROUPS:
        menu += SINGLE_AGE_MENU
    elif age_groups == database.timestandard.DOUBLE_AGE_GROUPS:
        menu += DOUBLE_AGE_MENU
    else:
        menu += SENIOR_AGE_MENU

    while True:
        print(menu)
        selection = input("Selection > ")

        # Exit if user selected back
        if selection == "b" or selection == "B":
            print()
            break

        # Retrieve and display dataframe
        try:
            selection = int(selection)
            age_group = age_groups[int(selection) - 1]
            assert selection in range(1, len(age_groups) + 1)
            df = TIME_STANDARD_INFO.get_time_standard_df(standard, age_group)
            print()
            print(df)
        except:
            display_error(f"invalid selection '{selection}'!")
        print()


def run_club_mode() -> None:
    """
    Run club code.
    """
    print("Club mode:")
    code = input("Enter club code (ex. SCSC) > ")
    try:
        club = DATABASE.find_club(code)
        assert club is not None
    except:
        display_error(f"could not find club with club code '{code}'!")
    else:
        print("Club found! Displaying swimmers...")
        print()

        # Sort swimmers by birthday
        swimmers = club.get_swimmers()
        swimmers.sort(key=lambda s: s.get_birthday_range()[0], reverse=True)

        # Print swimmer information
        for swimmer in swimmers:
            display_swimmer_information(swimmer)
    print()


def run_relay_mode() -> None:
    """
    Run relay mode.
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
                event = database.dutil.Event((dist, stroke, course))
                relays = RELAY_GENERATOR.generate_relays(event)

                print()
                display_relays(relays, event)
            case "3":
                dist = 200
                stroke = database.sdif.Stroke.MEDLEY_RELAY
                course = RELAY_GENERATOR.get_course()
                event = database.dutil.Event((dist, stroke, course))
                relays = RELAY_GENERATOR.generate_relays(event)

                print()
                display_relays(relays, event)
            case "4":
                dist = 400
                stroke = database.sdif.Stroke.FREESTYLE_RELAY
                course = RELAY_GENERATOR.get_course()
                event = database.dutil.Event((dist, stroke, course))
                relays = RELAY_GENERATOR.generate_relays(event)

                print()
                display_relays(relays, event)
            case "5":
                dist = 400
                stroke = database.sdif.Stroke.MEDLEY_RELAY
                course = RELAY_GENERATOR.get_course()
                event = database.dutil.Event((dist, stroke, course))
                relays = RELAY_GENERATOR.generate_relays(event)

                print()
                display_relays(relays, event)
            case "6":
                dist = 800
                stroke = database.sdif.Stroke.FREESTYLE_RELAY
                course = RELAY_GENERATOR.get_course()
                event = database.dutil.Event((dist, stroke, course))
                relays = RELAY_GENERATOR.generate_relays(event)

                print()
                display_relays(relays, event)
            case "7":
                print()
                display_excluded_relay_swimmers()
                id = input("ID of swimmer to exclude > ")
                try:
                    curr_club = RELAY_GENERATOR.get_club()
                    excluded_swimmer = curr_club.find_swimmer_with_long_id(id)
                    assert excluded_swimmer is not None
                    RELAY_GENERATOR.exclude_swimmer(excluded_swimmer)

                    full_name = excluded_swimmer.get_full_name()
                    print(f"Success! Excluded {full_name} ({id})")
                except:
                    display_error(f"couldn't exclude swimmer with id '{id}'!")
                print()

            case "8":
                print()
                display_excluded_relay_swimmers()
                id = input("ID of swimmer to include > ")
                try:
                    curr_club = RELAY_GENERATOR.get_club()
                    included_swimmer = curr_club.find_swimmer_with_long_id(id)
                    assert included_swimmer is not None
                    RELAY_GENERATOR.include_swimmer(included_swimmer)

                    full_name = included_swimmer.get_full_name()
                    print(f"Success! Included {full_name} ({id})")
                except:
                    display_error(f"couldn't include swimmer with id '{id}'!")
                print()
            case "b" | "B":
                print()
                break
            case _:
                print("Invalid selection!")
                print()


def run_relay_settings() -> None:
    """
    Display relay generation settings and allow the user to make changes.
    """
    while True:
        # Current settings
        cur_club = RELAY_GENERATOR.get_club()
        cur_min_age, cur_max_age = RELAY_GENERATOR.get_age_range()
        cur_sex = RELAY_GENERATOR.get_sex()
        cur_course = RELAY_GENERATOR.get_course()
        cur_date = RELAY_GENERATOR.get_relay_date()
        cur_num_relays = RELAY_GENERATOR.get_num_relays()
        current_settings = (
            f"Query settings:\n"
            + f" * {'Club:':<12} {cur_club.get_lsc()}-{cur_club.get_team_code()}\n"
            + f" * {'Age range:':<12} {cur_min_age}-{cur_max_age}\n"
            + f" * {'Sex:':<12} {cur_sex.get_name()}\n"
            + f" * {'Course:':<12} {cur_course}\n"
            + f" * {'Date::':<12} {cur_date}\n"
            + f" * {'Num relays:':<12} {cur_num_relays}\n"
        )

        # Allow the user to change settings
        print(current_settings)
        print(RELAY_SETTINGS_MENU)
        selection = input("Selection > ")
        match selection:
            case "1":
                code = input("New club code > ")
                try:
                    new_club = DATABASE.find_club(code)
                    assert new_club is not None
                except:
                    display_error(f"could not find club with code '{code}'!")
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
                    display_error(f"could not set age range ({min_age}, {max_age})!")
                else:
                    RELAY_GENERATOR.set_age_range((min_age, max_age))
                    print(f"Success! Age range set to ({min_age}, {max_age}).")
                print()
            case "3":
                print()
                print(SEX_MENU)
                selection = input("Selection > ")
                if selection == "b" or selection == "B":
                    print()
                    continue
                if not (selection in ["1", "2", "3"]):
                    display_error(f"invalid selection '{selection}'!")
                    print()
                    continue
                if selection == "1":
                    new_sex = database.sdif.Sex.FEMALE
                elif selection == "2":
                    new_sex = database.sdif.Sex.MALE
                else:
                    new_sex = database.sdif.Sex.MIXED
                RELAY_GENERATOR.set_sex(new_sex)
                print(f"Success! New sex set to: {new_sex.get_name()}")
                print()
            case "4":
                print()
                print(COURSE_MENU)
                selection = input("Selection > ")
                if not selection in ["1", "2", "3"]:
                    display_error(f"invalid selection '{selection}'!")
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
                    display_error(f"invalid selection!")
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
                    display_error(f"invalid selection!")
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


def display_statistics() -> None:
    """
    Display database statistics.
    """
    print("Statistics:")
    print(f"Number of clubs: {len(DATABASE.get_clubs()):,}")
    print(f"Number of swimmers: {len(DATABASE.get_swimmers()):,}")
    print(f"Number of meets: {len(DATABASE.get_meets()):,}")
    print(f"Number of meet results: {len(DATABASE.get_meet_results()):,}")
    print()


def display_relays(
    relays: list[list[database.swim.Swimmer]],
    event: database.dutil.Event,
) -> None:
    """
    Display each relay in relays.
    """
    # Calculate leg events
    leg_dist = event.get_distance() // 4
    course = event.get_course()
    if event.get_stroke() == database.sdif.Stroke.FREESTYLE_RELAY:
        relay_stroke = database.sdif.Stroke.FREESTYLE_RELAY
        leg_strokes = relaygen.FREESTYLE_RELAY_STROKES
    else:
        relay_stroke = database.sdif.Stroke.MEDLEY_RELAY
        leg_strokes = relaygen.MEDLEY_RELAY_STROKES
    leg_events = [database.dutil.Event((leg_dist, s, course)) for s in leg_strokes]

    relay_letter = "A"
    for relay in relays:
        # Calculate relay time
        if relay != []:
            relay_time = relaygen.get_relay_time(relay, event)
            total_time = str(relay_time)
        else:
            relay_time = None
            total_time = "-"

        # Calculate time standard
        standards = []
        if relay_time:
            standards = TIME_STANDARD_INFO.get_qualified_standards(
                relay_time,
                event,
                RELAY_GENERATOR.get_age_range()[0],
                RELAY_GENERATOR.get_sex(),
            )
        if len(standards) > 0:
            best_standard = standards[-1]
        else:
            best_standard = None

        # Display relay information
        relay_name = f"4x{leg_dist} {relay_stroke} {course}"
        if best_standard is not None:
            print(f"{relay_name}: '{relay_letter}' [{total_time}] [{best_standard}]")
        else:
            print(f"{relay_name}: '{relay_letter}' [{total_time}]")

        # If empty relay, display message and continue
        if relay == []:
            print("Not enough swimmers!")
            print()
            relay_letter = chr(ord(relay_letter) + 1)
            continue

        # Display information for each relay leg
        for i in range(4):
            leg_event = leg_events[i]
            swimmer = relay[i]
            club = RELAY_GENERATOR.get_club()
            mr = swimmer.get_best_meet_result(leg_event)

            # Swimmer should have a valid meet result
            assert mr is not None

            # Pull data
            full_name = swimmer.get_full_name()
            usa_id = swimmer.get_usa_id_long()
            stroke = str(leg_event.get_stroke())
            meet_name = mr.get_meet().get_name()
            best_time = str(mr.get_final_time())

            # Get time standard information
            time_standards = TIME_STANDARD_INFO.get_qualified_standards(
                mr.get_final_time(),
                leg_event,
                RELAY_GENERATOR.get_age_range()[0],
                swimmer.get_sex(),
            )
            if len(time_standards) > 0:
                best_standard = time_standards[-1]
            else:
                best_standard = None

            # Get full club code
            if club.get_lsc() is not None:
                full_club_code = f"{club.get_lsc()}-{club.get_team_code()}"
            else:
                full_club_code = club.get_team_code()

            # Condense age range if possible
            age_range = swimmer.get_age_range(RELAY_GENERATOR.get_relay_date())
            if age_range[0] == age_range[1]:
                age_range = age_range[0]

            # Get swimmer sex
            sex = str(swimmer.get_sex())

            # Display relay leg
            if best_standard is not None:
                print(
                    f" {stroke:<6}  {full_name:<20}  {age_range:>8}  {sex:<1}  "
                    + f"{usa_id:<14}  {full_club_code:<7}  {best_time:>8}  "
                    + f"{best_standard.short():<4}  {meet_name:<30}"
                )
            else:
                print(
                    f" {stroke:<6}  {full_name:<20}  {age_range:>8}  {sex:<1}  "
                    + f"{usa_id:<14}  {full_club_code:<7}  {best_time:>8}  "
                    + f"{meet_name:<30}"
                )
        print()
        relay_letter = chr(ord(relay_letter) + 1)


def display_swimmer_information(swimmer: database.swim.Swimmer) -> None:
    """
    Display swimmer information
    """
    # Calculate full name
    full_name = swimmer.get_full_name()

    # Calculate birthday
    b_range = swimmer.get_birthday_range()
    if b_range[0] == b_range[1]:
        b_range = f"{b_range[0]}"
    else:
        b_range = f"{b_range[0]}-{b_range[1]}"

    # Calculate age
    a_range = swimmer.get_age_range(datetime.date.today())
    min_age, max_age = a_range
    if min_age == max_age:
        a_range = f"{min_age}"
    else:
        a_range = f"{min_age}-{max_age}"

    # Calculate id
    long_id = swimmer.get_usa_id_long()
    if long_id == None:
        long_id = f"--------------"

    # Calcate club and lsc code
    club = swimmer.get_club()
    if club is None:
        full_club_code = "-------"
    elif club.get_lsc() is None:
        full_club_code = club.get_team_code()
    else:
        lsc_code = club.get_lsc()
        team_code = club.get_team_code()
        full_club_code = f"{lsc_code}-{team_code}"

    # Get swimmer sex
    sex = str(swimmer.get_sex())

    print(
        f"{full_name:<27}  {a_range:<5}  {sex:<1}  {long_id:<14}  {full_club_code:<7}  "
        + f"{b_range:<25}"
    )


def display_ind_meet_result_info(
    swimmer: database.swim.Swimmer,
    mr: database.swim.IndividualMeetResult,
) -> None:
    """
    Display individual meet result information.
    """
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

    # Calculate time standard
    time_standards = TIME_STANDARD_INFO.get_qualified_standards(
        final_time,
        event,
        swimmer.get_age_range(datetime.date.today())[0],
        swimmer.get_sex(),
    )
    if len(time_standards) == 0:
        print(
            f"{event}  {str(final_time):<8}  {session}  {age_class:<2}  {meet_name:<30}  "
            + f"{full_code:<7}  {swim_date}"
        )
    else:
        best_time_standard = time_standards[-1]
        best_time_standard_str = best_time_standard.short()
        print(
            f"{event}  {str(final_time):<8}  {session}  {age_class:<2}  {meet_name:<30}  "
            + f"{full_code:<7}  {swim_date}  [{best_time_standard_str}]"
        )


def display_excluded_relay_swimmers() -> None:
    """
    Display excluded swimmers in relay generator.
    """
    print("Excluded swimmers:")
    for swimmer in RELAY_GENERATOR.get_excluded_swimmers():
        display_swimmer_information(swimmer)
    print()


def display_error(message: str) -> None:
    """
    Display an error message to the user.
    """
    assert isinstance(message, str)
    print(f"Error: {message}")
