# `tunas.event` — the `Event` enum

`Event` represents a unique swimming event (distance, stroke, course). Every result has an `event`, and APIs filtering by event accept `Event` members.

## Design

- `Event` is a hand-rolled `(distance, stroke, course)` enum.
- Members are named `<STROKE>_<DISTANCE>_<COURSE>` for individual events and `<STROKE>_<DISTANCE>_RELAY_<COURSE>` for relays.
- Component combinations matching no enum member resolve to `None`. The parser treats this as a skipped record + warning, not a fatal error (see [parsing.md](parsing.md#mode-summary)).
- Use `Event.find(distance, stroke, course)` to resolve an event by its components (primarily inside the parser). Application code should reference members directly.

## Members

### Individual — short course yards (SCY)

```
FREE_25_SCY        BACK_25_SCY        BREAST_25_SCY        FLY_25_SCY
FREE_50_SCY        BACK_50_SCY        BREAST_50_SCY        FLY_50_SCY
FREE_100_SCY       BACK_100_SCY       BREAST_100_SCY       FLY_100_SCY
FREE_200_SCY       BACK_200_SCY       BREAST_200_SCY       FLY_200_SCY
FREE_400_SCY                                                IM_100_SCY
FREE_500_SCY                                                IM_200_SCY
FREE_800_SCY                                                IM_400_SCY
FREE_1000_SCY
FREE_1650_SCY
```

### Individual — short course meters (SCM)

```
FREE_25_SCM        BACK_25_SCM        BREAST_25_SCM        FLY_25_SCM
FREE_50_SCM        BACK_50_SCM        BREAST_50_SCM        FLY_50_SCM
FREE_100_SCM       BACK_100_SCM       BREAST_100_SCM       FLY_100_SCM
FREE_200_SCM       BACK_200_SCM       BREAST_200_SCM       FLY_200_SCM
FREE_400_SCM                                                IM_100_SCM
FREE_800_SCM                                                IM_200_SCM
FREE_1500_SCM                                               IM_400_SCM
```

### Individual — long course meters (LCM)

```
FREE_50_LCM        BACK_50_LCM        BREAST_50_LCM        FLY_50_LCM
FREE_100_LCM       BACK_100_LCM       BREAST_100_LCM       FLY_100_LCM
FREE_200_LCM       BACK_200_LCM       BREAST_200_LCM       FLY_200_LCM
FREE_400_LCM                                                IM_200_LCM
FREE_800_LCM                                                IM_400_LCM
FREE_1500_LCM
```

### Relays — SCY / SCM / LCM

```
FREE_200_RELAY_SCY       MEDLEY_200_RELAY_SCY
FREE_400_RELAY_SCY       MEDLEY_400_RELAY_SCY
FREE_800_RELAY_SCY
 
FREE_200_RELAY_SCM       MEDLEY_200_RELAY_SCM
FREE_400_RELAY_SCM       MEDLEY_400_RELAY_SCM
FREE_800_RELAY_SCM
 
FREE_200_RELAY_LCM       MEDLEY_200_RELAY_LCM
FREE_400_RELAY_LCM       MEDLEY_400_RELAY_LCM
FREE_800_RELAY_LCM
```

## Properties

Each `Event` exposes its components as computed properties:

| Property | Type | Description |
|---|---|---|
| `distance` | `int` | Event distance (total distance for relays, e.g., `FREE_400_RELAY_SCY.distance == 400`). |
| `stroke` | `Stroke` | The event's `Stroke` enum value. |
| `course` | `Course` | The event's `Course` enum value. |

```python
from tunas import Event

Event.FREE_100_SCY.distance     # 100
Event.FREE_100_SCY.stroke       # Stroke.FREESTYLE
Event.FREE_100_SCY.course       # Course.SCY

Event.MEDLEY_400_RELAY_SCY.distance  # 400 (total)
Event.MEDLEY_400_RELAY_SCY.stroke    # Stroke.MEDLEY_RELAY
```

## Classmethods

### `Event.find(distance: int, stroke: Stroke, course: Course) -> Event | None`

Look up an `Event` by its components. Returns `None` if no matching event exists (e.g., no `BREAST_25_LCM`).

```python
from tunas import Event, Stroke, Course

Event.find(100, Stroke.FREESTYLE, Course.SCY)
# → Event.FREE_100_SCY

Event.find(25, Stroke.BREASTSTROKE, Course.LCM)
# → None
```

Backed by an O(1) lookup table.

## Helpers

### `Event.is_relay() -> bool`

`True` if the event is a relay (`Stroke.FREESTYLE_RELAY` or `Stroke.MEDLEY_RELAY`).

### `Event.leg_distance() -> int`

For relays, returns `distance // 4`. For individual events, raises `ValueError`.

### `Event.leg_strokes() -> list[Stroke]`

For relays, returns the four leg strokes in order. For individual events, raises `ValueError`.

### `Event.leg_event(order: int) -> Event`

For relays, returns the **individual** `Event` swum on leg `order` (`1`–`4`), resolved via `Event.find`. Raises `ValueError` for individual events or orders outside `1`–`4`.

```python
# Free relay — every leg is the same freestyle individual event
Event.FREE_400_RELAY_SCY.leg_event(1)    # Event.FREE_100_SCY

# Medley relay — stroke depends on leg position
Event.MEDLEY_400_RELAY_SCY.leg_event(1)  # Event.BACK_100_SCY
Event.MEDLEY_400_RELAY_SCY.leg_event(2)  # Event.BREAST_100_SCY
Event.MEDLEY_400_RELAY_SCY.leg_event(3)  # Event.FLY_100_SCY
Event.MEDLEY_400_RELAY_SCY.leg_event(4)  # Event.FREE_100_SCY
```

All relay legs map to real individual event members across courses. `RelaySwim.event` relies on this helper (see [models.md](models.md#swim-interface-on-a-leg)).

## Ordering

Members compare by declaration order (SCY, SCM, LCM, then relays). Use explicit attribute filters when querying rather than ordinal comparisons.

## Example

```python
from tunas import Event, Stroke

# All 200 events across courses
events_200 = [e for e in Event if e.distance == 200 and not e.is_relay()]

# All medley relays
medley_relays = [e for e in Event if e.stroke is Stroke.MEDLEY_RELAY]
```
