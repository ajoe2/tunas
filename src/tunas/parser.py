"""Public entry points for reading `.cl2` (SDIF) and `.hy3` (Hy-Tek) result files."""

from __future__ import annotations

import os
from collections import deque
from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from itertools import islice
from pathlib import Path
from typing import TextIO

from tunas._parser.cl2 import _Cl2Engine
from tunas._parser.diagnostics import IssueKind, ParseReport, ParseWarning, Severity
from tunas._parser.engine import _BaseEngine
from tunas._parser.hy3 import _Hy3Engine
from tunas.models import Meet

__all__ = [
    "read_cl2",
    "read_hy3",
    "MeetArchive",
    "ParseReport",
    "ParseWarning",
    "Severity",
    "IssueKind",
]

# Path-like or iterable-of-paths or open text stream.
type Source = str | os.PathLike[str] | Iterable[str | os.PathLike[str]] | TextIO


@dataclass(slots=True)
class MeetArchive:
    """The parse result for a single source file (or stream).

    A single `.cl2`/`.hy3` file can legitimately hold more than one meet, so
    ``meets`` is a list. ``report`` carries the diagnostics and counts for *this
    source only* — readers yield one ``MeetArchive`` per file, never a merged one.
    """

    source: str  # file path, or "<stream>" for a text stream
    meets: list[Meet] = field(default_factory=list)
    report: ParseReport = field(default_factory=ParseReport)


def read_cl2(
    source: Source,
    *,
    strict: bool = False,
    encoding: str = "cp1252",
    errors: str = "replace",
    max_workers: int = 1,
) -> Iterator[MeetArchive]:
    """Parse `.cl2` / SDIF v3 files, yielding one :class:`MeetArchive` per source.

    Parsing is lazy: files are read and parsed as the iterator is consumed, so a
    large corpus is processed one file at a time without holding every meet in
    memory at once. To materialize everything, drain the iterator (e.g.
    ``meets = [m for arc in read_cl2(...) for m in arc.meets]``).

    Args:
        source: File path, directory (walked recursively for `*.cl2`), iterable of paths,
            or an open text stream. A stream yields exactly one archive (``source="<stream>"``).
        strict: If True, raises ParseError on the first recovered/skipped warning.
            Otherwise, parsing is lenient. Fatal M1 structural violations always raise.
        encoding: Text encoding to use when opening file paths.
        errors: Error handling scheme for decoding errors.
        max_workers: Thread-pool size for concurrent file parsing. Archives are always
            yielded in source order. Under CPython's GIL the parse is CPU-bound and
            workers effectively serialize; on a free-threaded interpreter they run in
            parallel with no change to the result. At most ``2 * max_workers`` files are
            parsed ahead of the consumer, bounding peak memory.

    Yields:
        :class:`MeetArchive` objects in source order — one per file/stream.

    Raises:
        ValueError: If ``max_workers < 1`` (raised eagerly, before iteration).
        ParseError: During iteration, on a fatal structural violation, or in strict
            mode on any parse warning. The earliest failing source raises first.
    """
    return _read(
        source,
        _Cl2Engine,
        ".cl2",
        strict=strict,
        encoding=encoding,
        errors=errors,
        max_workers=max_workers,
    )


def read_hy3(
    source: Source,
    *,
    strict: bool = False,
    encoding: str = "cp1252",
    errors: str = "replace",
    max_workers: int = 1,
) -> Iterator[MeetArchive]:
    """Parse Hy-Tek `.hy3` result files, yielding one :class:`MeetArchive` per source.

    Only fields confirmed by the reverse-engineered `.hy3` specification are parsed
    into the returned `Meet` object graph. Iteration, ordering, and ``max_workers``
    semantics are identical to :func:`read_cl2`.

    Args:
        source: File path, directory (walked recursively for `*.hy3`), iterable of paths,
            or an open text stream. A stream yields exactly one archive (``source="<stream>"``).
        strict: If True, raises ParseError on the first recovered/skipped warning.
            Otherwise, parsing is lenient. Fatal M1 structural violations always raise.
        encoding: Text encoding to use when opening file paths.
        errors: Error handling scheme for decoding errors.
        max_workers: Thread-pool size for concurrent file parsing (see :func:`read_cl2`).

    Yields:
        :class:`MeetArchive` objects in source order — one per file/stream.

    Raises:
        ValueError: If ``max_workers < 1`` (raised eagerly, before iteration).
        ParseError: During iteration, on a fatal structural violation, or in strict
            mode on any parse warning. The earliest failing source raises first.
    """
    return _read(
        source,
        _Hy3Engine,
        ".hy3",
        strict=strict,
        encoding=encoding,
        errors=errors,
        max_workers=max_workers,
    )


def _read(
    source: Source,
    engine_cls: type[_BaseEngine],
    suffix: str,
    *,
    strict: bool,
    encoding: str,
    errors: str,
    max_workers: int,
) -> Iterator[MeetArchive]:
    """Validate args eagerly, then return a lazy archive iterator; shared by both readers."""
    if max_workers < 1:
        raise ValueError(f"max_workers must be >= 1, got {max_workers}")

    if hasattr(source, "read"):  # an open text stream — a single unit of work
        return _iter_stream(source, engine_cls, strict)  # type: ignore[arg-type]

    paths = _resolve_paths(source, suffix)
    return _iter_paths(
        paths, engine_cls, strict=strict, encoding=encoding, errors=errors, max_workers=max_workers
    )


def _iter_stream(
    stream: TextIO, engine_cls: type[_BaseEngine], strict: bool
) -> Iterator[MeetArchive]:
    """Parse a single open text stream into exactly one archive."""
    engine = engine_cls(strict=strict)
    engine.parse_source(stream, "<stream>")
    yield MeetArchive(source="<stream>", meets=engine.meets, report=engine.report)


def _iter_paths(
    paths: list[Path],
    engine_cls: type[_BaseEngine],
    *,
    strict: bool,
    encoding: str,
    errors: str,
    max_workers: int,
) -> Iterator[MeetArchive]:
    """Yield one archive per path, in order, optionally parsing several files concurrently."""

    def parse(path: Path) -> MeetArchive:
        return _parse_one(path, engine_cls, strict, encoding, errors)

    if max_workers == 1 or len(paths) <= 1:
        for path in paths:
            yield parse(path)
        return

    # Bounded, order-preserving parallel map: at most ``window`` files are parsed
    # ahead of the consumer, so peak memory tracks the window — not the whole corpus.
    # The pool lives for the iterator's lifetime and is shut down when it is exhausted
    # or closed (e.g. the consumer stops early).
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        yield from _imap_ordered(pool, parse, paths, window=max_workers * 2)


def _imap_ordered(
    pool: ThreadPoolExecutor,
    fn: Callable[[Path], MeetArchive],
    items: Iterable[Path],
    window: int,
) -> Iterator[MeetArchive]:
    """Like ``pool.map``, but never more than ``window`` tasks are in flight.

    ``pool.map`` submits every task up front and buffers completed-but-unconsumed
    results, which for thousands of files defeats the streaming/memory goal. This
    keeps a sliding window of futures, refilling one as each result is yielded, and
    preserves submission order so strict mode re-raises the earliest failing file first.
    """
    items = iter(items)
    futures: deque[Future[MeetArchive]] = deque(
        pool.submit(fn, item) for item in islice(items, window)
    )
    for item in items:
        result = futures.popleft().result()  # wait for the oldest in-flight file
        futures.append(pool.submit(fn, item))  # refill the window before handing back
        yield result
    while futures:
        yield futures.popleft().result()


def _resolve_paths(
    source: str | os.PathLike[str] | Iterable[str | os.PathLike[str]],
    suffix: str,
) -> list[Path]:
    """Expand `source` into an ordered list of file paths whose suffix matches `suffix`."""
    if isinstance(source, (str, os.PathLike)):
        path = Path(os.fspath(source))
        if path.is_dir():
            return [
                child
                for child in sorted(path.rglob("*"))
                if child.is_file() and child.suffix.lower() == suffix
            ]
        return [path]
    return [Path(os.fspath(item)) for item in source]


def _parse_one(
    path: Path, engine_cls: type[_BaseEngine], strict: bool, encoding: str, errors: str
) -> MeetArchive:
    """Parse a single file with its own engine, returning its archive."""
    engine = engine_cls(strict=strict)
    with open(path, encoding=encoding, errors=errors) as fh:
        engine.parse_source(fh, str(path))
    return MeetArchive(source=str(path), meets=engine.meets, report=engine.report)
