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
    meets, report = read_hy3(io.StringIO(_single_meet_text()))
    assert isinstance(meets, list)
    assert len(meets) == report.meets_parsed == 1
    assert report.files_read == 1
    assert report.swimmers_parsed == 1
    assert report.individual_swims_parsed == 1


def test_file_path(tmp_path: object) -> None:
    p = os.path.join(str(tmp_path), "meet.hy3")
    with open(p, "w") as fh:
        fh.write(_single_meet_text())
    meets, report = read_hy3(p)
    assert len(meets) == 1
    assert report.files_read == 1


def test_directory_walk(tmp_path: object) -> None:
    d = str(tmp_path)
    for name in ("a.hy3", "b.HY3", "ignore.cl2"):
        with open(os.path.join(d, name), "w") as fh:
            fh.write(_single_meet_text() if name.lower().endswith(".hy3") else "junk")
    meets, report = read_hy3(d)
    assert len(meets) == 2  # only the two .hy3 files (case-insensitive)
    assert report.files_read == 2


def test_iterable_of_paths(tmp_path: object) -> None:
    paths = []
    for name in ("one.hy3", "two.hy3"):
        p = os.path.join(str(tmp_path), name)
        with open(p, "w") as fh:
            fh.write(_single_meet_text())
        paths.append(p)
    meets, _ = read_hy3(paths)
    assert len(meets) == 2


def test_file_like_stream() -> None:
    meets, _ = read_hy3(io.StringIO(_single_meet_text()))
    assert len(meets) == 1


def test_binary_stream_raises() -> None:
    with pytest.raises(TypeError):
        read_hy3(io.BytesIO(b"A107 stuff"))  # type: ignore[arg-type]


def test_bad_max_workers() -> None:
    with pytest.raises(ValueError):
        read_hy3(io.StringIO(_single_meet_text()), max_workers=0)


def test_parallel_matches_sequential(tmp_path: object) -> None:
    d = str(tmp_path)
    for i in range(6):
        with open(os.path.join(d, f"m{i}.hy3"), "w") as fh:
            fh.write(_single_meet_text())
    seq_meets, seq_report = read_hy3(d, max_workers=1)
    par_meets, par_report = read_hy3(d, max_workers=4)
    assert len(seq_meets) == len(par_meets) == 6
    assert seq_report.meets_parsed == par_report.meets_parsed == 6
    assert [m.name for m in seq_meets] == [m.name for m in par_meets]


def test_multi_file_no_merge(tmp_path: object) -> None:
    paths = []
    for name in ("a.hy3", "b.hy3"):
        p = os.path.join(str(tmp_path), name)
        with open(p, "w") as fh:
            fh.write(_single_meet_text())
        paths.append(p)
    meets, _ = read_hy3(paths)
    assert len(meets) == 2
    # Same athlete id, but two distinct Swimmer objects (no cross-file merge).
    assert meets[0].swimmers[0].id_short == meets[1].swimmers[0].id_short
    assert meets[0].swimmers[0] is not meets[1].swimmers[0]


def test_per_meet_scope_two_b1_blocks() -> None:
    text = "\n".join(
        [A1, B1_HY3, B2_HY3, C1_HY3, d1(), e1(), e2(), B1_HY3, B2_HY3, C1_HY3, d1(), e1(), e2()]
    )
    meets, _ = read_hy3(io.StringIO(text + "\n"))
    assert len(meets) == 2
    assert meets[0].swimmers[0].meet is meets[0]
    assert meets[1].swimmers[0].meet is meets[1]
    assert meets[0].swimmers[0] is not meets[1].swimmers[0]
