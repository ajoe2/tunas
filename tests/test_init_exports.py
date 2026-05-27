import tunas


def test_all_symbols_importable() -> None:
    missing = [name for name in tunas.__all__ if not hasattr(tunas, name)]
    assert not missing, missing


def test_version_string() -> None:
    assert isinstance(tunas.__version__, str)
    assert tunas.__version__.count(".") >= 1


def test_key_public_api_present() -> None:
    for name in (
        "read_cl2",
        "read_hy3",
        "MeetArchive",
        "Hy3FileType",
        "Meet",
        "Swimmer",
        "IndividualSwim",
        "Relay",
        "RelaySwim",
        "Swim",
        "Split",
        "Time",
        "Event",
        "TimeStandard",
        "qualifies_for",
        "standard_time",
        "all_qualified",
        "ParseError",
        "ParseReport",
        "ParseWarning",
        "Severity",
        "IssueKind",
        "Country",
        "LSC",
        "State",
    ):
        assert name in tunas.__all__
