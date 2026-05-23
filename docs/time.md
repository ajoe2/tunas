# `tunas.time` — the `Time` value type

`Time` represents a swim time. It is the unit returned everywhere times
appear in the API — `result.time`, `result.seed_time`, `Split.time`,
`RelayLeg.leg_time`, and the values returned by `standard_time(...)`.

## Design summary

- **Frozen dataclass** — `Time` instances are immutable, hashable, and
  comparable.
- **Single integer field** internally: `centiseconds: int`. Minutes,
  seconds, and hundredths are exposed as computed properties.
- **Natural ordering** — `t1 < t2` is "`t1` is a faster time."
- **Supports arithmetic** — addition and subtraction return new `Time`
  instances; subtraction raises if it would produce a negative result.
- **Marathon-friendly** — `centiseconds` is an unbounded `int`, so times
  longer than 60 minutes (e.g. open-water 10km) work correctly.

## Construction

```python
from tunas import Time
```

### `Time(centiseconds: int)`

Direct constructor. Useful when you already have the value in centiseconds
(e.g. from JSON):

```python
Time(12345)          # 2:03.45
```

### `Time.parse(s: str) -> Time` (classmethod)

Parses the standard swim-time string formats:

```python
Time.parse("23.45")        # 23.45 — Time(2345)
Time.parse("1:23.45")      # 1:23.45 — Time(8345)
Time.parse("0:23.45")      # 23.45 — Time(2345)
Time.parse("12:34.56")     # 12:34.56
```

Raises `ValueError` for unparseable input. The accepted grammar is:
optional `MM:`, then `SS`, then `.HH`. Whitespace is stripped. Empty or
whitespace-only strings raise `ValueError`.

### `Time.from_parts(minute=0, second=0, hundredth=0) -> Time` (classmethod)

Convenience for callers building a `Time` from individual components:

```python
Time.from_parts(1, 23, 45)     # 1:23.45
Time.from_parts(second=45)     # 0:45.00
```

Each component must be a non-negative integer. `second` and `hundredth`
must each be less than 60 and 100 respectively; `minute` is unbounded.

## Properties

| Property | Type | Notes |
|---|---|---|
| `centiseconds` | `int` | The stored value. Always ≥ 0. |
| `minute` | `int` | `centiseconds // 6000`. |
| `second` | `int` | `(centiseconds // 100) % 60`. |
| `hundredth` | `int` | `centiseconds % 100`. |
| `total_seconds` | `float` | `centiseconds / 100`. |

```python
t = Time.parse("1:23.45")
t.minute              # 1
t.second              # 23
t.hundredth           # 45
t.total_seconds       # 83.45
t.centiseconds        # 8345
```

## String formatting

`str(time)` returns the canonical swim-time format:

- `centiseconds == 0` → `""` (empty string — indicates "no time")
- `minute == 0` → `"SS.HH"` (e.g. `"23.45"`)
- otherwise → `"M:SS.HH"` (e.g. `"1:23.45"`)

`repr(time)` always returns `Time(centiseconds=N)` for unambiguous logging.

## Comparison and hashing

`Time` defines the full set of ordering operators (`<`, `<=`, `==`, `!=`,
`>=`, `>`) via `dataclass(order=True, frozen=True)`. Comparison is on
`centiseconds`, so smaller times compare as "less than" larger times.

```python
Time.parse("23.45") < Time.parse("23.46")       # True (faster)
sorted([t1, t2, t3])                              # fastest first
```

`Time` is hashable, so it can be used as a `dict` key or set member.
Comparison with `None` returns `NotImplemented` (Python then evaluates to
`False` for `==`).

## Arithmetic

### Addition

`t1 + t2` returns a new `Time` whose `centiseconds` is the sum:

```python
Time.parse("1:00.00") + Time.parse("30.50")     # Time.parse("1:30.50")
```

### Subtraction

`t1 - t2` returns a new `Time` whose `centiseconds` is `t1.centiseconds -
t2.centiseconds`. Raises `ValueError` if the result would be negative
(swim times don't go below zero):

```python
Time.parse("1:30.00") - Time.parse("30.00")     # Time.parse("1:00.00")
Time.parse("30.00") - Time.parse("1:00.00")     # raises ValueError
```

## Errors

`Time.parse(...)` and `Time.from_parts(...)` raise `ValueError` for malformed
input. `Time.__sub__` raises `ValueError` for negative results. All errors
include the offending input in their message.

## Example

```python
from tunas import Time

prelim = Time.parse("1:05.23")
final = Time.parse("1:04.87")
drop = prelim - final
print(f"dropped {drop}")                  # dropped 0.36
print(final < prelim)                       # True
print(f"final converted: {final.total_seconds:.2f} s")
```
