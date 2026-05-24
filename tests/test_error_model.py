"""The M1/M2 + lose-no-information contract — the heart of v1."""

from __future__ import annotations

import pytest
from conftest import A0, B1, C1, Z0, d0, e0, f0, parse_lines, rec

from tunas import IssueKind, ParseError, Severity


def _warning_count(report: object) -> int:
    return len(report.warnings)  # type: ignore[attr-defined]


# -- M1: fatal in both modes ------------------------------------------------- #


@pytest.mark.parametrize(
    "line",
    [
        d0(name=""),  # missing swimmer name
        d0(sex=""),  # missing sex
    ],
)
def test_m1_raises_in_lenient_mode(line: str) -> None:
    with pytest.raises(ParseError) as exc:
        parse_lines([A0, B1, C1, line, Z0])
    assert exc.value.warning.severity is Severity.FATAL


def test_partial_event_fields_skipped_not_fatal() -> None:
    # Partial/odd event fields are a data-quality issue, not structural corruption:
    # the record is skipped in lenient mode and raises only under strict.
    line = d0(esex="", dist="100", stroke="1", eage="1314")
    meets, report = parse_lines([A0, B1, C1, line, Z0])
    assert meets[0].individual_swims == []
    assert report.warnings_for(record_type="D0", severity=Severity.SKIPPED)
    with pytest.raises(ParseError):
        parse_lines([A0, B1, C1, line, Z0], strict=True)


def test_m1_missing_meet_name() -> None:
    bad_b1 = rec((1, "B1"), (3, "1"), (122, "01012025"))  # no name
    with pytest.raises(ParseError):
        parse_lines([A0, bad_b1, C1, d0(), Z0])


def test_m1_missing_meet_start_date() -> None:
    bad_b1 = rec((1, "B1"), (3, "1"), (12, "Meet"))  # no start date
    with pytest.raises(ParseError):
        parse_lines([A0, bad_b1, C1, d0(), Z0])


# -- M2 identity: skip D0, keep F0 ------------------------------------------- #


def test_m2_identity_d0_skipped() -> None:
    meets, report = parse_lines([A0, B1, C1, d0(uss=""), Z0])
    assert meets[0].swimmers == []
    assert report.records_skipped == 1
    w = report.warnings_for(record_type="D0", severity=Severity.SKIPPED)[0]
    assert w.kind is IssueKind.MISSING
    assert w.raw_line.startswith("D0")


def test_m2_identity_f0_keeps_leg() -> None:
    meets, report = parse_lines([A0, B1, C1, e0(), f0(uss="", id_long=""), Z0])
    assert meets[0].relays[0].legs[0].swimmer is None
    assert report.warnings_for(record_type="F0", severity=Severity.RECOVERED)


# -- Other M2: keep + null + RECOVERED --------------------------------------- #


def test_m2_blank_city_kept() -> None:
    b1 = rec(
        (1, "B1"), (3, "1"), (12, "Meet"), (106, "CA"), (121, "1"), (122, "01012025"), (150, "2")
    )  # no city
    meets, report = parse_lines([A0, b1, C1, d0(), Z0])
    assert meets[0].city is None
    assert report.warnings_for(record_type="B1", field="city", severity=Severity.RECOVERED)


def test_m2_blank_birthdate_kept() -> None:
    meets, report = parse_lines([A0, B1, C1, d0(birth=""), Z0])
    assert meets[0].swimmers[0].birthday is None
    assert report.fields_recovered >= 1


# -- Unresolvable event: skip (lenient) / raise (strict) --------------------- #


def test_unresolvable_event_skipped_lenient() -> None:
    line = d0(dist="25", stroke="3", finals="30.00", finals_course="L", seed="", seed_course="")
    meets, report = parse_lines([A0, B1, C1, line, Z0])
    assert meets[0].individual_swims == []
    assert report.warnings_for(record_type="D0", severity=Severity.SKIPPED)


def test_unresolvable_event_raises_strict() -> None:
    line = d0(dist="25", stroke="3", finals="30.00", finals_course="L", seed="", seed_course="")
    with pytest.raises(ParseError):
        parse_lines([A0, B1, C1, line, Z0], strict=True)


# -- Result outcomes --------------------------------------------------------- #


@pytest.mark.parametrize("code", ["NT", "NS", "DNF", "DQ", "SCR"])
def test_outcome_codes_kept_no_warning(code: str) -> None:
    from tunas import ResultStatus

    meets, report = parse_lines([A0, B1, C1, d0(finals=code), Z0])
    res = meets[0].swimmers[0].individual_swims[0]
    assert res.status is ResultStatus[code]
    assert res.time is None
    assert not report.warnings_for(record_type="D0", field="finals_time")


# -- Conditionals ------------------------------------------------------------ #


def test_conditional_star_missing_course() -> None:
    meets, report = parse_lines([A0, B1, C1, d0(finals="1:00.00", finals_course=""), Z0])
    assert len(meets[0].individual_swims) == 1
    assert [w for w in report.warnings if w.mandatory == "*"]


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
    meets, report = parse_lines([A0, champ_b1, C1, d0(finals_place=""), Z0])
    assert len(meets[0].individual_swims) == 1  # not raised
    assert [w for w in report.warnings if w.mandatory == "**"]


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
    meets, _ = parse_lines([A0, B1, C1, line, Z0])
    assert len(meets[0].swimmers) == 1
    assert meets[0].individual_swims == []


# -- Lines and unknown records ----------------------------------------------- #


def test_overlong_line_skipped() -> None:
    meets, report = parse_lines([A0, B1, C1, d0(), "X" * 200, Z0])
    assert report.warnings_for(kind=IssueKind.BAD_LENGTH)


def test_short_line_padded_and_parsed() -> None:
    meets, _ = parse_lines([A0, B1, C1, d0()[:130], Z0])
    assert len(meets[0].swimmers) == 1


def test_unknown_code_field() -> None:
    # Unknown ATTACH code on D0 (52/1) -> RECOVERED UNKNOWN_CODE, record kept.
    line = d0()
    line = line[:51] + "Z" + line[52:]
    meets, report = parse_lines([A0, B1, C1, line, Z0])
    assert len(meets[0].swimmers) == 1
    assert report.warnings_for(kind=IssueKind.UNKNOWN_CODE)


# -- Orphans ----------------------------------------------------------------- #


def test_orphan_f0_without_e0() -> None:
    meets, report = parse_lines([A0, B1, C1, f0(), Z0])
    assert meets[0].relays == []
    assert report.warnings_for(record_type="F0", kind=IssueKind.ORPHANED)


def test_orphan_g0_without_swim() -> None:
    from conftest import g0

    meets, report = parse_lines([A0, B1, C1, g0(), Z0])
    assert report.warnings_for(record_type="G0", kind=IssueKind.ORPHANED)


# -- Strict mode escalation -------------------------------------------------- #


def test_strict_escalates_recovered() -> None:
    with pytest.raises(ParseError):
        parse_lines([A0, B1, C1, d0(birth=""), Z0], strict=True)


def test_strict_escalates_skipped() -> None:
    with pytest.raises(ParseError):
        parse_lines([A0, B1, C1, d0(uss=""), Z0], strict=True)


def test_strict_escalates_unknown_record() -> None:
    j0 = rec((1, "J0"), (12, "x"))
    with pytest.raises(ParseError):
        parse_lines([A0, B1, j0, C1, d0(), Z0], strict=True)


# -- ParseWarning shape ------------------------------------------------------ #


def test_parse_warning_shape() -> None:
    meets, report = parse_lines([A0, B1, C1, d0(birth=""), Z0])
    w = report.warnings_for(record_type="D0", field="birthday")[0]
    assert w.source == "<stream>"
    assert w.line_no > 0
    assert w.column == "56/8"
    assert w.mandatory == "M2"
    assert w.severity is Severity.RECOVERED
    assert isinstance(w.raw_line, str)


def test_report_by_severity_and_filters() -> None:
    meets, report = parse_lines([A0, B1, C1, d0(uss=""), d0(birth=""), Z0])
    by_sev = report.by_severity
    assert by_sev[Severity.SKIPPED]
    assert by_sev[Severity.RECOVERED]
    assert report.warnings_for(severity=Severity.SKIPPED)
    assert report.has_warnings
