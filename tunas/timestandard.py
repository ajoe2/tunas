"""
Manages logic for time standard information
"""

import os
import enum

# Data path
TUNAS_DIRECTORY_PATH = os.path.dirname(os.path.realpath(__file__))
TIME_STANDARDS_PATH = os.path.dirname(TUNAS_DIRECTORY_PATH) + "/data/timeStandards"


class TimeStandard(enum.Enum):
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
    NAT = "Nations"
    OT = "Olympic Trials"
