"""Multithreaded parsing (``read_cl2(..., max_workers=N)``).

The contract: a parallel parse must be *identical* to the sequential default —
same meets, same order, same report — regardless of thread scheduling. Threads
only change how the work is dispatched, never the result.
"""

from __future__ import annotations

import inspect
import io
import os
from pathlib import Path
from typing import Any

import pytest
from conftest import A0, B1, C1, Z0, d0, rec

from tunas import ParseError, ParseReport, read_cl2

_DATA = Path(__file__).parent / "data"
_GOLDEN = [str(_DATA / "reno_walk_on_meet.cl2"), str(_DATA / "aaa_league_championship.cl2")]


def _single_meet_text(name: str = "Winter Champs") -> str:
    b1 = rec((1, "B1"), (3, "1"), (12, name), (122, "01012025")) if name != "Winter Champs" else B1
    return "\n".join([A0, b1, C1, d0(), Z0]) + "\n"


def _summary(meets: list[Any], report: ParseReport) -> dict[str, Any]:
    """A fully value-based fingerprint of a parse (models use identity equality)."""
    return {
        "meet_names": [m.name for m in meets],
        "swimmers_per_meet": [len(m.swimmers) for m in meets],
        "results_per_meet": [len(m.results) for m in meets],
        "splits_per_meet": [sum(len(s.splits) for s in m.individual_swims) for m in meets],
        "counters": (
            report.files_read,
            report.meets_parsed,
            report.swimmers_parsed,
            report.individual_swims_parsed,
            report.relays_parsed,
            report.splits_parsed,
            report.records_skipped,
            report.fields_recovered,
        ),
        "warnings": report.warnings,  # ParseWarning is a frozen, value-equal dataclass
    }


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
    seq_meets, seq_report = read_cl2(_GOLDEN, max_workers=1)
    par_meets, par_report = read_cl2(_GOLDEN, max_workers=4)
    assert _summary(par_meets, par_report) == _summary(seq_meets, seq_report)
    # sanity: this fixture actually exercises both files and produces real data
    assert seq_report.files_read == 2
    assert seq_report.meets_parsed >= 2


def test_parallel_matches_sequential_on_directory(tmp_path: Path) -> None:
    contents = {f"meet_{i:02d}.cl2": _single_meet_text(f"Meet {i:02d}") for i in range(12)}
    _write_files(str(tmp_path), contents)
    seq = read_cl2(str(tmp_path), max_workers=1)
    par = read_cl2(str(tmp_path), max_workers=6)
    assert _summary(*par) == _summary(*seq)
    assert seq[1].files_read == 12


# --- determinism: order independent of scheduling --------------------------- #


def test_parallel_preserves_source_order(tmp_path: Path) -> None:
    # Distinct meet name per file; sorted filenames => sorted meet names.
    letters = "abcdefgh"
    contents = {f"{c}.cl2": _single_meet_text(f"Meet {c}") for c in letters}
    _write_files(str(tmp_path), contents)
    expected = [f"Meet {c}" for c in letters]
    # Run several times: a race in the merge would eventually reorder the meets.
    for _ in range(5):
        meets, _report = read_cl2(str(tmp_path), max_workers=8)
        assert [m.name for m in meets] == expected


def test_parallel_iterable_preserves_given_order(tmp_path: Path) -> None:
    # Iterable order (not sorted) must be honored exactly.
    contents = {f"{c}.cl2": _single_meet_text(f"Meet {c}") for c in "abcd"}
    paths = _write_files(str(tmp_path), contents)
    reversed_paths = list(reversed(paths))
    meets, _report = read_cl2(reversed_paths, max_workers=4)
    assert [m.name for m in meets] == ["Meet d", "Meet c", "Meet b", "Meet a"]


# --- argument contract ------------------------------------------------------ #


def test_default_max_workers_is_one() -> None:
    assert inspect.signature(read_cl2).parameters["max_workers"].default == 1


@pytest.mark.parametrize("bad", [0, -1, -4])
def test_invalid_max_workers_raises(bad: int) -> None:
    with pytest.raises(ValueError, match="max_workers"):
        read_cl2([], max_workers=bad)


def test_stream_ignores_max_workers() -> None:
    # A single stream is one unit of work; max_workers must not break it.
    meets, report = read_cl2(io.StringIO(_single_meet_text()), max_workers=8)
    assert len(meets) == 1 and report.files_read == 1


# --- strict mode under threads ---------------------------------------------- #


def test_parallel_strict_still_raises(tmp_path: Path) -> None:
    good = _single_meet_text()
    bad = "\n".join([A0, B1, C1, d0(birth=""), Z0]) + "\n"  # missing birthday -> M2 warning
    paths = _write_files(str(tmp_path), {"good.cl2": good, "bad.cl2": bad})
    # Lenient: the M2 issue is recovered, both files parse.
    meets, report = read_cl2(paths, max_workers=2)
    assert len(meets) == 2 and report.has_warnings
    # Strict: the recovered warning escalates to a raised ParseError even threaded.
    with pytest.raises(ParseError):
        read_cl2(paths, max_workers=2, strict=True)


# --- report merge ----------------------------------------------------------- #


def test_parallel_counts_sum_across_files(tmp_path: Path) -> None:
    # Each file: 1 meet, 1 swimmer, 1 individual swim. Counts must add up exactly.
    contents = {f"m{i}.cl2": _single_meet_text(f"Meet {i}") for i in range(10)}
    _write_files(str(tmp_path), contents)
    _meets, report = read_cl2(str(tmp_path), max_workers=4)
    assert report.files_read == 10
    assert report.meets_parsed == 10
    assert report.swimmers_parsed == 10
    assert report.individual_swims_parsed == 10


def test_report_merge_method() -> None:
    a = ParseReport(files_read=1, meets_parsed=2, swimmers_parsed=3)
    b = ParseReport(files_read=1, meets_parsed=5, swimmers_parsed=7)
    a.merge(b)
    assert (a.files_read, a.meets_parsed, a.swimmers_parsed) == (2, 7, 10)
    # b is left untouched
    assert (b.files_read, b.meets_parsed, b.swimmers_parsed) == (1, 5, 7)
