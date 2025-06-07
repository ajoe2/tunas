"""
Time standard information logic.
"""

import os
import enum

# Data path
TUNAS_DIRECTORY_PATH = os.path.dirname(os.path.realpath(__file__))
TUNAS_PROJECT_PATH = os.path.dirname(TUNAS_DIRECTORY_PATH)
TIME_STANDARDS_PATH = os.path.join(TUNAS_PROJECT_PATH, "data", "timeStandards")


class TimeStandard(enum.Enum):
    """
    Represent every possible time standard.
    """

    B = "B"
    BB = "BB"
    A = "A"
    AGC = "Age Group Champs"
    AA = "AA"
    FW = "Far Westerns"
    AAA = "AAA"
    AAAA = "AAAA"
    SECT = "Sectionals"
    FUT = "Futures"
    JNAT = "Junior Nationals"
    NAT = "Nationals"
    OT = "Olympic Trials"
