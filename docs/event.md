# `tunas.event` — the `Event` enum

`Event` is the canonical identifier for a swimming event. Every
`MeetResult.event` is an `Event` member, and every API that filters or
queries by event takes an `Event`.

## Design

- `Event` is a `(distance, stroke, course)` enum with hand-rolled members.
- Members are named in the form `<STROKE>_<DISTANCE>_<COURSE>` for
  individual events and `<STROKE>_<DISTANCE>_RELAY_<COURSE>` for relays.
- The members are listed below in their natural enumeration order.
- Use `Event.find(distance, stroke, course)` to resolve an event when you
  have the components but not the member name (typically inside the parser).

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
| `distance` | `int` | Total event distance in yards (SCY) or meters (SCM/LCM). For relays, the **total** distance (e.g. `FREE_400_RELAY_SCY.distance == 400`). |
| `stroke` | `Stroke` | One of `FREESTYLE`, `BACKSTROKE`, `BREASTSTROKE`, `BUTTERFLY`, `INDIVIDUAL_MEDLEY`, `FREESTYLE_RELAY`, `MEDLEY_RELAY`. |
| `course` | `Course` | One of `SCY`, `SCM`, `LCM`. |

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

Look up an `Event` by its components. Returns `None` if no matching event
exists (e.g. there is no `BREAST_25_LCM`).

```python
from tunas import Event, Stroke, Course

Event.find(100, Stroke.FREESTYLE, Course.SCY)
# → Event.FREE_100_SCY

Event.find(25, Stroke.BREASTSTROKE, Course.LCM)
# → None
```

`Event.find` is primarily used by the parser to resolve events from raw
SDIF tuples. Application code usually references members directly
(`Event.FREE_100_SCY`).

## Helpers

### `Event.is_relay() -> bool`

`True` if the event's stroke is `FREESTYLE_RELAY` or `MEDLEY_RELAY`.

### `Event.leg_distance() -> int`

For relay events, returns `distance // 4` (the per-swimmer distance).
For individual events, raises `ValueError`.

```python
Event.FREE_400_RELAY_SCY.leg_distance()    # 100
```

### `Event.leg_strokes() -> list[Stroke]`

For relay events, returns the four leg strokes in order. For a freestyle
relay this is `[FREESTYLE, FREESTYLE, FREESTYLE, FREESTYLE]`; for a
medley relay it is `[BACKSTROKE, BREASTSTROKE, BUTTERFLY, FREESTYLE]`.
For individual events, raises `ValueError`.

```python
Event.MEDLEY_400_RELAY_SCY.leg_strokes()
# → [Stroke.BACKSTROKE, Stroke.BREASTSTROKE, Stroke.BUTTERFLY, Stroke.FREESTYLE]
```

## Ordering

Members compare by enumeration position (the order in which they are
declared, which matches the layout above — SCY individuals, then SCM, then
LCM, then SCY relays, etc.). Use `Event.<name>` membership tests rather
than ordering when filtering.

## Example

```python
from tunas import Event, Stroke

# All 200 events across courses
events_200 = [e for e in Event if e.distance == 200 and not e.is_relay()]

# All medley relays
medley_relays = [e for e in Event if e.stroke is Stroke.MEDLEY_RELAY]
```
