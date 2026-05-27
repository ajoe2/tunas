import dataclasses
import datetime

import pytest

from tunas import (
    AttachStatus,
    Club,
    Course,
    Event,
    IndividualSwim,
    Meet,
    MeetResult,
    Organization,
    Relay,
    RelayLegOrder,
    RelaySwim,
    ResultStatus,
    Session,
    Sex,
    Split,
    SplitType,
    Swim,
    Swimmer,
    Time,
)


def _meet() -> Meet:
    return Meet(organization=Organization.USS, name="M", start_date=datetime.date(2025, 1, 1))


def _swimmer(m: Meet) -> Swimmer:
    return Swimmer(
        meet=m,
        first_name="Irene",
        last_name="Zhong",
        sex=Sex.FEMALE,
        id_short="49AC52F69618",
        middle_initial="Q",
    )


def _individual(m: Meet, s: Swimmer, **kw: object) -> IndividualSwim:
    base: dict[str, object] = dict(
        meet=m,
        club=None,
        organization=Organization.USS,
        session=Session.FINALS,
        event=Event.FREE_100_SCY,
        event_min_age=None,
        event_max_age=None,
        event_sex=Sex.FEMALE,
        status=ResultStatus.OK,
        time=Time.parse("1:00.00"),
        date=datetime.date(2025, 1, 1),
        swimmer=s,
    )
    base.update(kw)
    return IndividualSwim(**base)  # type: ignore[arg-type]


def _relay(m: Meet, **kw: object) -> Relay:
    base: dict[str, object] = dict(
        meet=m,
        club=None,
        organization=Organization.USS,
        session=Session.FINALS,
        event=Event.FREE_400_RELAY_SCY,
        event_min_age=None,
        event_max_age=None,
        event_sex=Sex.FEMALE,
        status=ResultStatus.OK,
        time=Time.parse("3:30.00"),
        date=datetime.date(2025, 1, 2),
        relay_letter="A",
    )
    base.update(kw)
    return Relay(**base)  # type: ignore[arg-type]


def test_swim_is_abstract() -> None:
    with pytest.raises(TypeError):
        Swim()  # type: ignore[abstract]


def test_individual_swim_is_swim_and_meetresult() -> None:
    m = _meet()
    ind = _individual(m, _swimmer(m))
    assert isinstance(ind, Swim)
    assert isinstance(ind, MeetResult)
    assert ind.is_relay_leg is False
    assert ind.course is Course.SCY


def test_slots_no_dict_and_no_undeclared_attr() -> None:
    m = _meet()
    ind = _individual(m, _swimmer(m))
    assert not hasattr(ind, "__dict__")
    with pytest.raises(AttributeError):
        ind.nonexistent = 1  # type: ignore[attr-defined]


def test_identity_equality_and_hash() -> None:
    m = _meet()
    s = _swimmer(m)
    a, b = _individual(m, s), _individual(m, s)
    assert a == a
    assert a != b  # eq=False -> identity
    assert hash(a) != hash(b)


def test_relay_leg_delegation_and_individual_leg_event() -> None:
    m = _meet()
    s = _swimmer(m)
    relay = _relay(m)
    leg = RelaySwim(
        swimmer=s, relay=relay, order=RelayLegOrder.LEG_1, time=Time.parse("52.00"), takeoff_time=29
    )
    relay.legs.append(leg)
    assert leg.is_relay_leg is True
    assert leg.event is Event.FREE_100_SCY  # individual leg event
    assert leg.date == relay.date
    assert leg.meet is relay.meet
    assert leg.session is relay.session
    assert leg.session == leg.relay.session
    assert leg.takeoff_time == 29
    assert not isinstance(leg, MeetResult)


def test_medley_alternate_event_none_free_alternate_resolves() -> None:
    m = _meet()
    medley = _relay(m, event=Event.MEDLEY_400_RELAY_SCY)
    medley_alt = RelaySwim(swimmer=None, relay=medley, order=RelayLegOrder.ALTERNATE)
    assert medley_alt.event is None
    free = _relay(m)
    free_alt = RelaySwim(swimmer=None, relay=free, order=RelayLegOrder.ALTERNATE)
    assert free_alt.event is Event.FREE_100_SCY


def test_swimmer_views_and_swims_in() -> None:
    m = _meet()
    s = _swimmer(m)
    ind = _individual(m, s)
    pre = _individual(m, s, session=Session.PRELIMS, status=ResultStatus.NT, time=None)
    relay = _relay(m)
    leg = RelaySwim(swimmer=s, relay=relay, order=RelayLegOrder.LEG_1)
    s.swims.extend([ind, pre, leg])
    assert s.individual_swims == [ind, pre]
    assert s.relay_swims == [leg]
    # swims_in matches both individual swims and the relay leg (by individual leg event)
    assert s.swims_in(Event.FREE_100_SCY) == [ind, pre, leg]
    assert s.full_name == "Irene Q Zhong"


def test_swimmer_full_name_no_middle() -> None:
    m = _meet()
    s = Swimmer(meet=m, first_name="Kevin", last_name="Zhou", sex=Sex.MALE, id_short="X")
    assert s.full_name == "Kevin Zhou"


def test_meet_and_club_views() -> None:
    m = _meet()
    s = _swimmer(m)
    ind = _individual(m, s)
    relay = _relay(m)
    m.results.extend([ind, relay])
    assert m.individual_swims == [ind]
    assert m.relays == [relay]
    assert m.individual_swims_for(Event.FREE_100_SCY) == [ind]
    assert m.individual_swims_for(Event.FREE_200_SCY) == []
    assert m.relays_for(Event.FREE_400_RELAY_SCY) == [relay]


def test_no_analysis_or_find_methods() -> None:
    for name in (
        "find_swimmer",
        "find_swimmers",
        "find_club",
        "age_on",
        "age_range_on",
        "best_swim",
        "date_most_recent_swim",
        "roster",
    ):
        assert not hasattr(Meet, name)
        assert not hasattr(Swimmer, name)


def test_split_frozen_hashable() -> None:
    sp = Split(distance=50, time=Time.parse("25.00"), split_type=SplitType.CUMULATIVE)
    assert hash(sp)
    with pytest.raises(dataclasses.FrozenInstanceError):
        sp.distance = 100  # type: ignore[misc]


def test_open_ended_age_and_optionals() -> None:
    m = _meet()
    s = _swimmer(m)
    ind = _individual(
        m, s, event_min_age=None, event_max_age=None, status=ResultStatus.DNF, time=None, date=None
    )
    assert ind.event_min_age is None and ind.event_max_age is None
    assert ind.status is ResultStatus.DNF and ind.time is None and ind.date is None
    assert ind.attach_status is AttachStatus.ATTACHED


def test_splits_live_on_leg_with_none_time() -> None:
    m = _meet()
    relay = _relay(m)
    leg = RelaySwim(swimmer=None, relay=relay, order=RelayLegOrder.LEG_1)
    leg.splits.append(Split(distance=50, time=None, split_type=SplitType.INTERVAL))
    assert leg.splits[0].time is None
    # SDIF leaves the relay-level splits empty (they live on the legs); the
    # whole-relay `Relay.splits` list is only populated by the `.hy3` reader.
    assert relay.splits == []


# --------------------------------------------------------------------------- #
# repr / str — must stay concise and finite despite the cyclic object graph
# --------------------------------------------------------------------------- #


def _fully_wired_meet() -> Meet:
    """A meet with every back-reference populated, mirroring parser output."""
    m = _meet()
    s = _swimmer(m)
    m.swimmers.append(s)
    ind = _individual(m, s)
    relay = _relay(m)
    leg = RelaySwim(swimmer=s, relay=relay, order=RelayLegOrder.LEG_1, time=Time.parse("52.00"))
    relay.legs.append(leg)
    s.swims.extend([ind, leg])
    m.results.extend([ind, relay])
    return m


def test_repr_terminates_on_cyclic_graph() -> None:
    """Every aggregate's repr is finite and small even with cycles wired up.

    The dataclass-default repr walks back-references (Meet<->Club<->Swimmer<->
    result) and blows up combinatorially; a populated meet would render into
    megabytes. The custom reprs summarise collections by count and reference
    related objects by a short label, so each stays a single short line.
    """
    m = _fully_wired_meet()
    ind, relay = m.results
    leg = relay.legs[0]  # type: ignore[attr-defined]
    s = m.swimmers[0]
    for obj in (m, s, ind, relay, leg):
        assert len(repr(obj)) < 250
        assert len(str(obj)) < 250


def test_repr_does_not_recurse_into_related_objects() -> None:
    """A repr names related objects by a short label, never their full repr."""
    m = _fully_wired_meet()
    # Meet shows collection counts, not the nested Swimmer/Club/result reprs.
    assert "Swimmer(" not in repr(m)
    assert "IndividualSwim(" not in repr(m)
    assert "clubs=" in repr(m) and "swimmers=" in repr(m) and "results=" in repr(m)
    # A swim references its swimmer by name, not by expanding the Swimmer repr.
    ind = m.results[0]
    assert "Swimmer(" not in repr(ind)
    assert "Irene Q Zhong" in repr(ind)


def test_meet_repr_and_str() -> None:
    m = _fully_wired_meet()
    assert repr(m) == (
        "Meet(name='M', organization=USS, start_date=2025-01-01, "
        "clubs=0, swimmers=1, results=2)"
    )
    assert str(m) == "M (2025-01-01)"


def test_club_repr_and_str() -> None:
    m = _meet()
    c = Club(meet=m, organization=Organization.USS, team_code="ABC", full_name="ABC Aquatics")
    assert repr(c) == (
        "Club(team_code='ABC', lsc=None, full_name='ABC Aquatics', swimmers=0, results=0)"
    )
    assert str(c) == "ABC Aquatics"
    # Falls back to the team code when no full name is set.
    bare = Club(meet=m, organization=Organization.USS, team_code="XYZ")
    assert str(bare) == "XYZ"


def test_swimmer_repr_and_str() -> None:
    m = _meet()
    s = _swimmer(m)
    assert repr(s) == (
        "Swimmer(full_name='Irene Q Zhong', id_short='49AC52F69618', "
        "sex=FEMALE, club=None, swims=0)"
    )
    assert str(s) == "Irene Q Zhong"


def test_individual_swim_repr_and_str() -> None:
    m = _meet()
    ind = _individual(m, _swimmer(m))
    assert repr(ind) == (
        "IndividualSwim(swimmer='Irene Q Zhong', event=FREE_100_SCY, "
        "status=OK, time=1:00.00, splits=0)"
    )
    assert str(ind) == "Irene Q Zhong FREE_100_SCY 1:00.00"


def test_relay_repr_and_str() -> None:
    m = _meet()
    relay = _relay(m)
    assert repr(relay) == (
        "Relay(relay_letter='A', event=FREE_400_RELAY_SCY, club=None, "
        "status=OK, time=3:30.00, legs=0)"
    )
    # No club -> "?" placeholder rather than a recursion-prone label.
    assert str(relay) == "? A FREE_400_RELAY_SCY 3:30.00"


def test_relay_swim_repr_and_str() -> None:
    m = _meet()
    s = _swimmer(m)
    relay = _relay(m)
    leg = RelaySwim(swimmer=s, relay=relay, order=RelayLegOrder.LEG_1, time=Time.parse("52.00"))
    assert repr(leg) == (
        "RelaySwim(swimmer='Irene Q Zhong', order=LEG_1, time=52.00, status=OK, relay='A')"
    )
    assert str(leg) == "Irene Q Zhong LEG_1 52.00"


def test_repr_handles_none_swimmer_and_order() -> None:
    """An alternate roster slot (no swimmer, no leg order) still renders."""
    m = _meet()
    alt = RelaySwim(swimmer=None, relay=_relay(m), order=None)
    assert repr(alt) == "RelaySwim(swimmer=None, order=None, time=None, status=OK, relay='A')"
    assert str(alt) == "None None None"


def test_meetresult_base_repr_uses_runtime_type_name() -> None:
    """The base repr defers the class name so subclasses inherit it safely."""
    m = _meet()
    base = MeetResult(
        meet=m,
        club=None,
        organization=Organization.USS,
        session=Session.PRELIMS,
        event=Event.FREE_50_SCY,
        event_min_age=None,
        event_max_age=None,
        event_sex=Sex.MALE,
        status=ResultStatus.DQ,
        time=None,
        date=None,
    )
    assert repr(base) == (
        "MeetResult(event=FREE_50_SCY, session=PRELIMS, status=DQ, time=None, club=None)"
    )
