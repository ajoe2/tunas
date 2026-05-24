# `tunas.exceptions` — exception hierarchy

All library-specific exceptions inherit from `TunasError` and are importable from the top-level package.

```python
from tunas import TunasError, ParseError, StandardsError
```

## Hierarchy

```
Exception
└── TunasError                  Base class for all exceptions raised by tunas.
    ├── ParseError              Raised on fatal structural (M1) violations, or on
    │                           any warning in strict=True mode. Carries the warning.
    └── StandardsError          Raised when time-standards data is missing,
                                unreadable, or inconsistent.
```

## `TunasError`

```python
class TunasError(Exception):
    """Base class for all exceptions raised by tunas."""
```

Catch `TunasError` to handle all library-specific failures uniformly:

```python
try:
    meets, _ = read_cl2("results.cl2", strict=True)
    standard = qualifies_for(time, event, age, sex)
except TunasError as exc:
    log.error("tunas failed: %s", exc)
```

## `ParseError`

```python
class ParseError(TunasError):
    """Raised on a fatal (M1) violation, or on any problem under strict mode."""

    warning: ParseWarning           # the underlying warning
```

`ParseError` is raised in two cases (see [parsing.md](parsing.md#error-model-m1-vs-m2-fields)):

1. **M1 (structural) violations:** Missing or unparseable structural fields (e.g. swimmer/team name, swimmer sex, meet name and start date, relay team code/letter, split sequence/distance/type) always raise `ParseError` as the record layout is broken. (Invalid or unresolvable *event* fields are not fatal — that record is skipped; see [parsing.md](parsing.md#unresolvable-events--skipped-not-fatal).)
2. **First warning under `strict=True`:** Minor M2 data-quality violations are promoted to a raised `ParseError`.

The `warning` attribute contains the underlying [`ParseWarning`](parsing.md#parsewarning):

```python
try:
    meets, _ = read_cl2(path, strict=True)
except ParseError as exc:
    w = exc.warning
    print(f"{w.source}:{w.line_no} [{w.severity.value}] "
          f"{w.record_type}.{w.field}: {w.reason}")
```

## `StandardsError`

```python
class StandardsError(TunasError):
    """Raised when time-standards data is missing or inconsistent."""
```

Raised by `tunas.standards` when:
- The bundled JSON file cannot be read.
- An internal data consistency check fails.

## Post-parse warning validation

To collect all warnings instead of failing immediately, parse in lenient mode and check the report:

```python
meets, report = read_cl2(path)
if report.warnings:
    raise ParseError(report.warnings[0])
```


