"""
Entry point for tunas application.
"""

import parser


def main():
    """
    Run Tunas application.
    """
    print("Program started")
    db = parser.read_cl2("/Users/ajoe/code/tunas/data/meetData")
    print(f"Number of meets: {len(db.get_meets())}")
    print(f"Number of meet results: {len(db.get_meet_results())}")
    print(f"Number of swimmers: {len(db.get_swimmers())}")
    print(f"Number of clubs: {len(db.get_clubs())}")
    print("Program ended")


if __name__ == "__main__":
    main()
