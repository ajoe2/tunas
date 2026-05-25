# Domain Model

The object graph produced by [`read_cl2`](parsing.md). Aggregates (`Meet`, `Club`, `Swimmer`, the result types) are mutable with identity equality; the small value types are frozen and hashable.

::: tunas.models
