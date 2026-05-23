# `tunas.exceptions` — exception hierarchy

`tunas` raises a small, focused set of exceptions, all rooted at
`TunasError`. They are importable from the top-level package:

```python
from tunas import TunasError, ParseError, StandardsError
```

## Hierarchy

```
Exception
└── TunasError                  Base class for all exceptions raised by tunas.
    ├── ParseError              Raised by read_cl2(..., strict=True) on the first
    │                           malformed record. Carries the offending warning.
    └── StandardsError          Raised when time-standards data is missing,
                                unreadable, or inconsistent for the requested
                                quad / standard / event combination.
```

## `TunasError`

```python
class TunasError(Exception):
    """Base class for all exceptions raised by tunas."""
```

Catch this if you want to handle any tunas-specific failure uniformly:

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
    """Raised by read_cl2(..., strict=True) on the first malformed record."""

    warning: ParseWarning           # the underlying warning
```

`ParseError` is **only** raised in strict mode. The default lenient mode
appends warnings to `ParseReport.warnings` and continues.

The `warning` attribute carries the full `ParseWarning` (source, line
number, record type, reason, raw line) so error handlers can report the
exact location of the failure:

```python
try:
    meets, _ = read_cl2(path, strict=True)
except ParseError as exc:
    w = exc.warning
    print(f"{w.source}:{w.line_no} ({w.record_type}): {w.reason}")
    print(f"  {w.raw_line!r}")
```

## `StandardsError`

```python
class StandardsError(TunasError):
    """Raised when time-standards data is missing or inconsistent."""
```

Raised by `tunas.standards.*` functions when:

- The requested `quad` (e.g. `"2025-2028"`) is not bundled with this
  release.
- The bundled JSON file is corrupt or cannot be read (this should never
  happen in a released wheel, but is surfaced rather than swallowed).
- An internal consistency check fails — for example, two standards
  with the same `(standard, age_group, sex, event)` key.

Functions in `tunas.standards` that take a `quad=` kwarg raise
`StandardsError` for an unknown quad, never `KeyError` or `ValueError`.

## Catching all parse warnings as errors

If you want a "strict in production, lenient in dev" pattern, lenient
mode plus a post-parse check is the idiomatic approach:

```python
meets, report = read_cl2(path)
if report.warnings:
    raise ParseError(report.warnings[0])
```

This avoids `strict=True`'s fail-fast behavior — you get the *full* list
of bad records in the report, and decide what to do based on policy.
