
import os

import dataprocessor as dp
from interface import Interface

src_path = os.path.dirname(os.path.realpath(__file__))
swimdatabase_path = os.path.dirname(src_path)
meet_results_path = swimdatabase_path + r"/data/meetData"

def main():
    """
    Run SwimDatabase application.
    """
    print(Interface.LOGO)
    database = dp.read_cl2(meet_results_path)
    print(Interface.FILE_LOAD_END_STR)
    ui = Interface(database)
    running = True
    while running:
        running = ui.print_menu_and_process_input()
    print("Program terminated!")      
    
if __name__ == "__main__":
    main()
