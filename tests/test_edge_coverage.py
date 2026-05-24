"""Targeted tests for defensive branches and orphan handling."""

from __future__ import annotations

import pytest
from conftest import A0, B1, C1, Z0, d0, parse_lines, rec

from tunas import Event, IssueKind, Severity, StandardsError, Time
from tunas import standards as standards_mod
from tunas._parser.names import parse_name

# -- value-type NotImplemented branches -------------------------------------- #


def test_time_arithmetic_typeerror_with_non_time() -> None:
    with pytest.raises(TypeError):
        Time(100) + 5  # type: ignore[operator]
    with pytest.raises(TypeError):
        Time(100) - 5  # type: ignore[operator]


def test_event_comparison_typeerror_with_non_event() -> None:
    for op in ("__lt__", "__le__", "__gt__", "__ge__"):
        assert getattr(Event.FREE_50_SCY, op)(5) is NotImplemented


# -- name parsing edges ------------------------------------------------------ #


def test_parse_name_no_comma() -> None:
    assert parse_name("Madonna") == ("Madonna", "", None)


def test_parse_name_comma_no_first() -> None:
    assert parse_name("Smith,") == ("Smith", "", None)


def test_d0_name_without_comma() -> None:
    meets, _ = parse_lines([A0, B1, C1, d0(name="Madonna"), Z0])
    sw = meets[0].swimmers[0]
    assert sw.last_name == "Madonna"
    assert sw.first_name == ""


# -- orphan / no-context branches -------------------------------------------- #


def test_d0_before_b1_is_orphan() -> None:
    meets, report = parse_lines([A0, d0(), Z0])
    assert meets == []
    assert report.warnings_for(record_type="D0", kind=IssueKind.ORPHANED)


def test_e0_before_b1_is_orphan() -> None:
    from conftest import e0

    meets, report = parse_lines([A0, e0(), Z0])
    assert report.warnings_for(record_type="E0", kind=IssueKind.ORPHANED)


def test_d1_d2_d3_before_swimmer_are_orphans() -> None:
    d1 = rec((1, "D1"), (3, "1"), (19, "Nobody, No"))
    d2 = rec((1, "D2"), (3, "1"), (19, "Nobody, No"))
    d3 = rec((1, "D3"), (3, "49AC52F6961843"))
    meets, report = parse_lines([A0, B1, C1, d1, d2, d3, Z0])
    assert len(report.warnings_for(kind=IssueKind.ORPHANED)) == 3


def test_b2_before_b1_ignored() -> None:
    b2 = rec((1, "B2"), (3, "1"), (12, "Host"))
    meets, report = parse_lines([A0, b2, B1, C1, d0(), Z0])
    assert meets[0].host is None  # B2 before the meet is dropped silently


def test_c2_before_club_ignored() -> None:
    c2 = rec((1, "C2"), (3, "1"), (12, "PCSCSC"), (18, "Coach"))
    meets, _ = parse_lines([A0, B1, c2, C1, d0(), Z0])
    assert meets[0].clubs[0].coach is None  # C2 with no current club ignored


def test_blank_lines_ignored() -> None:
    meets, _ = parse_lines([A0, B1, "", "   ", C1, d0(), Z0])
    assert len(meets[0].swimmers) == 1


# -- standards error paths --------------------------------------------------- #


def test_standards_missing_file_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(standards_mod, "_DATA_FILE", "does-not-exist.json")
    standards_mod._load_index.cache_clear()
    with pytest.raises(StandardsError):
        standards_mod._load_index()
    standards_mod._load_index.cache_clear()


def test_standards_duplicate_rows_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    dup = {
        "standards": [
            {
                "standard": "B",
                "age_group": "10_U",
                "sex": "F",
                "event": "FREE_50_SCY",
                "cutoff_centiseconds": 1,
            },
            {
                "standard": "B",
                "age_group": "10_U",
                "sex": "F",
                "event": "FREE_50_SCY",
                "cutoff_centiseconds": 2,
            },
        ]
    }
    monkeypatch.setattr("tunas.standards.json.loads", lambda *_a, **_k: dup)
    standards_mod._load_index.cache_clear()
    with pytest.raises(StandardsError):
        standards_mod._load_index()
    standards_mod._load_index.cache_clear()


def test_standards_age_buckets() -> None:
    from tunas import Sex, TimeStandard, standard_time

    cuts = {
        age: standard_time(TimeStandard.B, Event.FREE_50_SCY, age=age, sex=Sex.MALE)
        for age in (10, 12, 14, 16, 18)
    }
    assert all(c is not None for c in cuts.values())


# -- more field/handler branches --------------------------------------------- #


def test_d0_unknown_stroke_skipped_not_fatal() -> None:
    # An unknown STROKE code (e.g. diving event "H") makes the event unresolvable:
    # skip the record in lenient mode, raise in strict — never abort the file.
    from tunas import ParseError

    line = d0(stroke="H")
    meets, report = parse_lines([A0, B1, C1, line, Z0])
    assert meets[0].individual_swims == []
    assert meets[0].swimmers == []
    assert report.warnings_for(record_type="D0", severity=Severity.SKIPPED)
    with pytest.raises(ParseError):
        parse_lines([A0, B1, C1, line, Z0], strict=True)


def test_d0_malformed_distance_skipped_not_fatal() -> None:
    line = d0(dist="12X")
    meets, report = parse_lines([A0, B1, C1, line, Z0])
    assert meets[0].individual_swims == []
    assert report.warnings_for(record_type="D0", severity=Severity.SKIPPED)


def test_d0_partial_event_fields_skipped() -> None:
    # esex blank but distance/stroke present -> unresolvable -> skipped (not fatal).
    line = d0(esex="", dist="100", stroke="1", eage="1314")
    meets, report = parse_lines([A0, B1, C1, line, Z0])
    assert meets[0].individual_swims == []
    assert report.warnings_for(record_type="D0", severity=Severity.SKIPPED)


def test_d0_unknown_citizenship_recovered() -> None:
    line = d0()
    line = line[:52] + "ZZZ" + line[55:]  # citizenship 53/3 = "ZZZ"
    meets, report = parse_lines([A0, B1, C1, line, Z0])
    assert meets[0].swimmers[0].citizenship is None
    assert report.warnings_for(field="citizenship", kind=IssueKind.UNKNOWN_CODE)


def test_d0_citizenship_country_and_dual() -> None:
    from tunas import Citizenship, Country

    line_country = d0()
    line_country = line_country[:52] + "CAN" + line_country[55:]
    meets, _ = parse_lines([A0, B1, C1, line_country, Z0])
    assert meets[0].swimmers[0].citizenship is Country.CANADA
    line_dual = d0()
    line_dual = line_dual[:52] + "2AL" + line_dual[55:]
    meets, _ = parse_lines([A0, B1, C1, line_dual, Z0])
    assert meets[0].swimmers[0].citizenship is Citizenship.DUAL


def test_d0_malformed_finals_time_recovered_no_result() -> None:
    meets, report = parse_lines([A0, B1, C1, d0(finals="9:9X.zz"), Z0])
    # malformed time -> no result for that session, RECOVERED warning
    assert meets[0].individual_swims == []
    assert report.warnings_for(field="finals_time", kind=IssueKind.MALFORMED)


def test_g0_bad_sequence_is_fatal() -> None:
    from conftest import g0

    from tunas import ParseError

    bad = g0(seq="")  # missing M1 sequence number
    with pytest.raises(ParseError):
        parse_lines([A0, B1, C1, d0(), bad, Z0])


def test_e0_unresolvable_relay_event_skipped() -> None:
    from conftest import e0, f0

    # 25 medley relay does not exist -> SKIPPED, F0 then orphaned
    bad_e0 = e0(dist="25", stroke="7")
    meets, report = parse_lines([A0, B1, C1, bad_e0, f0(), Z0])
    assert meets[0].relays == []
    assert report.warnings_for(record_type="E0", severity=Severity.SKIPPED)
