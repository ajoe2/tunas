# Parsing & errors

The parser is exposed as two top-level functions that parse `.cl2` (SDIF) and `.hy3` (Hy-Tek) result files into structured [`Meet`](models.md) objects:

```python
from tunas import read_cl2, read_hy3
```

Both return a **lazy iterator** of [`MeetArchive`](#meetarchive) objects — one per source file. Parsing is lenient by default, recovering from non-fatal formatting issues and collecting warnings.

## `MeetArchive`

Each item yielded by a reader is the parse result for a single source file (or stream):

```python
@dataclass(slots=True)
class MeetArchive:
    source: str                # file path, or "<stream>" for a text stream
    meets: list[Meet]          # a file may hold more than one meet
    report: ParseReport        # diagnostics and counts for THIS source only
```

Because the readers yield archives lazily and per file, a large corpus is parsed one file at a time — the whole object graph is never held in memory at once, and each file's diagnostics stay attached to that file rather than being merged into one global report. To pull everything into memory, drain the iterator:

```python
# all meets, flattened across files
meets = [m for arc in read_cl2("season/") for m in arc.meets]

# or process and discard one file at a time (bounded memory)
for arc in read_cl2("season/"):
    handle(arc.source, arc.meets, arc.report)
```

## `read_cl2`

```python
def read_cl2(
    source: str | os.PathLike | Iterable[str | os.PathLike] | TextIO,
    *,
    strict: bool = False,
    encoding: str = "cp1252",
    errors: str = "replace",
) -> Iterator[MeetArchive]: ...
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `source` | `str \| Path \| Iterable[Path] \| TextIO` | Input source — path, directory, list of paths, or text stream. |
| `strict` | `bool` | If `True`, any warning raises a `ParseError`. If `False` (default), collects warnings and continues. **M1 structural violations always raise.** |
| `encoding` | `str` | Text encoding for file paths. Defaults to `"cp1252"` (common for SDIF/DOS files) to preserve alignments and accented names. |
| `errors` | `str` | Encoding error policy. Defaults to `"replace"`. |

### Lazy iteration

Parsing is single-threaded and lazy: each file is read and parsed only when you consume its archive, so a whole season's corpus is processed one file at a time without ever holding every meet in memory at once.

```python
for arc in read_cl2("season_archive/"):
    handle(arc.meets, arc.report)  # previous archive is freed before the next file is parsed
```

Archives are yielded in source order, and in `strict` mode the earliest failing file raises first. The lazy iterator (one archive per file) keeps peak memory flat regardless of corpus size — that is the main scaling lever.

!!! note "Why single-threaded"
    Parsing is CPU-bound pure Python. On a standard (GIL) interpreter a thread pool only overlaps file I/O and can be measurably *slower* under contention; even on a free-threaded build (3.13t+) the speed-up is sublinear and plateaus — cross-thread contention on shared immutables (`Event`/`Stroke`/`Course` enum members, interned strings) and cyclic-GC coordination over the cross-referenced meet graph dominate. A concurrent reader added complexity for no reliable gain, so `tunas` parses sequentially. To use multiple cores, shard the file list across separate processes.

### Source types

1. **File path:** Single `.cl2` file → one archive.
2. **Directory path:** Walked recursively for `*.cl2` files (case-insensitive) → one archive per file, in sorted path order.
3. **Iterable of paths:** One archive per path, in the given order.
4. **Text stream:** One archive (uses `"<stream>"` as its `source`). Stream must yield `str`, not `bytes`.

No cross-file merging or deduplication is performed: each file's meets, swimmers, and clubs stay in their own archive.

### Examples

```python
# Directory walk — one archive per file
for arc in read_cl2("results_dir/"):
    print(arc.source, len(arc.meets))

# Strict validation (errors surface as the iterator is consumed)
try:
    for arc in read_cl2("messy.cl2", strict=True):
        ...
except ParseError as exc:
    print(f"Failed at line {exc.warning.line_no}: {exc.warning.reason}")
```

## `read_hy3`

`read_hy3` parses Hy-Tek's proprietary `.hy3` format into the same [`Meet`](models.md) structure as `read_cl2`. Its signature, options, and source handling behavior are identical to `read_cl2`:

```python
def read_hy3(
    source: str | os.PathLike | Iterable[str | os.PathLike] | TextIO,
    *,
    strict: bool = False,
    encoding: str = "cp1252",
    errors: str = "replace",
) -> Iterator[MeetArchive]: ...
```

```python
from tunas import read_hy3

(archive,) = read_hy3("Meet Results-Winter Champs-001.hy3")  # a single file -> one archive
meets, report = archive.meets, archive.report
```

### Supported records and fields

`read_hy3` parses only the confirmed fields (marked **C**) documented in the [`.hy3` reference](../formats/hy3_format.md). It processes `A1`, `B1`/`B2`, `C1`/`C3`, `D1`, `E1`/`E2`, `F1`/`F2`/`F3`, `G1`, and `H1`/`H2` records. Unconfirmed or unmapped records (like `C2` and `C8`) are skipped silently.

The following model fields are populated exclusively by `read_hy3` (remaining `None` or at their defaults under `read_cl2`):

| Field | Source |
|---|---|
| [`SourceFile`][tunas.models.SourceFile]`.hy3_file_type` / `.created_time` / `.licensee` | `A1` |
| [`Meet`][tunas.models.Meet]`.venue` / `.age_up_date` / `.sanction_number` | `B1` / `B2` |
| [`Club`][tunas.models.Club]`.email` | `C3` |
| [`MeetResult`][tunas.models.MeetResult]`.dq_code` / `.dq_reason` | `E2`/`F2` + `H1`/`H2` |
| `MeetResult.converted_seed_time` / `.converted_seed_course` | `E1`/`F1` (converted seed) |
| `MeetResult.backup_times` | `E2`/`F2` manual watch times |
| [`Relay`][tunas.models.Relay]`.splits` | `G1` (whole-relay cumulative splits) |

Exhibition swims (status `S`) are parsed as [`ResultStatus`][tunas.ResultStatus]`.EXHIBITION`.

### Differences from `read_cl2`

These differences reflect genuine format variation, not parser limitations:

- **Zero times**: A `.hy3` time of `0.00` ("no time") is parsed as `None`.
- **Disqualifications**: Preserves the swum `time` (SDIF sets it to `None`) and populates `dq_code` and `dq_reason`.
- **Seed times**: Populates both the original `seed_time`/`seed_course` and the converted-course fields.
- **Relay splits**: Parsed into `Relay.splits` as whole-relay cumulative splits. Individual splits attach to `IndividualSwim.splits` as usual. `0.00` placeholders are ignored.
- **Swimmer IDs**: Populates `Swimmer.id_short` with the 14-character `.hy3` member ID. `id_long` is unused.
- **Checksums**: Line checksums (columns 129–130) are not validated, as they are omitted in some exports (e.g. `USAS Club Times Export`).

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
carried by each file's [`MeetArchive`](#meetarchive) (`arc.report`).

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
for arc in read_cl2("messy_data/"):
    for w in arc.report.warnings:
        print(f"{w.source}:{w.line_no} ({w.record_type}) [{w.severity.value}]: {w.reason}")
```

## Exceptions

All library errors subclass [`TunasError`][tunas.exceptions.TunasError], so a single
`except TunasError` catches everything tunas raises.

- **`ParseError`** — raised on a fatal M1 violation, or on the first warning when
  `strict=True`. Its `.warning` attribute is the underlying `ParseWarning`:

  ```python
  try:
      for arc in read_cl2(path, strict=True):
          ...
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
- **Relay legs fanning out:** A single `F0` spanning multiple sessions creates one `RelaySwim` per session. The single `F0` leg time is filed on the finals leg.
- **Relay splits:** A relay's `G0` records carry whole-relay cumulative splits, attached to the relay row (`Relay.splits`) with distances climbing 50/100/150/200/… across the records — matching the `.hy3` reader. Relays whose `G0`s follow the `E0` with no `F0` legs still attach to the row rather than being dropped. Each leg's `RelaySwim.splits` is then *derived* from that row (re-based to the leg start), and empty when there is nothing to derive.
- **Individual splits attachment:** For individual swims, `G0` splits link to the preceding `D0` swum session based on the G0's `prelims/finals` code.
- **Blank split slots:** Skipped individually; a recorded split in a later slot is still kept (no information is lost when an earlier split is missing).

## Performance

- Scans single-pass.
- Performs **O(1)** swimmer and club lookups.
- Scales linearly with file size.
- Streams files line-by-line.
- Yields archives lazily, one file at a time: a consumer that processes and discards each archive keeps peak memory bounded by a single file's object graph, not the whole corpus.
