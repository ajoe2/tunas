# `tunas.time` — the `Time` value type

`Time` represents a swim time, stored with centisecond precision. It is used throughout the library's API (e.g., `swim.time`, `Split.time`, and `standard_time`).

## Design summary

- **Immutable Frozen Dataclass:** Immutable, hashable, and comparable.
- **Centisecond Storage:** Stores `centiseconds: int` internally; exposes computed properties for minutes, seconds, hundredths, and total seconds.
- **Natural Ordering:** Faster times compare as less than slower times (e.g., `t1 < t2` is `True` if `t1` is faster).
- **Arithmetic Support:** Supports addition and subtraction (subtraction raises `ValueError` on negative results).
- **Marathon Friendly:** Safe for open-water marathon times (internally an unbounded `int`).

## Construction

```python
from tunas import Time
```

### `Time(centiseconds: int)`

Constructs an instance directly from centiseconds:

```python
Time(12345)          # 2:03.45
```

### `Time.parse(s: str) -> Time`

Parses standard `[MM:]SS.HH` swim-time strings. Strips whitespace. Empty or invalid strings raise `ValueError`.

```python
Time.parse("23.45")        # 23.45 — Time(2345)
Time.parse("1:23.45")      # 1:23.45 — Time(8345)
Time.parse("0:23.45")      # 23.45 — Time(2345)
Time.parse("12:34.56")     # 12:34.56
```

## Properties

| Property | Type | Notes |
|---|---|---|
| `centiseconds` | `int` | The stored value (always ≥ 0). |
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

`str(time)` returns canonical swim-time formatting:
- `minute == 0` → `"SS.HH"` (e.g., `"23.45"`; `Time(0)` → `"0.00"`)
- `minute > 0` → `"M:SS.HH"` (e.g., `"1:23.45"`)

Missing or non-time outcomes (DQ, scratch, etc.) are represented by `time=None` with a [`ResultStatus`](enums.md#resultstatus), so `str(Time(...))` is never lossy and round-trips with `Time.parse`.

`repr(time)` returns `Time(centiseconds=N)`.

## Comparison and hashing

`Time` supports ordering (`<`, `<=`, `==`, `!=`, `>=`, `>`) based on centiseconds (faster first).

```python
Time.parse("23.45") < Time.parse("23.46")       # True (faster)
sorted([t1, t2, t3])                            # Sorted fastest first
```

Instances are hashable and can be used in sets or as dictionary keys. Comparing with `None` returns `False` for `==`.

## Arithmetic

### Addition

```python
Time.parse("1:00.00") + Time.parse("30.50")     # Time.parse("1:30.50")
```

### Subtraction

Raises `ValueError` if the result is negative:

```python
Time.parse("1:30.00") - Time.parse("30.00")     # Time.parse("1:00.00")
Time.parse("30.00") - Time.parse("1:00.00")     # Raises ValueError
```

## Example

```python
from tunas import Time

prelim = Time.parse("1:05.23")
final = Time.parse("1:04.87")
drop = prelim - final
print(f"dropped {drop}")                        # dropped 0.36
print(final < prelim)                           # True
print(f"final converted: {final.total_seconds:.2f} s")
```


