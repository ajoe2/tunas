"""The SDIF parse engine: one handler per record type, wired by ``_Engine``.

The engine reads padded lines, dispatches by 2-char header, and assembles the
object graph under the M1/M2 + lose-no-information error model documented in
``docs/parsing.md``.
"""

from __future__ import annotations

import datetime
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import replace
from enum import StrEnum
from typing import NoReturn, TypeVar

from tunas._parser.diagnostics import IssueKind, ParseReport, ParseWarning, Severity
from tunas._parser.fields import (
    RECORD_WIDTH,
    Record,
    code_value,
    course_value,
    date_value,
    decimal_value,
    event_age_value,
    int_value,
    time_value,
)
from tunas._parser.ids import normalize_id
from tunas._parser.names import parse_name
from tunas._parser.state import ParserState, PendingIndividual
from tunas.enums import (
    Affiliation,
    AttachStatus,
    Citizenship,
    Course,
    Ethnicity,
    EventTimeClass,
    FileType,
    MeetType,
    MemberStatus,
    Organization,
    Region,
    RelayLegOrder,
    ResultStatus,
    Season,
    Session,
    Sex,
    SplitType,
    Stroke,
)
from tunas.event import Event
from tunas.exceptions import ParseError
from tunas.geography import LSC, Country, State
from tunas.models import (
    Club,
    ClubEntryCounts,
    IndividualSwim,
    Meet,
    MeetHost,
    Relay,
    RelaySwim,
    SourceFile,
    Split,
    Swimmer,
    SwimmerContact,
    SwimmerRegistration,
)
from tunas.time import Time

_E = TypeVar("_E", bound=StrEnum)

_CONTINUATION = {"D1", "D2", "D3", "G0"}
_CHAMPIONSHIP = {MeetType.NATIONAL_CHAMPIONSHIP, MeetType.JUNIORS}
_RELAY_LEG_SESSIONS: list[tuple[Session, int]] = [
    (Session.PRELIMS, 77),
    (Session.SWIM_OFFS, 78),
    (Session.FINALS, 79),
]
_AFFILIATION_COLUMNS: list[tuple[int, Affiliation]] = [
    (34, Affiliation.JUNIOR_HIGH),
    (35, Affiliation.SENIOR_HIGH),
    (36, Affiliation.YMCA_YWCA),
    (37, Affiliation.COLLEGE),
    (38, Affiliation.SUMMER_LEAGUE),
    (39, Affiliation.MASTERS),
    (40, Affiliation.DISABLED_SPORTS),
    (41, Affiliation.WATER_POLO),
]


class _Engine:
    """Stateful parser. One instance per ``read_cl2`` call, reused across files."""

    def __init__(self, *, strict: bool) -> None:
        self.strict = strict
        self.report = ParseReport()
        self.meets: list[Meet] = []
        self.source = "<stream>"
        self.source_file: SourceFile | None = None
        self.file_counts: Counter[str] = Counter()
        self.meets_this_file = 0
        self.state: ParserState | None = None

    # -- public driver ----------------------------------------------------- #

    def parse_source(self, lines: Iterable[object], source: str) -> None:
        """Parse one file/stream's lines, accumulating into ``self.meets``."""
        self.source = source
        self.report.files_read += 1
        self.source_file = None
        self.file_counts = Counter()
        self.meets_this_file = 0
        self.state = None

        first = True
        for line_no, raw in enumerate(lines, start=1):
            if not isinstance(raw, str):
                raise TypeError("read_cl2 requires a text source yielding str, not bytes")
            if first:
                raw = raw.lstrip("﻿")
                first = False
            self._feed(raw, line_no)
        self._commit_pending()

    # -- line handling ----------------------------------------------------- #

    def _feed(self, raw: str, line_no: int) -> None:
        line = raw.rstrip("\r\n")
        if not line.strip():
            return
        if len(line) > RECORD_WIDTH:
            self._emit(
                self.source,
                line_no,
                line[0:2] or None,
                None,
                None,
                None,
                Severity.SKIPPED,
                IssueKind.BAD_LENGTH,
                f"line is {len(line)} chars (> {RECORD_WIDTH})",
                line,
            )
            return
        if len(line) < RECORD_WIDTH:
            line = line.ljust(RECORD_WIDTH)

        rec = Record(line, line_no, self.source)
        self.file_counts[rec.type] += 1

        if rec.type not in _CONTINUATION and self.state and self.state.pending_individual:
            self._commit_pending()

        handler = _HANDLERS.get(rec.type)
        if handler is None:
            self._warn(
                rec,
                None,
                None,
                None,
                Severity.SKIPPED,
                IssueKind.UNKNOWN_RECORD,
                f"unmodeled record type {rec.type!r}",
            )
            return
        handler(self, rec)

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

    def _require_code(
        self, rec: Record, start: int, length: int, enum_cls: type[_E], field: str, column: str
    ) -> _E:
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

    def _code(
        self,
        rec: Record,
        start: int,
        length: int,
        enum_cls: type[_E],
        field: str,
        column: str,
        mandatory: str | None,
    ) -> _E | None:
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

    def _citizenship(self, rec: Record, start: int, length: int) -> Citizenship | Country | None:
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

    def _time_classes(
        self, rec: Record, start: int
    ) -> tuple[EventTimeClass | None, EventTimeClass | None]:
        raw = rec.raw(start, 2)

        def one(ch: str) -> EventTimeClass | None:
            ch = ch.strip().upper()
            if ch in ("", "U", "O"):  # blank / no-lower / no-upper
                return None
            try:
                return EventTimeClass(ch)
            except ValueError:
                return None

        return one(raw[0:1]), one(raw[1:2])

    def _place(
        self, rec: Record, start: int, field: str, column: str, championship: bool
    ) -> int | None:
        tag, val = int_value(rec.raw(start, 3))
        if tag == "blank":
            if championship:
                self._warn(
                    rec,
                    field,
                    column,
                    "**",
                    Severity.RECOVERED,
                    IssueKind.MISSING,
                    f"missing {field} at a championship meet",
                )
            return None
        if tag == "bad" or val is None or val <= 0:
            return None
        return val

    # -- swimmer registration ---------------------------------------------- #

    def _register_swimmer(self, swimmer: Swimmer, results: list[IndividualSwim]) -> Swimmer:
        st = self.state
        assert st is not None
        keys = [k for k in (swimmer.id_short, swimmer.id_long) if k]
        target: Swimmer | None = None
        for k in keys:
            target = st.swimmers_by_id.get(k)
            if target is not None:
                break
        if target is None:
            target = swimmer
            st.meet.swimmers.append(target)
            if target.club is not None:
                target.club.swimmers.append(target)
            self.report.swimmers_parsed += 1
        else:
            self._merge_swimmer(target, swimmer)
        for k in keys:
            st.swimmers_by_id.setdefault(k, target)
        for r in results:
            r.swimmer = target
            target.swims.append(r)
            st.meet.results.append(r)
            if r.club is not None:
                r.club.results.append(r)
            self.report.individual_swims_parsed += 1
        return target

    @staticmethod
    def _merge_swimmer(existing: Swimmer, other: Swimmer) -> None:
        for attr in (
            "id_short",
            "id_long",
            "middle_initial",
            "preferred_first_name",
            "birthday",
            "citizenship",
            "contact",
            "registration",
            "club",
        ):
            if getattr(existing, attr) is None and getattr(other, attr) is not None:
                setattr(existing, attr, getattr(other, attr))

    def _commit_pending(self) -> None:
        st = self.state
        if st is None or st.pending_individual is None:
            return
        p = st.pending_individual
        st.pending_individual = None
        if p.swimmer.id_short is None and p.swimmer.id_long is None:
            # The record is discarded, so back out any splits a trailing G0
            # already counted against the now-dropped results (keeps
            # splits_parsed consistent with the object graph).
            self.report.splits_parsed -= sum(len(r.splits) for r in p.results)
            self._emit(
                self.source,
                p.line_no,
                "D0",
                "id_short",
                "40/12",
                "M2",
                Severity.SKIPPED,
                IssueKind.MISSING,
                "no USS# (id_short or id_long); record skipped",
                p.raw_line,
            )
            return
        self._register_swimmer(p.swimmer, p.results)

    def _resolve_relay_swimmer(
        self,
        rec: Record,
        id_short: str | None,
        id_long: str | None,
        *,
        first: str,
        last: str,
        middle: str | None,
        sex: Sex,
        birthday: datetime.date | None,
        citizenship: Citizenship | Country | None,
        preferred: str | None,
    ) -> Swimmer | None:
        st = self.state
        assert st is not None
        keys = [k for k in (id_short, id_long) if k]
        if not keys:
            return None
        for k in keys:
            existing = st.swimmers_by_id.get(k)
            if existing is not None:
                return existing
        swimmer = Swimmer(
            meet=st.meet,
            first_name=first,
            last_name=last,
            sex=sex,
            id_short=id_short,
            id_long=id_long,
            middle_initial=middle,
            preferred_first_name=preferred,
            birthday=birthday,
            citizenship=citizenship,
            club=None if st.unattached else st.current_club,
        )
        st.meet.swimmers.append(swimmer)
        if swimmer.club is not None:
            swimmer.club.swimmers.append(swimmer)
        self.report.swimmers_parsed += 1
        for k in keys:
            st.swimmers_by_id[k] = swimmer
        return swimmer

    # -- contact / registration enrichment --------------------------------- #

    @staticmethod
    def _update_contact(sw: Swimmer, **kw: object) -> None:
        present = {k: v for k, v in kw.items() if v is not None}
        if present:
            sw.contact = replace(sw.contact or SwimmerContact(), **present)  # type: ignore[arg-type]

    @staticmethod
    def _update_registration(sw: Swimmer, **kw: object) -> None:
        present = {k: v for k, v in kw.items() if v is not None}
        if present:
            sw.registration = replace(sw.registration or SwimmerRegistration(), **present)  # type: ignore[arg-type]

    # ===================================================================== #
    # Record handlers
    # ===================================================================== #

    def _h_a0(self, rec: Record) -> None:
        self.source_file = SourceFile(
            path=self.source,
            file_type=self._code(rec, 12, 2, FileType, "file_type", "12/2", "M1"),
            sdif_version=rec.text(4, 8),
            software_name=rec.text(44, 20),
            software_version=rec.text(64, 10),
            contact_name=rec.text(74, 20),
            contact_phone=rec.text(94, 12),
            created=self._date(rec, 106, 8, "created", "106/8", None),
            submitted_by_lsc=self._code(rec, 156, 2, LSC, "submitted_by_lsc", "156/2", None),
        )

    def _h_b1(self, rec: Record) -> None:
        self._commit_pending()
        org = self._code(rec, 3, 1, Organization, "organization", "3/1", "M2") or Organization.USS
        name = self._require_text(rec, 12, 30, "name", "12/30")
        start = self._date(rec, 122, 8, "start_date", "122/8", "M1")
        if start is None:
            self._fatal(
                rec, "start_date", "122/8", "M1", IssueKind.MISSING, "missing meet start date"
            )
        meet = Meet(
            organization=org,
            name=name,
            start_date=start,
            end_date=self._date(rec, 130, 8, "end_date", "130/8", "M2"),
            city=self._m2_text(rec, 86, 20, "city", "86/20"),
            address_one=rec.text(42, 22),
            address_two=rec.text(64, 22),
            state=self._m2_code(rec, 106, 2, State, "state", "106/2"),
            postal_code=rec.text(108, 10),
            country=self._code(rec, 118, 3, Country, "country", "118/3", None),
            course=self._opt_course(rec, 150),
            altitude=self._opt_int(rec, 138, 4),
            meet_type=self._m2_code(rec, 121, 1, MeetType, "meet_type", "121/1"),
            source_file=self.source_file,
        )
        self.meets.append(meet)
        self.report.meets_parsed += 1
        self.meets_this_file += 1
        self.state = ParserState(meet=meet)

    def _m2_text(self, rec: Record, start: int, length: int, field: str, column: str) -> str | None:
        v = rec.text(start, length)
        if v is None:
            self._warn(
                rec, field, column, "M2", Severity.RECOVERED, IssueKind.MISSING, f"missing {field}"
            )
        return v

    def _m2_code(
        self, rec: Record, start: int, length: int, enum_cls: type[_E], field: str, column: str
    ) -> _E | None:
        tag, val = code_value(rec.raw(start, length), enum_cls)
        if tag == "blank":
            self._warn(
                rec, field, column, "M2", Severity.RECOVERED, IssueKind.MISSING, f"missing {field}"
            )
        elif tag == "unknown":
            self._warn(
                rec,
                field,
                column,
                "M2",
                Severity.RECOVERED,
                IssueKind.UNKNOWN_CODE,
                f"unknown {field} code {rec.raw(start, length).strip()!r}",
            )
        return val

    def _h_b2(self, rec: Record) -> None:
        if self.state is None:
            return
        self.state.meet.host = MeetHost(
            name=self._m2_text(rec, 12, 30, "host_name", "12/30"),
            address_one=rec.text(42, 22),
            address_two=rec.text(64, 22),
            city=rec.text(86, 20),
            state=self._code(rec, 106, 2, State, "state", "106/2", None),
            postal_code=rec.text(108, 10),
            country=self._code(rec, 118, 3, Country, "country", "118/3", None),
            phone=rec.text(121, 12),
        )

    def _team_code(self, rec: Record, code_start: int, ext_start: int) -> tuple[str, LSC | None]:
        base = rec.raw(code_start, 6)
        lsc_raw = base[0:2].strip()
        team = base[2:].strip()
        ext = rec.raw(ext_start, 1).strip()
        full = (lsc_raw + team + ext) or base.strip()
        try:
            lsc: LSC | None = LSC(lsc_raw) if lsc_raw else None
        except ValueError:
            lsc = None
        return full, lsc

    def _h_c1(self, rec: Record) -> None:
        st = self.state
        if st is None:
            return
        self._commit_pending()
        org = self._code(rec, 3, 1, Organization, "organization", "3/1", "M2") or Organization.USS
        team_code, lsc = self._team_code(rec, 12, 150)
        name = self._require_text(rec, 18, 30, "full_team_name", "18/30")
        team_part = rec.raw(12, 6)[2:].strip().upper()
        if team_part == "UN" or "UNATTACHED" in name.upper():
            st.unattached = True
            st.current_club = None
            return
        st.unattached = False
        key = (team_code, lsc)
        existing = st.clubs_by_key.get(key)
        if existing is not None:
            st.current_club = existing
            return
        club = Club(
            meet=st.meet,
            organization=org,
            team_code=team_code,
            lsc=lsc,
            full_name=name,
            abbreviated_name=rec.text(48, 16),
            address_one=rec.text(64, 22),
            address_two=rec.text(86, 22),
            city=rec.text(108, 20),
            state=self._code(rec, 128, 2, State, "state", "128/2", None),
            postal_code=rec.text(130, 10),
            country=self._code(rec, 140, 3, Country, "country", "140/3", None),
            region=self._code(rec, 143, 1, Region, "region", "143/1", None),
        )
        st.clubs_by_key[key] = club
        st.meet.clubs.append(club)
        st.current_club = club

    def _h_c2(self, rec: Record) -> None:
        st = self.state
        if st is None or st.current_club is None:
            return
        club = st.current_club
        coach = self._m2_text(rec, 18, 30, "coach", "18/30")
        if coach is not None:
            club.coach = coach
        phone = rec.text(48, 12)
        if phone is not None:
            club.coach_phone = phone
        short = rec.text(89, 16)
        if short is not None:
            club.short_name = short
        club.entry_counts = ClubEntryCounts(
            num_individual_swims=self._opt_int(rec, 60, 6),
            num_athletes=self._opt_int(rec, 66, 6),
            num_relay_entries=self._opt_int(rec, 72, 5),
            num_relay_name_records=self._opt_int(rec, 77, 6),
            num_split_records=self._opt_int(rec, 83, 6),
        )

    def _h_d0(self, rec: Record) -> None:
        st = self.state
        if st is None:
            self._warn(
                rec,
                None,
                None,
                None,
                Severity.SKIPPED,
                IssueKind.ORPHANED,
                "D0 with no preceding B1 meet",
            )
            return
        org = self._code(rec, 3, 1, Organization, "organization", "3/1", "M2") or Organization.USS
        last, first, middle = parse_name(self._require_text(rec, 12, 28, "swimmer_name", "12/28"))
        id_short = normalize_id(rec.raw(40, 12))
        citizenship = self._citizenship(rec, 53, 3)
        birthday = self._date(rec, 56, 8, "birthday", "56/8", "M2")
        sex = self._require_code(rec, 66, 1, Sex, "sex", "66/1")
        age_class = rec.text(64, 2)
        date_of_swim = self._date(rec, 81, 8, "date", "81/8", "M2")

        esex_tag, esex = code_value(rec.raw(67, 1), Sex)
        dist_tag, dist = int_value(rec.raw(68, 4))
        stroke_tag, stroke = code_value(rec.raw(72, 1), Stroke)
        eage_tag, emin, emax = event_age_value(rec.raw(77, 4))
        present = [
            esex_tag != "blank",
            dist_tag != "blank",
            stroke_tag != "blank",
            eage_tag != "blank",
        ]

        attach_status = (
            AttachStatus.UNATTACHED
            if st.unattached
            else (
                self._code(rec, 52, 1, AttachStatus, "attach_status", "52/1", None)
                or AttachStatus.ATTACHED
            )
        )
        swimmer = Swimmer(
            meet=st.meet,
            first_name=first,
            last_name=last,
            sex=sex,
            id_short=id_short,
            middle_initial=middle,
            birthday=birthday,
            citizenship=citizenship,
            club=None if st.unattached else st.current_club,
        )

        results: list[IndividualSwim] = []
        if any(present):
            # Any invalid/partial/unresolvable event field means we cannot model the
            # swim — skip the whole record (lenient) / raise (strict). This is NOT a
            # fatal M1: one bad/odd record (e.g. a diving event with stroke "H") must
            # not abort an otherwise-valid file.
            course = self._event_course(rec, [124, 106, 115, 97], st.meet.course)
            event = (
                Event.find(dist, stroke, course)
                if all(present)
                and esex is not None
                and dist is not None
                and stroke is not None
                and eage_tag != "bad"
                and course is not None
                else None
            )
            if event is None:
                self._warn(
                    rec,
                    "event",
                    "67/1",
                    "M1#",
                    Severity.SKIPPED,
                    IssueKind.UNKNOWN_CODE,
                    f"unresolvable event (distance={rec.raw(68, 4).strip()!r} "
                    f"stroke={rec.raw(72, 1).strip()!r} course={course})",
                )
                st.current_individual_swims = []
                st.current_swimmer = None
                st.last_leaf = None
                return
            assert esex is not None
            seed_t = self._opt_time(rec, 89)
            seed_c = self._opt_course(rec, 97)
            min_tc, max_tc = self._time_classes(rec, 143)
            champ = st.meet.meet_type in _CHAMPIONSHIP
            shared: dict[str, object] = dict(
                meet=st.meet,
                club=None if st.unattached else st.current_club,
                organization=org,
                event=event,
                event_min_age=emin,
                event_max_age=emax,
                event_sex=esex,
                event_number=rec.text(73, 4),
                date=date_of_swim,
                seed_time=seed_t,
                seed_course=seed_c,
                event_min_time_class=min_tc,
                event_max_time_class=max_tc,
                swimmer=swimmer,
                swimmer_age_class=age_class,
                attach_status=attach_status,
            )
            specs = [
                (Session.PRELIMS, 98, 106, 125, 127, 133, None),
                (Session.SWIM_OFFS, 107, 115, None, None, None, None),
                (Session.FINALS, 116, 124, 129, 131, 136, 139),
            ]
            for session, t_pos, c_pos, h_pos, l_pos, p_pos, pts_pos in specs:
                r = self._individual_session(
                    rec, session, t_pos, c_pos, h_pos, l_pos, p_pos, pts_pos, champ, shared
                )
                if r is not None:
                    results.append(r)

        if id_short:
            target = self._register_swimmer(swimmer, results)
            st.current_swimmer = target
        else:
            st.pending_individual = PendingIndividual(swimmer, results, rec.line, rec.line_no)
            st.current_swimmer = swimmer
        st.current_individual_swims = results
        st.last_leaf = "individual"

    def _individual_session(
        self,
        rec: Record,
        session: Session,
        t_pos: int,
        c_pos: int,
        h_pos: int | None,
        l_pos: int | None,
        p_pos: int | None,
        pts_pos: int | None,
        champ: bool,
        shared: dict[str, object],
    ) -> IndividualSwim | None:
        tag, val = time_value(rec.raw(t_pos, 8))
        if tag == "blank":
            return None
        status = ResultStatus.OK
        time: Time | None = None
        if tag == "status":
            assert isinstance(val, ResultStatus)
            status = val
        elif tag == "bad":
            self._warn(
                rec,
                f"{session.name.lower()}_time",
                f"{t_pos}/8",
                None,
                Severity.RECOVERED,
                IssueKind.MALFORMED,
                "malformed time",
            )
            return None
        else:
            assert isinstance(val, Time)
            time = val
            ctag, _cv = course_value(rec.raw(c_pos, 1))
            if ctag == "dq":
                status = ResultStatus.DQ
            elif ctag == "blank":
                self._warn(
                    rec,
                    "course",
                    f"{c_pos}/1",
                    "*",
                    Severity.RECOVERED,
                    IssueKind.MISSING,
                    "course required when time present",
                )
            elif ctag == "unknown":
                self._warn(
                    rec,
                    "course",
                    f"{c_pos}/1",
                    "*",
                    Severity.RECOVERED,
                    IssueKind.UNKNOWN_CODE,
                    "unknown course code",
                )
        rank = (
            self._place(rec, p_pos, f"{session.name.lower()}_place", f"{p_pos}/3", champ)
            if p_pos is not None
            else None
        )
        points = None
        if pts_pos is not None:
            _, points = decimal_value(rec.raw(pts_pos, 4))
        return IndividualSwim(
            session=session,
            status=status,
            time=time,
            heat=self._opt_int(rec, h_pos, 2) if h_pos else None,
            lane=self._opt_int(rec, l_pos, 2) if l_pos else None,
            rank=rank,
            points=points,
            **shared,  # type: ignore[arg-type]
        )

    def _event_course(
        self, rec: Record, positions: list[int], default: Course | None
    ) -> Course | None:
        for pos in positions:
            tag, course = course_value(rec.raw(pos, 1))
            if tag == "ok":
                return course
        return default

    def _opt_time(self, rec: Record, start: int) -> Time | None:
        tag, val = time_value(rec.raw(start, 8))
        return val if tag == "time" and isinstance(val, Time) else None

    def _opt_course(self, rec: Record, start: int) -> Course | None:
        tag, val = course_value(rec.raw(start, 1))
        return val if tag == "ok" else None

    def _h_d1(self, rec: Record) -> None:
        st = self.state
        if st is None or st.current_swimmer is None:
            self._warn(
                rec,
                None,
                None,
                None,
                Severity.SKIPPED,
                IssueKind.ORPHANED,
                "D1 with no current swimmer",
            )
            return
        sw = st.current_swimmer
        self._update_contact(sw, phone_primary=rec.text(125, 12), phone_secondary=rec.text(137, 12))
        self._update_registration(
            sw,
            member_status=self._code(rec, 157, 1, MemberStatus, "member_status", "157/1", None),
            registration_date=self._date(rec, 149, 8, "registration_date", "149/8", None),
            old_member_number=rec.text(105, 20),
            admin_info=rec.text(75, 30),
        )

    def _h_d2(self, rec: Record) -> None:
        st = self.state
        if st is None or st.current_swimmer is None:
            self._warn(
                rec,
                None,
                None,
                None,
                Severity.SKIPPED,
                IssueKind.ORPHANED,
                "D2 with no current swimmer",
            )
            return
        sw = st.current_swimmer
        self._update_contact(
            sw,
            address=rec.text(77, 30),
            city=rec.text(107, 20),
            state=self._code(rec, 127, 2, State, "state", "127/2", None),
            postal_code=rec.text(141, 10),
            country=self._code(rec, 151, 3, Country, "country", "151/3", None),
            region=self._code(rec, 154, 1, Region, "region", "154/1", None),
            alt_mailing_name=rec.text(47, 30),
        )
        self._update_registration(
            sw,
            season=self._code(rec, 156, 1, Season, "season", "156/1", None),
            fina_other_federation=rec.text(155, 1),
        )

    def _h_d3(self, rec: Record) -> None:
        st = self.state
        if st is None or st.current_swimmer is None:
            self._warn(
                rec,
                None,
                None,
                None,
                Severity.SKIPPED,
                IssueKind.ORPHANED,
                "D3 with no current swimmer",
            )
            return
        sw = st.current_swimmer
        id_long = normalize_id(rec.raw(3, 14))
        preferred = rec.text(17, 15)
        if id_long is not None and sw.id_long is None:
            sw.id_long = id_long
        if preferred is not None:
            sw.preferred_first_name = preferred

        eth = rec.raw(32, 2)
        affiliations = frozenset(
            aff
            for col, aff in _AFFILIATION_COLUMNS
            if rec.raw(col, 1).strip().upper() in ("Y", "T", "1")
        )
        self._update_registration(
            sw,
            ethnicity_primary=self._eth(eth[0:1]),
            ethnicity_secondary=self._eth(eth[1:2]),
            affiliations=affiliations if affiliations else None,
        )

        # If this D3 supplies the identity for a deferred (blank-id) D0, commit now;
        # otherwise just make the long id resolvable for an already-registered swimmer.
        pending = st.pending_individual
        if pending is not None and pending.swimmer is sw and sw.id_long is not None:
            st.pending_individual = None
            st.current_swimmer = self._register_swimmer(sw, pending.results)
        elif id_long is not None:
            st.swimmers_by_id.setdefault(id_long, sw)

    @staticmethod
    def _eth(ch: str) -> Ethnicity | None:
        ch = ch.strip().upper()
        if not ch:
            return None
        try:
            return Ethnicity(ch)
        except ValueError:
            return None

    def _h_e0(self, rec: Record) -> None:
        st = self.state
        if st is None:
            self._warn(
                rec,
                None,
                None,
                None,
                Severity.SKIPPED,
                IssueKind.ORPHANED,
                "E0 with no preceding B1 meet",
            )
            return
        self._commit_pending()
        org = self._code(rec, 3, 1, Organization, "organization", "3/1", "M2") or Organization.USS
        relay_letter = self._require_text(rec, 12, 1, "relay_letter", "12/1")
        esex = code_value(rec.raw(21, 1), Sex)[1]
        dist = int_value(rec.raw(22, 4))[1]
        stroke = code_value(rec.raw(26, 1), Stroke)[1]
        eage_tag, emin, emax = event_age_value(rec.raw(31, 4))
        date_of_swim = self._date(rec, 38, 8, "date", "38/8", "M2")
        # Unresolvable relay event -> skip record (lenient) / raise (strict), not fatal.
        course = self._event_course(rec, [81, 63, 72, 54], st.meet.course)
        event = (
            Event.find(dist, stroke, course)
            if dist is not None
            and stroke is not None
            and esex is not None
            and eage_tag != "bad"
            and course is not None
            else None
        )
        if event is None:
            self._warn(
                rec,
                "event",
                "22/4",
                "M1",
                Severity.SKIPPED,
                IssueKind.UNKNOWN_CODE,
                f"unresolvable relay event (distance={rec.raw(22, 4).strip()!r} "
                f"stroke={rec.raw(26, 1).strip()!r} course={course})",
            )
            st.current_relays = {}
            st.current_relay_legs = {}
            st.last_leaf = None
            return
        assert esex is not None

        seed_t = self._opt_time(rec, 46)
        seed_c = self._opt_course(rec, 54)
        min_tc, max_tc = self._time_classes(rec, 100)
        total_age = self._opt_int(rec, 35, 3)
        champ = st.meet.meet_type in _CHAMPIONSHIP
        shared: dict[str, object] = dict(
            meet=st.meet,
            club=None if st.unattached else st.current_club,
            organization=org,
            event=event,
            event_min_age=emin,
            event_max_age=emax,
            event_sex=esex,
            event_number=rec.text(27, 4),
            date=date_of_swim,
            seed_time=seed_t,
            seed_course=seed_c,
            event_min_time_class=min_tc,
            event_max_time_class=max_tc,
        )
        st.current_relays = {}
        specs = [
            (Session.PRELIMS, 55, 63, 82, 84, 90, None),
            (Session.SWIM_OFFS, 64, 72, None, None, None, None),
            (Session.FINALS, 73, 81, 86, 88, 93, 96),
        ]
        for session, t_pos, c_pos, h_pos, l_pos, p_pos, pts_pos in specs:
            relay = self._relay_session(
                rec,
                session,
                t_pos,
                c_pos,
                h_pos,
                l_pos,
                p_pos,
                pts_pos,
                champ,
                relay_letter,
                total_age,
                shared,
            )
            if relay is not None:
                st.current_relays[session] = relay
        st.current_relay_legs = {}
        st.last_leaf = "relay"

    def _relay_session(
        self,
        rec: Record,
        session: Session,
        t_pos: int,
        c_pos: int,
        h_pos: int | None,
        l_pos: int | None,
        p_pos: int | None,
        pts_pos: int | None,
        champ: bool,
        relay_letter: str,
        total_age: int | None,
        shared: dict[str, object],
    ) -> Relay | None:
        tag, val = time_value(rec.raw(t_pos, 8))
        if tag == "blank":
            return None
        status = ResultStatus.OK
        time: Time | None = None
        if tag == "status":
            assert isinstance(val, ResultStatus)
            status = val
        elif tag == "bad":
            self._warn(
                rec,
                f"{session.name.lower()}_time",
                f"{t_pos}/8",
                None,
                Severity.RECOVERED,
                IssueKind.MALFORMED,
                "malformed relay time",
            )
            return None
        else:
            assert isinstance(val, Time)
            time = val
            ctag, _cv = course_value(rec.raw(c_pos, 1))
            if ctag == "dq":
                status = ResultStatus.DQ
            elif ctag == "blank":
                self._warn(
                    rec,
                    "course",
                    f"{c_pos}/1",
                    "*",
                    Severity.RECOVERED,
                    IssueKind.MISSING,
                    "course required when relay time present",
                )
            elif ctag == "unknown":
                self._warn(
                    rec,
                    "course",
                    f"{c_pos}/1",
                    "*",
                    Severity.RECOVERED,
                    IssueKind.UNKNOWN_CODE,
                    "unknown course code",
                )
        rank = (
            self._place(rec, p_pos, f"{session.name.lower()}_place", f"{p_pos}/3", champ)
            if p_pos is not None
            else None
        )
        points = None
        if pts_pos is not None:
            _, points = decimal_value(rec.raw(pts_pos, 4))
        st = self.state
        assert st is not None
        relay = Relay(
            session=session,
            status=status,
            time=time,
            relay_letter=relay_letter,
            total_age=total_age,
            heat=self._opt_int(rec, h_pos, 2) if h_pos else None,
            lane=self._opt_int(rec, l_pos, 2) if l_pos else None,
            rank=rank,
            points=points,
            **shared,  # type: ignore[arg-type]
        )
        st.meet.results.append(relay)
        if relay.club is not None:
            relay.club.results.append(relay)
        self.report.relays_parsed += 1
        return relay

    def _h_f0(self, rec: Record) -> None:
        st = self.state
        if st is None or not st.current_relays:
            self._warn(
                rec,
                None,
                None,
                None,
                Severity.SKIPPED,
                IssueKind.ORPHANED,
                "F0 relay name with no preceding E0 relay event",
            )
            return
        last, first, middle = parse_name(self._require_text(rec, 23, 28, "swimmer_name", "23/28"))
        sex = self._require_code(rec, 76, 1, Sex, "sex", "76/1")
        id_short = normalize_id(rec.raw(51, 12))
        id_long = normalize_id(rec.raw(93, 14))
        citizenship = self._citizenship(rec, 63, 3)
        birthday = self._date(rec, 66, 8, "birthday", "66/8", "M2")
        age_class = rec.text(74, 2)
        preferred = rec.text(107, 15)

        swimmer = self._resolve_relay_swimmer(
            rec,
            id_short,
            id_long,
            first=first,
            last=last,
            middle=middle,
            sex=sex,
            birthday=birthday,
            citizenship=citizenship,
            preferred=preferred,
        )
        if swimmer is None:
            self._warn(
                rec,
                "id_short",
                "51/12",
                "M2",
                Severity.RECOVERED,
                IssueKind.MISSING,
                "relay swimmer has no USS#; leg kept with swimmer=None",
            )

        leg_time = self._opt_time(rec, 80)
        leg_course = self._opt_course(rec, 88)
        tk_tag, tk = decimal_value(rec.raw(89, 4))
        takeoff = round(tk * 100) if tk is not None else None

        created: dict[Session, RelaySwim] = {}
        for session, order_pos in _RELAY_LEG_SESSIONS:
            order = self._code(rec, order_pos, 1, RelayLegOrder, "order", f"{order_pos}/1", None)
            if order is None or order is RelayLegOrder.NOT_SWUM:
                continue
            relay = st.current_relays.get(session)
            if relay is None:
                continue
            leg = RelaySwim(
                swimmer=swimmer,
                relay=relay,
                order=order,
                status=relay.status,
                swimmer_age_class=age_class,
                citizenship=citizenship,
            )
            if order is RelayLegOrder.ALTERNATE:
                relay.alternates.append(leg)
            else:
                relay.legs.append(leg)
                if swimmer is not None:
                    swimmer.swims.append(leg)
            created[session] = leg

        # The F0 carries one leg time/course/takeoff — file it on the finals leg.
        if created:
            target = created.get(Session.FINALS) or next(iter(created.values()))
            target.time = leg_time
            target.course = leg_course
            target.takeoff_time = takeoff

        st.current_relay_legs = created
        st.current_swimmer = swimmer
        st.last_leaf = "relay"

    def _h_g0(self, rec: Record) -> None:
        st = self.state
        if st is None:
            self._warn(
                rec,
                None,
                None,
                None,
                Severity.SKIPPED,
                IssueKind.ORPHANED,
                "G0 splits with no preceding swim",
            )
            return
        seq = self._require_int(rec, 56, 1, "sequence_number", "56/1")
        if seq < 1:
            # Sequence is 1-based; a 0/negative value would yield negative split
            # distances. Recover by treating it as the first record.
            self._warn(
                rec,
                "sequence_number",
                "56/1",
                "M1",
                Severity.RECOVERED,
                IssueKind.MALFORMED,
                f"sequence number {seq} < 1; treated as 1",
            )
            seq = 1
        increment = self._require_int(rec, 59, 4, "split_distance", "59/4")
        split_type = self._require_code(rec, 63, 1, SplitType, "split_type", "63/1")
        session = self._code(rec, 144, 1, Session, "session", "144/1", None)

        target_splits = self._g0_target(rec, session)
        if target_splits is None:
            self._warn(
                rec,
                None,
                None,
                None,
                Severity.SKIPPED,
                IssueKind.ORPHANED,
                "G0 splits could not be attached to a swim",
            )
            return
        base = (seq - 1) * 10
        for j in range(10):
            start = 64 + j * 8
            tag, val = time_value(rec.raw(start, 8))
            if tag == "blank":
                # Skip an empty slot rather than stopping: a blank early split
                # followed by a recorded later split (e.g. only the final
                # cumulative time present) must not discard that real time.
                continue
            distance = increment * (base + j + 1)
            if tag == "bad":
                self._warn(
                    rec,
                    "split_time",
                    f"{start}/8",
                    None,
                    Severity.RECOVERED,
                    IssueKind.MALFORMED,
                    "malformed split time",
                )
                target_splits.append(Split(distance=distance, time=None, split_type=split_type))
            else:
                assert isinstance(val, Time)
                target_splits.append(Split(distance=distance, time=val, split_type=split_type))
            self.report.splits_parsed += 1

    def _require_int(self, rec: Record, start: int, length: int, field: str, column: str) -> int:
        tag, val = int_value(rec.raw(start, length))
        if tag != "int" or val is None:
            self._fatal(rec, field, column, "M1", IssueKind.MALFORMED, f"missing/malformed {field}")
        assert val is not None
        return val

    def _g0_target(self, rec: Record, session: Session | None) -> list[Split] | None:
        st = self.state
        assert st is not None
        if st.last_leaf == "relay":
            if not st.current_relay_legs:
                return None
            leg = (
                (st.current_relay_legs.get(session) if session is not None else None)
                or st.current_relay_legs.get(Session.FINALS)
                or next(iter(st.current_relay_legs.values()))
            )
            return leg.splits
        if st.last_leaf == "individual":
            if not st.current_individual_swims:
                return None
            for r in st.current_individual_swims:
                if session is not None and r.session is session:
                    return r.splits
            return st.current_individual_swims[0].splits
        return None

    def _h_z0(self, rec: Record) -> None:
        self._commit_pending()
        notes = rec.text(14, 30)
        if notes is not None and self.source_file is not None:
            self.source_file = replace(self.source_file, notes=notes)
            for meet in self.meets:
                if meet.source_file is not None and meet.source_file.path == self.source_file.path:
                    meet.source_file = self.source_file
        self._z0_counts(rec)
        self.state = None

    def _z0_counts(self, rec: Record) -> None:
        actual_by_letter: Counter[str] = Counter()
        for rt, n in self.file_counts.items():
            actual_by_letter[rt[0]] += n
        checks = [
            ("44/3", 44, 3, actual_by_letter["B"], "B records"),
            ("47/3", 47, 3, self.meets_this_file, "meets"),
            ("50/4", 50, 4, actual_by_letter["C"], "C records"),
            ("58/6", 58, 6, actual_by_letter["D"], "D records"),
            ("70/5", 70, 5, actual_by_letter["E"], "E records"),
            ("75/6", 75, 6, actual_by_letter["F"], "F records"),
            ("81/6", 81, 6, actual_by_letter["G"], "G records"),
        ]
        for column, start, length, actual, label in checks:
            tag, declared = int_value(rec.raw(start, length))
            if tag == "int" and declared != actual:
                self._warn(
                    rec,
                    label,
                    column,
                    None,
                    Severity.RECOVERED,
                    IssueKind.COUNT_MISMATCH,
                    f"Z0 declares {declared} {label} but parsed {actual}",
                )


# Dispatch table — every modeled record type.
_HANDLERS: dict[str, Callable[[_Engine, Record], None]] = {
    "A0": _Engine._h_a0,
    "B1": _Engine._h_b1,
    "B2": _Engine._h_b2,
    "C1": _Engine._h_c1,
    "C2": _Engine._h_c2,
    "D0": _Engine._h_d0,
    "D1": _Engine._h_d1,
    "D2": _Engine._h_d2,
    "D3": _Engine._h_d3,
    "E0": _Engine._h_e0,
    "F0": _Engine._h_f0,
    "G0": _Engine._h_g0,
    "Z0": _Engine._h_z0,
}
