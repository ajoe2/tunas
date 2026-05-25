# Events & Time

## Events

[`Event`][tunas.event.Event] is a 90+ member enum; each member is a `(distance, stroke,
course)` tuple, named `<STROKE>_<DISTANCE>_<COURSE>` for individual events (e.g.
`FREE_100_SCY`) and `<STROKE>_<DISTANCE>_RELAY_<COURSE>` for relays (e.g.
`MEDLEY_400_RELAY_LCM`). Members compare in **declaration order**, so `sorted(...)` yields a
natural event ordering.

- **Components:** `event.distance`, `event.stroke` ([`Stroke`][tunas.enums.Stroke]), `event.course` ([`Course`][tunas.enums.Course]).
- **Lookup:** `Event.find(distance, stroke, course)` → the matching `Event` or `None`.
- **Relays:** `event.is_relay()`, `event.leg_distance()`, `event.leg_strokes()`, and
  `event.leg_event(order)` — the individual event swum on a given leg (1–4). This is what lets
  a relay leg sort alongside flat-start swims of the same individual event.

## Time

[`Time`][tunas.time.Time] stores `centiseconds: int` and formats as `[M:]SS.HH`. See the
[data-model guide](../guide/models.md#times) for usage; the full API is below.

::: tunas.event

::: tunas.time
