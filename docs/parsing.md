# `tunas.parser` — reading `.cl2` files

The parser turns one or more `.cl2` files into a list of `Meet` objects
plus a `ParseReport`. It is exposed as a single function:

```python
from tunas import read_cl2
```

## `read_cl2`

```python
def read_cl2(
    source: str | os.PathLike | Iterable[str | os.PathLike] | TextIO,
    *,
    strict: bool = False,
    encoding: str = "utf-8",
    errors: str = "replace",
) -> tuple[list[Meet], ParseReport]: ...
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `source` | `str` or `Path` or iterable of paths or text file-like | What to parse — see *source types* below. |
| `strict` | `bool` | If `True`, raise `ParseError` on the first malformed record. If `False` (the default), append a `ParseWarning` to the returned report and continue. |
| `encoding` | `str` | Text encoding used when reading from a file path. Defaults to `"utf-8"`; some legacy exports use `"cp1252"`. Ignored when `source` is a file-like object. |
| `errors` | `str` | The encoding error policy. Defaults to `"replace"` (corrupt bytes become `U+FFFD`), which matches the original tunas behavior and is appropriate for real-world `.cl2` files. Set to `"strict"` for fail-fast decoding. |

### Source types

`source` accepts four shapes:

1. **A single file path** (`str` or `os.PathLike`): the file is parsed.
2. **A directory path**: walked recursively for files matching `*.cl2`
   (case-insensitive). All files are parsed into one shared state, so a
   swimmer who appears in two files becomes one merged `Swimmer`.
3. **An iterable of paths**: each is parsed in order into shared state.
   Equivalent semantics to passing a directory that contains those files.
4. **A text file-like object** (anything with `.read()` returning `str`):
   parsed from the buffer. Useful for testing and for parsing files
   downloaded into memory.

### Return value

A tuple `(meets, report)`:

- `meets: list[Meet]` — one entry per B1/Z0 block encountered across all
  inputs. Order matches the order meets first appear in the source.
- `report: ParseReport` — summary statistics and any warnings (see below).

### Examples

```python
# Single file
meets, report = read_cl2("results.cl2")

# Directory walk
meets, report = read_cl2("results_dir/")

# Explicit list
meets, report = read_cl2(["meet1.cl2", "meet2.cl2"])

# In-memory buffer
import io
text = open("results.cl2").read()
meets, report = read_cl2(io.StringIO(text))

# Strict mode — first malformed record raises
meets, report = read_cl2("results.cl2", strict=True)
```

## `ParseReport`

```python
@dataclass
class ParseReport:
    warnings: list[ParseWarning] = field(default_factory=list)
    files_read: int = 0
    meets_parsed: int = 0
    swimmers_parsed: int = 0
    individual_results_parsed: int = 0
    relay_results_parsed: int = 0
    splits_parsed: int = 0

    @property
    def has_warnings(self) -> bool: ...
```

The fields are populated as the parser runs and reflect the entire call.
`swimmers_parsed` counts **distinct** swimmers after merging, not raw D0
record count.

## `ParseWarning`

```python
@dataclass(frozen=True)
class ParseWarning:
    source: str             # file path, or "<stream>" for file-like input
    line_no: int            # 1-indexed
    record_type: str | None # e.g. "D0", or None if the header was unreadable
    reason: str             # human-readable explanation
    raw_line: str           # the offending line (truncated to 200 chars)
```

Frozen and hashable, so warnings can go in a set if you want to de-dup
across multiple `read_cl2` calls.

## Strict vs lenient mode

The default lenient mode silently skips malformed records and records a
warning for each:

```python
meets, report = read_cl2("messy.cl2")
print(report.has_warnings)             # True
for w in report.warnings:
    print(f"{w.source}:{w.line_no} ({w.record_type}): {w.reason}")
```

Strict mode raises a `ParseError` on the first malformed record. The
exception carries the underlying `ParseWarning` for inspection:

```python
try:
    meets, _ = read_cl2("messy.cl2", strict=True)
except ParseError as exc:
    w = exc.warning
    print(f"failed at {w.source}:{w.line_no}: {w.reason}")
```

**Use lenient mode for ingesting real data.** Use strict mode for
testing, validation pipelines, or when you have a known-good upstream
and want to be alerted if it regresses.

## Multi-file semantics

When multiple files are parsed in one call, the parser maintains a single
shared `_ParserState`. Entities are deduplicated across files using the
rules in [models.md → multi-file merging](models.md#multi-file-merging--rules):

- **Clubs** are merged on `(team_code, lsc)`. Null fields are filled from
  the second file; non-null fields are preserved.
- **Swimmers** are merged first on `usa_id_short`, then on
  `(first_name, last_name, birthday)`. Same null-fill rule.
- **Meets** are merged on `(name, start_date, organization)`. Result
  lists are concatenated.

A swimmer who races at two meets in two files therefore appears as
exactly one `Swimmer` whose `individual_results` spans both.

Single-call semantics: order of files within one call does not affect
the final domain model (only the order of warnings in the report).
**Cross-call semantics:** every `read_cl2` call returns fresh objects.
Merging across calls is the application's responsibility.

## Record types and handling

The parser handles every record type defined in SDIF v3:

| Record | Purpose | Handling |
|---|---|---|
| `A0` | File description header | Read for metadata, no domain object created. |
| `B1` | Meet record | Creates a `Meet`. |
| `B2` | Meet host | Enriches the current `Meet` with `host_team_code`, `host_phone`. |
| `C1` | Team / club | Creates or merges a `Club`, or marks the swimmer context unattached. |
| `C2` | Team entry | Enriches the current `Club` with coach name and `entry_counts`. |
| `D0` | Individual event entry/result | Creates `IndividualMeetResult` records (one per session). Resolves or creates a `Swimmer`. |
| `D1` | Address continuation | Populates `IndividualMeetResult.swimmer_contact` (PII). |
| `D2` | Phone/email continuation | Populates `IndividualMeetResult.swimmer_contact` (PII). |
| `D3` | Long ID / preferred name | Updates the current `Swimmer` with `usa_id_long` and `preferred_first_name`. |
| `E0` | Relay event | Creates a `RelayMeetResult`. |
| `F0` | Relay name | Appends a `RelayLeg` to the current `RelayMeetResult`. Resolves the swimmer reference. |
| `G0` | Splits | Appends `Split` entries to the current individual or relay result. |
| `Z0` | File terminator | Resets the current meet/club/swimmer/result context. |

Trailing records that depend on an earlier record (D1/D2 after D0, F0
after E0, G0 after D0 or F0) are bound to the most recent matching
context. If the antecedent is missing, a warning is emitted and the
trailing record is dropped (or it raises `ParseError` in strict mode).

## Edge cases the parser handles

These cases appear in real-world `.cl2` exports and are handled
deliberately. Each entry below results in either a successful parse, a
warning + skip, or — in strict mode — a `ParseError`.

### Encoding

- **Non-UTF-8 bytes** (legacy CP-1252 input): replaced with `U+FFFD` by
  default (`errors="replace"`). Pass `errors="strict"` for fail-fast.
- **BOM marker** at start of file: stripped silently.
- **Mixed line endings** (`\r\n`, `\r`, `\n`): normalized.

### Record-level

- **Line length not 162 chars**: skipped + warning. The SDIF spec
  mandates exactly 162-byte records (160 data + 2-byte checksum).
- **Unknown 2-char record header**: ignored silently (forward-compatible
  with future SDIF revisions).
- **Trailing whitespace** on a record: trimmed; record still processed.

### Meet (`B1`)

- **Malformed date** (MM/DD/YYYY parsing fails): skipped + warning. The
  meet is not created.
- **Missing course code**: `Meet.course = None`.
- **Invalid course letter** (not `S`, `Y`, `L`, `1`, `2`, or `3`):
  `Meet.course = None` + warning.

### Club (`C1`)

- **Unattached detection**: any of `lsc_code == "UN"`, `team_code.upper()
  == "UN"`, `"unattached" in name.lower()`, or `("UN" in team_code and
  "unat" in name.lower())` ⇒ no `Club` created; the swimmer context is
  marked unattached.
- **Invalid LSC code**: `Club.lsc = None` + warning.
- **Invalid state / country code**: field set to `None` + warning.
- **Duplicate club** (same `(team_code, lsc)`): merged, null-fill rules.

### Swimmer / individual result (`D0`)

- **`usa_id_short` not 12 chars**: skipped + warning. Result not created.
- **Unknown stroke code**: skipped + warning.
- **Name parsing fails**: skipped + warning.
- **Missing birthday**: `Swimmer.birthday = None`. **No inference** —
  unlike the original tunas tool, this library never reverse-engineers a
  birthday from the legacy USS# format.
- **Missing or `ignored` finish times** (`""`, `"NT"`, `"NS"`, `"DNF"`,
  `"DQ"`, `"SCR"`): the result for that session is not created. Not a
  warning — these are normal entries in heat sheets.
- **Place value `≤ 0`**: `rank = None`. Not a warning.
- **Invalid course code** on prelim/finals/swim-off: the result for that
  session is not created + warning.
- **Invalid event-age code** (`"UN<NN>"` / `"<NN>OV"`): `event_min_age =
  0` / `event_max_age = 1000`.
- **Swimmer match across files**: if a later `D0` references a swimmer
  who already exists (by `usa_id_short`, then by `(name, birthday)`),
  the existing swimmer is reused and its fields are null-filled.

### Long ID / preferred name (`D3`)

- **No preceding `D0`**: silently ignored (no `current_swimmer` to
  update).
- **`usa_id_long` not 14 chars**: ignored.
- **Old-format ID** (legacy 14-char USS#): not stored as
  `usa_id_long`. The library only stores the new long-ID format.

### Relay event (`E0`)

- **Event not resolvable** (`Event.find(distance, stroke, course)`
  returns `None`): the relay is skipped + warning.
- **Missing date** or **invalid course**: warning, fields set to `None`,
  relay still created if possible.

### Relay name (`F0`)

- **No preceding `E0`**: skipped + warning. The leg cannot be attached
  to a relay.
- **Swimmer cannot be resolved** from name + USS# + birthday: a leg is
  still created with `swimmer = None` and a warning is emitted.
- **More than 4 F0 records for one E0**: extra legs are stored but a
  warning is emitted (alternates may be reported on additional records
  per the spec; the library preserves them).

### Splits (`G0`)

- **No preceding `D0` or `F0`**: skipped + warning.
- **Out-of-order sequence numbers**: splits from later sequence numbers
  are appended; final ordering is by `distance` ascending.
- **Invalid split type code**: `SplitType.CUMULATIVE` assumed +
  warning.

### File-level

- **Missing `Z0`**: tolerated. The parser flushes its state at EOF.
- **Multiple `B1`s without intervening `Z0`s**: each `B1` ends the prior
  meet implicitly + warning.
- **Truncated file**: tolerated. Counts in `ParseReport` reflect what
  was successfully read.

## Performance notes

- The parser is **single-pass** with **O(1) lookups** by `usa_id_short`,
  `(team_code, lsc)`, and `(first_name, last_name, birthday)`. Parsing
  scales roughly linearly with file size.
- Reading from a file path streams line-by-line; the whole file is not
  held in memory.
- Reading from a file-like reads `.read()` once. If you have a very
  large in-memory buffer, prefer writing it to a temp file and passing
  the path.

## Strict-mode invariant

In strict mode, every situation listed above as "+ warning" instead
raises `ParseError(warning)`. The exception is raised at the first such
record, with all previously parsed records preserved on the partially
constructed `Meet` objects (but `read_cl2` does not return them — they
go away when the exception unwinds).

## See also

- [`models.md`](models.md) — the dataclasses the parser produces.
- [`cl2_format.md`](cl2_format.md) — background on SDIF v3.
- [`exceptions.md`](exceptions.md) — error hierarchy.
