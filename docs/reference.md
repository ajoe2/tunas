# API reference

This page is generated directly from source docstrings and type hints. All symbols are importable from the top-level `tunas` package:

```python
from tunas import read_cl2, Meet, Swimmer, Event, Time, qualifies_for
```

For guides and examples, see the [Getting Started Guide](getting_started.md).

## Parsing and diagnostics

::: tunas.read_cl2

::: tunas.ParseReport

::: tunas.ParseWarning

::: tunas.Severity

::: tunas.IssueKind

## Exceptions

::: tunas.exceptions

## Domain model

The object graph produced by [`read_cl2`](#parsing-and-diagnostics). Aggregates (`Meet`,
`Club`, `Swimmer`, the result types) are mutable with identity equality; the small
value types are frozen and hashable.

::: tunas.models

## Events and time

::: tunas.event

::: tunas.time

## Enumerations

Categorical SDIF fields. The SDIF code is each member's *value*, so a raw byte
resolves with e.g. `Sex("F")` or `Course("3")`; unknown codes raise `ValueError`.

::: tunas.enums

## Geography

Large geographic code enums — Local Swimming Committees, US states, and FINA
country codes.

::: tunas.geography

## Time standards

Offline lookups against the bundled USA Swimming motivational standards.

::: tunas.standards
