import pytest

from tunas.geography import LSC, Country, State


@pytest.mark.parametrize(
    "code,country",
    [
        ("GEO", Country.GEORGIA),
        ("GEQ", Country.EQUATORIAL_GUINEA),
        ("DOM", Country.DOMINICAN_REPUBLIC),
        ("SYR", Country.SYRIA),
    ],
)
def test_country_codes(code: str, country: Country) -> None:
    assert Country(code) is country


def test_no_citizenship_codes_in_country() -> None:
    # "2AL"/"FGN" are Citizenship, not Country.
    assert {"2AL", "FGN"}.isdisjoint(c.value for c in Country)


def test_lsc_and_state_lookup() -> None:
    assert LSC("PC") is LSC.PACIFIC
    assert State("CA") is State.CALIFORNIA
