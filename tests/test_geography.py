from tunas.geography import LSC, Country, State


def test_geo_geq_collision_fixed() -> None:
    assert Country("GEO") is Country.GEORGIA
    assert Country("GEQ") is Country.EQUATORIAL_GUINEA
    assert Country.GEORGIA is not Country.EQUATORIAL_GUINEA


def test_dominican_republic_code_fixed() -> None:
    assert Country("DOM") is Country.DOMINICAN_REPUBLIC


def test_syria_present() -> None:
    assert Country("SYR") is Country.SYRIA


def test_no_duplicate_country_values() -> None:
    members = list(Country)
    assert len({c.value for c in members}) == len(members)


def test_no_citizenship_codes_in_country() -> None:
    # "2AL"/"FGN" are Citizenship, not Country.
    assert "2AL" not in {c.value for c in Country}
    assert "FGN" not in {c.value for c in Country}


def test_lsc_and_state_roundtrip() -> None:
    assert LSC("PC") is LSC.PACIFIC
    assert State("CA") is State.CALIFORNIA
    assert len({m.value for m in LSC}) == len(list(LSC))
    assert len({m.value for m in State}) == len(list(State))
