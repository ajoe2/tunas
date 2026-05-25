# Parsing & errors

The parser is exposed as a single top-level function that parses `.cl2` files into structured [`Meet`](models.md) objects:

```python
from tunas import read_cl2
```

`read_cl2` returns `(list[Meet], ParseReport)`. Parsing is lenient by default, recovering from non-fatal formatting issues and collecting warnings.

## `read_cl2`

```python
def read_cl2(
    source: str | os.PathLike | Iterable[str | os.PathLike] | TextIO,
    *,
    strict: bool = False,
    encoding: str = "cp1252",
    errors: str = "replace",
    max_workers: int = 1,
) -> tuple[list[Meet], ParseReport]: ...
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `source` | `str \| Path \| Iterable[Path] \| TextIO` | Input source — path, directory, list of paths, or text stream. |
| `strict` | `bool` | If `True`, any warning raises a `ParseError`. If `False` (default), collects warnings and continues. **M1 structural violations always raise.** |
| `encoding` | `str` | Text encoding for file paths. Defaults to `"cp1252"` (common for SDIF/DOS files) to preserve alignments and accented names. |
| `errors` | `str` | Encoding error policy. Defaults to `"replace"`. |
| `max_workers` | `int` | Maximum parser threads. Defaults to `1` (sequential). With `max_workers > 1`, files are parsed concurrently — one file per task — and results are merged back **in source order**, so the output is identical to the sequential default. Must be `>= 1`. |

### Parallel parsing

Pass `max_workers > 1` to parse a directory or list of files concurrently using a thread pool:

```python
meets, report = read_cl2("season_archive/", max_workers=8)
```

Results are deterministically merged in source order, matching sequential execution. The speed-up is largest when parsing many files due to overlapping file I/O. In `strict` mode, the earliest encountered `ParseError` is raised.

### Source types

1. **File path:** Single `.cl2` file is parsed.
2. **Directory path:** Walked recursively for `*.cl2` files (case-insensitive).
3. **Iterable of paths:** Each path is parsed; meets are concatenated.
4. **Text stream:** Parsed from the buffer (uses `"<stream>"` as warning source). Stream must yield `str`, not `bytes`.

Concatenating multi-file lists performs no cross-file merging or deduplication.

### Examples

```python
# Directory walk
meets, report = read_cl2("results_dir/")

# Strict validation
try:
    meets, report = read_cl2("messy.cl2", strict=True)
except ParseError as exc:
    print(f"Failed at line {exc.warning.line_no}: {exc.warning.reason}")
```

## Per-meet scope

- **One Meet per block:** Fresh meets start at each `B1` record.
- **Meet-scoped clubs:** Repeated `C1` records for the same `(team_code, lsc)` reuse the existing `Club` instance.
- **Meet-scoped swimmers:** Swimmers are grouped by member ID (`id_short` or `id_long`). The same athlete in different meets becomes separate `Swimmer` objects. Cross-meet indexing is delegated to application code.

## Error model: M1 vs M2 fields

### M1 — fatal (always raises)

Missing or unparseable structural fields indicate a broken record and always raise `ParseError`. These include the record-type constant, swimmer and team names, swimmer sex, meet name, start date, relay team code/letter, and split sequence/distance/type (`G0`).

### Unresolvable events — skipped (not fatal)

A swim's event fields (sex, distance, stroke, age) are not treated as fatal M1. If they are partial, invalid, or do not map to a known [`Event`][tunas.event.Event] (e.g., a diving event with a non-swim stroke), the record is skipped with a `SKIPPED` warning in lenient mode or raises `ParseError` in strict mode. A single invalid event record never aborts an otherwise valid file. (A `D0` with all event fields blank denotes a relay-only swimmer; see the `#` marker below).

### M2 — recoverable (kept as `None`)

Data-quality fields skip corrupt or blank values with a `RECOVERED` warning and set the field to `None` in lenient mode, or raise `ParseError` in strict mode:
- **Swimmer ID (USS#):** Uses `id_short` (12-char), falling back to `id_long` (14-char) from subsequent `D3` records. A `D0` record lacking both is skipped (`SKIPPED`). An `F0` record lacking both is kept with `swimmer=None` (`RECOVERED`).

### Conditional markers

- **`*` (Conditional Course):** Course bytes are required only if a time is present. Missing courses warn and set `course=None`. A course byte of `"X"` denotes a **disqualification**; the swim is kept with `status=DQ` while preserving its recorded time.
- **`**` (Championship Place/Points):** Required only at championship meets. Missing values are set to `None` with a warning.
- **`#` (Relay-Only Swimmers):** Swimmer records with all event parameters blank create a `Swimmer` without generating an `IndividualSwim`. Partial or invalid event parameters skip the record (see [Unresolvable events](#unresolvable-events-skipped-not-fatal)).

### Result outcomes (NT / NS / DNF / DQ / SCR)

Outcome codes in time fields are kept as official results with `status` set to the code and `time=None`. Combined with course `"X"`, all swims are preserved for analysis.

### Other parsing behaviors

- **Malformed optional field / Unknown code:** Sets the field to `None` and warns.
- **Orphaned record:** A trailing `F0` (without `E0`) or `G0` (without `D0`/`F0`) is dropped and warns (`SKIPPED`/`ORPHANED`).
- **Record length:** Lines under 160 characters are right-padded with blanks and parsed. Lines over 160 characters are skipped and warn.
- **Unknown record type:** Unmodeled types (e.g., `J0`–`J2`) are skipped and warn (`UNKNOWN_RECORD`), preserving the raw line.
- **Split sequence < 1:** A `G0` sequence number below 1 (which would imply negative cumulative split distances) is recovered to 1 with a `RECOVERED`/`MALFORMED` warning.

### Mode summary

| Situation | Lenient (`strict=False`) | Strict (`strict=True`) |
|---|---|---|
| M1 field missing/unparseable | **raise `ParseError`** | raise `ParseError` |
| Event fields invalid, partial, or unresolvable | skip record + warn (`SKIPPED`) | raise `ParseError` |
| `D0` with no `id_short` **and** no `id_long` | skip record + warn (`SKIPPED`) | raise `ParseError` |
| `F0` with no `id_short`/`id_long` | keep leg, `swimmer=None` + warn | raise `ParseError` |
| Other M2 (dates, birthdate, etc.) | keep record, null field + warn | raise `ParseError` |
| Result outcome code (`NT`/`DQ`/etc.) | keep result, `status` set, `time=None` | keep result |
| Course byte `X` (disqualified) | keep result + time, `status=DQ` | keep result |
| `*` course missing for present time | keep, `course=None` + warn | raise `ParseError` |
| Optional / unknown-code field | null field + warn | raise `ParseError` |
| Orphaned record (`F0`/`G0`) | drop record + warn | raise `ParseError` |
| Short line (< 160 chars) | right-pad + parse | right-pad + parse |
| Over-long / unusable line | skip record + warn | raise `ParseError` |
| Unknown record type | skip record + warn | raise `ParseError` |
| Z0 count ≠ parsed total | warn (`COUNT_MISMATCH`) | raise `ParseError` |

## Diagnostics

Lenient parsing never silently loses data: every problem is recorded as a
[`ParseWarning`][tunas.ParseWarning] on the [`ParseReport`][tunas.ParseReport]
returned alongside the meets.

`ParseReport` carries the full `warnings` list plus running counts — `files_read`,
`meets_parsed`, `swimmers_parsed`, `individual_swims_parsed`, `relays_parsed`,
`splits_parsed`, `records_skipped`, `fields_recovered` — and a `warnings_for(...)`
filter. Each `ParseWarning` pins down one issue: `source`, `line_no`,
`record_type`, `field`, `column`, `mandatory`, `severity`, `kind`, `reason`, and the
truncated `raw_line`. See the [API reference](../reference/parsing.md)
for the exact fields and methods.

Every warning is tagged with a **severity** and a **kind**:

| `Severity` | Meaning |
|---|---|
| `FATAL` | Structural (M1) violation; carried by the raised `ParseError`. |
| `SKIPPED` | The record was dropped entirely. |
| `RECOVERED` | A field was set to `None` and the record kept. |

| `IssueKind` | Meaning |
|---|---|
| `MISSING` | Blank mandatory field. |
| `MALFORMED` | Unparseable value (date / time / int). |
| `UNKNOWN_CODE` | Invalid code-table value or unresolvable event. |
| `BAD_LENGTH` | Over-long / unusable line. |
| `ORPHANED` | No anchor record found. |
| `UNKNOWN_RECORD` | Unmodeled record header. |
| `COUNT_MISMATCH` | `Z0` declared count ≠ parsed total. |

```python
meets, report = read_cl2("messy_data/")
for w in report.warnings:
    print(f"{w.source}:{w.line_no} ({w.record_type}) [{w.severity.value}]: {w.reason}")
```

## Exceptions

All library errors subclass [`TunasError`][tunas.exceptions.TunasError], so a single
`except TunasError` catches everything tunas raises.

- **`ParseError`** — raised on a fatal M1 violation, or on the first warning when
  `strict=True`. Its `.warning` attribute is the underlying `ParseWarning`:

  ```python
  try:
      meets, _ = read_cl2(path, strict=True)
  except ParseError as exc:
      w = exc.warning
      print(f"{w.source}:{w.line_no} {w.record_type}.{w.field}: {w.reason}")
  ```

- **`StandardsError`** — raised by the [time-standards](../reference/standards.md)
  lookups if the bundled data is missing or inconsistent.

To collect every problem instead of failing fast, parse leniently and inspect
`report.warnings` afterwards (see [Recipes](cookbook.md)).

## Mandatory-field reference

Detailed structural contracts enforced by the parser:

**`A0` — File description → [`SourceFile`][tunas.models.SourceFile]**
- *Captures:* FILE code (`file_type`), SDIF version, software name/version, contact name/phone, creation date, submitting LSC. Malformed fields warn.

**`B1` — Meet (Anchor)**
- *M1:* `"B1"` header, meet **name**, meet **start date**.
- *M2:* ORG, **city**, **state**, **meet type**, **end date**.
- *Optional:* Addresses, postal code, country, altitude, course.

**`B2` — Meet host (Enrich → `Meet.host`)**
- *M2:* host **name**. *Captures:* Address, city, state, postal, country, phone.

**`C1` — Team/Club (Context)**
- *M1:* `"C1"` header, **team code**, **full team name**.
- *Optional:* Abbreviated name, 5th team code char, address, city/state, postal, country, region.
- *Unattached Heuristic:* A team code ending in `"UN"` (e.g. `"PCUN"`) or a name containing `"unattached"` marks the context as unattached. No `Club` is created; `swimmer.club` remains `None`.

**`C2` — Team entry (Enrich `Club`)**
- *M2:* team code, **coach name**. *Captures:* `coach_phone`, `entry_counts` (D0/athlete/E0/F0/G0 record counts), `short_name`.

**`D0` — Individual event (Leaf)**
- *M1 (fatal):* `"D0"` header, swimmer **name**, **sex**.
- *Event (skipped if unresolvable, not fatal):* event **sex**, **distance**, **stroke**, **event age** — invalid/partial/unresolvable values skip the record; all blank ⇒ relay-only swimmer (`#`).
- *M2:* ORG; **USS#** (`id_short` falling back to `D3`'s `id_long`); **date of swim**; **birth date**.
- *`*`:* prelim/swim-off/finals **course** (mandatory if time present).
- *`**`:* prelim/finals **place**, **points** (championship-only).
- *Optional:* Citizenship, age/class, seed time, heat/lane, event time class.

**`D1` — Swimmer administrative (Enrich `Swimmer.contact` / `.registration`)**
- *Captures (PII):* Phone numbers, registration date, member status, old member number, admin-info text.

**`D2` — Swimmer contact (Enrich `Swimmer.contact` / `.registration`)**
- *Captures (PII):* Mailing address/city/state/postal/country, region, season, FINA-federation byte.

**`D3` — Swimmer information (Enrich `Swimmer` / `.registration`)**
- *M2:* 14-char **USS#** (`id_long`).
- *Captures (PII):* Preferred first name, ethnicity (primary/secondary), D3 program affiliations.

**`E0` — Relay event (Anchor)**
- *M1 (fatal):* `"E0"` header, relay **team letter**. (The relay attaches to the current `C1` club.)
- *Event (skipped if unresolvable, not fatal):* event **sex**, **distance**, **stroke**, **event age**.
- *M2:* ORG, **date of swim**.
- *`*`/`**`:* session **courses** (if times present), place/points.
- *Optional:* Combined squad `total_age`, seed time, event time class.

**`F0` — Relay name (Leaf)**
- *M1 (fatal):* `"F0"` header, **team code**, swimmer **name**, **sex**, **relay letter**.
- *Leg order:* the three per-session ORDER codes select which sessions the swimmer raced; an unknown code or `NOT_SWUM` simply omits that session's leg (not fatal).
- *M2:* ORG, **USS#** (`id_short`/`id_long`), **birth date**.
- *Captures:* Leg time, takeoff time, course (`*`), age/class, citizenship, preferred name. Spans prelims/finals, fanning out into one `RelaySwim` per session swum.

**`G0` — Splits (Leaf)**
- *M1 (fatal):* `"G0"` header, **sequence number**, **split distance**, **split type**.
- *Attaches to:* Preceding `IndividualSwim` or `RelaySwim` matching the G0 session code (`P`/`F`/`S`).
- *Blank slots:* An empty split slot is skipped (not treated as end-of-list), so a record that fills only a later slot — e.g. just the final cumulative time — still contributes that split, at the cumulative distance implied by its slot position.

**`Z0` — File terminator**
- *M1:* `"Z0"` header. Resets parser context. Notes map to `SourceFile.notes`. FILE code is cross-checked against parsed record counts (mismatch warns).

## Edge cases handled

- **BOM & Line Endings:** Stripped and normalized.
- **Short/Long Lines:** Right-padded (< 160) or skipped (> 160).
- **Unattached:** Auto-detected by LSC prefix or `"unattached"` names.
- **Missing course byte `*`:** Kept with `course=None` + warning. Course `X` sets `status=DQ` and retains recorded time.
- **Relay-only swimmers:** Created with no `IndividualSwim` if all event fields are blank.
- **Relay alternates:** Swimmers with order `ALTERNATE` are routed to `Relay.alternates` instead of `legs`, and excluded from `Swimmer.swims`.
- **Relay legs fanning out:** A single `F0` spanning multiple sessions creates one `RelaySwim` per session. The single `F0` leg time is filed on the finals leg; splits from `G0` records tag their respective session swims.
- **Splits attachment:** Attachment links to the preceding `D0`/`F0` swum session based on the G0's `prelims/finals` code.
- **Blank split slots:** Skipped individually; a recorded split in a later slot is still kept (no information is lost when an earlier split is missing).

## Performance

- Scans single-pass.
- Performs **O(1)** swimmer and club lookups.
- Scales linearly with file size.
- Streams files line-by-line.
