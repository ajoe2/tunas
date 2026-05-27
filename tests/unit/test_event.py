import pytest

from tunas import Course, Event, Stroke


def test_find_every_member_roundtrips() -> None:
    for e in Event:
        assert Event.find(e.distance, e.stroke, e.course) is e


def test_find_unknown_combo_returns_none() -> None:
    assert Event.find(25, Stroke.BREASTSTROKE, Course.LCM) is None
    assert Event.find(999, Stroke.FREESTYLE, Course.SCY) is None


def test_component_properties() -> None:
    e = Event.FREE_100_SCY
    assert e.distance == 100
    assert e.stroke is Stroke.FREESTYLE
    assert e.course is Course.SCY
    assert Event.MEDLEY_400_RELAY_SCY.distance == 400


def test_is_relay() -> None:
    assert Event.FREE_400_RELAY_SCY.is_relay()
    assert Event.MEDLEY_200_RELAY_LCM.is_relay()
    assert not Event.FREE_100_SCY.is_relay()


def test_leg_distance() -> None:
    assert Event.FREE_400_RELAY_SCY.leg_distance() == 100
    assert Event.MEDLEY_200_RELAY_SCM.leg_distance() == 50
    with pytest.raises(ValueError):
        Event.FREE_100_SCY.leg_distance()


def test_leg_strokes() -> None:
    assert Event.FREE_400_RELAY_SCY.leg_strokes() == [Stroke.FREESTYLE] * 4
    assert Event.MEDLEY_400_RELAY_SCY.leg_strokes() == [
        Stroke.BACKSTROKE,
        Stroke.BREASTSTROKE,
        Stroke.BUTTERFLY,
        Stroke.FREESTYLE,
    ]
    with pytest.raises(ValueError):
        Event.FREE_100_SCY.leg_strokes()


def test_leg_event_free_and_medley() -> None:
    assert Event.FREE_400_RELAY_SCY.leg_event(1) is Event.FREE_100_SCY
    assert Event.MEDLEY_400_RELAY_SCY.leg_event(1) is Event.BACK_100_SCY
    assert Event.MEDLEY_400_RELAY_SCY.leg_event(2) is Event.BREAST_100_SCY
    assert Event.MEDLEY_400_RELAY_SCY.leg_event(3) is Event.FLY_100_SCY
    assert Event.MEDLEY_400_RELAY_SCY.leg_event(4) is Event.FREE_100_SCY


def test_leg_event_invalid() -> None:
    with pytest.raises(ValueError):
        Event.FREE_100_SCY.leg_event(1)
    with pytest.raises(ValueError):
        Event.FREE_400_RELAY_SCY.leg_event(5)
    with pytest.raises(ValueError):
        Event.FREE_400_RELAY_SCY.leg_event(0)


def test_every_relay_leg_resolves() -> None:
    for e in Event:
        if e.is_relay():
            for order in range(1, 5):
                assert isinstance(e.leg_event(order), Event)


def test_ordering_by_declaration() -> None:
    assert Event.FREE_50_SCY < Event.FREE_100_SCY
    assert Event.FREE_100_SCY <= Event.FREE_100_SCY
    assert Event.FREE_200_SCY > Event.FREE_100_SCY
    assert Event.FREE_200_SCY >= Event.FREE_200_SCY
