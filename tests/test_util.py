"""
Tests for database.util package.
"""

from database import stime, util
from database import sdif


def test_create_time_from_string_basic1():
    t_str = "1:52.65"
    t = util.create_time_from_str(t_str)
    assert t == stime.Time(1, 52, 65)


def test_create_time_from_string_error1():
    try:
        t_str = "]fw*Ds1"  # Garbage
        t = util.create_time_from_str(t_str)
        success = True
    except:
        success = False
    assert not success


def test_create_time_from_string_error2():
    try:
        t_str = "1:99.99"  # Invalid minutes
        t = util.create_time_from_str(t_str)
        success = True
    except:
        success = False
    assert not success


def test_create_time_from_string_error3():
    try:
        t_str = "1:59.999"  # Invalid hundredths
        t = util.create_time_from_str(t_str)
        success = True
    except:
        success = False
    assert not success
