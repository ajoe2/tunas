"""Source handling, per-meet scope, grouping, and report shape."""

from __future__ import annotations

import io
import os

import pytest
from conftest import A0, B1, C1, Z0, d0, e0, f0, g0, parse_lines, rec

from tunas import read_cl2


def _single_meet_text() -> str:
    return "\n".join([A0, B1, C1, d0(), Z0]) + "\n"


def test_return_shape() -> None:
    relay_g0 = g0(times=("26.50",), total="1", session="F")
    archive = parse_lines([A0, B1, C1, d0(), g0(), e0(), f0(), relay_g0, Z0])
    report = archive.report
    assert isinstance(archive.meets, list)
    assert len(archive.meets) == report.meets_parsed == 1
    assert report.files_read == 1
    assert report.swimmers_parsed == 1
    assert report.individual_swims_parsed == 1
    assert report.relays_parsed == 1
    assert report.splits_parsed == 3  # 2 individual + 1 relay leg
    for absent in ("files_skipped", "results_dropped", "reports", "last_report"):
        assert not hasattr(report, absent)


def test_file_path(tmp_path: object) -> None:
    p = os.path.join(str(tmp_path), "meet.cl2")
    with open(p, "w") as fh:
        fh.write(_single_meet_text())
    archive = next(iter(read_cl2(p)))
    assert len(archive.meets) == 1
    assert archive.report.files_read == 1


def test_directory_walk(tmp_path: object) -> None:
    d = str(tmp_path)
    for name in ("a.cl2", "b.CL2", "ignore.txt"):
        with open(os.path.join(d, name), "w") as fh:
            fh.write(_single_meet_text() if name.lower().endswith(".cl2") else "junk")
    archives = list(read_cl2(d))
    assert len(archives) == 2  # one archive per .cl2 file (the .txt is ignored)
    assert sum(len(a.meets) for a in archives) == 2


def test_iterable_of_paths(tmp_path: object) -> None:
    paths = []
    for name in ("one.cl2", "two.cl2"):
        p = os.path.join(str(tmp_path), name)
        with open(p, "w") as fh:
            fh.write(_single_meet_text())
        paths.append(p)
    archives = list(read_cl2(paths))
    assert [os.path.basename(a.source) for a in archives] == ["one.cl2", "two.cl2"]
    assert sum(len(a.meets) for a in archives) == 2


def test_file_like_stream() -> None:
    archive = next(iter(read_cl2(io.StringIO(_single_meet_text()))))
    assert len(archive.meets) == 1
    # warnings (if any) use the stream source label
    archive = next(iter(read_cl2(io.StringIO("\n".join([A0, B1, C1, d0(birth=""), Z0]) + "\n"))))
    assert all(w.source == "<stream>" for w in archive.report.warnings)


def test_binary_stream_raises() -> None:
    with pytest.raises(TypeError):
        list(read_cl2(io.BytesIO(b"A0 stuff")))  # type: ignore[arg-type]  # bytes stream rejected


def test_multi_file_no_merge(tmp_path: object) -> None:
    paths = []
    for name in ("a.cl2", "b.cl2"):
        p = os.path.join(str(tmp_path), name)
        with open(p, "w") as fh:
            fh.write(_single_meet_text())
        paths.append(p)
    a, b = read_cl2(paths)  # one archive per file, in order
    # same id_short, but two distinct Swimmer objects (no cross-file merge)
    assert a.meets[0].swimmers[0].id_short == b.meets[0].swimmers[0].id_short
    assert a.meets[0].swimmers[0] is not b.meets[0].swimmers[0]


def test_per_meet_scope_two_b1_blocks() -> None:
    meets = parse_lines([A0, B1, C1, d0(), Z0, B1, C1, d0(), Z0]).meets
    assert len(meets) == 2
    s0 = set(map(id, meets[0].swimmers))
    s1 = set(map(id, meets[1].swimmers))
    assert s0.isdisjoint(s1)
    assert meets[0].swimmers[0].meet is meets[0]
    assert meets[1].swimmers[0].meet is meets[1]


def test_swimmer_grouping_total_within_meet() -> None:
    # Two D0s sharing an id -> one Swimmer with two individual swims.
    line2 = d0(dist="50", finals="28.00")
    meets = parse_lines([A0, B1, C1, d0(), line2, Z0]).meets
    assert len(meets[0].swimmers) == 1
    sw = meets[0].swimmers[0]
    assert len(sw.individual_swims) == 2
    assert sw.id_short is not None


def test_club_repeated_c1_reuses() -> None:
    meets = parse_lines([A0, B1, C1, d0(), C1, d0(dist="50", finals="28.00"), Z0]).meets
    assert len(meets[0].clubs) == 1


def test_result_status_outcomes_and_dq_rate() -> None:
    from collections import Counter

    from tunas import ResultStatus

    lines = [
        A0,
        B1,
        C1,
        d0(name="A, A", uss="AAAAAAAAAAAA", finals="1:00.00"),
        d0(name="B, B", uss="BBBBBBBBBBBB", finals="DQ"),
        d0(name="C, C", uss="CCCCCCCCCCCC", finals="NS"),
        Z0,
    ]
    meets = parse_lines(lines).meets
    statuses = Counter(r.status for r in meets[0].individual_swims)
    assert statuses[ResultStatus.OK] == 1
    assert statuses[ResultStatus.DQ] == 1
    assert statuses[ResultStatus.NS] == 1
    for r in meets[0].individual_swims:
        assert (r.status is ResultStatus.OK) == (r.time is not None)


def test_capture_everything_full_spec() -> None:
    b2 = rec((1, "B2"), (3, "1"), (12, "Host Club"), (121, "5550001111"))
    c2 = rec((1, "C2"), (3, "1"), (12, "PCSCSC"), (18, "Coach Bob"), (48, "5559999"), (89, "SCSC"))
    d1 = rec(
        (1, "D1"),
        (3, "1"),
        (19, "Zhong, Irene"),
        (48, "49AC52F69618"),
        (125, "5551112222"),
        (149, "09012024"),
        (157, "N"),
        (75, "note"),
    )
    d2 = rec(
        (1, "D2"),
        (3, "1"),
        (19, "Zhong, Irene"),
        (77, "1 Pool St"),
        (107, "City"),
        (127, "CA"),
        (156, "1"),
    )
    d3 = rec((1, "D3"), (3, "49AC52F6961843"), (17, "Reney"), (32, "S"), (36, "Y"))
    alt = f0(name="Sub, A", uss="ALT000000001", order_finals="A", leg_time="")
    g_bad = g0(times=("29.00", "bad"), total="2")
    lines = [A0, B1, b2, C1, c2, d0(), d1, d2, d3, g_bad, e0(), f0(), alt, Z0]
    m = parse_lines(lines).meets[0]
    assert m.source_file is not None and m.source_file.file_type is not None
    assert m.host is not None and m.host.name == "Host Club"
    club = m.clubs[0]
    assert club.coach_phone == "5559999" and club.short_name == "SCSC"
    sw = next(s for s in m.swimmers if s.id_short == "49AC52F69618")
    assert sw.registration is not None
    assert sw.registration.member_status is not None
    assert sw.registration.ethnicity_primary is not None
    assert sw.registration.affiliations
    relay = m.relays[0]
    assert relay.legs[0].takeoff_time == 29
    assert len(relay.alternates) == 1
    # an unparseable split survived as None
    fin = next(s for s in m.individual_swims if s.splits)
    assert any(sp.time is None for sp in fin.splits)
