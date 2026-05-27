"""Threaded parsing (``read_cl2(..., max_workers=N)``) and the lazy archive iterator.

The contract: a threaded parse must be *identical* to the sequential default —
same archives, same order, same per-file reports — regardless of thread
scheduling. ``max_workers`` only changes how the work is dispatched, never the
result. (Under CPython's GIL the workers serialize; the equivalence is what we
can assert portably.)
"""

from __future__ import annotations

import inspect
import io
import os
from pathlib import Path
from typing import Any

import pytest
from conftest import A0, B1, C1, DATA_DIR, Z0, d0, rec

from tunas import MeetArchive, ParseError, ParseReport, read_cl2

_GOLDEN = [str(DATA_DIR / "reno_walk_on_meet.cl2"), str(DATA_DIR / "aaa_league_championship.cl2")]


def _single_meet_text(name: str = "Winter Champs") -> str:
    b1 = rec((1, "B1"), (3, "1"), (12, name), (122, "01012025")) if name != "Winter Champs" else B1
    return "\n".join([A0, b1, C1, d0(), Z0]) + "\n"


def _fingerprint(archives: list[MeetArchive]) -> list[Any]:
    """A fully value-based fingerprint of an archive stream (models use identity equality)."""
    return [
        {
            "source": os.path.basename(a.source),
            "meet_names": [m.name for m in a.meets],
            "swimmers_per_meet": [len(m.swimmers) for m in a.meets],
            "results_per_meet": [len(m.results) for m in a.meets],
            "splits_per_meet": [sum(len(s.splits) for s in m.individual_swims) for m in a.meets],
            "counters": (
                a.report.files_read,
                a.report.meets_parsed,
                a.report.swimmers_parsed,
                a.report.individual_swims_parsed,
                a.report.relays_parsed,
                a.report.splits_parsed,
                a.report.records_skipped,
                a.report.fields_recovered,
            ),
            "warnings": a.report.warnings,  # ParseWarning is a frozen, value-equal dataclass
        }
        for a in archives
    ]


def _write_files(directory: str, contents: dict[str, str]) -> list[str]:
    paths = []
    for name, text in contents.items():
        p = os.path.join(directory, name)
        with open(p, "w") as fh:
            fh.write(text)
        paths.append(p)
    return paths


# --- equivalence: parallel == sequential ----------------------------------- #


def test_parallel_matches_sequential_on_golden_files() -> None:
    """The real meet files (one relay-heavy, one not) parse identically threaded."""
    seq = list(read_cl2(_GOLDEN, max_workers=1))
    par = list(read_cl2(_GOLDEN, max_workers=4))
    assert _fingerprint(par) == _fingerprint(seq)
    # sanity: one archive per file, both exercised and producing real data
    assert len(seq) == 2
    assert sum(a.report.meets_parsed for a in seq) >= 2


def test_parallel_matches_sequential_on_directory(tmp_path: Path) -> None:
    contents = {f"meet_{i:02d}.cl2": _single_meet_text(f"Meet {i:02d}") for i in range(12)}
    _write_files(str(tmp_path), contents)
    seq = list(read_cl2(str(tmp_path), max_workers=1))
    par = list(read_cl2(str(tmp_path), max_workers=6))
    assert _fingerprint(par) == _fingerprint(seq)
    assert len(seq) == 12  # one archive per file


# --- determinism: order independent of scheduling --------------------------- #


def test_parallel_preserves_source_order(tmp_path: Path) -> None:
    # Distinct meet name per file; sorted filenames => sorted archive order.
    letters = "abcdefgh"
    contents = {f"{c}.cl2": _single_meet_text(f"Meet {c}") for c in letters}
    _write_files(str(tmp_path), contents)
    expected = [f"Meet {c}" for c in letters]
    # Run several times: a scheduling race in the look-ahead window would reorder.
    for _ in range(5):
        archives = list(read_cl2(str(tmp_path), max_workers=8))
        assert [a.meets[0].name for a in archives] == expected
        assert [os.path.basename(a.source) for a in archives] == [f"{c}.cl2" for c in letters]


def test_parallel_iterable_preserves_given_order(tmp_path: Path) -> None:
    # Iterable order (not sorted) must be honored exactly.
    contents = {f"{c}.cl2": _single_meet_text(f"Meet {c}") for c in "abcd"}
    paths = _write_files(str(tmp_path), contents)
    reversed_paths = list(reversed(paths))
    archives = list(read_cl2(reversed_paths, max_workers=4))
    assert [a.meets[0].name for a in archives] == ["Meet d", "Meet c", "Meet b", "Meet a"]


# --- laziness ---------------------------------------------------------------- #


def test_iteration_is_lazy_per_file(tmp_path: Path) -> None:
    # Default (max_workers=1) parses one file per ``next``; a later bad path is only
    # touched when the consumer reaches it.
    good = os.path.join(str(tmp_path), "good.cl2")
    with open(good, "w") as fh:
        fh.write(_single_meet_text())
    missing = os.path.join(str(tmp_path), "missing.cl2")
    it = read_cl2([good, missing])
    first = next(it)
    assert len(first.meets) == 1  # good file parsed, missing one not yet opened
    with pytest.raises(FileNotFoundError):
        next(it)  # only now is the missing file opened


# --- argument contract ------------------------------------------------------ #


def test_default_max_workers_is_one() -> None:
    assert inspect.signature(read_cl2).parameters["max_workers"].default == 1


@pytest.mark.parametrize("bad", [0, -1, -4])
def test_invalid_max_workers_raises(bad: int) -> None:
    # Validated eagerly, before the iterator is created.
    with pytest.raises(ValueError, match="max_workers"):
        read_cl2([], max_workers=bad)


def test_stream_is_single_archive_regardless_of_max_workers() -> None:
    # A single stream is one unit of work; max_workers must not split or break it.
    archives = list(read_cl2(io.StringIO(_single_meet_text()), max_workers=8))
    assert len(archives) == 1
    assert len(archives[0].meets) == 1 and archives[0].report.files_read == 1


# --- strict mode under threads ---------------------------------------------- #


def test_parallel_strict_still_raises(tmp_path: Path) -> None:
    good = _single_meet_text()
    bad = "\n".join([A0, B1, C1, d0(birth=""), Z0]) + "\n"  # missing birthday -> M2 warning
    paths = _write_files(str(tmp_path), {"good.cl2": good, "bad.cl2": bad})
    # Lenient: the M2 issue is recovered, both files parse into two archives.
    archives = list(read_cl2(paths, max_workers=2))
    assert len(archives) == 2 and any(a.report.has_warnings for a in archives)
    # Strict: the recovered warning escalates to a raised ParseError even threaded.
    with pytest.raises(ParseError):
        list(read_cl2(paths, max_workers=2, strict=True))


# --- per-file report --------------------------------------------------------- #


def test_each_archive_reports_only_its_own_file(tmp_path: Path) -> None:
    # Each file: 1 meet, 1 swimmer, 1 individual swim. Every archive's report is local.
    contents = {f"m{i}.cl2": _single_meet_text(f"Meet {i}") for i in range(10)}
    _write_files(str(tmp_path), contents)
    archives = list(read_cl2(str(tmp_path), max_workers=4))
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
