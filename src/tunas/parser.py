"""``read_cl2`` — read ``.cl2`` (SDIF v3) files into ``Meet`` objects.

Also the public home of the parse-diagnostic types (re-exported from
:mod:`tunas._parser.diagnostics`).
"""

from __future__ import annotations

import os
from collections.abc import Iterable
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
) -> tuple[list[Meet], ParseReport]:
    """Parse one or more ``.cl2`` files into ``(list[Meet], ParseReport)``.

    ``source`` may be a file path, a directory (walked recursively for ``*.cl2``),
    an iterable of paths, or an open text stream. Parsing is lenient by default;
    pass ``strict=True`` to raise :class:`~tunas.exceptions.ParseError` on the
    first problem. M1 structural violations always raise.
    """
    engine = _Engine(strict=strict)

    if hasattr(source, "read"):  # text stream
        engine.parse_source(source, "<stream>")  # type: ignore[arg-type]
    elif isinstance(source, (str, os.PathLike)):
        path = Path(os.fspath(source))
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix.lower() == ".cl2":
                    _parse_path(engine, child, encoding, errors)
        else:
            _parse_path(engine, path, encoding, errors)
    else:  # iterable of paths
        for item in source:
            _parse_path(engine, Path(os.fspath(item)), encoding, errors)

    return engine.meets, engine.report


def _parse_path(engine: _Engine, path: Path, encoding: str, errors: str) -> None:
    with open(path, encoding=encoding, errors=errors) as fh:
        engine.parse_source(fh, str(path))
