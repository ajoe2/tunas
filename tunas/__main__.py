"""
Tunas application entry point.
"""
import os
import sys
import argparse

import interface
import scraper

TUNAS_DIRECTORY_PATH = os.path.dirname(os.path.realpath(__file__))
MEET_DATA_PATH = os.path.join(os.path.dirname(TUNAS_DIRECTORY_PATH), "data", "meetData")

def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', action='store_true', help="download meet result files from pacswim")
    parser.add_argument('-r', action='store_true', help="run tunas application")
    args = parser.parse_args()

    # If no flags, download meet results and run application
    if len(sys.argv) == 1:
        scraper.download_meet_result_data(MEET_DATA_PATH)
        print()
        interface.run_tunas_application()

    # If -u flag is specified, download meet result data
    if args.u:
        scraper.download_meet_result_data(MEET_DATA_PATH)
    
    # If -r flag is specified or no flags specified, run tunas application
    if args.r:
        print()
        interface.run_tunas_application()


if __name__ == "__main__":
    main()
