
import os
import pandas as pd

from util import *


class TimeStandard():
    """
    Class containing all time standards information. Can only be accessed
    through Database object methods when running main. 
    """
    src_path = os.path.dirname(os.path.realpath(__file__))
    swimdatabase_path = os.path.dirname(src_path)
    time_standards_path = swimdatabase_path + r"/data/timeStandards"
    standards = ["B", "BB", "A", "AGC", "AA", "FW", "AAA", "AAAA", 
                 "Sect", "Fut", "Jnat", "Nat", "OT"]
    standard_to_full_name = {"B": "B", "BB": "BB", "A": "A", "AA": "AA",
                             "AAA": "AAA", "AAAA": "AAAA", 
                             "AGC": "Age Group Champs", "FW": "Far Westerns",
                             "Sect": "Sectionals", "Fut": "Futures", 
                             "Jnat": "Junior Nationals", "Nat": "Nationals", 
                             "OT": "Olympic Trials"}
    single_age_groups = ['10&u', '11', '12', '13', '14']
    double_age_groups = ['10&u', '11-12', '13-14', '15-16', '17-18']
    senior_age_groups = ['18u', '19o']
    normal_age_groups = ['10&u', '11-12', '13-14', 'senior']
    file_paths = {"B": time_standards_path + r"/B-2028.xlsx",
                  "BB": time_standards_path + r"/BB-2028.xlsx",
                  "A": time_standards_path + r"/A-2028.xlsx",
                  "AA": time_standards_path + r"/AA-2028.xlsx",
                  "AAA": time_standards_path + r"/AAA-2028.xlsx",
                  "AAAA": time_standards_path + r"/AAAA-2028.xlsx",
                  "AGC": time_standards_path + r"/AGC-WinSpr2025.xlsx",
                  "FW": time_standards_path + r"/FW-Spr2025.xlsx",
                  "Sect": time_standards_path + r"/sectionals-2023.xlsx",
                  "Fut": time_standards_path + r"/futures-2025.xlsx",
                  "Jnat": time_standards_path + r"/jnat-2025.xlsx",
                  "Nat": time_standards_path + r"/nat-2025.xlsx",
                  "OT": time_standards_path + r"/ot-2024.xlsx"}
    age_groups = {"B": double_age_groups, "BB": double_age_groups,
                  "A": double_age_groups, "AA": double_age_groups,
                  "AAA": double_age_groups, "AAAA": double_age_groups,
                  "AGC": single_age_groups, "FW": double_age_groups,
                  "Sect": senior_age_groups, "Fut": senior_age_groups,
                  "Jnat": senior_age_groups, "Nat": senior_age_groups,
                  "OT": senior_age_groups}

    def __init__(self):
        """
        Load dataframes into self.ts_data using file paths specified in
        TimeStandards class. 
        """
        self.ts_data = {}
        for standard in TimeStandard.standards:
            self.ts_data[standard] = self.load_df(standard)

    def load_df(self, standard: str) -> dict[str: pd.DataFrame]:
        """
        Return a mapping of age groups to time standard dataframes. See
        TimeStandards class for valid standards.

        Keyword arguments:
        standard -- desired time standard
        """
        inv_std_str = f"Cannot find time standard '{standard}'"
        assert standard in TimeStandard.standards, inv_std_str

        file_path = TimeStandard.file_paths[standard]
        age_groups = TimeStandard.age_groups[standard]
        dfs = {}
        for sheet_index in range(1, len(age_groups) + 1):
            age_group = age_groups[sheet_index - 1]
            df = pd.read_excel(file_path, sheet_name=sheet_index).fillna('0')
            df = df.set_index("Event").rename_axis(None).astype(str)
            df = df.map(lambda x: Time(time_str=x))
            dfs[age_group] = df
        return dfs

    def get_time_standards(self, standard: str, age_group: str) -> pd.DataFrame:
        """
        Return dataframe containing time standards information for 
        specified age_group and standard. See TimeStandards class
        for valid standards and age groups.

        Keyword arguments:
        standard -- desired time standard
        age_group -- desired age group
        """
        inv_std_str = f"Cannot find time standard '{standard}'"
        inv_ag_str = f"Invalid age group '{age_group}'"
        assert standard in TimeStandard.standards, inv_std_str
        assert age_group in TimeStandard.age_groups[standard], inv_ag_str

        return self.ts_data[standard][age_group]
    
    def get_time_standard(self, standard: str, sex: str, age_group: str, 
                          stroke: int, distance: int, course: str, 
                          relay=False) -> Time:
        """
        Return qualifying time for specified standard. See TimeStandard
        and Util classes for valid inputs.

        Keyword arguments:
        standard -- desired time standard
        sex -- desired sex
        age_group -- desired age_group
        stroke -- desired stroke
        distance -- desired distance
        course -- desired course
        relay -- True if querying relay qualifying time, False otherwise
        """
        inv_std_str = f"Cannot find time standard {standard}"
        inv_ag_str = f"Invalid age group: {age_group}"
        inv_sex_str = f"Invalid sex: {sex}"
        inv_evnt_str = f"Invalid event: ({distance} {stroke} {course})"
        assert standard in TimeStandard.standards, inv_std_str
        assert age_group in TimeStandard.age_groups[standard], inv_ag_str
        assert sex in Util.sex_code, inv_sex_str
        assert (distance, stroke, course) in Util.valid_events, inv_evnt_str
        
        df = self.get_time_standards(standard, age_group)
        column = f"{Util.course_to_str[course]}-{sex}"
        if distance == 1500 or distance == 1650:
            row = f"1500/1650 FR"
        elif not relay and (distance == 1000 or distance == 800):
            row = f"800/1000 FR"
        elif not relay and stroke == 1 and (distance == 500 or distance == 400):
            row = f"400/500 FR"
        else:
            row = f"{distance} {Util.stroke_to_str_short[stroke]}"
        if relay:
            row = f"{row} Relay"
        return df.loc[row, column]
    
    def get_highest_standard(self, time: Time, sex: str, age: int, 
                             stroke: int, distance: int, course: str, 
                             relay=False) -> str:
        """
        Return the highest qualifying standard that is satisfied by time. 

        Keyword arguments:
        time -- time of event
        sex -- desired sex
        age_group -- desired age
        stroke -- desired stroke
        distance -- desired distance
        course -- desired course
        relay -- True if querying relay qualifying time, False otherwise
        """
        qualified = self.get_qualified_standards(time, sex, age, stroke, 
                                                 distance, course, relay)
        return qualified[-1] if len(qualified) >= 1 else None
        
    def get_qualified_standards(self, time: Time, sex: str, age: int, 
                             stroke: int, distance: int, course: str, 
                             relay=False) -> list[str]:
        """
        Return a list of all time standards that are satisfied by time.

        Keyword arguments:
        time -- time of event
        sex -- desired sex
        age_group -- desired age
        stroke -- desired stroke
        distance -- desired distance
        course -- desired course
        relay -- True if querying relay qualifying time, False otherwise
        """
        qualified = []
        for standard in TimeStandard.standards:
            age_group = TimeStandard.age_to_age_group(age, standard)
            age_groups = TimeStandard.age_groups[standard]
            if distance == 25 or age_group not in age_groups:
                continue
            else:
                time_standard = self.get_time_standard(standard, sex, 
                                                       age_group, stroke, 
                                                       distance, course, relay)
                if time <= time_standard:
                    qualified.append(standard)
        return qualified
    
    def age_to_age_group(age: int, standard: str) -> str:
        """
        Map age to particular age group convention used by standard.

        Keyword arguments:
        age -- age of swimmer
        standard -- desired time standard
        """
        match standard:
            case "AGC":
                if age <= 10:
                    age_group = "10&u"
                else:
                    age_group = str(age)
            case "FW" | "B" | "BB" | "A" | "AA" | "AAA" | "AAAA":
                if age <= 10:
                    age_group = "10&u"
                elif age % 2 == 0:
                    age_group = f"{age - 1}-{age}"
                else:
                    age_group = f"{age}-{age + 1}"
            case "Sect" | "Fut" | "Jnat" | "Nat" | "OT":
                if age <= 18:
                    age_group = "18u"
                else:
                    age_group = "19o"
            case "normal":
                if age <= 10:
                    age_group = "10&u"
                elif age <= 14 and age % 2 == 0:
                    age_group = f"{age - 1}-{age}"
                elif age <=14:
                    age_group = f"{age}-{age + 1}"
                else:
                    age_group = f"senior"
        return age_group

