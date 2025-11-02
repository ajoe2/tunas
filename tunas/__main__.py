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
    no_flags = len(sys.argv) == 1 # No flags set

    # Apply settings
    download_data = True if no_flags or args.u else False
    run_application = True if no_flags or args.r else False

    if download_data:
        try:
            scraper.download_meet_result_data(MEET_DATA_PATH)
        except Exception:
            print("Error downloading meet result data. Check network connection and try again.")
            return
        except KeyboardInterrupt:
            print()
            print("Exited gracefully.")
            return

    if run_application:
        print()
        try:
            interface.run_tunas_application()
        except Exception:
            print("Something went wrong. Please restart the application.")
        except KeyboardInterrupt:
            print()
            print("Exited gracefully.")
            return


if __name__ == "__main__":
    main()
