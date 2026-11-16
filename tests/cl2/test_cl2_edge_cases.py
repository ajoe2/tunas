"""Targeted tests for defensive branches and orphan handling."""

from __future__ import annotations

import pytest
from conftest import A0, B1, C1, Z0, d0, e0, f0, parse_lines, rec

from tunas import (
    Citizenship,
    Country,
    Event,
    IssueKind,
    ParseError,
    Severity,
    Sex,
    StandardsError,
    Time,
    TimeStandard,
    standard_time,
)
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


@pytest.mark.parametrize(
    "raw,parsed",
    [
        ("Madonna", ("Madonna", "", None)),
        ("Smith,", ("Smith", "", None)),
        ("Smith, John Q", ("Smith", "John", "Q")),  # single-letter trailing token = initial
        ("Smith, John Q.", ("Smith", "John", "Q")),
        # A whole-word trailing token belongs to a compound first name.
        ("Zhou, Melissa Hanlin", ("Zhou", "Melissa Hanlin", None)),
        ("Lam, Lok Yiu", ("Lam", "Lok Yiu", None)),
        ("Doe, Anne Marie B", ("Doe", "Anne Marie", "B")),
    ],
)
def test_parse_name(raw: str, parsed: tuple[str, str, str | None]) -> None:
    assert parse_name(raw) == parsed


def test_d0_name_without_comma() -> None:
    archive = parse_lines([A0, B1, C1, d0(name="Madonna"), Z0])
    sw = archive.meets[0].swimmers[0]
    assert sw.last_name == "Madonna"
    assert sw.first_name == ""


# -- orphan / no-context branches -------------------------------------------- #


def test_d0_before_b1_is_orphan() -> None:
    archive = parse_lines([A0, d0(), Z0])
    assert archive.meets == []
    assert archive.report.warnings_for(record_type="D0", kind=IssueKind.ORPHANED)


def test_e0_before_b1_is_orphan() -> None:
    archive = parse_lines([A0, e0(), Z0])
    assert archive.report.warnings_for(record_type="E0", kind=IssueKind.ORPHANED)


def test_b2_before_b1_ignored() -> None:
    b2 = rec((1, "B2"), (3, "1"), (12, "Host"))
    archive = parse_lines([A0, b2, B1, C1, d0(), Z0])
    assert archive.meets[0].host is None


def test_c2_before_club_ignored() -> None:
    c2 = rec((1, "C2"), (3, "1"), (12, "PCSCSC"), (18, "Coach"))
    archive = parse_lines([A0, B1, c2, C1, d0(), Z0])
    assert archive.meets[0].clubs[0].coach is None


def test_blank_lines_ignored() -> None:
    archive = parse_lines([A0, B1, "", "   ", C1, d0(), Z0])
    assert len(archive.meets[0].swimmers) == 1


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
    cuts = {
        age: standard_time(TimeStandard.B, Event.FREE_50_SCY, age=age, sex=Sex.MALE)
        for age in (10, 12, 14, 16, 18)
    }
    assert all(c is not None for c in cuts.values())


# -- more field/handler branches --------------------------------------------- #


def test_d0_unknown_stroke_skipped_not_fatal() -> None:
    # An unknown STROKE code (e.g. diving "H") makes the event unresolvable.
    line = d0(stroke="H")
    archive = parse_lines([A0, B1, C1, line, Z0])
    assert archive.meets[0].individual_swims == []
    assert archive.meets[0].swimmers == []
    assert archive.report.warnings_for(record_type="D0", severity=Severity.SKIPPED)
    with pytest.raises(ParseError):
        parse_lines([A0, B1, C1, line, Z0], strict=True)


def test_d0_malformed_distance_skipped_not_fatal() -> None:
    line = d0(dist="12X")
    archive = parse_lines([A0, B1, C1, line, Z0])
    assert archive.meets[0].individual_swims == []
    assert archive.report.warnings_for(record_type="D0", severity=Severity.SKIPPED)


def test_d0_unknown_citizenship_recovered() -> None:
    line = d0()
    line = line[:52] + "ZZZ" + line[55:]  # citizenship 53/3 = "ZZZ"
    archive = parse_lines([A0, B1, C1, line, Z0])
    assert archive.meets[0].swimmers[0].citizenship is None
    assert archive.report.warnings_for(field="citizenship", kind=IssueKind.UNKNOWN_CODE)


@pytest.mark.parametrize("code,value", [("CAN", Country.CANADA), ("2AL", Citizenship.DUAL)])
def test_d0_citizenship_country_and_dual(code: str, value: object) -> None:
    line = d0()
    archive = parse_lines([A0, B1, C1, line[:52] + code + line[55:], Z0])
    assert archive.meets[0].swimmers[0].citizenship is value


def test_d0_malformed_finals_time_recovered_no_result() -> None:
    archive = parse_lines([A0, B1, C1, d0(finals="9:9X.zz"), Z0])
    assert archive.meets[0].individual_swims == []
    assert archive.report.warnings_for(field="finals_time", kind=IssueKind.MALFORMED)


def test_e0_unresolvable_relay_event_skipped() -> None:
    # No 25 medley relay exists.
    bad_e0 = e0(dist="25", stroke="7")
    archive = parse_lines([A0, B1, C1, bad_e0, f0(), Z0])
    assert archive.meets[0].relays == []
    assert archive.report.warnings_for(record_type="E0", severity=Severity.SKIPPED)
