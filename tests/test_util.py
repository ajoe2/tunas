from tunas import *

### Time class ###

def test_create_time_from_string_basic1():
    time_str = "1:52.65"
    time = create_time_from_str(time_str)
    assert time == Time(1, 52, 65)

def test_create_time_from_string_error1():
    try:
        time_str = "]fw*Ds1" # Garbage
        time = create_time_from_str(time_str)
        success = True
    except:
        success = False
    assert not success

def test_create_time_from_string_error2():
    try:
        time_str = "1:99.99" # Invalid minutes
        time = create_time_from_str(time_str)
        success = True
    except:
        success = False
    assert not success

def test_create_time_from_string_error3():
    try:
        time_str = "1:59.999" # Invalid hundredths
        time = create_time_from_str(time_str)
        success = True
    except:
        success = False
    assert not success