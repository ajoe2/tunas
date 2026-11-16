"""Nasty input: lenient ``read_cl2`` recovers or warns; only M1 violations raise ParseError."""

from __future__ import annotations

import contextlib
import io
from pathlib import Path

import pytest
from conftest import A0, B1, C1, Z0, d0, e0, f0, g0, parse_lines, rec

from tunas import IssueKind, ParseError, ResultStatus, read_cl2

# -- Degenerate / empty inputs ---------------------------------------------------


@pytest.mark.parametrize(
    "lines",
    [
        [],
        [""],
        ["   ", "\t", ""],
        [Z0],
        [A0],
        [A0, Z0],
        [Z0, Z0, Z0],
        [B1],  # meet with nothing after
        [C1],  # club with no meet
        [d0()],  # swim with no meet/club
        [g0()],  # splits with nothing
        [f0()],  # relay name with no event
    ],
)
def test_degenerate_inputs_never_crash(lines: list[str]) -> None:
    archive = parse_lines(lines)
    assert isinstance(archive.meets, list)
    assert archive.report.files_read == 1


def test_completely_empty_stream() -> None:
    archive = next(iter(read_cl2(io.StringIO(""))))
    assert archive.meets == []
    assert archive.report.meets_parsed == 0


def test_only_garbage_lines() -> None:
    archive = parse_lines(["garbage", "!!!!", "12345", "??", "\x00\x01\x02"])
    assert archive.meets == []
    assert archive.report.has_warnings


# -- Line-length and line-ending abuse -----------------------------------------


@pytest.mark.parametrize("length", [0, 1, 2, 3, 159, 160, 161, 320, 1000])
def test_arbitrary_line_lengths(length: int) -> None:
    # Garbage "D0..." may hit a fatal M1 (e.g. an invalid sex byte); only ParseError is allowed.
    line = ("D0" + "x" * 1000)[:length]
    with contextlib.suppress(ParseError):
        parse_lines([A0, B1, C1, line, Z0])


@pytest.mark.parametrize("line", ["D0" + "z" * 300, "X" * 200])
def test_overlong_line_warns_bad_length(line: str) -> None:
    report = parse_lines([A0, B1, C1, d0(), line, Z0]).report
    assert report.warnings_for(kind=IssueKind.BAD_LENGTH)


@pytest.mark.parametrize(
    "prefix,sep,end", [("", "\r\n", "\r\n"), ("", "\n", ""), ("\ufeff", "\n", "\n")]
)
def test_line_endings_and_bom(prefix: str, sep: str, end: str) -> None:
    text = prefix + sep.join([A0, B1, C1, d0(), Z0]) + end
    archive = next(iter(read_cl2(io.StringIO(text))))
    assert len(archive.meets) == 1
    assert archive.meets[0].source_file is not None  # A0 recognized despite a BOM


def test_trailing_whitespace_padding() -> None:
    # A short line padded by the parser, plus trailing spaces on a full line.
    archive = parse_lines([A0, B1, C1, d0().rstrip() + "        ", Z0])
    assert len(archive.meets[0].swimmers) == 1


# -- Malformed numeric / coded fields ------------------------------------------


@pytest.mark.parametrize(
    "line",
    [d0(dist=v) for v in ["ABCD", "    ", "12X", "-50", "9999", "0000"]]
    + [
        d0(finals=v)
        for v in ["::", ".", "1:2:3.4", "999999:99.99", "-1.00", "  :  .  ", "abc", "1:.", ":12.34"]
    ]
    + [d0(eage=v) for v in ["UNUN", "OVOV", "ABCD", "9999", "1 12", "U12", "    "]]
    + [d0(name="Bad\x07\x00Name, X")],
)
def test_garbage_fields_never_crash(line: str) -> None:
    assert isinstance(parse_lines([A0, B1, C1, line, Z0]).meets, list)


@pytest.mark.parametrize(
    "birth", ["13012025", "02302025", "00000000", "99999999", "0101", "ABCDEFGH", "        "]
)
def test_garbage_birthdate_kept_as_none(birth: str) -> None:
    archive = parse_lines([A0, B1, C1, d0(birth=birth), Z0])
    assert archive.meets[0].swimmers[0].birthday is None


def test_huge_altitude_truncated_to_field_width() -> None:
    b1 = rec(
        (1, "B1"),
        (3, "1"),
        (12, "M"),
        (86, "C"),
        (106, "CA"),
        (121, "1"),
        (122, "01012025"),
        (138, "99999999"),
        (150, "2"),
    )
    archive = parse_lines([A0, b1, C1, d0(), Z0])
    assert archive.meets[0].altitude == 9999  # only 4 bytes (138/4) are read


def test_negative_place_becomes_none() -> None:
    line = d0(finals_place="")
    line = line[:135] + "-1 " + line[138:]  # finals place 136/3 = "-1"
    archive = parse_lines([A0, B1, C1, line, Z0])
    assert archive.meets[0].individual_swims[0].rank is None


def test_unknown_codes_across_fields_never_crash() -> None:
    line = d0()
    line = line[:51] + "Z" + line[52:]  # ATTACH (52/1) bogus
    line = line[:52] + "ZZZ" + line[55:]  # CITIZEN (53/3) bogus
    archive = parse_lines([A0, B1, C1, line, Z0])
    assert len(archive.meets[0].swimmers) == 1


# -- G0 split arithmetic abuse -------------------------------------------------


def test_g0_sequence_zero_no_negative_distances() -> None:
    gz = g0(seq="0", times=("29.00", "1:00.00"))
    archive = parse_lines([A0, B1, C1, d0(), gz, Z0])
    fin = next(s for s in archive.meets[0].individual_swims if s.splits)
    assert all(sp.distance > 0 for sp in fin.splits)
    assert archive.report.warnings_for(record_type="G0", field="sequence_number")


def test_g0_max_sequence_keeps_positive_distances() -> None:
    g9 = g0(seq="9", split_dist="50", times=tuple(f"{i}.00" for i in range(10, 20)))
    archive = parse_lines([A0, B1, C1, d0(), g9, Z0])
    fin = next(s for s in archive.meets[0].individual_swims if s.splits)
    assert all(sp.distance > 0 for sp in fin.splits)
    assert fin.splits[0].distance == 50 * ((9 - 1) * 10 + 1)


def test_g0_all_blank_splits() -> None:
    gb = g0(times=())
    archive = parse_lines([A0, B1, C1, d0(), gb, Z0])
    assert archive.meets[0].individual_swims[0].splits == []


def test_g0_non_digit_sequence_is_fatal() -> None:
    gb = g0(seq="")  # M1 sequence missing
    with pytest.raises(ParseError):
        parse_lines([A0, B1, C1, d0(), gb, Z0])


def test_g0_bad_split_type_is_fatal() -> None:
    gb = rec(
        (1, "G0"),
        (44, "49AC52F69618"),
        (56, "1"),
        (57, "2"),
        (59, "50"),
        (63, "Z"),
        (64, "29.00"),
        (144, "F"),
    )
    with pytest.raises(ParseError):
        parse_lines([A0, B1, C1, d0(), gb, Z0])


# -- Relay abuse ---------------------------------------------------------------


def test_more_than_four_relay_legs_all_retained() -> None:
    legs = [f0(name=f"S{i}, X", uss=f"ID{i:010d}") for i in range(8)]
    archive = parse_lines([A0, B1, C1, e0(), *legs, Z0])
    # Lose no information: every F0 leg is recorded even past 4.
    assert len(archive.meets[0].relays[0].legs) == 8


def test_relay_all_legs_not_swum() -> None:
    leg = f0(order_prelim="0", order_swimoff="0", order_finals="0")
    archive = parse_lines([A0, B1, C1, e0(), leg, Z0])
    assert archive.meets[0].relays[0].legs == []
    assert archive.meets[0].relays[0].alternates == []


def test_relay_unknown_order_code_skips_leg() -> None:
    leg = f0(order_finals="9")  # not a valid ORDER code (0-4, A)
    archive = parse_lines([A0, B1, C1, e0(), leg, Z0])
    assert archive.meets[0].relays[0].legs == []


def test_f0_before_e0_orphaned() -> None:
    archive = parse_lines([A0, B1, C1, f0(), Z0])
    assert archive.meets[0].relays == []
    assert archive.report.warnings_for(record_type="F0", kind=IssueKind.ORPHANED)


# -- Out-of-order / misplaced records ------------------------------------------


def test_records_before_meet_are_orphans_or_ignored() -> None:
    archive = parse_lines([A0, g0(), f0(), d0(), e0(), B1, C1, d0(), Z0])
    assert len(archive.meets) == 1
    assert len(archive.meets[0].swimmers) == 1  # only the post-B1 D0 counted


def test_d1_d2_d3_before_any_swimmer() -> None:
    d1 = rec((1, "D1"), (3, "1"), (19, "No, One"))
    d2 = rec((1, "D2"), (3, "1"), (19, "No, One"))
    d3 = rec((1, "D3"), (3, "ID000000000001"))
    archive = parse_lines([A0, B1, C1, d1, d2, d3, Z0])
    assert len(archive.report.warnings_for(kind=IssueKind.ORPHANED)) == 3


def test_lowercase_record_header_is_unknown() -> None:
    lower = rec((1, "d0"), (12, "x, y"))
    archive = parse_lines([A0, B1, lower, C1, d0(), Z0])
    assert archive.report.warnings_for(kind=IssueKind.UNKNOWN_RECORD)
    assert len(archive.meets[0].swimmers) == 1


# -- Conflicting / duplicate identity data -------------------------------------


def test_same_id_conflicting_names_first_wins() -> None:
    a = d0(name="Smith, Anna", finals="1:00.00")
    b = d0(name="Jones, Bob", dist="50", finals="28.00")  # same default id
    archive = parse_lines([A0, B1, C1, a, b, Z0])
    assert len(archive.meets[0].swimmers) == 1
    sw = archive.meets[0].swimmers[0]
    assert sw.last_name == "Smith"  # first non-None value wins
    assert len(sw.individual_swims) == 2


def test_same_id_in_two_clubs_groups_once() -> None:
    c1b = rec((1, "C1"), (3, "1"), (12, "PCOTHR"), (18, "Other Club"), (143, "1"))
    archive = parse_lines(
        [A0, B1, C1, d0(finals="1:00.00"), c1b, d0(dist="50", finals="28.00"), Z0]
    )
    # Same id across two club blocks -> grouped into one swimmer (meet-scoped id).
    assert len(archive.meets[0].swimmers) == 1
    assert len(archive.meets[0].clubs) == 2


# -- Unicode / control characters / encoding -----------------------------------


def test_accented_and_unicode_names() -> None:
    archive = parse_lines([A0, B1, C1, d0(name="Núñez, José"), Z0])
    sw = archive.meets[0].swimmers[0]
    assert sw.last_name == "Núñez"
    assert sw.first_name == "José"


def test_binary_stream_rejected() -> None:
    with pytest.raises(TypeError):
        list(read_cl2(io.BytesIO(b"\x00\x01\x02 A0 B1")))  # type: ignore[arg-type]


def test_invalid_utf8_with_replace_errors(tmp_path: Path) -> None:
    p = tmp_path / "bytes.cl2"
    lines = (A0, B1, C1, d0(name="Mu\xf1oz, A"), Z0)
    p.write_bytes(b"".join(line.encode("cp1252") + b"\n" for line in lines))
    archive = next(iter(read_cl2(p, encoding="utf-8", errors="replace")))
    assert len(archive.meets) == 1


# -- Strict mode: anything dirty raises, but only ParseError -------------------


@pytest.mark.parametrize(
    "line",
    [d0(birth=""), d0(uss=""), d0(stroke="H"), d0(finals="1:00.00", finals_course="")],
)
def test_strict_mode_only_raises_parse_error(line: str) -> None:
    with pytest.raises(ParseError):
        parse_lines([A0, B1, C1, line, Z0], strict=True)


# -- Outcome-code abuse in time fields -----------------------------------------


@pytest.mark.parametrize("code", ["nt", "Dq", "scr"])
def test_outcome_codes_case_insensitive(code: str) -> None:
    archive = parse_lines([A0, B1, C1, d0(finals=code), Z0])
    res = archive.meets[0].swimmers[0].individual_swims[0]
    assert res.status is not ResultStatus.OK
    assert res.time is None
