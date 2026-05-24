"""Exception hierarchy for the tunas library."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tunas.parser import ParseWarning

__all__ = ["TunasError", "ParseError", "StandardsError"]


class TunasError(Exception):
    """Base exception for all tunas library errors."""


class ParseError(TunasError):
    """Raised on a fatal structural violation, or on warnings in strict mode.

    The originating ParseWarning is attached as `warning`.
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
    """Raised when bundled time-standards data is missing or inconsistent."""
