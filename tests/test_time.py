import pytest

from tunas import Time


@pytest.mark.parametrize(
    "text,cs",
    [
        ("23.45", 2345),
        ("1:23.45", 8345),
        ("0:23.45", 2345),
        ("12:34.56", 75456),
        ("  23.45  ", 2345),
        ("5.2", 520),  # 1-digit fraction tolerated
    ],
)
def test_parse_formats(text: str, cs: int) -> None:
    assert Time.parse(text).centiseconds == cs


@pytest.mark.parametrize("bad", ["12", "1:2:3", "", "abc", "  ", ":.", "1:.5"])
def test_parse_invalid(bad: str) -> None:
    with pytest.raises(ValueError):
        Time.parse(bad)


def test_negative_centiseconds_raises() -> None:
    with pytest.raises(ValueError):
        Time(-1)


@pytest.mark.parametrize(
    "cs,text",
    [(0, "0.00"), (2345, "23.45"), (8345, "1:23.45"), (6005, "1:00.05"), (523, "5.23")],
)
def test_str_roundtrip(cs: int, text: str) -> None:
    assert str(Time(cs)) == text
    assert Time.parse(text) == Time(cs)


def test_repr() -> None:
    assert repr(Time(8345)) == "Time(centiseconds=8345)"


def test_properties() -> None:
    t = Time.parse("1:23.45")
    assert (t.minute, t.second, t.hundredth) == (1, 23, 45)
    assert t.total_seconds == 83.45
    assert t.centiseconds == 8345


def test_marathon_time_over_an_hour() -> None:
    t = Time(6000 * 70 + 1234)
    assert t.minute == 70
    assert str(t) == "70:12.34"


def test_ordering_and_sorting() -> None:
    a, b, c = Time(2345), Time(2346), Time(8345)
    assert a < b < c
    assert sorted([c, a, b]) == [a, b, c]


def test_hash_and_equality() -> None:
    assert hash(Time(2345)) == hash(Time(2345))
    assert len({Time(1), Time(2), Time(1)}) == 2
    assert (Time(2345) == None) is False  # noqa: E711


def test_addition() -> None:
    assert Time.parse("1:00.00") + Time.parse("30.50") == Time.parse("1:30.50")
    # carry across centiseconds and seconds
    assert Time(99) + Time(1) == Time(100)
    assert Time(5999) + Time(1) == Time(6000)


def test_subtraction() -> None:
    assert Time.parse("1:30.00") - Time.parse("30.00") == Time.parse("1:00.00")
    with pytest.raises(ValueError):
        _ = Time.parse("30.00") - Time.parse("1:00.00")
