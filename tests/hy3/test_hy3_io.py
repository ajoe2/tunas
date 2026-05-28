"""Source handling for ``read_hy3``: paths, directory walk, streams, and parallelism."""

from __future__ import annotations

import io
import os

import pytest
from conftest import A1, B1_HY3, B2_HY3, C1_HY3, d1, e1, e2

from tunas import read_hy3


def _single_meet_text() -> str:
    return "\n".join([A1, B1_HY3, B2_HY3, C1_HY3, d1(), e1(), e2()]) + "\n"


def test_return_shape() -> None:
    archive = next(iter(read_hy3(io.StringIO(_single_meet_text()))))
    report = archive.report
    assert isinstance(archive.meets, list)
    assert len(archive.meets) == report.meets_parsed == 1
    assert report.files_read == 1
    assert report.swimmers_parsed == 1
    assert report.individual_swims_parsed == 1


def test_stream_yields_single_archive() -> None:
    archives = list(read_hy3(io.StringIO(_single_meet_text())))
    assert len(archives) == 1
    assert archives[0].source == "<stream>"
    assert len(archives[0].meets) == 1
    assert archives[0].report.files_read == 1


def test_file_path(tmp_path: object) -> None:
    p = os.path.join(str(tmp_path), "meet.hy3")
    with open(p, "w") as fh:
        fh.write(_single_meet_text())
    archive = next(iter(read_hy3(p)))
    assert len(archive.meets) == 1
    assert archive.report.files_read == 1


def test_directory_walk(tmp_path: object) -> None:
    d = str(tmp_path)
    for name in ("a.hy3", "b.HY3", "ignore.cl2"):
        with open(os.path.join(d, name), "w") as fh:
            fh.write(_single_meet_text() if name.lower().endswith(".hy3") else "junk")
    archives = list(read_hy3(d))
    assert len(archives) == 2  # only the two .hy3 files (case-insensitive)
    assert sum(len(a.meets) for a in archives) == 2


def test_archive_per_file(tmp_path: object) -> None:
    # A directory of N files yields N archives, each tagged with its own source path.
    d = str(tmp_path)
    names = ("a.hy3", "b.hy3", "c.hy3")
    for name in names:
        with open(os.path.join(d, name), "w") as fh:
            fh.write(_single_meet_text())
    archives = list(read_hy3(d))
    assert [os.path.basename(a.source) for a in archives] == list(names)
    assert all(a.report.files_read == 1 and len(a.meets) == 1 for a in archives)


def test_iterable_of_paths(tmp_path: object) -> None:
    paths = []
    for name in ("one.hy3", "two.hy3"):
        p = os.path.join(str(tmp_path), name)
        with open(p, "w") as fh:
            fh.write(_single_meet_text())
        paths.append(p)
    archives = list(read_hy3(paths))
    assert sum(len(a.meets) for a in archives) == 2


def test_file_like_stream() -> None:
    archive = next(iter(read_hy3(io.StringIO(_single_meet_text()))))
    assert len(archive.meets) == 1


def test_binary_stream_raises() -> None:
    with pytest.raises(TypeError):
        list(read_hy3(io.BytesIO(b"A107 stuff")))  # type: ignore[arg-type]


def test_directory_yields_one_archive_per_file_in_order(tmp_path: object) -> None:
    d = str(tmp_path)
    for i in range(6):
        with open(os.path.join(d, f"m{i}.hy3"), "w") as fh:
            fh.write(_single_meet_text())
    archives = list(read_hy3(d))
    assert len(archives) == 6
    assert sum(a.report.meets_parsed for a in archives) == 6
    # rglob sorts, so archives arrive in sorted-filename order
    assert [os.path.basename(a.source) for a in archives] == [f"m{i}.hy3" for i in range(6)]


def test_multi_file_no_merge(tmp_path: object) -> None:
    paths = []
    for name in ("a.hy3", "b.hy3"):
        p = os.path.join(str(tmp_path), name)
        with open(p, "w") as fh:
            fh.write(_single_meet_text())
        paths.append(p)
    a, b = read_hy3(paths)  # one archive per file, in order
    # Same athlete id, but two distinct Swimmer objects (no cross-file merge).
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
