"""
Functions for manipulating underlying sdif and stime modules.
"""

from . import stime


def create_time_from_str(time_str: str) -> stime.Time:
    """
    Create and return a time object corresponding to time_str. time_str
    should be in mm:ss.hh format.
    """
    minute_str, second_str, hundredth_str = "0", "0", "0"
    minute, second, hundredth = 0, 0, 0

    # Parse string
    first_split = time_str.split(":")
    if len(first_split) == 2:
        minute_str = first_split[0]
    next_split = first_split[-1].split(".")
    if len(next_split) != 2:
        raise Exception(f"Invalid input: '{time_str}'. Should be in 'mm:ss.hh' format.")
    second_str = next_split[0]
    hundredth_str = next_split[1]
    try:
        minute = int(minute_str)
        second = int(second_str)
        hundredth = int(hundredth_str)
    except:
        raise Exception(f"Invalid input: '{time_str}'. Time is not a valid time.")

    return stime.Time(minute, second, hundredth)
