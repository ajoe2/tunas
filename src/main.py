
import os
import sys

import dataprocessor as dp
from interface import Interface

src_path = os.path.dirname(os.path.realpath(__file__))
swimdatabase_path = os.path.dirname(src_path)
meet_results_path = swimdatabase_path + r"/data/meetData"

def main():
    """
    Run SwimDatabase application or test mode if -t flag is present.
    """
    print(Interface.LOGO)
    args = sys.argv[1:]
    if args != [] and args[0] == "-t":
        run_tests()
    else:
        database = dp.read_cl2(meet_results_path)
        print(Interface.FILE_LOAD_END_STR)
        ui = Interface(database)
        running = True
        while running:
            running = ui.print_menu_and_process_input()
    print("Program terminated!")      

def run_tests():
    """
    Run database application tests. Invoked at command line with -t flag.
    """
    print("Running tests...")
    
if __name__ == "__main__":
    main()
