"""The M1/M2 + lose-no-information contract."""

from __future__ import annotations

import pytest
from conftest import A0, B1, C1, Z0, d0, g0, parse_lines, rec

from tunas import IssueKind, ParseError, ResultStatus, Severity

# -- M1: fatal in both modes ------------------------------------------------- #


@pytest.mark.parametrize(
    "lines",
    [
        [A0, B1, C1, d0(name=""), Z0],
        [A0, B1, C1, d0(sex=""), Z0],
        [A0, rec((1, "B1"), (3, "1"), (122, "01012025")), C1, d0(), Z0],  # no meet name
        [A0, rec((1, "B1"), (3, "1"), (12, "Meet")), C1, d0(), Z0],  # no start date
    ],
)
def test_m1_raises_in_lenient_mode(lines: list[str]) -> None:
    with pytest.raises(ParseError) as exc:
        parse_lines(lines)
    assert exc.value.warning.severity is Severity.FATAL


def test_partial_event_fields_skipped_not_fatal() -> None:
    # Data quality, not structural corruption: skipped leniently, raises only under strict.
    line = d0(esex="", dist="100", stroke="1", eage="1314")
    archive = parse_lines([A0, B1, C1, line, Z0])
    assert archive.meets[0].individual_swims == []
    assert archive.report.warnings_for(record_type="D0", severity=Severity.SKIPPED)
    with pytest.raises(ParseError):
        parse_lines([A0, B1, C1, line, Z0], strict=True)


# -- Other M2: keep + null + RECOVERED --------------------------------------- #


def test_m2_blank_city_kept() -> None:
    b1 = rec(
        (1, "B1"), (3, "1"), (12, "Meet"), (106, "CA"), (121, "1"), (122, "01012025"), (150, "2")
    )  # no city
    archive = parse_lines([A0, b1, C1, d0(), Z0])
    assert archive.meets[0].city is None
    assert archive.report.warnings_for(record_type="B1", field="city", severity=Severity.RECOVERED)


# -- Unresolvable event: skip (lenient) / raise (strict) --------------------- #


def test_unresolvable_event() -> None:
    line = d0(dist="25", stroke="3", finals="30.00", finals_course="L", seed="", seed_course="")
    archive = parse_lines([A0, B1, C1, line, Z0])
    assert archive.meets[0].individual_swims == []
    assert archive.report.warnings_for(record_type="D0", severity=Severity.SKIPPED)
    with pytest.raises(ParseError):
        parse_lines([A0, B1, C1, line, Z0], strict=True)


# -- Result outcomes --------------------------------------------------------- #


@pytest.mark.parametrize("code", ["NT", "NS", "DNF", "DQ", "SCR"])
def test_outcome_codes_kept_no_warning(code: str) -> None:
    archive = parse_lines([A0, B1, C1, d0(finals=code), Z0])
    res = archive.meets[0].swimmers[0].individual_swims[0]
    assert res.status is ResultStatus[code]
    assert res.time is None
    assert not archive.report.warnings_for(record_type="D0", field="finals_time")


# -- Conditionals ------------------------------------------------------------ #


def test_conditional_starstar_no_raise_at_championship() -> None:
    # MEET type 6 (national championship); finals place blank -> warn, no raise.
    champ_b1 = rec(
        (1, "B1"),
        (3, "1"),
        (12, "Champs"),
        (86, "City"),
        (106, "CA"),
        (121, "6"),
        (122, "01012025"),
        (150, "2"),
    )
    archive = parse_lines([A0, champ_b1, C1, d0(finals_place=""), Z0])
    assert len(archive.meets[0].individual_swims) == 1  # not raised
    assert [w for w in archive.report.warnings if w.mandatory == "**"]


def test_conditional_hash_relay_only() -> None:
    line = d0(
        esex="",
        dist="",
        stroke="",
        eage="",
        finals="",
        seed="",
        seed_course="",
        finals_course="",
        finals_place="",
    )
    archive = parse_lines([A0, B1, C1, line, Z0])
    assert len(archive.meets[0].swimmers) == 1
    assert archive.meets[0].individual_swims == []


# -- Lines and unknown records ----------------------------------------------- #


def test_short_line_padded_and_parsed() -> None:
    archive = parse_lines([A0, B1, C1, d0()[:130], Z0])
    assert len(archive.meets[0].swimmers) == 1


def test_unknown_code_field() -> None:
    # Unknown ATTACH code on D0 (52/1): recovered, record kept.
    line = d0()
    line = line[:51] + "Z" + line[52:]
    archive = parse_lines([A0, B1, C1, line, Z0])
    assert len(archive.meets[0].swimmers) == 1
    assert archive.report.warnings_for(kind=IssueKind.UNKNOWN_CODE)


# -- Orphans ----------------------------------------------------------------- #


def test_orphan_g0_without_swim() -> None:
    archive = parse_lines([A0, B1, C1, g0(), Z0])
    assert archive.report.warnings_for(record_type="G0", kind=IssueKind.ORPHANED)


# -- Strict mode escalation -------------------------------------------------- #


def test_strict_escalates_unknown_record() -> None:
    j0 = rec((1, "J0"), (12, "x"))
    with pytest.raises(ParseError):
        parse_lines([A0, B1, j0, C1, d0(), Z0], strict=True)


# -- ParseWarning shape ------------------------------------------------------ #


def test_parse_warning_shape() -> None:
    archive = parse_lines([A0, B1, C1, d0(birth=""), Z0])
    w = archive.report.warnings_for(record_type="D0", field="birthday")[0]
    assert w.source == "<stream>"
    assert w.line_no > 0
    assert w.column == "56/8"
    assert w.mandatory == "M2"
    assert w.severity is Severity.RECOVERED
    assert isinstance(w.raw_line, str)


def test_report_by_severity_and_filters() -> None:
    archive = parse_lines([A0, B1, C1, d0(esex=""), d0(birth=""), Z0])
    by_sev = archive.report.by_severity
    assert by_sev[Severity.SKIPPED]
    assert by_sev[Severity.RECOVERED]
    assert archive.report.warnings_for(severity=Severity.SKIPPED)
    assert archive.report.has_warnings
