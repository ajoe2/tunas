"""Hy-Tek `.hy3` parse engine: assembles the same object graph as the SDIF reader.

Only fields confirmed by the reverse-engineered `.hy3` specification are parsed
(see ``docs/formats/hy3_format.md``). Unlike SDIF — which packs an athlete, their
entry, and their result into one `D0` — `.hy3` splits these across `D1` / `E1` /
`E2` records, so each entry (`E1`/`F1`) is buffered until its result (`E2`/`F2`).
"""

from __future__ import annotations

import datetime
from collections.abc import Callable
from typing import ClassVar

from tunas._parser.checksum import RECORD_WIDTH as HY3_RECORD_WIDTH
from tunas._parser.diagnostics import IssueKind, Severity
from tunas._parser.engine import _BaseEngine
from tunas._parser.fields import Record, time_value
from tunas._parser.ids import normalize_id
from tunas._parser.state import Hy3Entry, Hy3RelayEntry, Hy3State
from tunas.enums import (
    Hy3FileType,
    Organization,
    RelayLegOrder,
    ResultStatus,
    Session,
    Sex,
    SplitType,
    Stroke,
)
from tunas.geography import LSC
from tunas.models import (
    Club,
    IndividualSwim,
    Meet,
    MeetResult,
    Relay,
    RelaySwim,
    SourceFile,
    Split,
    Swimmer,
)
from tunas.time import Time

# Hy-Tek stroke letter (E1/F1 col 22) -> SDIF Stroke. Diving (F/G) maps nowhere,
# so those events stay unresolvable and are skipped like any non-swim event.
_STROKE: dict[str, Stroke] = {
    "A": Stroke.FREESTYLE,
    "B": Stroke.BACKSTROKE,
    "C": Stroke.BREASTSTROKE,
    "D": Stroke.BUTTERFLY,
    "E": Stroke.INDIVIDUAL_MEDLEY,
}
_RELAY_STROKE: dict[str, Stroke] = {"A": Stroke.FREESTYLE_RELAY, "E": Stroke.MEDLEY_RELAY}

# Hy-Tek event-sex letter (E1/F1 col 15) -> SDIF Sex.
_EVENT_SEX: dict[str, Sex] = {
    "W": Sex.FEMALE,  # Women
    "G": Sex.FEMALE,  # Girls
    "M": Sex.MALE,  # Men
    "B": Sex.MALE,  # Boys
    "X": Sex.MIXED,
}

# E2/F2 result-status flag (col 13) -> (status, time_is_valid). A blank flag is a
# normal finish. DNF/NS/scratch carry no time; DQ and exhibition retain theirs.
_STATUS: dict[str, tuple[ResultStatus, bool]] = {
    "": (ResultStatus.OK, True),
    "Q": (ResultStatus.DQ, True),
    "D": (ResultStatus.DNF, False),
    "F": (ResultStatus.NS, False),
    "R": (ResultStatus.SCR, False),
    "S": (ResultStatus.EXHIBITION, True),
}

# F3 leg/slot character (slot offset 13) -> leg order; others are alternates.
_LEG_ORDER: dict[str, RelayLegOrder] = {
    "1": RelayLegOrder.LEG_1,
    "2": RelayLegOrder.LEG_2,
    "3": RelayLegOrder.LEG_3,
    "4": RelayLegOrder.LEG_4,
}

# Known record types carrying no confirmed field that maps to the model: the
# team mailing address (all inferred) and the rare undocumented team block.
_IGNORED = {"C2", "C8"}

# Backup/watch-time start columns on E2/F2 (each 7 wide).
_BACKUP_COLS = (38, 46, 54)

# E1/F1 event age range (min cols 23-25, max 26-28). Open-ended groups use
# sentinels that map to None, matching how `.cl2` represents an open bound.
_AGE_OPEN_LOW = 0  # "& Under" — no lower bound
_AGE_OPEN_HIGH = 109  # "& Over" — no upper bound

# G1 split layout: up to eleven 11-char blocks starting at column 3.
_SPLITS_PER_RECORD = 11
_SPLIT_WIDTH = 11
_FIRST_SPLIT_COL = 3
# F3 athlete layout: up to eight 13-char slots starting at column 3.
_SLOTS_PER_RECORD = 8
_SLOT_WIDTH = 13
_FIRST_SLOT_COL = 3


class _Hy3Engine(_BaseEngine):
    """Stateful Hy-Tek parser. One instance per ``read_hy3`` call, reused across files."""

    RECORD_WIDTH: ClassVar[int] = HY3_RECORD_WIDTH
    READER: ClassVar[str] = "read_hy3"

    def __init__(self, *, strict: bool) -> None:
        super().__init__(strict=strict)
        self.state: Hy3State | None = None

    # -- per-file hooks ---------------------------------------------------- #

    def _reset_state(self) -> None:
        self.state = None

    def _feed(self, raw: str, line_no: int) -> None:
        line = raw.rstrip("\r\n")
        if not line.strip():
            return
        rec = self._sized_record(line, line_no)
        if rec is None:
            return
        self.file_counts[rec.type] += 1

        # Columns 129-130 hold a checksum that we don't validate: it isn't a data
        # field, and `USAS Club Times Export` files omit it entirely. Field slicing
        # only ever touches columns 1-128, so the trailing checksum is simply ignored.
        handler = _HANDLERS.get(rec.type)
        if handler is None:
            if rec.type not in _IGNORED:
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

    # -- hy3-specific field helpers ---------------------------------------- #

    def _hy3_time(self, rec: Record, start: int, length: int) -> Time | None:
        """A `.hy3` decimal-seconds time, treating the `0.00` "no time" sentinel as None."""
        t = self._opt_time(rec, start, length)
        return t if t is not None and t.centiseconds > 0 else None

    def _time_of_day(
        self, rec: Record, start: int, length: int, field: str, column: str
    ) -> datetime.time | None:
        """Parse a `H:MM AM/PM` clock time (A1 creation time), or None."""
        raw = rec.text(start, length)
        if raw is None:
            return None
        for fmt in ("%I:%M %p", "%H:%M"):
            try:
                return datetime.datetime.strptime(raw, fmt).time()
            except ValueError:
                continue
        self._warn(
            rec,
            field,
            column,
            None,
            Severity.RECOVERED,
            IssueKind.MALFORMED,
            f"malformed time {raw!r}",
        )
        return None

    def _event_sex(self, rec: Record, col: int) -> Sex | None:
        raw = rec.raw(col, 1).strip().upper()
        if not raw:
            return None
        sex = _EVENT_SEX.get(raw)
        if sex is None:
            self._warn(
                rec,
                "event_sex",
                f"{col}/1",
                None,
                Severity.RECOVERED,
                IssueKind.UNKNOWN_CODE,
                f"unknown event sex {raw!r}",
            )
        return sex

    @staticmethod
    def _stroke(rec: Record, col: int, table: dict[str, Stroke]) -> Stroke | None:
        return table.get(rec.raw(col, 1).strip().upper())

    def _rank(self, rec: Record, start: int, length: int) -> int | None:
        val = self._opt_int(rec, start, length)
        return val if val is not None and val > 0 else None

    def _event_age(self, rec: Record, start: int, open_sentinel: int) -> int | None:
        """Parse a 3-col event age bound; the open-ended sentinel maps to None."""
        val = self._opt_int(rec, start, 3)
        return None if val is None or val == open_sentinel else val

    def _backup_times(self, rec: Record) -> tuple[Time, ...]:
        return tuple(t for c in _BACKUP_COLS if (t := self._hy3_time(rec, c, 7)) is not None)

    def _result_status(self, rec: Record) -> tuple[ResultStatus, bool]:
        """Map the E2/F2 status flag (col 13) to ``(status, time_is_valid)``."""
        raw = rec.raw(13, 1).strip().upper()
        mapped = _STATUS.get(raw)
        if mapped is None:
            self._warn(
                rec,
                "status",
                "13/1",
                None,
                Severity.RECOVERED,
                IssueKind.UNKNOWN_CODE,
                f"unknown result status {raw!r}",
            )
            return ResultStatus.OK, True
        return mapped

    # ===================================================================== #
    # Record handlers
    # ===================================================================== #

    def _h_a1(self, rec: Record) -> None:
        self.source_file = SourceFile(
            path=self.source,
            hy3_file_type=self._code(rec, 3, 2, Hy3FileType, "hy3_file_type", "3/2", None),
            software_name=rec.text(45, 14),
            created=self._date(rec, 59, 8, "created", "59/8", None),
            created_time=self._time_of_day(rec, 68, 8, "created_time", "68/8"),
            licensee=rec.text(76, 53),
        )

    def _h_b1(self, rec: Record) -> None:
        name = self._require_text(rec, 3, 45, "name", "3/45")
        start = self._date(rec, 93, 8, "start_date", "93/8", "M1")
        if start is None:
            self._fatal(
                rec, "start_date", "93/8", "M1", IssueKind.MISSING, "missing meet start date"
            )
        meet = Meet(
            organization=Organization.USS,  # `.hy3` carries no org code; USA Swimming context
            name=name,
            start_date=start,
            end_date=self._date(rec, 101, 8, "end_date", "101/8", "M2"),
            venue=rec.text(48, 45),
            age_up_date=self._date(rec, 109, 8, "age_up_date", "109/8", None),
            altitude=self._opt_int(rec, 117, 4),
            source_file=self.source_file,
        )
        self.meets.append(meet)
        self.report.meets_parsed += 1
        self.meets_this_file += 1
        self.state = Hy3State(meet=meet)

    def _h_b2(self, rec: Record) -> None:
        st = self.state
        if st is None:
            return
        course = self._opt_course(rec, 99)
        if course is not None:
            st.meet.course = course
        sanction = rec.text(109, 8)
        if sanction is not None:
            st.meet.sanction_number = sanction

    def _h_c1(self, rec: Record) -> None:
        st = self.state
        if st is None:
            return
        abbrev = self._require_text(rec, 3, 5, "team_code", "3/5")
        name = self._require_text(rec, 8, 30, "full_team_name", "8/30")
        lsc = self._code(rec, 54, 2, LSC, "lsc", "54/2", None)
        if abbrev.upper() == "UN" or "UNATTACHED" in name.upper():
            st.unattached = True
            st.current_club = None
            return
        st.unattached = False
        key = (abbrev, lsc)
        existing = st.clubs_by_key.get(key)
        if existing is not None:
            st.current_club = existing
            return
        club = Club(
            meet=st.meet,
            organization=Organization.USS,
            team_code=abbrev,
            lsc=lsc,
            full_name=name,
        )
        st.clubs_by_key[key] = club
        st.meet.clubs.append(club)
        st.current_club = club

    def _h_c3(self, rec: Record) -> None:
        st = self.state
        if st is None or st.current_club is None:
            return
        email = rec.text(93, 30)
        if email is not None:
            st.current_club.email = email

    def _h_d1(self, rec: Record) -> None:
        st = self.state
        if st is None:
            self._skip_orphan(rec, "D1 athlete with no preceding B1 meet")
            return
        number = rec.text(4, 5)
        if number is None:
            self._warn(
                rec,
                "athlete_number",
                "4/5",
                "M1",
                Severity.SKIPPED,
                IssueKind.MISSING,
                "D1 athlete with no athlete number",
            )
            st.current_swimmer = None
            st.current_age_class = None
            st.current_individual_swim = None
            st.current_relay = None
            st.last_leaf = None
            return
        sex = self._require_code(rec, 3, 1, Sex, "sex", "3/1")
        last = self._require_text(rec, 9, 20, "last_name", "9/20")
        first = self._require_text(rec, 29, 20, "first_name", "29/20")

        swimmer = Swimmer(
            meet=st.meet,
            first_name=first,
            last_name=last,
            sex=sex,
            id_short=normalize_id(rec.raw(70, 14)),
            middle_initial=rec.text(69, 1),
            preferred_first_name=rec.text(49, 20),
            birthday=self._date(rec, 89, 8, "birthday", "89/8", "M2"),
            citizenship=self._citizenship(rec, 113, 3),
            club=st.attached_club,
        )
        self._attach_swimmer(st.meet, swimmer)
        st.swimmers_by_number[number] = swimmer
        st.current_swimmer = swimmer
        st.current_age_class = rec.text(98, 2)
        st.current_individual_swim = None
        st.current_relay = None
        st.last_leaf = None

    def _h_e1(self, rec: Record) -> None:
        st = self.state
        if st is None:
            return
        number = rec.text(4, 5)
        st.pending_entry = Hy3Entry(
            swimmer=st.swimmers_by_number.get(number) if number else None,
            event_sex=self._event_sex(rec, 15),
            distance=self._opt_int(rec, 16, 6),
            stroke=self._stroke(rec, 22, _STROKE),
            event_min_age=self._event_age(rec, 23, _AGE_OPEN_LOW),
            event_max_age=self._event_age(rec, 26, _AGE_OPEN_HIGH),
            event_number=rec.text(39, 4),
            seed_time=self._hy3_time(rec, 53, 7),
            seed_course=self._opt_course(rec, 60),
            converted_seed_time=self._hy3_time(rec, 44, 7),
            converted_seed_course=self._opt_course(rec, 51),
        )

    def _h_e2(self, rec: Record) -> None:
        st = self.state
        if st is None:
            return
        entry = st.pending_entry
        st.pending_entry = None
        if entry is None:
            self._skip_orphan(rec, "E2 result with no preceding E1 entry")
            return
        if entry.swimmer is None:
            self._skip_orphan(rec, "E2 result with no resolvable athlete")
            return

        course = self._opt_course(rec, 12)
        event = self._resolve_event(
            rec,
            distance=entry.distance,
            stroke=entry.stroke,
            sex=entry.event_sex,
            course=course,
            field="event",
            column="12/1",
            mandatory="M1#",
            noun="event",
            distance_display=str(entry.distance),
            stroke_display=repr(rec.raw(22, 1).strip()),
        )
        if event is None:
            st.current_individual_swim = None
            st.current_relay = None
            st.last_leaf = None
            return
        assert entry.event_sex is not None  # guaranteed by the event guard above

        status, valid = self._result_status(rec)
        swim = IndividualSwim(
            meet=st.meet,
            club=st.attached_club,
            organization=Organization.USS,
            event=event,
            event_min_age=entry.event_min_age,
            event_max_age=entry.event_max_age,
            event_sex=entry.event_sex,
            event_number=entry.event_number,
            session=self._code(rec, 3, 1, Session, "round", "3/1", "M2") or Session.FINALS,
            status=status,
            time=self._hy3_time(rec, 5, 7) if valid else None,
            date=self._date(rec, 88, 8, "date", "88/8", "M2"),
            heat=self._opt_int(rec, 22, 2),
            lane=self._opt_int(rec, 25, 2),
            rank=self._rank(rec, 31, 3),
            seed_time=entry.seed_time,
            seed_course=entry.seed_course,
            converted_seed_time=entry.converted_seed_time,
            converted_seed_course=entry.converted_seed_course,
            dq_code=rec.text(14, 2) if status is ResultStatus.DQ else None,
            backup_times=self._backup_times(rec),
            swimmer=entry.swimmer,
            swimmer_age_class=st.current_age_class,
        )
        entry.swimmer.swims.append(swim)
        self._attach_result(st.meet, swim)
        self.report.individual_swims_parsed += 1
        st.current_individual_swim = swim
        st.current_relay = None
        st.last_leaf = "individual"

    def _h_f1(self, rec: Record) -> None:
        st = self.state
        if st is None:
            return
        st.pending_relay_entry = Hy3RelayEntry(
            relay_letter=self._require_text(rec, 8, 1, "relay_letter", "8/1"),
            event_sex=self._event_sex(rec, 15),
            distance=self._opt_int(rec, 19, 3),
            stroke=self._stroke(rec, 22, _RELAY_STROKE),
            event_min_age=self._event_age(rec, 23, _AGE_OPEN_LOW),
            event_max_age=self._event_age(rec, 26, _AGE_OPEN_HIGH),
            event_number=rec.text(39, 4),
            seed_time=self._hy3_time(rec, 53, 7),
            seed_course=self._opt_course(rec, 60),
            converted_seed_time=self._hy3_time(rec, 44, 7),
            converted_seed_course=self._opt_course(rec, 51),
        )

    def _h_f2(self, rec: Record) -> None:
        st = self.state
        if st is None:
            return
        entry = st.pending_relay_entry
        st.pending_relay_entry = None
        if entry is None:
            self._skip_orphan(rec, "F2 relay result with no preceding F1 entry")
            return

        course = self._opt_course(rec, 12)
        event = self._resolve_event(
            rec,
            distance=entry.distance,
            stroke=entry.stroke,
            sex=entry.event_sex,
            course=course,
            field="event",
            column="12/1",
            mandatory="M1",
            noun="relay event",
            distance_display=str(entry.distance),
            stroke_display=repr(rec.raw(22, 1).strip()),
        )
        if event is None:
            st.current_relay = None
            st.current_individual_swim = None
            st.last_leaf = None
            return
        assert entry.event_sex is not None  # guaranteed by the event guard above

        status, valid = self._result_status(rec)
        relay = Relay(
            meet=st.meet,
            club=st.attached_club,
            organization=Organization.USS,
            event=event,
            event_min_age=entry.event_min_age,
            event_max_age=entry.event_max_age,
            event_sex=entry.event_sex,
            event_number=entry.event_number,
            session=self._code(rec, 3, 1, Session, "round", "3/1", "M2") or Session.FINALS,
            status=status,
            time=self._hy3_time(rec, 6, 6) if valid else None,
            date=self._date(rec, 103, 8, "date", "103/8", "M2"),
            heat=self._opt_int(rec, 22, 2),
            lane=self._opt_int(rec, 25, 2),
            rank=self._rank(rec, 31, 3),
            seed_time=entry.seed_time,
            seed_course=entry.seed_course,
            converted_seed_time=entry.converted_seed_time,
            converted_seed_course=entry.converted_seed_course,
            dq_code=rec.text(14, 2) if status is ResultStatus.DQ else None,
            backup_times=self._backup_times(rec),
            relay_letter=entry.relay_letter,
        )
        self._attach_result(st.meet, relay)
        self.report.relays_parsed += 1
        st.current_relay = relay
        st.current_individual_swim = None
        st.last_leaf = "relay"

    def _h_f3(self, rec: Record) -> None:
        st = self.state
        if st is None or st.current_relay is None:
            self._skip_orphan(rec, "F3 relay athletes with no preceding F2 relay")
            return
        relay = st.current_relay
        for slot in range(_SLOTS_PER_RECORD):
            chunk = rec.raw(_FIRST_SLOT_COL + slot * _SLOT_WIDTH, _SLOT_WIDTH)
            if not chunk.strip():
                continue
            number = chunk[1:6].strip()
            swimmer = st.swimmers_by_number.get(number) if number else None
            order = _LEG_ORDER.get(chunk[12:13].strip(), RelayLegOrder.ALTERNATE)
            leg = RelaySwim(swimmer=swimmer, relay=relay, order=order, status=relay.status)
            if order is RelayLegOrder.ALTERNATE:
                relay.alternates.append(leg)
            else:
                relay.legs.append(leg)
                if swimmer is not None:
                    swimmer.swims.append(leg)

    def _h_g1(self, rec: Record) -> None:
        st = self.state
        if st is None:
            return
        target = self._g1_target()
        if target is None:
            self._skip_orphan(rec, "G1 splits could not be attached to a swim")
            return
        for slot in range(_SPLITS_PER_RECORD):
            block = rec.raw(_FIRST_SPLIT_COL + slot * _SPLIT_WIDTH, _SPLIT_WIDTH)
            if not block.strip():
                continue
            counter = block[1:3].strip()
            if not counter.isdigit():
                self._warn(
                    rec,
                    "split_distance",
                    None,
                    None,
                    Severity.RECOVERED,
                    IssueKind.MALFORMED,
                    f"malformed split distance counter {counter!r}",
                )
                continue
            distance = int(counter) * 25
            tag, val = time_value(block[3:_SPLIT_WIDTH])
            if tag == "blank" or (isinstance(val, Time) and val.centiseconds == 0):
                continue  # blank or `0.00` placeholder for an unrecorded split
            self._append_split(rec, target, distance, tag, val, SplitType.CUMULATIVE)

    def _g1_target(self) -> list[Split] | None:
        st = self.state
        assert st is not None
        if st.last_leaf == "individual" and st.current_individual_swim is not None:
            return st.current_individual_swim.splits
        if st.last_leaf == "relay" and st.current_relay is not None:
            return st.current_relay.splits
        return None

    def _h_h1(self, rec: Record) -> None:
        self._append_dq_reason(rec)

    def _h_h2(self, rec: Record) -> None:
        self._append_dq_reason(rec)

    def _append_dq_reason(self, rec: Record) -> None:
        st = self.state
        if st is None:
            return
        result: MeetResult | None = (
            st.current_individual_swim
            if st.last_leaf == "individual"
            else st.current_relay
            if st.last_leaf == "relay"
            else None
        )
        text = rec.text(5, 48)
        if result is None or text is None:
            return
        result.dq_reason = f"{result.dq_reason} {text}".strip() if result.dq_reason else text


# Dispatch table — every record type we extract confirmed fields from.
_HANDLERS: dict[str, Callable[[_Hy3Engine, Record], None]] = {
    "A1": _Hy3Engine._h_a1,
    "B1": _Hy3Engine._h_b1,
    "B2": _Hy3Engine._h_b2,
    "C1": _Hy3Engine._h_c1,
    "C3": _Hy3Engine._h_c3,
    "D1": _Hy3Engine._h_d1,
    "E1": _Hy3Engine._h_e1,
    "E2": _Hy3Engine._h_e2,
    "F1": _Hy3Engine._h_f1,
    "F2": _Hy3Engine._h_f2,
    "F3": _Hy3Engine._h_f3,
    "G1": _Hy3Engine._h_g1,
    "H1": _Hy3Engine._h_h1,
    "H2": _Hy3Engine._h_h2,
}
