"""Public entry points for reading `.cl2` (SDIF) and `.hy3` (Hy-Tek) result files."""

from __future__ import annotations

import os
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
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
    "ParseReport",
    "ParseWarning",
    "Severity",
    "IssueKind",
]

# Path-like or iterable-of-paths or open text stream.
type Source = str | os.PathLike[str] | Iterable[str | os.PathLike[str]] | TextIO


def read_cl2(
    source: Source,
    *,
    strict: bool = False,
    encoding: str = "cp1252",
    errors: str = "replace",
    max_workers: int = 1,
) -> tuple[list[Meet], ParseReport]:
    """Parse `.cl2` / SDIF v3 files into a list of meets and a parse report.

    Args:
        source: File path, directory (walked recursively for `*.cl2`), iterable of paths,
            or an open text stream.
        strict: If True, raises ParseError on the first recovered/skipped warning.
            Otherwise, parsing is lenient. Fatal M1 structural violations always raise.
        encoding: Text encoding to use when opening file paths.
        errors: Error handling scheme for decoding errors.
        max_workers: Thread pool size for concurrent file parsing. Order is preserved.

    Returns:
        A tuple of `(meets, report)` where `meets` is the list of parsed `Meet` objects
        and `report` contains parsed counts and diagnostics.

    Raises:
        ParseError: If a fatal structural violation occurs, or in strict mode if any
            parse warning is encountered.
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
) -> tuple[list[Meet], ParseReport]:
    """Parse Hy-Tek `.hy3` result files into a list of meets and a parse report.

    Only fields confirmed by the reverse-engineered `.hy3` specification are parsed
    into the returned `Meet` object graph.

    Args:
        source: File path, directory (walked recursively for `*.hy3`), iterable of paths,
            or an open text stream.
        strict: If True, raises ParseError on the first recovered/skipped warning.
            Otherwise, parsing is lenient. Fatal M1 structural violations always raise.
        encoding: Text encoding to use when opening file paths.
        errors: Error handling scheme for decoding errors.
        max_workers: Thread pool size for concurrent file parsing. Order is preserved.

    Returns:
        A tuple of `(meets, report)` where `meets` is the list of parsed `Meet` objects
        and `report` contains parsed counts and diagnostics.

    Raises:
        ParseError: If a fatal structural violation occurs, or in strict mode if any
            parse warning is encountered.
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
) -> tuple[list[Meet], ParseReport]:
    """Drive ``engine_cls`` over ``source``; shared by :func:`read_cl2` / :func:`read_hy3`."""
    if max_workers < 1:
        raise ValueError(f"max_workers must be >= 1, got {max_workers}")

    if hasattr(source, "read"):  # an open text stream — a single unit of work
        engine = engine_cls(strict=strict)
        engine.parse_source(source, "<stream>")  # type: ignore[arg-type]
        return engine.meets, engine.report

    paths = _resolve_paths(source, suffix)

    if max_workers == 1 or len(paths) <= 1:
        # Sequential: one engine accumulates across the files, in order.
        engine = engine_cls(strict=strict)
        for path in paths:
            _parse_path(engine, path, encoding, errors)
        return engine.meets, engine.report

    # Parallel: an independent engine per file, merged back in source order.
    def parse(path: Path) -> _BaseEngine:
        engine = engine_cls(strict=strict)
        _parse_path(engine, path, encoding, errors)
        return engine

    meets: list[Meet] = []
    report = ParseReport()
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        # ``map`` yields in submission order, so the merge is deterministic; in
        # strict mode it re-raises the earliest failing file's ParseError.
        for engine in pool.map(parse, paths):
            meets.extend(engine.meets)
            report.merge(engine.report)
    return meets, report


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


def _parse_path(engine: _BaseEngine, path: Path, encoding: str, errors: str) -> None:
    with open(path, encoding=encoding, errors=errors) as fh:
        engine.parse_source(fh, str(path))
