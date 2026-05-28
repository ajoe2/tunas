"""Structured parse diagnostics (Severity, IssueKind, ParseWarning, ParseReport)."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field, fields

__all__ = ["Severity", "IssueKind", "ParseWarning", "ParseReport"]


class Severity(enum.Enum):
    """How a parse issue was handled."""

    FATAL = "fatal"  # Structural (M1) violation; carried only by the raised ParseError
    SKIPPED = "skipped"  # Record dropped entirely
    RECOVERED = "recovered"  # Field set to None, record kept


class IssueKind(enum.Enum):
    """What kind of data problem a warning describes."""

    MISSING = "missing"  # Blank mandatory field
    MALFORMED = "malformed"  # Unparseable value (date/time/int)
    UNKNOWN_CODE = "unknown_code"  # Invalid code-table value or unresolvable event
    BAD_LENGTH = "bad_length"  # Over-long / unusable line
    ORPHANED = "orphaned"  # No anchor record found
    UNKNOWN_RECORD = "unknown_record"  # Unmodeled record header
    COUNT_MISMATCH = "count_mismatch"  # Z0 declared count != parsed total


@dataclass(frozen=True)
class ParseWarning:
    """A single structured diagnostic."""

    source: str
    line_no: int
    record_type: str | None
    field: str | None
    column: str | None  # SDIF "start/length", e.g. "40/12"
    mandatory: str | None  # "M1" | "M2" | "M1#" | "*" | "**" | None
    severity: Severity
    kind: IssueKind
    reason: str
    raw_line: str  # truncated to 200 chars


@dataclass
class ParseReport:
    """Metrics and warnings for a single parsed source (one file or stream).

    Both :func:`~tunas.read_cl2` and :func:`~tunas.read_hy3` attach one report per
    :class:`~tunas.MeetArchive`; use :meth:`merge` to fold several into a corpus-wide total.
    """

    warnings: list[ParseWarning] = field(default_factory=list)
    files_read: int = 0
    meets_parsed: int = 0
    swimmers_parsed: int = 0
    individual_swims_parsed: int = 0
    relays_parsed: int = 0
    splits_parsed: int = 0
    records_skipped: int = 0  # records dropped entirely
    fields_recovered: int = 0  # nulled M2 fields (excludes COUNT_MISMATCH)

    def merge(self, other: ParseReport) -> None:
        """Fold another report into this report: append warnings and sum all counts."""
        self.warnings.extend(other.warnings)
        for f in fields(self):
            if f.name != "warnings":
                setattr(self, f.name, getattr(self, f.name) + getattr(other, f.name))

    @property
    def has_warnings(self) -> bool:
        """True if any warnings were collected."""
        return bool(self.warnings)

    @property
    def by_severity(self) -> dict[Severity, list[ParseWarning]]:
        """Warnings grouped by Severity."""
        out: dict[Severity, list[ParseWarning]] = {s: [] for s in Severity}
        for w in self.warnings:
            out[w.severity].append(w)
        return out

    def warnings_for(
        self,
        *,
        record_type: str | None = None,
        field: str | None = None,
        severity: Severity | None = None,
        kind: IssueKind | None = None,
    ) -> list[ParseWarning]:
        """Warnings filtered by attributes."""
        return [
            w
            for w in self.warnings
            if (record_type is None or w.record_type == record_type)
            and (field is None or w.field == field)
            and (severity is None or w.severity is severity)
            and (kind is None or w.kind is kind)
        ]
