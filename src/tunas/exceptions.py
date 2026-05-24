"""The :class:`TunasError` exception hierarchy."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tunas.parser import ParseWarning

__all__ = ["TunasError", "ParseError", "StandardsError"]


class TunasError(Exception):
    """Base class for all exceptions raised by tunas."""


class ParseError(TunasError):
    """Raised on a fatal (M1) structural violation, or on any warning in strict mode.

    The originating :class:`~tunas.parser.ParseWarning` is attached as
    ``warning`` for diagnostics.
    """

    def __init__(self, warning: ParseWarning) -> None:
        self.warning = warning
        super().__init__(
            f"{warning.source}:{warning.line_no} "
            f"[{warning.severity.value}] "
            f"{warning.record_type or '??'}"
            f"{'.' + warning.field if warning.field else ''}: {warning.reason}"
        )


class StandardsError(TunasError):
    """Raised when bundled time-standards data is missing, unreadable, or inconsistent."""
