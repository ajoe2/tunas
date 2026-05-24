"""``read_cl2`` — read ``.cl2`` (SDIF v3) files into ``Meet`` objects.

Also the public home of the parse-diagnostic types (re-exported from
:mod:`tunas._parser.diagnostics`).
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TextIO

from tunas._parser.diagnostics import IssueKind, ParseReport, ParseWarning, Severity
from tunas._parser.handlers import _Engine
from tunas.models import Meet

__all__ = [
    "read_cl2",
    "ParseReport",
    "ParseWarning",
    "Severity",
    "IssueKind",
]


def read_cl2(
    source: str | os.PathLike[str] | Iterable[str | os.PathLike[str]] | TextIO,
    *,
    strict: bool = False,
    encoding: str = "cp1252",
    errors: str = "replace",
    max_workers: int = 1,
) -> tuple[list[Meet], ParseReport]:
    """Parse one or more ``.cl2`` files into ``(list[Meet], ParseReport)``.

    ``source`` may be a file path, a directory (walked recursively for ``*.cl2``),
    an iterable of paths, or an open text stream. Parsing is lenient by default;
    pass ``strict=True`` to raise :class:`~tunas.exceptions.ParseError` on the
    first problem. M1 structural violations always raise.

    With ``max_workers > 1`` the files are parsed concurrently on a thread pool —
    one file per task — and the per-file results are merged back **in source
    order**, so the output is identical to the sequential default
    (``max_workers=1``), regardless of thread scheduling. Threads mainly overlap
    file I/O (parsing itself holds the GIL), so the speed-up is largest on many
    files. A single text stream is always parsed inline.
    """
    if max_workers < 1:
        raise ValueError(f"max_workers must be >= 1, got {max_workers}")

    if hasattr(source, "read"):  # an open text stream — a single unit of work
        engine = _Engine(strict=strict)
        engine.parse_source(source, "<stream>")  # type: ignore[arg-type]
        return engine.meets, engine.report

    paths = _resolve_paths(source)

    if max_workers == 1 or len(paths) <= 1:
        # Sequential: one engine accumulates across the files, in order.
        engine = _Engine(strict=strict)
        for path in paths:
            _parse_path(engine, path, encoding, errors)
        return engine.meets, engine.report

    # Parallel: an independent engine per file, merged back in source order.
    def parse(path: Path) -> _Engine:
        engine = _Engine(strict=strict)
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
) -> list[Path]:
    """Expand ``source`` to the ordered list of files to parse.

    A directory is walked recursively for ``*.cl2`` (sorted); a single path is
    returned as-is; an iterable of paths is taken in iteration order.
    """
    if isinstance(source, (str, os.PathLike)):
        path = Path(os.fspath(source))
        if path.is_dir():
            return [
                child
                for child in sorted(path.rglob("*"))
                if child.is_file() and child.suffix.lower() == ".cl2"
            ]
        return [path]
    return [Path(os.fspath(item)) for item in source]


def _parse_path(engine: _Engine, path: Path, encoding: str, errors: str) -> None:
    with open(path, encoding=encoding, errors=errors) as fh:
        engine.parse_source(fh, str(path))
