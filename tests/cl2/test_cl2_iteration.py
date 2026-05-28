"""The lazy archive iterator: one archive per source, deterministic order, per-file reports.

``read_cl2`` parses a corpus one file at a time as the iterator is consumed, yielding
exactly one :class:`MeetArchive` per file/stream in source order, each carrying only its
own meets and diagnostics.
"""

from __future__ import annotations

import io
import os
from pathlib import Path

import pytest
from conftest import A0, B1, C1, DATA_DIR, Z0, d0, rec

from tunas import ParseError, ParseReport, read_cl2

_GOLDEN = [str(DATA_DIR / "reno_walk_on_meet.cl2"), str(DATA_DIR / "aaa_league_championship.cl2")]


def _single_meet_text(name: str = "Winter Champs") -> str:
    b1 = rec((1, "B1"), (3, "1"), (12, name), (122, "01012025")) if name != "Winter Champs" else B1
    return "\n".join([A0, b1, C1, d0(), Z0]) + "\n"


def _write_files(directory: str, contents: dict[str, str]) -> list[str]:
    paths = []
    for name, text in contents.items():
        p = os.path.join(directory, name)
        with open(p, "w") as fh:
            fh.write(text)
        paths.append(p)
    return paths


# --- one archive per source ------------------------------------------------- #


def test_golden_files_yield_one_archive_each() -> None:
    """The real meet files (one relay-heavy, one not) each parse into one archive."""
    archives = list(read_cl2(_GOLDEN))
    assert len(archives) == 2  # one per file
    assert sum(a.report.meets_parsed for a in archives) >= 2


def test_directory_yields_one_archive_per_file(tmp_path: Path) -> None:
    contents = {f"meet_{i:02d}.cl2": _single_meet_text(f"Meet {i:02d}") for i in range(12)}
    _write_files(str(tmp_path), contents)
    archives = list(read_cl2(str(tmp_path)))
    assert len(archives) == 12


# --- deterministic source order --------------------------------------------- #


def test_directory_yields_in_sorted_order(tmp_path: Path) -> None:
    letters = "abcdefgh"
    contents = {f"{c}.cl2": _single_meet_text(f"Meet {c}") for c in letters}
    _write_files(str(tmp_path), contents)
    archives = list(read_cl2(str(tmp_path)))
    assert [a.meets[0].name for a in archives] == [f"Meet {c}" for c in letters]
    assert [os.path.basename(a.source) for a in archives] == [f"{c}.cl2" for c in letters]


def test_iterable_preserves_given_order(tmp_path: Path) -> None:
    # An explicit iterable's order (not sorted) is honored exactly.
    contents = {f"{c}.cl2": _single_meet_text(f"Meet {c}") for c in "abcd"}
    paths = _write_files(str(tmp_path), contents)
    archives = list(read_cl2(list(reversed(paths))))
    assert [a.meets[0].name for a in archives] == ["Meet d", "Meet c", "Meet b", "Meet a"]


# --- laziness ---------------------------------------------------------------- #


def test_iteration_is_lazy_per_file(tmp_path: Path) -> None:
    # One file is parsed per ``next``; a later bad path is only touched when reached.
    good = os.path.join(str(tmp_path), "good.cl2")
    with open(good, "w") as fh:
        fh.write(_single_meet_text())
    missing = os.path.join(str(tmp_path), "missing.cl2")
    it = read_cl2([good, missing])
    first = next(it)
    assert len(first.meets) == 1  # good file parsed, missing one not yet opened
    with pytest.raises(FileNotFoundError):
        next(it)  # only now is the missing file opened


# --- stream is a single unit of work ---------------------------------------- #


def test_stream_is_single_archive() -> None:
    archives = list(read_cl2(io.StringIO(_single_meet_text())))
    assert len(archives) == 1
    assert len(archives[0].meets) == 1 and archives[0].report.files_read == 1


# --- strict mode ------------------------------------------------------------- #


def test_strict_raises_on_recovered_warning(tmp_path: Path) -> None:
    good = _single_meet_text()
    bad = "\n".join([A0, B1, C1, d0(birth=""), Z0]) + "\n"  # missing birthday -> M2 warning
    paths = _write_files(str(tmp_path), {"good.cl2": good, "bad.cl2": bad})
    # Lenient: the M2 issue is recovered, both files parse into two archives.
    archives = list(read_cl2(paths))
    assert len(archives) == 2 and any(a.report.has_warnings for a in archives)
    # Strict: the recovered warning escalates to a raised ParseError.
    with pytest.raises(ParseError):
        list(read_cl2(paths, strict=True))


# --- per-file report --------------------------------------------------------- #


def test_each_archive_reports_only_its_own_file(tmp_path: Path) -> None:
    # Each file: 1 meet, 1 swimmer, 1 individual swim. Every archive's report is local.
    contents = {f"m{i}.cl2": _single_meet_text(f"Meet {i}") for i in range(10)}
    _write_files(str(tmp_path), contents)
    archives = list(read_cl2(str(tmp_path)))
    assert len(archives) == 10
    for a in archives:
        assert a.report.files_read == 1
        assert a.report.meets_parsed == 1
        assert a.report.swimmers_parsed == 1
        assert a.report.individual_swims_parsed == 1


def test_report_merge_method() -> None:
    # ParseReport.merge stays available for callers that fold per-file reports together.
    a = ParseReport(files_read=1, meets_parsed=2, swimmers_parsed=3)
    b = ParseReport(files_read=1, meets_parsed=5, swimmers_parsed=7)
    a.merge(b)
    assert (a.files_read, a.meets_parsed, a.swimmers_parsed) == (2, 7, 10)
    # b is left untouched
    assert (b.files_read, b.meets_parsed, b.swimmers_parsed) == (1, 5, 7)
