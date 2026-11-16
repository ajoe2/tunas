"""Source handling for ``read_hy3``: paths, directory walk, and streams."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from conftest import A1, B1_HY3, B2_HY3, C1_HY3, d1, e1, e2

from tunas import read_hy3


def _single_meet_text() -> str:
    return "\n".join([A1, B1_HY3, B2_HY3, C1_HY3, d1(), e1(), e2()]) + "\n"


def test_stream_yields_single_archive() -> None:
    archives = list(read_hy3(io.StringIO(_single_meet_text())))
    assert len(archives) == 1
    archive = archives[0]
    report = archive.report
    assert archive.source == "<stream>"
    assert len(archive.meets) == report.meets_parsed == 1
    assert report.files_read == 1
    assert report.swimmers_parsed == 1
    assert report.individual_swims_parsed == 1


def test_file_with_a_utf8_bom(tmp_path: Path) -> None:
    # Decoded as CP-1252 (the default), a UTF-8 BOM reads as three extra characters
    # that would push the A1 past the record width.
    p = tmp_path / "meet.hy3"
    p.write_bytes(b"\xef\xbb\xbf" + _single_meet_text().encode("cp1252"))
    archive = next(iter(read_hy3(str(p))))
    assert archive.meets[0].source_file is not None
    without_bom = next(iter(read_hy3(io.StringIO(_single_meet_text()))))
    reasons = [w.reason for w in archive.report.warnings]
    assert reasons == [w.reason for w in without_bom.report.warnings]


def test_directory_walk(tmp_path: Path) -> None:
    for name in ("a.hy3", "b.HY3"):
        (tmp_path / name).write_text(_single_meet_text())
    (tmp_path / "ignore.cl2").write_text("junk")
    archives = list(read_hy3(str(tmp_path)))
    assert [Path(a.source).name for a in archives] == ["a.hy3", "b.HY3"]
    assert all(a.report.files_read == 1 and len(a.meets) == 1 for a in archives)


def test_directory_yields_in_sorted_order(tmp_path: Path) -> None:
    names = [f"m{i}.hy3" for i in range(6)]
    for name in reversed(names):
        (tmp_path / name).write_text(_single_meet_text())
    archives = list(read_hy3(str(tmp_path)))
    assert [Path(a.source).name for a in archives] == names


def test_binary_stream_raises() -> None:
    with pytest.raises(TypeError):
        list(read_hy3(io.BytesIO(b"A107 stuff")))  # type: ignore[arg-type]


def test_multi_file_no_merge(tmp_path: Path) -> None:
    paths = [tmp_path / "a.hy3", tmp_path / "b.hy3"]
    for p in paths:
        p.write_text(_single_meet_text())
    a, b = read_hy3(paths)
    assert a.meets[0].swimmers[0].id_short == b.meets[0].swimmers[0].id_short
    assert a.meets[0].swimmers[0] is not b.meets[0].swimmers[0]


def test_per_meet_scope_two_b1_blocks() -> None:
    text = "\n".join(
        [A1, B1_HY3, B2_HY3, C1_HY3, d1(), e1(), e2(), B1_HY3, B2_HY3, C1_HY3, d1(), e1(), e2()]
    )
    meets = next(iter(read_hy3(io.StringIO(text + "\n")))).meets
    assert len(meets) == 2
    assert meets[0].swimmers[0].meet is meets[0]
    assert meets[1].swimmers[0].meet is meets[1]
    assert meets[0].swimmers[0] is not meets[1].swimmers[0]
