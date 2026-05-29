"""Public entry points for reading `.cl2` (SDIF) and `.hy3` (Hy-Tek) result files."""

from __future__ import annotations

import os
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
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

    Attributes:
        source: File path, or "<stream>" for an open text stream.
        meets: List of Meet objects parsed from the source.
        report: Diagnostic and metric report for the parsed source.
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
) -> Iterator[MeetArchive]:
    """Parse `.cl2` / SDIF v3 files, yielding one :class:`MeetArchive` per source.

    Parsing is lazy: files are read and parsed one at a time as the iterator is
    consumed, so a large corpus is never held in memory all at once. To materialize
    everything, drain the iterator (e.g.
    ``meets = [m for arc in read_cl2(...) for m in arc.meets]``).

    Per the SDIF spec a "no time" is a blank field or a status code
    (``NT``/``NS``/``DNF``/``DQ``/``SCR``) — never ``0.00`` — so a missing time
    surfaces as ``time=None`` with a non-OK :class:`~tunas.ResultStatus` (Hy-Tek
    `.hy3` instead uses a ``0.00`` sentinel; see :func:`read_hy3`).

    Args:
        source: File path, directory (walked recursively for `*.cl2`), iterable of paths,
            or an open text stream. A stream yields exactly one archive (``source="<stream>"``).
        strict: If True, raises ParseError on the first recovered/skipped warning.
            Otherwise, parsing is lenient. Fatal M1 structural violations always raise.
        encoding: Text encoding to use when opening file paths.
        errors: Error handling scheme for decoding errors.

    Yields:
        :class:`MeetArchive` objects in source order — one per file/stream.

    Raises:
        ParseError: During iteration, on a fatal structural violation, or in strict
            mode on any parse warning. The earliest failing source raises first.
    """
    return _read(source, _Cl2Engine, ".cl2", strict=strict, encoding=encoding, errors=errors)


def read_hy3(
    source: Source,
    *,
    strict: bool = False,
    encoding: str = "cp1252",
    errors: str = "replace",
) -> Iterator[MeetArchive]:
    """Parse Hy-Tek `.hy3` result files, yielding one :class:`MeetArchive` per source.

    Only fields confirmed by the reverse-engineered `.hy3` specification are parsed
    into the returned `Meet` object graph. Iteration and ordering semantics are
    identical to :func:`read_cl2`.

    Hy-Tek encodes a "no time" entry as the sentinel ``0.00``, normalized here to
    ``time=None`` (SDIF instead uses a blank field or an ``NT`` code; see
    :func:`read_cl2`).

    Args:
        source: File path, directory (walked recursively for `*.hy3`), iterable of paths,
            or an open text stream. A stream yields exactly one archive (``source="<stream>"``).
        strict: If True, raises ParseError on the first recovered/skipped warning.
            Otherwise, parsing is lenient. Fatal M1 structural violations always raise.
        encoding: Text encoding to use when opening file paths.
        errors: Error handling scheme for decoding errors.

    Yields:
        :class:`MeetArchive` objects in source order — one per file/stream.

    Raises:
        ParseError: During iteration, on a fatal structural violation, or in strict
            mode on any parse warning. The earliest failing source raises first.
    """
    return _read(source, _Hy3Engine, ".hy3", strict=strict, encoding=encoding, errors=errors)


def _read(
    source: Source,
    engine_cls: type[_BaseEngine],
    suffix: str,
    *,
    strict: bool,
    encoding: str,
    errors: str,
) -> Iterator[MeetArchive]:
    """Dispatch to the stream or path iterator; shared by both readers."""
    if hasattr(source, "read"):  # an open text stream — a single unit of work
        return _iter_stream(source, engine_cls, strict)  # type: ignore[arg-type]

    paths = _resolve_paths(source, suffix)
    return _iter_paths(paths, engine_cls, strict=strict, encoding=encoding, errors=errors)


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
) -> Iterator[MeetArchive]:
    """Yield one archive per path, in order, parsing each file as it is consumed."""
    for path in paths:
        yield _parse_one(path, engine_cls, strict, encoding, errors)


def _resolve_paths(
    source: str | os.PathLike[str] | Iterable[str | os.PathLike[str]],
    suffix: str,
) -> list[Path]:
    """Expand `source` into an ordered list of file paths whose suffix matches `suffix`."""
    if isinstance(source, (str, os.PathLike)):
        path = Path(os.fspath(source))
        if path.is_dir():
            return sorted(
                child
                for child in path.rglob("*")
                if child.is_file() and child.suffix.lower() == suffix
            )
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
