"""
Time standard information logic.
"""

from __future__ import annotations
from typing import Optional
import os
import enum
import pandas as pd

from . import dutil, stime


# Paths
TUNAS_DIRECTORY_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
TUNAS_PROJECT_PATH = os.path.dirname(TUNAS_DIRECTORY_PATH)
TIME_STANDARDS_PATH = os.path.join(TUNAS_PROJECT_PATH, "data", "timeStandards")

# Time standard file names
B_XLSX_FILE_NAME = "B-2028.xlsx"
BB_XLSX_FILE_NAME = "BB-2028.xlsx"
A_XLSX_FILE_NAME = "A-2028.xlsx"
AA_XLSX_FILE_NAME = "AA-2028.xlsx"
AAA_XLSX_FILE_NAME = "AAA-2028.xlsx"
AAAA_XLSX_FILE_NAME = "AAAA-2028.xlsx"
AGC_XLSX_FILE_NAME = "AGC-WinSpr2025.xlsx"
FW_XLSX_FILE_NAME = "FW-Spr2025.xlsx"
SECT_XLSX_FILE_NAME = "sectionals-2023.xlsx"
FUT_XLSX_FILE_NAME = "futures-2025.xlsx"
JNAT_XLSX_FILE_NAME = "jnat-2025.xlsx"
NAT_XLSX_FILE_NAME = "nat-2025.xlsx"
OT_XLSX_FILE_NAME = "ot-2024.xlsx"

# Age group types
SINGLE_AGE_GROUPS = [
    dutil.AgeGroup._10_U,
    dutil.AgeGroup._11,
    dutil.AgeGroup._12,
    dutil.AgeGroup._13,
    dutil.AgeGroup._14,
]
DOUBLE_AGE_GROUPS = [
    dutil.AgeGroup._10_U,
    dutil.AgeGroup._11_12,
    dutil.AgeGroup._13_14,
    dutil.AgeGroup._15_16,
    dutil.AgeGroup._17_18,
]
STANDARD_AGE_GROUPS = [
    dutil.AgeGroup._10_U,
    dutil.AgeGroup._11_12,
    dutil.AgeGroup._13_14,
    dutil.AgeGroup.SENIOR,
]
SENIOR_AGE_GROUPS = [
    dutil.AgeGroup._18_U,
    dutil.AgeGroup._19_O,
]


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


class TimeStandardInfo:
    """
    Contains time standard information.
    """

    file_paths = {
        TimeStandard.B: os.path.join(TIME_STANDARDS_PATH, B_XLSX_FILE_NAME),
        TimeStandard.BB: os.path.join(TIME_STANDARDS_PATH, BB_XLSX_FILE_NAME),
        TimeStandard.A: os.path.join(TIME_STANDARDS_PATH, A_XLSX_FILE_NAME),
        TimeStandard.AGC: os.path.join(TIME_STANDARDS_PATH, AGC_XLSX_FILE_NAME),
        TimeStandard.AA: os.path.join(TIME_STANDARDS_PATH, AA_XLSX_FILE_NAME),
        TimeStandard.FW: os.path.join(TIME_STANDARDS_PATH, FW_XLSX_FILE_NAME),
        TimeStandard.AAA: os.path.join(TIME_STANDARDS_PATH, AAA_XLSX_FILE_NAME),
        TimeStandard.AAAA: os.path.join(TIME_STANDARDS_PATH, AAAA_XLSX_FILE_NAME),
        TimeStandard.SECT: os.path.join(TIME_STANDARDS_PATH, SECT_XLSX_FILE_NAME),
        TimeStandard.FUT: os.path.join(TIME_STANDARDS_PATH, FUT_XLSX_FILE_NAME),
        TimeStandard.JNAT: os.path.join(TIME_STANDARDS_PATH, JNAT_XLSX_FILE_NAME),
        TimeStandard.NAT: os.path.join(TIME_STANDARDS_PATH, NAT_XLSX_FILE_NAME),
        TimeStandard.OT: os.path.join(TIME_STANDARDS_PATH, OT_XLSX_FILE_NAME),
    }
    age_group_types = {
        TimeStandard.B: DOUBLE_AGE_GROUPS,
        TimeStandard.BB: DOUBLE_AGE_GROUPS,
        TimeStandard.A: DOUBLE_AGE_GROUPS,
        TimeStandard.AGC: SINGLE_AGE_GROUPS,
        TimeStandard.AA: DOUBLE_AGE_GROUPS,
        TimeStandard.FW: DOUBLE_AGE_GROUPS,
        TimeStandard.AAA: DOUBLE_AGE_GROUPS,
        TimeStandard.AAAA: DOUBLE_AGE_GROUPS,
        TimeStandard.SECT: SENIOR_AGE_GROUPS,
        TimeStandard.FUT: SENIOR_AGE_GROUPS,
        TimeStandard.JNAT: SENIOR_AGE_GROUPS,
        TimeStandard.NAT: SENIOR_AGE_GROUPS,
        TimeStandard.OT: SENIOR_AGE_GROUPS,
    }

    def __init__(self) -> None:
        """
        Initialize TimeStandardInfo object.
        """
        self.ts_data = dict()
        self.load_time_standard_data()

    def load_time_standard_data(self) -> None:
        """
        Load time standard dataframes into self.
        """
        for ts in TimeStandard:
            file_path = TimeStandardInfo.file_paths[ts]
            age_groups = TimeStandardInfo.age_group_types[ts]
            age_group_to_df = dict()
            for sheet_index in range(1, len(age_groups) + 1):
                age_group = age_groups[sheet_index - 1]
                df = (
                    pd.read_excel(file_path, sheet_name=sheet_index)
                    .fillna("0")
                    .set_index("Event")
                    .rename_axis(None)
                    .astype(str)
                    .map(lambda x: x[:-1] if x[-1] == "*" else x)
                    .map(
                        lambda x: (
                            stime.create_time_from_str(x)
                            if x != "0"
                            else stime.Time(0, 0, 0)
                        )
                    )
                )
                age_group_to_df[age_group] = df
            self.ts_data[ts] = age_group_to_df

    def get_time_standard_df(
        self, standard: TimeStandard, age_group: dutil.AgeGroup
    ) -> Optional[pd.DataFrame]:
        assert type(standard) == TimeStandard
        assert type(age_group) == dutil.AgeGroup
        try:
            df = self.ts_data[standard][age_group]
            return df
        except KeyError:
            return None
