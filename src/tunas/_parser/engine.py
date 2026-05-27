"""Shared parse-engine base for the SDIF (`.cl2`) and Hy-Tek (`.hy3`) readers.

`_BaseEngine` owns everything the two fixed-width formats have in common: the
streaming line loop, record sizing/padding, structured diagnostics, and the
typed field-coercion helpers that wrap :mod:`tunas._parser.fields`. Each format
subclasses it and supplies its own per-meet state, record width, and handler
dispatch (see :mod:`tunas._parser.cl2` and :mod:`tunas._parser.hy3`).
"""

from __future__ import annotations

import datetime
from collections import Counter
from collections.abc import Iterable
from enum import StrEnum
from typing import ClassVar, NoReturn

from tunas._parser.diagnostics import IssueKind, ParseReport, ParseWarning, Severity
from tunas._parser.fields import (
    Record,
    code_value,
    course_value,
    date_value,
    int_value,
    time_value,
)
from tunas.enums import Citizenship, Course, ResultStatus, Sex, SplitType, Stroke
from tunas.event import Event
from tunas.exceptions import ParseError
from tunas.geography import Country
from tunas.models import CitizenshipOrCountry, Meet, MeetResult, SourceFile, Split, Swimmer
from tunas.time import Time


class _BaseEngine:
    """Stateful fixed-width parser. One instance per reader call, reused across files."""

    #: Total record width (data + any trailing checksum); padded/limited per line.
    RECORD_WIDTH: ClassVar[int]
    #: Public reader name, used in the bytes-source error message.
    READER: ClassVar[str]

    def __init__(self, *, strict: bool) -> None:
        self.strict = strict
        self.report = ParseReport()
        self.meets: list[Meet] = []
        self.source = "<stream>"
        self.source_file: SourceFile | None = None
        self.file_counts: Counter[str] = Counter()
        self.meets_this_file = 0

    # -- public driver ----------------------------------------------------- #

    def parse_source(self, lines: Iterable[object], source: str) -> None:
        """Parse one file/stream's lines, accumulating into ``self.meets``."""
        self.source = source
        self.report.files_read += 1
        self.source_file = None
        self.file_counts = Counter()
        self.meets_this_file = 0
        self._reset_state()

        first = True
        for line_no, raw in enumerate(lines, start=1):
            if not isinstance(raw, str):
                raise TypeError(f"{self.READER} requires a text source yielding str, not bytes")
            if first:
                raw = raw.lstrip("﻿")
                first = False
            self._feed(raw, line_no)
        self._finish_file()

    # -- per-format hooks (overridden by subclasses) ----------------------- #

    def _reset_state(self) -> None:
        """Clear per-file/per-meet state at the start of each file."""

    def _feed(self, raw: str, line_no: int) -> None:
        """Handle one raw line. Subclasses build the record and dispatch it."""
        raise NotImplementedError  # pragma: no cover - always overridden

    def _finish_file(self) -> None:
        """Flush any pending state at end of file."""

    def _sized_record(self, line: str, line_no: int) -> Record | None:
        """Length-check and right-pad a line to ``RECORD_WIDTH``, or skip if too long."""
        width = self.RECORD_WIDTH
        if len(line) > width:
            self._emit(
                self.source,
                line_no,
                line[0:2] or None,
                None,
                None,
                None,
                Severity.SKIPPED,
                IssueKind.BAD_LENGTH,
                f"line is {len(line)} chars (> {width})",
                line,
            )
            return None
        if len(line) < width:
            line = line.ljust(width)
        return Record(line, line_no, self.source)

    # -- diagnostics ------------------------------------------------------- #

    def _emit(
        self,
        source: str,
        line_no: int,
        record_type: str | None,
        field: str | None,
        column: str | None,
        mandatory: str | None,
        severity: Severity,
        kind: IssueKind,
        reason: str,
        raw_line: str,
    ) -> None:
        w = ParseWarning(
            source=source,
            line_no=line_no,
            record_type=record_type,
            field=field,
            column=column,
            mandatory=mandatory,
            severity=severity,
            kind=kind,
            reason=reason,
            raw_line=raw_line[:200],
        )
        if severity is Severity.FATAL or self.strict:
            raise ParseError(w)
        self.report.warnings.append(w)
        if severity is Severity.SKIPPED:
            self.report.records_skipped += 1
        elif severity is Severity.RECOVERED and kind is not IssueKind.COUNT_MISMATCH:
            self.report.fields_recovered += 1

    def _warn(
        self,
        rec: Record,
        field: str | None,
        column: str | None,
        mandatory: str | None,
        severity: Severity,
        kind: IssueKind,
        reason: str,
    ) -> None:
        self._emit(
            rec.source,
            rec.line_no,
            rec.type,
            field,
            column,
            mandatory,
            severity,
            kind,
            reason,
            rec.line,
        )

    def _skip_orphan(self, rec: Record, reason: str) -> None:
        """Skip a record that arrived without its required parent context."""
        self._warn(rec, None, None, None, Severity.SKIPPED, IssueKind.ORPHANED, reason)

    def _fatal(
        self, rec: Record, field: str, column: str, mandatory: str, kind: IssueKind, reason: str
    ) -> NoReturn:
        raise ParseError(
            ParseWarning(
                source=rec.source,
                line_no=rec.line_no,
                record_type=rec.type,
                field=field,
                column=column,
                mandatory=mandatory,
                severity=Severity.FATAL,
                kind=kind,
                reason=reason,
                raw_line=rec.line[:200],
            )
        )

    # -- typed field helpers ----------------------------------------------- #

    def _require_text(self, rec: Record, start: int, length: int, field: str, column: str) -> str:
        v = rec.text(start, length)
        if v is None:
            self._fatal(rec, field, column, "M1", IssueKind.MISSING, f"missing {field}")
        assert v is not None  # _fatal raised
        return v

    def _require_code[E: StrEnum](
        self, rec: Record, start: int, length: int, enum_cls: type[E], field: str, column: str
    ) -> E:
        tag, val = code_value(rec.raw(start, length), enum_cls)
        if tag == "blank":
            self._fatal(rec, field, column, "M1", IssueKind.MISSING, f"missing {field}")
        if tag == "unknown":
            self._fatal(
                rec,
                field,
                column,
                "M1",
                IssueKind.UNKNOWN_CODE,
                f"unknown {field} code {rec.raw(start, length).strip()!r}",
            )
        assert val is not None
        return val

    def _code[E: StrEnum](
        self,
        rec: Record,
        start: int,
        length: int,
        enum_cls: type[E],
        field: str,
        column: str,
        mandatory: str | None,
    ) -> E | None:
        tag, val = code_value(rec.raw(start, length), enum_cls)
        if tag == "unknown":
            self._warn(
                rec,
                field,
                column,
                mandatory,
                Severity.RECOVERED,
                IssueKind.UNKNOWN_CODE,
                f"unknown {field} code {rec.raw(start, length).strip()!r}",
            )
        return val

    def _date(
        self, rec: Record, start: int, length: int, field: str, column: str, mandatory: str | None
    ) -> datetime.date | None:
        tag, val = date_value(rec.raw(start, length))
        if tag == "bad":
            self._warn(
                rec,
                field,
                column,
                mandatory,
                Severity.RECOVERED,
                IssueKind.MALFORMED,
                f"malformed {field} date {rec.raw(start, length).strip()!r}",
            )
        elif tag == "blank" and mandatory == "M2":
            self._warn(
                rec,
                field,
                column,
                mandatory,
                Severity.RECOVERED,
                IssueKind.MISSING,
                f"missing {field}",
            )
        return val

    def _opt_int(self, rec: Record, start: int, length: int) -> int | None:
        _, val = int_value(rec.raw(start, length))
        return val

    def _require_int(self, rec: Record, start: int, length: int, field: str, column: str) -> int:
        tag, val = int_value(rec.raw(start, length))
        if tag != "int" or val is None:
            self._fatal(rec, field, column, "M1", IssueKind.MALFORMED, f"missing/malformed {field}")
        assert val is not None
        return val

    def _opt_time(self, rec: Record, start: int, length: int = 8) -> Time | None:
        tag, val = time_value(rec.raw(start, length))
        return val if tag == "time" and isinstance(val, Time) else None

    def _opt_course(self, rec: Record, start: int) -> Course | None:
        tag, val = course_value(rec.raw(start, 1))
        return val if tag == "ok" else None

    def _citizenship(self, rec: Record, start: int, length: int) -> CitizenshipOrCountry | None:
        v = rec.raw(start, length).strip()
        if not v:
            return None
        try:
            return Citizenship(v)
        except ValueError:
            pass
        try:
            return Country(v)
        except ValueError:
            self._warn(
                rec,
                "citizenship",
                f"{start}/{length}",
                None,
                Severity.RECOVERED,
                IssueKind.UNKNOWN_CODE,
                f"unknown citizenship {v!r}",
            )
            return None

    # -- shared assembly helpers ------------------------------------------- #

    def _attach_swimmer(self, meet: Meet, swimmer: Swimmer) -> None:
        """Link a new swimmer into its meet (and club, if attached) and count it.

        Centralizes the meet/club back-references so a swimmer can never end up
        registered on one side of the graph but missing from the other.
        """
        meet.swimmers.append(swimmer)
        if swimmer.club is not None:
            swimmer.club.swimmers.append(swimmer)
        self.report.swimmers_parsed += 1

    @staticmethod
    def _attach_result(meet: Meet, result: MeetResult) -> None:
        """Link a result into its meet (and club, if attached).

        Counting is left to the caller because the metric differs by result type
        (``individual_swims_parsed`` vs ``relays_parsed``).
        """
        meet.results.append(result)
        if result.club is not None:
            result.club.results.append(result)

    def _resolve_event(
        self,
        rec: Record,
        *,
        distance: int | None,
        stroke: Stroke | None,
        sex: Sex | None,
        course: Course | None,
        field: str,
        column: str,
        mandatory: str,
        noun: str,
        distance_display: str,
        stroke_display: str,
        extra_ok: bool = True,
    ) -> Event | None:
        """Resolve a `(distance, stroke, course)` event, or warn and return None.

        Every component must be present and resolve to a defined :class:`Event`;
        any gap (or a falsy ``extra_ok``, for format-specific guards like a bad
        age range) means the swim can't be modeled, so the record is skipped
        (lenient) or raises (strict). The caller resets its own per-swim state.
        """
        event = (
            Event.find(distance, stroke, course)
            if extra_ok
            and distance is not None
            and stroke is not None
            and sex is not None
            and course is not None
            else None
        )
        if event is None:
            self._warn(
                rec,
                field,
                column,
                mandatory,
                Severity.SKIPPED,
                IssueKind.UNKNOWN_CODE,
                f"unresolvable {noun} (distance={distance_display} "
                f"stroke={stroke_display} course={course})",
            )
        return event

    def _append_split(
        self,
        rec: Record,
        target: list[Split],
        distance: int,
        tag: str,
        val: Time | ResultStatus | None,
        split_type: SplitType,
        *,
        column: str | None = None,
    ) -> None:
        """Append one parsed split to ``target`` and count it.

        ``tag``/``val`` come from :func:`time_value`; a ``"bad"`` time is recovered
        as a ``Split`` with ``time=None`` plus a warning, anything else stores the
        time. Blank/placeholder slots are filtered out by the caller beforehand.
        """
        if tag == "bad":
            self._warn(
                rec,
                "split_time",
                column,
                None,
                Severity.RECOVERED,
                IssueKind.MALFORMED,
                "malformed split time",
            )
            target.append(Split(distance=distance, time=None, split_type=split_type))
        else:
            assert isinstance(val, Time)
            target.append(Split(distance=distance, time=val, split_type=split_type))
        self.report.splits_parsed += 1
