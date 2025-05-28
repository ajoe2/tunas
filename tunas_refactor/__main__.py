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
    swimmers = db.get_clubs()[0].get_swimmers()
    swimmers.sort(key=lambda s: s.get_first_name() + s.get_last_name())
    for swimmer in swimmers:
        print(f"{swimmer.first_name} {swimmer.last_name} {swimmer.get_usa_id_short()}")
    print("Program ended")


if __name__ == "__main__":
    main()
