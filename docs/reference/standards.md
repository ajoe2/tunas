# Time Standards

Offline lookups against the bundled USA Swimming motivational standards (the **2025–2028**
cuts), shipped as JSON inside the package — no setup or network access. USA Swimming revises
the cuts every four years, so refreshing them is just a matter of upgrading `tunas`.

[`TimeStandard`][tunas.standards.TimeStandard] is an ordered `IntEnum` from slowest to
fastest — `B < BB < A < AA < AAA < AAAA` — so a `qualifies_for(...)` result can be compared
directly (`std >= TimeStandard.AA`). Each member has a `.display()` name.

Lookups take an `event`, an `age`, and a `sex`, bucketing the age into single-year groups
(**10 & under, 11-12, 13-14, 15-16, 17-18**). Standards exist for `MALE`/`FEMALE` only —
passing `Sex.MIXED` raises `ValueError`. An event/age/sex with no defined cut returns `None`
(or an empty list).

- [`qualifies_for`][tunas.standards.qualifies_for] — the single fastest standard a time meets, or `None`.
- [`all_qualified`][tunas.standards.all_qualified] — every standard met, ordered slowest first.
- [`standard_time`][tunas.standards.standard_time] — the cutoff [`Time`][tunas.time.Time] for one standard, or `None`.

If the bundled data is missing or malformed, lookups raise
[`StandardsError`][tunas.exceptions.StandardsError].

::: tunas.standards
