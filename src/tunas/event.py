"""The :class:`Event` enum — a swimming event as (distance, stroke, course)."""

from __future__ import annotations

from enum import Enum

from tunas.enums import Course, Stroke

__all__ = ["Event"]

_FREE = Stroke.FREESTYLE
_BACK = Stroke.BACKSTROKE
_BREAST = Stroke.BREASTSTROKE
_FLY = Stroke.BUTTERFLY
_IM = Stroke.INDIVIDUAL_MEDLEY
_FREE_R = Stroke.FREESTYLE_RELAY
_MEDLEY_R = Stroke.MEDLEY_RELAY
_SCY = Course.SCY
_SCM = Course.SCM
_LCM = Course.LCM

# Standard medley-relay leg order.
_MEDLEY_LEG_STROKES = (_BACK, _BREAST, _FLY, _FREE)


class Event(Enum):
    """A unique swimming event. Value is ``(distance, stroke, course)``.

    Members are named ``<STROKE>_<DISTANCE>_<COURSE>`` for individual events and
    ``<STROKE>_<DISTANCE>_RELAY_<COURSE>`` for relays. Compare members by
    declaration order; prefer attribute filters over ordinal comparisons.
    """

    # --- Individual, short course yards (SCY) ---
    FREE_25_SCY = (25, _FREE, _SCY)
    BACK_25_SCY = (25, _BACK, _SCY)
    BREAST_25_SCY = (25, _BREAST, _SCY)
    FLY_25_SCY = (25, _FLY, _SCY)
    FREE_50_SCY = (50, _FREE, _SCY)
    BACK_50_SCY = (50, _BACK, _SCY)
    BREAST_50_SCY = (50, _BREAST, _SCY)
    FLY_50_SCY = (50, _FLY, _SCY)
    FREE_100_SCY = (100, _FREE, _SCY)
    BACK_100_SCY = (100, _BACK, _SCY)
    BREAST_100_SCY = (100, _BREAST, _SCY)
    FLY_100_SCY = (100, _FLY, _SCY)
    FREE_200_SCY = (200, _FREE, _SCY)
    BACK_200_SCY = (200, _BACK, _SCY)
    BREAST_200_SCY = (200, _BREAST, _SCY)
    FLY_200_SCY = (200, _FLY, _SCY)
    FREE_400_SCY = (400, _FREE, _SCY)
    IM_100_SCY = (100, _IM, _SCY)
    FREE_500_SCY = (500, _FREE, _SCY)
    IM_200_SCY = (200, _IM, _SCY)
    FREE_800_SCY = (800, _FREE, _SCY)
    IM_400_SCY = (400, _IM, _SCY)
    FREE_1000_SCY = (1000, _FREE, _SCY)
    FREE_1650_SCY = (1650, _FREE, _SCY)

    # --- Individual, short course meters (SCM) ---
    FREE_25_SCM = (25, _FREE, _SCM)
    BACK_25_SCM = (25, _BACK, _SCM)
    BREAST_25_SCM = (25, _BREAST, _SCM)
    FLY_25_SCM = (25, _FLY, _SCM)
    FREE_50_SCM = (50, _FREE, _SCM)
    BACK_50_SCM = (50, _BACK, _SCM)
    BREAST_50_SCM = (50, _BREAST, _SCM)
    FLY_50_SCM = (50, _FLY, _SCM)
    FREE_100_SCM = (100, _FREE, _SCM)
    BACK_100_SCM = (100, _BACK, _SCM)
    BREAST_100_SCM = (100, _BREAST, _SCM)
    FLY_100_SCM = (100, _FLY, _SCM)
    FREE_200_SCM = (200, _FREE, _SCM)
    BACK_200_SCM = (200, _BACK, _SCM)
    BREAST_200_SCM = (200, _BREAST, _SCM)
    FLY_200_SCM = (200, _FLY, _SCM)
    FREE_400_SCM = (400, _FREE, _SCM)
    IM_100_SCM = (100, _IM, _SCM)
    FREE_800_SCM = (800, _FREE, _SCM)
    IM_200_SCM = (200, _IM, _SCM)
    FREE_1500_SCM = (1500, _FREE, _SCM)
    IM_400_SCM = (400, _IM, _SCM)

    # --- Individual, long course meters (LCM) ---
    FREE_50_LCM = (50, _FREE, _LCM)
    BACK_50_LCM = (50, _BACK, _LCM)
    BREAST_50_LCM = (50, _BREAST, _LCM)
    FLY_50_LCM = (50, _FLY, _LCM)
    FREE_100_LCM = (100, _FREE, _LCM)
    BACK_100_LCM = (100, _BACK, _LCM)
    BREAST_100_LCM = (100, _BREAST, _LCM)
    FLY_100_LCM = (100, _FLY, _LCM)
    FREE_200_LCM = (200, _FREE, _LCM)
    BACK_200_LCM = (200, _BACK, _LCM)
    BREAST_200_LCM = (200, _BREAST, _LCM)
    FLY_200_LCM = (200, _FLY, _LCM)
    FREE_400_LCM = (400, _FREE, _LCM)
    IM_200_LCM = (200, _IM, _LCM)
    FREE_800_LCM = (800, _FREE, _LCM)
    IM_400_LCM = (400, _IM, _LCM)
    FREE_1500_LCM = (1500, _FREE, _LCM)

    # --- Relays ---
    FREE_200_RELAY_SCY = (200, _FREE_R, _SCY)
    MEDLEY_200_RELAY_SCY = (200, _MEDLEY_R, _SCY)
    FREE_400_RELAY_SCY = (400, _FREE_R, _SCY)
    MEDLEY_400_RELAY_SCY = (400, _MEDLEY_R, _SCY)
    FREE_800_RELAY_SCY = (800, _FREE_R, _SCY)
    FREE_200_RELAY_SCM = (200, _FREE_R, _SCM)
    MEDLEY_200_RELAY_SCM = (200, _MEDLEY_R, _SCM)
    FREE_400_RELAY_SCM = (400, _FREE_R, _SCM)
    MEDLEY_400_RELAY_SCM = (400, _MEDLEY_R, _SCM)
    FREE_800_RELAY_SCM = (800, _FREE_R, _SCM)
    FREE_200_RELAY_LCM = (200, _FREE_R, _LCM)
    MEDLEY_200_RELAY_LCM = (200, _MEDLEY_R, _LCM)
    FREE_400_RELAY_LCM = (400, _FREE_R, _LCM)
    MEDLEY_400_RELAY_LCM = (400, _MEDLEY_R, _LCM)
    FREE_800_RELAY_LCM = (800, _FREE_R, _LCM)

    # --- Component properties ---

    @property
    def distance(self) -> int:
        """Total event distance in yards/meters (e.g. ``400`` for a 400 relay)."""
        return self.value[0]

    @property
    def stroke(self) -> Stroke:
        return self.value[1]

    @property
    def course(self) -> Course:
        return self.value[2]

    # --- Lookup ---

    @classmethod
    def find(cls, distance: int, stroke: Stroke, course: Course) -> Event | None:
        """Resolve an event by its components, or ``None`` if none matches."""
        return _BY_COMPONENTS.get((distance, stroke, course))

    # --- Relay helpers ---

    def is_relay(self) -> bool:
        return self.stroke in (_FREE_R, _MEDLEY_R)

    def leg_distance(self) -> int:
        """Per-leg distance (``distance // 4``). Raises for individual events."""
        if not self.is_relay():
            raise ValueError(f"{self.name} is not a relay")
        return self.distance // 4

    def leg_strokes(self) -> list[Stroke]:
        """The four leg strokes in order. Raises for individual events."""
        if not self.is_relay():
            raise ValueError(f"{self.name} is not a relay")
        if self.stroke is _MEDLEY_R:
            return list(_MEDLEY_LEG_STROKES)
        return [_FREE, _FREE, _FREE, _FREE]

    def leg_event(self, order: int) -> Event:
        """The individual :class:`Event` swum on leg ``order`` (1-4).

        >>> Event.MEDLEY_400_RELAY_SCY.leg_event(2)
        <Event.BREAST_100_SCY: ...>
        """
        if not self.is_relay():
            raise ValueError(f"{self.name} is not a relay")
        if not 1 <= order <= 4:
            raise ValueError(f"Relay leg order must be 1-4, got {order}")
        leg_stroke = self.leg_strokes()[order - 1]
        event = Event.find(self.leg_distance(), leg_stroke, self.course)
        if event is None:  # pragma: no cover - every defined relay has real legs
            raise ValueError(f"No individual event for leg {order} of {self.name}")
        return event

    # --- Ordering by declaration order ---

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Event):
            return _ORDER[self] < _ORDER[other]
        return NotImplemented

    def __le__(self, other: object) -> bool:
        if isinstance(other, Event):
            return _ORDER[self] <= _ORDER[other]
        return NotImplemented

    def __gt__(self, other: object) -> bool:
        if isinstance(other, Event):
            return _ORDER[self] > _ORDER[other]
        return NotImplemented

    def __ge__(self, other: object) -> bool:
        if isinstance(other, Event):
            return _ORDER[self] >= _ORDER[other]
        return NotImplemented


_BY_COMPONENTS: dict[tuple[int, Stroke, Course], Event] = {e.value: e for e in Event}
_ORDER: dict[Event, int] = {e: i for i, e in enumerate(Event)}
