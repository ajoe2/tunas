import pytest

from tunas import Event, Sex, Time, TimeStandard, all_qualified, qualifies_for, standard_time
from tunas.standards import _load_index


def test_timestandard_six_members_ordered() -> None:
    assert [s.name for s in TimeStandard] == ["B", "BB", "A", "AA", "AAA", "AAAA"]
    assert TimeStandard.B < TimeStandard.AAAA
    assert max([TimeStandard.B, TimeStandard.AA, TimeStandard.AAA]) is TimeStandard.AAA


def test_display() -> None:
    assert TimeStandard.AAAA.display() == "AAAA"
    assert TimeStandard.BB.display() == "BB"


def test_standard_time_known_cutoff() -> None:
    # B, 10&under, F, 50 Free SCY = 39.79 in the 2025-2028 sheet.
    assert standard_time(TimeStandard.B, Event.FREE_50_SCY, age=10, sex=Sex.FEMALE) == Time.parse(
        "39.79"
    )


def test_standard_time_undefined_returns_none() -> None:
    # No 25 events in the motivational standards.
    assert standard_time(TimeStandard.B, Event.FREE_25_SCY, age=10, sex=Sex.FEMALE) is None


def test_qualifies_for_at_cutoff() -> None:
    cut = standard_time(TimeStandard.B, Event.FREE_50_SCY, age=10, sex=Sex.FEMALE)
    assert cut is not None
    std = qualifies_for(cut, Event.FREE_50_SCY, age=10, sex=Sex.FEMALE)
    assert std is not None and std >= TimeStandard.B


def test_qualifies_for_returns_fastest() -> None:
    fast = standard_time(TimeStandard.AAAA, Event.FREE_50_SCY, age=10, sex=Sex.FEMALE)
    assert fast is not None
    assert qualifies_for(fast, Event.FREE_50_SCY, age=10, sex=Sex.FEMALE) is TimeStandard.AAAA


def test_qualifies_for_too_slow_returns_none() -> None:
    assert qualifies_for(Time.parse("5:00.00"), Event.FREE_50_SCY, age=10, sex=Sex.FEMALE) is None


def test_all_qualified_ordered_slowest_first() -> None:
    fast = standard_time(TimeStandard.AAAA, Event.FREE_50_SCY, age=10, sex=Sex.FEMALE)
    assert fast is not None
    result = all_qualified(fast, Event.FREE_50_SCY, age=10, sex=Sex.FEMALE)
    assert result == [
        TimeStandard.B,
        TimeStandard.BB,
        TimeStandard.A,
        TimeStandard.AA,
        TimeStandard.AAA,
        TimeStandard.AAAA,
    ]


def test_age_bucketing() -> None:
    # Different age buckets resolve to different cutoffs for the same event/sex.
    young = standard_time(TimeStandard.B, Event.FREE_50_SCY, age=10, sex=Sex.MALE)
    older = standard_time(TimeStandard.B, Event.FREE_50_SCY, age=15, sex=Sex.MALE)
    assert young is not None and older is not None
    assert young != older


def test_mixed_sex_raises() -> None:
    with pytest.raises(ValueError):
        qualifies_for(Time.parse("39.79"), Event.FREE_50_SCY, age=10, sex=Sex.MIXED)
    with pytest.raises(ValueError):
        standard_time(TimeStandard.B, Event.FREE_50_SCY, age=10, sex=Sex.MIXED)
    with pytest.raises(ValueError):
        all_qualified(Time.parse("39.79"), Event.FREE_50_SCY, age=10, sex=Sex.MIXED)


def test_lazy_load_cached_once() -> None:
    _load_index.cache_clear()
    first = _load_index()
    assert _load_index() is first
    assert len(first) > 1000
