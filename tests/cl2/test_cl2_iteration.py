"""The lazy archive iterator: one archive per source, deterministic order, per-file reports."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from conftest import A0, B1, C1, DATA_DIR, Z0, d0, rec

from tunas import ParseError, ParseReport, read_cl2

_GOLDEN = [str(DATA_DIR / "reno_walk_on_meet.cl2"), str(DATA_DIR / "aaa_league_championship.cl2")]


def _single_meet_text(name: str = "Winter Champs") -> str:
    b1 = rec((1, "B1"), (3, "1"), (12, name), (122, "01012025")) if name != "Winter Champs" else B1
    return "\n".join([A0, b1, C1, d0(), Z0]) + "\n"


def _write_files(directory: Path, contents: dict[str, str]) -> list[Path]:
    for name, text in contents.items():
        (directory / name).write_text(text)
    return [directory / name for name in contents]


def test_golden_files_yield_one_archive_each() -> None:
    archives = list(read_cl2(_GOLDEN))
    assert len(archives) == 2
    assert sum(a.report.meets_parsed for a in archives) >= 2


def test_directory_yields_in_sorted_order(tmp_path: Path) -> None:
    letters = "abcdefgh"
    contents = {f"{c}.cl2": _single_meet_text(f"Meet {c}") for c in letters}
    _write_files(tmp_path, contents)
    archives = list(read_cl2(str(tmp_path)))
    assert [a.meets[0].name for a in archives] == [f"Meet {c}" for c in letters]
    assert [Path(a.source).name for a in archives] == [f"{c}.cl2" for c in letters]


def test_iterable_preserves_given_order(tmp_path: Path) -> None:
    contents = {f"{c}.cl2": _single_meet_text(f"Meet {c}") for c in "abcd"}
    paths = _write_files(tmp_path, contents)
    archives = list(read_cl2(list(reversed(paths))))
    assert [a.meets[0].name for a in archives] == ["Meet d", "Meet c", "Meet b", "Meet a"]


def test_iteration_is_lazy_per_file(tmp_path: Path) -> None:
    (good,) = _write_files(tmp_path, {"good.cl2": _single_meet_text()})
    it = read_cl2([good, tmp_path / "missing.cl2"])
    assert len(next(it).meets) == 1
    with pytest.raises(FileNotFoundError):
        next(it)


def test_stream_is_single_archive() -> None:
    archives = list(read_cl2(io.StringIO(_single_meet_text())))
    assert len(archives) == 1
    assert len(archives[0].meets) == 1 and archives[0].report.files_read == 1


def test_strict_raises_on_recovered_warning(tmp_path: Path) -> None:
    good = _single_meet_text()
    bad = "\n".join([A0, B1, C1, d0(birth=""), Z0]) + "\n"
    paths = _write_files(tmp_path, {"good.cl2": good, "bad.cl2": bad})
    archives = list(read_cl2(paths))
    assert len(archives) == 2 and any(a.report.has_warnings for a in archives)
    with pytest.raises(ParseError):
        list(read_cl2(paths, strict=True))


def test_each_archive_reports_only_its_own_file(tmp_path: Path) -> None:
    contents = {f"m{i}.cl2": _single_meet_text(f"Meet {i}") for i in range(10)}
    _write_files(tmp_path, contents)
    archives = list(read_cl2(str(tmp_path)))
    assert len(archives) == 10
    for a in archives:
        assert a.report.files_read == 1
        assert a.report.meets_parsed == 1
        assert a.report.swimmers_parsed == 1
        assert a.report.individual_swims_parsed == 1


def test_report_merge_method() -> None:
    a = ParseReport(files_read=1, meets_parsed=2, swimmers_parsed=3)
    b = ParseReport(files_read=1, meets_parsed=5, swimmers_parsed=7)
    a.merge(b)
    assert (a.files_read, a.meets_parsed, a.swimmers_parsed) == (2, 7, 10)
    assert (b.files_read, b.meets_parsed, b.swimmers_parsed) == (1, 5, 7)
