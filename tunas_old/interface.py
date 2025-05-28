
from database import *
from relaymode import RelayMode


class Interface():
    """
    Class for managing user interface. Print commands and user input are
    managed here.
    """
    MENU = "1) Swimmer information\n" + \
           "2) Time standards\n" + \
           "3) Club information\n" + \
           "4) Relay mode\n" + \
           "5) Statistics\n" + \
           "Quit (q/Q)\n"
    SWIMMER_MODE_MENU = "1) Full time history\n" + \
                        "2) Best times\n" + \
                        "Back (b/B)\n"
    CLUB_MODE_MENU = " 1) Display all swimmers\n" + \
                     " 2) Display B time qualifiers\n" + \
                     " 3) Display BB time qualifiers\n" + \
                     " 4) Display A time qualifiers\n" + \
                     " 5) Display AGC qualifiers\n" + \
                     " 6) Display AA time qualifiers\n" + \
                     " 7) Display FW qualifiers\n" + \
                     " 8) Display AAA time qualifiers\n" + \
                     " 9) Display AAAA time qualifiers\n" + \
                     "10) Display Sectionals qualifiers\n" + \
                     "11) Display Futures qualifiers\n" + \
                     "12) Display Junior National qualifiers\n" + \
                     "13) Display Nationals qualifiers\n" + \
                     "14) Display Olympic Trials qualifiers\n" + \
                     "Back (b/B)\n"
    TIME_STANDARD_MODE_MENU = "1) Age Group Champs\n" + \
                              "2) Far Westerns\n" + \
                              "3) Sectionals\n" + \
                              "4) Futures\n" + \
                              "5) Junior Nationals\n" + \
                              "6) Nationals\n" + \
                              "7) Olympic Trials\n" + \
                              "Back (b/B)\n"
    SINGLE_AGE_MENU = "1) 10 & under\n" + \
                      "2) 11\n" + \
                      "3) 12\n" + \
                      "4) 13\n" + \
                      "5) 14\n" + \
                      "Back (b/B)\n"
    DOUBLE_AGE_MENU = "1) 10 & under\n" + \
                      "2) 11-12\n" + \
                      "3) 13-14\n" + \
                      "4) 15-16\n" + \
                      "5) 17-18\n" + \
                      "Back (b/B)\n"
    SENIOR_AGE_MENU = "1) 18 & under\n" + \
                      "2) 19 & over\n" + \
                      "Back (b/B)\n"
    LOGO = "\n" + \
           "#############################################################\n" + \
           "##########              Swim Database              ##########\n" + \
           "#############################################################\n" + \
           "Version: 1.0.0\n"
    INVALID_IPT = "Invalid input! Please try again."
    FILE_LOAD_END_STR = "Finished processing files!\n-----------------" + \
                        "--------------------------------------------\n"

    def __init__(self, db: Database):
        """
        Initialize interface object.

        Keyword arguments:
        db -- database where all swim data is stored.
        """
        self.db = db
        self.relays = RelayMode(self.db)

    def print_menu_and_process_input(self) -> bool:
        """
        Display options menu and process user input. Return true if user did
        not quit and false otherwise. 
        """
        print(Interface.MENU)
        ipt = input("Select mode > ")
        match ipt:
            case '1':
                self.run_swimmer_mode()
            case '2':
                self.run_time_standard_mode()
            case '3':
                self.run_club_mode()
            case '4':
                self.run_relay_mode()
            case '5':
                print()
                print("Database statistics:")
                print(f"Number of clubs: {len(self.db.get_clubs())}")
                print(f"Number of swimmers: {len(self.db.get_swimmers())}")
                print(f"Number of meets: {len(self.db.get_meets())}")
                print(f"Number of meet results: {len(self.db.get_meet_results())}")
                print()
            case 'q' | 'Q':
                return False
            case _:
                print(f"Invalid input: {ipt}.")
        return True
    
    def run_swimmer_mode(self):
        """
        Run swimmer mode. Supports searching for best time and all time
        history for a particular swimmer. 
        """
        print()
        while True:
            print(self.SWIMMER_MODE_MENU)
            ipt = input("Select mode > ")
            match ipt:
                case "1":
                    swimmer_id = input("Swimmer ID: ")
                    swimmer = self.db.find_swimmer(swimmer_id)
                    if not swimmer:
                        print(f"Swimmer not found with id '{swimmer_id}'\n")
                    else:
                        print()
                        self.display_time_history(swimmer)
                case "2":
                    swimmer_id = input("Swimmer ID: ")
                    swimmer = self.db.find_swimmer(swimmer_id)
                    if not swimmer:
                        print(f"Swimmer not found with id '{swimmer_id}'\n")
                    else:
                        print()
                        self.display_best_times(swimmer)
                case "b" | "B":
                    print()
                    break
                case _:
                    print(Interface.INVALID_IPT + "\n")
    
    def run_time_standard_mode(self):
        """
        Run time standard mode. Print time standards dataframe for
        corresponding user input. 
        """
        print()
        while True:
            print(Interface.TIME_STANDARD_MODE_MENU)
            ipt = input("Selection > ")
            match ipt:
                case "1":
                    self.ts_mode_helper("AGC")
                case "2":
                    self.ts_mode_helper("FW")
                case "3":
                    self.ts_mode_helper("Sect")
                case "4":
                    self.ts_mode_helper("Fut")
                case "5":
                    self.ts_mode_helper("Jnat")
                case "6":
                    self.ts_mode_helper("Nat")
                case "7":
                    self.ts_mode_helper("OT")
                case "B" | "b":
                    print()
                    break
                case _:
                    print(Interface.INVALID_IPT + "\n")

    def ts_mode_helper(self, standard: str):
        """
        Helper function for time standard mode function. Print time stnadard
        dataframe corresponding to standard. 
        """
        assert standard in TimeStandard.standards
        age_groups = TimeStandard.age_groups[standard]
        if age_groups == TimeStandard.single_age_groups:
            menu = Interface.SINGLE_AGE_MENU
        elif age_groups == TimeStandard.double_age_groups:
            menu = Interface.DOUBLE_AGE_MENU
        else:
            menu = Interface.SENIOR_AGE_MENU
        print()
        while True:
            print(menu)
            selection = input("Selection > ")
            if selection == "B" or selection == "b":
                print()
                break
            elif (selection not in ["1", "2", "3", "4", "5"]
                  or int(selection) not in range(1, len(age_groups) + 1)):
                print(Interface.INVALID_IPT + "\n")
            else:
                age_group = age_groups[int(selection) - 1]
                df = self.db.get_time_standard_df(standard, age_group)
                print("\n", df, "\n")

    def run_club_mode(self):
        """
        Run club mode. Print all swimmers in club specified by user input. 
        """
        print()
        while True:
            print(Interface.CLUB_MODE_MENU)
            ipt = input("Selection > ")
            if ipt == 'b' or ipt == "B":
                break
            elif ipt not in [str(num) for num in range(1, 15)]:
                print(Interface.INVALID_IPT + "\n")
            else:
                numb = int(ipt)
                if numb == 1:
                    standard = None
                else:
                    standard = TimeStandard.standards[numb - 2]
                club_code = input("Club code ('b'/'B' to go back): ")
                if club_code != 'b' and club_code != 'B':
                    self.display_all_swimmers(club_code, standard)
                else:
                    print()
                
    def display_all_swimmers(self, club_code, standard=None): 
        if standard:
            assert standard in TimeStandard.standards
        club = self.db.find_club(club_code)
        if not club:
            print("Club not found! Check club code and try again.\n")
        else:
            if standard:
                name = TimeStandard.standard_to_full_name[standard]
                print(f"\nClub found! Displaying {name} qualifiers for {club}.")
            else:
                print(f"\nClub found! Displaying all swimmers for {club}.")
            swimmers = club.get_swimmers()
            swimmers.sort(reverse=True, key=lambda s: s.get_birthday())
            if standard:
                swimmers = filter(lambda s: standard in 
                                  self.db.get_qualified_standards(s),
                                  swimmers)
            self.print_swimmers_by_age_group(swimmers)
    
    def run_relay_mode(self):
        """
        Run relay mode. Logic is handled by relay object created during 
        initialization. 
        """
        self.relays.run_relays()
        print()

    def display_time_history(self, swimmer: Swimmer):
        """
        Print all time history for swimmer.

        Keyword arguments:
        swimmer -- the swimmer whose time history will be printed.
        """
        print(f"Displaying time history for: {swimmer}")
        print(f"Time standards: " + \
              f"{self.db.get_qualified_standards(swimmer)}")
        for result in swimmer.get_time_history():
            print(result)
        print()

    def display_best_times(self, swimmer: Swimmer):
        """
        Print best times for swimmer.

        Keyword arguments:
        swimmer -- the swimmer whose best times will be printed.
        """
        print(f"Displaying best times for: {swimmer}")
        print(f"Time standards: " + \
              f"{self.db.get_qualified_standards(swimmer)}")
        for d, s, c in Event.valid_events:
            best_result = swimmer.get_best_meet_result(d, s, c)
            if best_result:
                print(best_result)
        print()

    def print_swimmers_by_age_group(self, swimmers: list[Swimmer]):
        """
        Print swimmers in swimmers list grouped by age group. 

        Keyword arguments:
        swimmers -- list of swimmers sorted by age.
        """
        print()
        sorted = {age_group: [] for age_group in TimeStandard.normal_age_groups}
        for swimmer in swimmers:
            age = swimmer.get_age(date.today())
            age_group = TimeStandard.age_to_age_group(age, "normal")
            sorted[age_group].append(swimmer)
        for ag in sorted:
            print(f"------------------------ {ag} swimmers ------------------------\n")
            lst = sorted[ag]
            for s in lst:
                print(s)
            print()

    
    