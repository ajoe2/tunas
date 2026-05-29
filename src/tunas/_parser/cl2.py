"""SDIF (`.cl2`) parse engine: dispatches record types and assembles the object graph."""

from __future__ import annotations

import datetime
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import ClassVar, TypedDict

from tunas._parser.diagnostics import IssueKind, Severity
from tunas._parser.engine import _BaseEngine
from tunas._parser.fields import (
    RECORD_WIDTH,
    Record,
    code_value,
    course_value,
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
from tunas.geography import LSC, Country, State
from tunas.models import (
    CitizenshipOrCountry,
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
# A D3 affiliation flag counts as set when its byte is one of these.
_AFFIRMATIVE = {"Y", "T", "1"}

# COURSE-byte columns tried in priority order, falling back to the meet's course.
_D0_COURSE_COLS = [124, 106, 115, 97]
_E0_COURSE_COLS = [81, 63, 72, 54]

# G0 split layout: ten 8-char split-time slots starting at column 64.
_SPLITS_PER_RECORD = 10
_SPLIT_WIDTH = 8
_FIRST_SPLIT_COL = 64


@dataclass(frozen=True)
class SessionColumns:
    """1-indexed start columns for one session's result fields on a D0/E0 record."""

    session: Session
    time: int
    course: int
    heat: int | None
    lane: int | None
    place: int | None
    points: int | None


# Per-session result columns for the three sessions on a D0 (individual) record.
_INDIVIDUAL_SESSIONS = (
    SessionColumns(
        Session.PRELIMS, time=98, course=106, heat=125, lane=127, place=133, points=None
    ),
    SessionColumns(
        Session.SWIM_OFFS, time=107, course=115, heat=None, lane=None, place=None, points=None
    ),
    SessionColumns(Session.FINALS, time=116, course=124, heat=129, lane=131, place=136, points=139),
)
# ...and on an E0 (relay) record.
_RELAY_SESSIONS = (
    SessionColumns(Session.PRELIMS, time=55, course=63, heat=82, lane=84, place=90, points=None),
    SessionColumns(
        Session.SWIM_OFFS, time=64, course=72, heat=None, lane=None, place=None, points=None
    ),
    SessionColumns(Session.FINALS, time=73, course=81, heat=86, lane=88, place=93, points=96),
)


@dataclass(frozen=True)
class _SessionResult:
    """Result fields parsed from one session column-group, before model assembly."""

    session: Session
    status: ResultStatus
    time: Time | None
    heat: int | None
    lane: int | None
    rank: int | None
    points: float | None


class _CommonResultFields(TypedDict):
    """The ``MeetResult`` fields shared by an individual swim and a relay."""

    meet: Meet
    club: Club | None
    organization: Organization | None
    event: Event
    event_min_age: int | None
    event_max_age: int | None
    event_sex: Sex
    event_number: str | None
    date: datetime.date | None
    seed_time: Time | None
    seed_course: Course | None
    event_min_time_class: EventTimeClass | None
    event_max_time_class: EventTimeClass | None


@dataclass(frozen=True)
class _Z0Check:
    """One Z0 declared-vs-parsed count check. ``letter`` is the record-type letter
    to tally, or ``None`` for the meet count."""

    column: str
    start: int
    length: int
    letter: str | None
    label: str


_Z0_CHECKS = (
    _Z0Check("44/3", 44, 3, "B", "B records"),
    _Z0Check("47/3", 47, 3, None, "meets"),
    _Z0Check("50/4", 50, 4, "C", "C records"),
    _Z0Check("58/6", 58, 6, "D", "D records"),
    _Z0Check("70/5", 70, 5, "E", "E records"),
    _Z0Check("75/6", 75, 6, "F", "F records"),
    _Z0Check("81/6", 81, 6, "G", "G records"),
)


class _Cl2Engine(_BaseEngine):
    """Stateful SDIF parser. ``parse_source`` resets per-file state, so one instance
    can parse many files in turn (each call yields only that source's results)."""

    RECORD_WIDTH: ClassVar[int] = RECORD_WIDTH
    READER: ClassVar[str] = "read_cl2"

    def __init__(self, *, strict: bool) -> None:
        super().__init__(strict=strict)
        self.state: ParserState | None = None

    # -- per-file hooks ---------------------------------------------------- #

    def _reset_state(self) -> None:
        self.state = None

    def _finish_file(self) -> None:
        self._commit_pending()

    def _feed(self, raw: str, line_no: int) -> None:
        line = raw.rstrip("\r\n")
        if not line.strip():
            return
        rec = self._sized_record(line, line_no)
        if rec is None:
            return
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

    # -- typed field helpers (cl2-specific) -------------------------------- #

    def _time_classes(
        self, rec: Record, start: int
    ) -> tuple[EventTimeClass | None, EventTimeClass | None]:
        raw = rec.raw(start, 2)

        def parse_class(ch: str) -> EventTimeClass | None:
            ch = ch.strip().upper()
            if ch in ("", "U", "O"):  # blank / no-lower / no-upper
                return None
            try:
                return EventTimeClass(ch)
            except ValueError:
                return None

        return parse_class(raw[0:1]), parse_class(raw[1:2])

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
            self._attach_swimmer(st.meet, target)
        else:
            self._merge_swimmer(target, swimmer)
        for k in keys:
            st.swimmers_by_id.setdefault(k, target)
        for r in results:
            r.swimmer = target
            target.swims.append(r)
            self._attach_result(st.meet, r)
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
        ):
            if getattr(existing, attr) is None and getattr(other, attr) is not None:
                setattr(existing, attr, getattr(other, attr))
        # Backfilling the club of a previously-unattached swimmer must also add the
        # back-reference, or the swimmer ends up on `swimmer.club` yet missing from
        # `club.swimmers` — breaking the invariant `_attach_swimmer` guarantees.
        if existing.club is None and other.club is not None:
            existing.club = other.club
            other.club.swimmers.append(existing)

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
        citizenship: CitizenshipOrCountry | None,
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
            club=st.attached_club,
        )
        self._attach_swimmer(st.meet, swimmer)
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
        org = self._code(rec, 3, 1, Organization, "organization", "3/1", "M2")
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

    def _m2_code[E: StrEnum](
        self, rec: Record, start: int, length: int, enum_cls: type[E], field: str, column: str
    ) -> E | None:
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
        org = self._code(rec, 3, 1, Organization, "organization", "3/1", "M2")
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
            self._skip_orphan(rec, "D0 with no preceding B1 meet")
            return
        org = self._code(rec, 3, 1, Organization, "organization", "3/1", "M2")
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
        event_fields_present = [
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
            club=st.attached_club,
        )

        results: list[IndividualSwim] = []
        if any(event_fields_present):
            # Any invalid/partial/unresolvable event field means we cannot model the
            # swim — skip the whole record (lenient) / raise (strict). This is NOT a
            # fatal M1: one bad/odd record (e.g. a diving event with stroke "H") must
            # not abort an otherwise-valid file.
            course = self._event_course(rec, _D0_COURSE_COLS, st.meet.course)
            event = self._resolve_event(
                rec,
                distance=dist,
                stroke=stroke,
                sex=esex,
                course=course,
                field="event",
                column="67/1",
                mandatory="M1#",
                noun="event",
                distance_display=repr(rec.raw(68, 4).strip()),
                stroke_display=repr(rec.raw(72, 1).strip()),
                extra_ok=all(event_fields_present) and eage_tag != "bad",
            )
            if event is None:
                st.current_individual_swims = []
                st.current_swimmer = None
                st.last_result_kind = None
                return
            assert esex is not None
            min_tc, max_tc = self._time_classes(rec, 143)
            champ = st.meet.meet_type in _CHAMPIONSHIP
            common: _CommonResultFields = {
                "meet": st.meet,
                "club": st.attached_club,
                "organization": org,
                "event": event,
                "event_min_age": emin,
                "event_max_age": emax,
                "event_sex": esex,
                "event_number": rec.text(73, 4),
                "date": date_of_swim,
                "seed_time": self._opt_time(rec, 89),
                "seed_course": self._opt_course(rec, 97),
                "event_min_time_class": min_tc,
                "event_max_time_class": max_tc,
            }
            for cols in _INDIVIDUAL_SESSIONS:
                sr = self._parse_session(rec, cols, champ, "time")
                if sr is None:
                    continue
                results.append(
                    IndividualSwim(
                        session=sr.session,
                        status=sr.status,
                        time=sr.time,
                        heat=sr.heat,
                        lane=sr.lane,
                        rank=sr.rank,
                        points=sr.points,
                        swimmer=swimmer,
                        swimmer_age_class=age_class,
                        attach_status=attach_status,
                        **common,
                    )
                )

        if id_short:
            target = self._register_swimmer(swimmer, results)
            st.current_swimmer = target
        else:
            st.pending_individual = PendingIndividual(swimmer, results, rec.line, rec.line_no)
            st.current_swimmer = swimmer
        st.current_individual_swims = results
        st.last_result_kind = "individual"

    def _parse_session(
        self, rec: Record, cols: SessionColumns, champ: bool, noun: str
    ) -> _SessionResult | None:
        """Parse one session's shared result fields, or ``None`` for a blank/bad time.

        Used for both individual swims and relays; ``noun`` ("time" / "relay time")
        only tunes the warning text so the two callers read identically.
        """
        tag, val = time_value(rec.raw(cols.time, 8))
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
                f"{cols.session.name.lower()}_time",
                f"{cols.time}/8",
                None,
                Severity.RECOVERED,
                IssueKind.MALFORMED,
                f"malformed {noun}",
            )
            return None
        else:
            assert isinstance(val, Time)
            time = val
            ctag, _cv = course_value(rec.raw(cols.course, 1))
            if ctag == "dq":
                status = ResultStatus.DQ
            elif ctag == "blank":
                self._warn(
                    rec,
                    "course",
                    f"{cols.course}/1",
                    "*",
                    Severity.RECOVERED,
                    IssueKind.MISSING,
                    f"course required when {noun} present",
                )
            elif ctag == "unknown":
                self._warn(
                    rec,
                    "course",
                    f"{cols.course}/1",
                    "*",
                    Severity.RECOVERED,
                    IssueKind.UNKNOWN_CODE,
                    "unknown course code",
                )
        rank = (
            self._place(
                rec, cols.place, f"{cols.session.name.lower()}_place", f"{cols.place}/3", champ
            )
            if cols.place is not None
            else None
        )
        points = None
        if cols.points is not None:
            _, points = decimal_value(rec.raw(cols.points, 4))
        return _SessionResult(
            session=cols.session,
            status=status,
            time=time,
            heat=self._opt_int(rec, cols.heat, 2) if cols.heat else None,
            lane=self._opt_int(rec, cols.lane, 2) if cols.lane else None,
            rank=rank,
            points=points,
        )

    def _event_course(
        self, rec: Record, positions: list[int], default: Course | None
    ) -> Course | None:
        for pos in positions:
            tag, course = course_value(rec.raw(pos, 1))
            if tag == "ok":
                return course
        return default

    def _h_d1(self, rec: Record) -> None:
        st = self.state
        if st is None or st.current_swimmer is None:
            self._skip_orphan(rec, "D1 with no current swimmer")
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
            self._skip_orphan(rec, "D2 with no current swimmer")
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
            self._skip_orphan(rec, "D3 with no current swimmer")
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
            if rec.raw(col, 1).strip().upper() in _AFFIRMATIVE
        )
        self._update_registration(
            sw,
            ethnicity_primary=self._ethnicity(eth[0:1]),
            ethnicity_secondary=self._ethnicity(eth[1:2]),
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
    def _ethnicity(ch: str) -> Ethnicity | None:
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
            self._skip_orphan(rec, "E0 with no preceding B1 meet")
            return
        self._commit_pending()
        org = self._code(rec, 3, 1, Organization, "organization", "3/1", "M2")
        relay_letter = self._require_text(rec, 12, 1, "relay_letter", "12/1")
        esex = code_value(rec.raw(21, 1), Sex)[1]
        dist = int_value(rec.raw(22, 4))[1]
        stroke = code_value(rec.raw(26, 1), Stroke)[1]
        eage_tag, emin, emax = event_age_value(rec.raw(31, 4))
        date_of_swim = self._date(rec, 38, 8, "date", "38/8", "M2")
        # Unresolvable relay event -> skip record (lenient) / raise (strict), not fatal.
        course = self._event_course(rec, _E0_COURSE_COLS, st.meet.course)
        event = self._resolve_event(
            rec,
            distance=dist,
            stroke=stroke,
            sex=esex,
            course=course,
            field="event",
            column="22/4",
            mandatory="M1",
            noun="relay event",
            distance_display=repr(rec.raw(22, 4).strip()),
            stroke_display=repr(rec.raw(26, 1).strip()),
            extra_ok=eage_tag != "bad",
        )
        if event is None:
            st.current_relays = {}
            st.current_relay_legs = {}
            st.last_result_kind = None
            return
        assert esex is not None

        min_tc, max_tc = self._time_classes(rec, 100)
        total_age = self._opt_int(rec, 35, 3)
        champ = st.meet.meet_type in _CHAMPIONSHIP
        common: _CommonResultFields = {
            "meet": st.meet,
            "club": st.attached_club,
            "organization": org,
            "event": event,
            "event_min_age": emin,
            "event_max_age": emax,
            "event_sex": esex,
            "event_number": rec.text(27, 4),
            "date": date_of_swim,
            "seed_time": self._opt_time(rec, 46),
            "seed_course": self._opt_course(rec, 54),
            "event_min_time_class": min_tc,
            "event_max_time_class": max_tc,
        }
        st.current_relays = {}
        for cols in _RELAY_SESSIONS:
            sr = self._parse_session(rec, cols, champ, "relay time")
            if sr is None:
                continue
            relay = Relay(
                session=sr.session,
                status=sr.status,
                time=sr.time,
                relay_letter=relay_letter,
                total_age=total_age,
                heat=sr.heat,
                lane=sr.lane,
                rank=sr.rank,
                points=sr.points,
                **common,
            )
            self._attach_result(st.meet, relay)
            self.report.relays_parsed += 1
            st.current_relays[sr.session] = relay
        st.current_relay_legs = {}
        st.last_result_kind = "relay"

    def _h_f0(self, rec: Record) -> None:
        st = self.state
        if st is None or not st.current_relays:
            self._skip_orphan(rec, "F0 relay name with no preceding E0 relay event")
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
        st.last_result_kind = "relay"

    def _h_g0(self, rec: Record) -> None:
        st = self.state
        if st is None:
            self._skip_orphan(rec, "G0 splits with no preceding swim")
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
            self._skip_orphan(rec, "G0 splits could not be attached to a swim")
            return
        is_relay = st.last_result_kind == "relay"
        base = (seq - 1) * _SPLITS_PER_RECORD
        for j in range(_SPLITS_PER_RECORD):
            start = _FIRST_SPLIT_COL + j * _SPLIT_WIDTH
            tag, val = time_value(rec.raw(start, _SPLIT_WIDTH))
            if tag == "blank":
                # Skip an empty slot rather than stopping: a blank early split
                # followed by a recorded later split (e.g. only the final
                # cumulative time present) must not discard that real time.
                continue
            if is_relay:
                # Relay G0s carry whole-relay cumulative splits spread across the
                # successive per-leg records; each leg's record restarts at slot 0,
                # so the relay position is the running count of splits already on
                # the relay row, not the per-record slot index. This yields
                # 50/100/150/200 (and beyond for longer relays) instead of every
                # leg's split collapsing to the same distance.
                distance = increment * (len(target_splits) + 1)
            else:
                distance = increment * (base + j + 1)
            self._append_split(
                rec, target_splits, distance, tag, val, split_type, column=f"{start}/8"
            )

    def _g0_target(self, rec: Record, session: Session | None) -> list[Split] | None:
        st = self.state
        assert st is not None
        if st.last_result_kind == "relay":
            if not st.current_relays:
                return None
            # Whole-relay cumulative splits belong on the relay row (matching the
            # `.hy3` reader and `Relay.splits` semantics), not on an individual
            # leg. Attaching here also rescues relays whose G0s follow the E0
            # directly with no F0 leg records (which would otherwise be orphaned).
            relay = (
                (st.current_relays.get(session) if session is not None else None)
                or st.current_relays.get(Session.FINALS)
                or next(iter(st.current_relays.values()))
            )
            return relay.splits
        if st.last_result_kind == "individual":
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
        for chk in _Z0_CHECKS:
            actual = self.meets_this_file if chk.letter is None else actual_by_letter[chk.letter]
            tag, declared = int_value(rec.raw(chk.start, chk.length))
            if tag == "int" and declared != actual:
                self._warn(
                    rec,
                    chk.label,
                    chk.column,
                    None,
                    Severity.RECOVERED,
                    IssueKind.COUNT_MISMATCH,
                    f"Z0 declares {declared} {chk.label} but parsed {actual}",
                )


# Dispatch table — every modeled record type.
_HANDLERS: dict[str, Callable[[_Cl2Engine, Record], None]] = {
    "A0": _Cl2Engine._h_a0,
    "B1": _Cl2Engine._h_b1,
    "B2": _Cl2Engine._h_b2,
    "C1": _Cl2Engine._h_c1,
    "C2": _Cl2Engine._h_c2,
    "D0": _Cl2Engine._h_d0,
    "D1": _Cl2Engine._h_d1,
    "D2": _Cl2Engine._h_d2,
    "D3": _Cl2Engine._h_d3,
    "E0": _Cl2Engine._h_e0,
    "F0": _Cl2Engine._h_f0,
    "G0": _Cl2Engine._h_g0,
    "Z0": _Cl2Engine._h_z0,
}
