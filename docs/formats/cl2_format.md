# The `.cl2` / SDIF v3 file format

`.cl2` files contain USA-Swimming meet results in **Standard Data Interchange Format
version 3 (SDIF v3)** — the format produced and consumed by Hy-Tek Meet Manager and
TeamUnify, and parsed by `tunas`.

This page is a **complete field-level reference** for SDIF v3: every record type, every
field (column position, mandatory level, data type), and every code table. It then marks,
inline and in [§7](#7-how-real-cl2-files-deviate-from-the-spec), **where real-world `.cl2`
files deviate from the published standard** — based on an empirical sweep of **2,190 files
/ 6,354,732 records** from two LSCs (Pacific and Michigan).

!!! info "How to read the deviation marks"
    The authoritative SDIF v3 specification is bundled verbatim with the library at
    `src/tunas/_data/sdif-v3.txt`; the tables below are derived from it. A
    **🔶 cl2:** note flags an **empirically verified** divergence or convention of real
    Hy-Tek/TeamUnify output — every such note states the measured fact (and its rate) from
    the 2,190-file corpus. Fields with no note behave as the spec describes. Nothing is
    marked on suspicion; only on counted evidence.

??? note "Introduction — official SDIF v3 (April 28, 1998), abridged"
    United States Swimming developed a standard interchange format for technical data so
    swimming data could be transmitted among clubs, Local Swimming Committees (LSCs), and the
    USS headquarters office — distributing meet results to swimmers and clubs, and letting
    LSCs compile statistics without retyping printed sheets. An ad-hoc committee, with input
    from US Masters Swimming and a coach familiar with high-school and college requirements,
    prepared the design so all aquatic-sports organizations could share one standard; new
    records, codes, and fields can be added.

    The format is **modular and fixed-length**. Each file combines records in an order that
    matches the data being transmitted (meet entries have one order, time standards another),
    and record types that aren't needed are simply omitted. The file structure implies an
    order of less-frequent data preceding more-frequent data (one meet, multiple teams,
    multiple athletes per team). Certain fields are declared **mandatory** to identify the
    data adequately and to preserve unique identifiers.

---

## 1. Physical record format

- Each record is a **fixed 162 bytes**: **160 data bytes + CR (byte 161) + LF (byte 162)**.
- Bytes **1–2** are a case-sensitive **record-type code** (`A0`, `B1`, …).
- Fields occupy fixed columns; **unused ("future use") space must be blank-filled**.
- Only **two records are required** — `A0` (first) and `Z0` (last); all others are optional.

    > 🔶 cl2: **Confirmed.** Every one of 6,354,732 records was 160 data chars (2 lone
    > 159-char lines aside), terminated by **CRLF**, with `A0` the first and `Z0` the last
    > record in 100% of 2,190 files. Files are encoded **CP-1252**, not 7-bit ASCII —
    > accented names use high bytes (decode as CP-1252 to keep columns aligned). The spec
    > states the extension is `.SD3`; meet-results files are distributed as **`.cl2`**
    > (and sometimes `.sd3`) — same format.

### Field data types

| Type | Meaning |
|---|---|
| `CONST` | Literal constant (the 2-char record code) |
| `ALPHA` | Text, left-justified; numeric-only ALPHA right-justified |
| `INT` | ASCII digits, right-justified, blank-filled |
| `DEC` | ASCII digits, right-justified; optional decimal point |
| `CODE` | Value from a code table (§6); **case-sensitive, exact match** |
| `DATE` | `MMDDYYYY`, zero-filled, no blanks |
| `TIME` | `mm:ss.ss` (colon at byte 3, period at byte 6), **or** all-blank, **or** a TIME code (`NT`/`NS`/`DNF`/`DQ`/`SCR`) |
| `PHONE` | Free-form phone number |
| `USPS` | Two-letter US Postal state abbreviation, capitalized |
| `NAME` | `Last, First MI` packed into the field width |
| `USSNUM` | 14-char USA-Swimming member ID — see [construction](#field-format-conventions) |
| `LOGICAL` | Upper-case `T`, upper-case `F`, or blank |

### Mandatory levels

| Level | Meaning |
|---|---|
| **M1** | Must contain a non-blank, valid entry for the record to be usable |
| **M2** | Should be present; a reader must report (not reject) a blank M2 field |
| *(blank)* | Optional |
| `*` / `**` / `#` | Conditional — see the footnotes under each record |

### Field-format conventions

From the spec's *Format Design* section — the rules behind the blank-handling and
justification seen in real files:

- **"No blanks" vs "non-blank".** *No blanks* means not a single blank **anywhere** in the
  field; *non-blank* means blanks **may** appear, but the field must hold **at least one**
  non-blank character.
- **POSTAL CODE** may be left- *or* right-justified, but should keep leading zeroes where
  defined (e.g. a Vermont ZIP of `05452`).
- **DATE** (`MMDDYYYY`) must contain no blanks when supplied — zero-fill each part.

**USSNUM construction.** The member ID packs **`MMDDYY` birth date + first 3 letters of the
legal first name + middle initial + first 4 letters of the last name**. An **asterisk**
fills any position with no available character (missing MI, or a name too short to fill its
slots), and special characters are stripped first:

| Swimmer | USSNUM |
|---|---|
| Catherine A. Durance | `011553CATADURA` |
| Cy V. Young | `091879CY*VYOUN` |
| Thomas Chu | `020981THO*CHU*` |
| Ty Lee | `011873TY**LEE*` |
| Dave T. O'Neil | `030367DAVTONEI` |

---

## 2. Record hierarchy

```
A0  File description ....... 1 per file (required, first)
 B1 Meet ................... 1 per file
  B2 Meet host ............. optional
   C1 Team ID .............. 1 per team
    C2 Team entry .......... coach + record counts (optional)
     D0 Individual event ... 1 per individual splash
      D3 Individual info ... new USS#, preferred name (1 after a swimmer's first D0)
       G0 Splits ........... 0+ per D0
     E0 Relay event ........ 1 per relay squad
      F0 Relay name ........ 4+ per E0 (legs + alternates)
       G0 Splits ........... 0+ per F0
Z0  File terminator ........ 1 per file (required, last)
```

The spec also defines records for other transmission types — `D1`/`D2` (LSC registration),
`J0`/`J1`/`J2` (time-standard lists) — documented in [§5](#5-records-not-used-by-meet-results).

> 🔶 cl2: **Confirmed.** Across 2,190 meet-results files the *only* record codes that ever
> appear are **`A0 B1 C1 D0 D3 E0 F0 G0 Z0`**. `B2`, `C2`, `D1`, `D2`, `J0`, `J1`, `J2`
> were **never emitted** (0 occurrences in 6.35 M records). These are optional or belong to
> other transmission pyramids, so omitting them is spec-legal — but note the `D0` record's
> own rule (below) that it "must be preceded by a `C1` **and** a `C2`": real files supply
> `C1` only and rely on the C2-absent fallback.

### Other transmission pyramids

The tree above is the **Meet pyramid**. The spec defines three more record orders for other
transmission types; their records are detailed in
[§5](#5-records-not-used-by-meet-results) but **never appear in meet-results `.cl2`**.

**Record Times** (Top-16 / record times — for Top-16 only, multiple meets are allowed):

```
A0  File description
 D0 Individual event ... 1 per time achieved
  D3 Individual info
   G0 Splits ........... 0+ per D0
Z0  File terminator
```

**Time Standards:**

```
A0  File description
 J0 Meet qualifying times .. 1 per event (all pool types)
 J1 NAG qualifying times ... 1 per event + course
 J2 USS motivational times . 1 per event + level
Z0  File terminator
```

**LSC Registration:**

```
A0  File description
 C1 Team ID
  D1 Individual administrative .. 1 per swimmer
  D2 Individual contact ......... 1 per swimmer
  D3 Individual info ............ 1 per swimmer
Z0  File terminator
```

---

## 3. Common records

### A0 — File description (required, first record)

| Cols | M | Type | Field |
|---|---|---|---|
| 1–2 | M1 | CONST | `A0` |
| 3 | M2 | CODE | ORG code (001) |
| 4–11 | | ALPHA | SDIF version number |
| 12–13 | M1 | CODE | FILE / transmission type (003) |
| 14–43 | | | future use |
| 44–63 | | ALPHA | software name |
| 64–73 | | ALPHA | software version |
| 74–93 | M1 | ALPHA | contact name |
| 94–105 | M1 | PHONE | contact phone |
| 106–113 | M1 | DATE | file creation/update date |
| 114–155 | | | future use |
| 156–157 | | ALPHA | submitted-by LSC (Top-16) |
| 158–160 | | | future use |

> 🔶 cl2: contact name and phone (both M1) are **populated in 100%** of files. FILE code is
> `02` (Meet Results) for normal exports.

> **Spec note.** In the spec these A0 fields (plus software name/version) carry an extra
> `*`, marking them as *additionally* required when the file submits **LSC-registration**
> data. For meet results, the plain M1/M2 levels shown above apply.

### B1 — Meet (1 per file)

| Cols | M | Type | Field |
|---|---|---|---|
| 1–2 | M1 | CONST | `B1` |
| 3 | M2 | CODE | ORG code (001) |
| 4–11 | | | future use |
| 12–41 | M1 | ALPHA | meet name |
| 42–63 | | ALPHA | meet address line 1 |
| 64–85 | | ALPHA | meet address line 2 |
| 86–105 | M2 | ALPHA | meet city |
| 106–107 | M2 | USPS | meet state |
| 108–117 | | ALPHA | postal code |
| 118–120 | | CODE | COUNTRY code (004) |
| **121** | **M2** | CODE | **MEET type code (005)** |
| 122–129 | M1 | DATE | meet start |
| 130–137 | M2 | DATE | meet end |
| 138–141 | | INT | altitude of pool (feet) |
| 142–149 | | | future use |
| 150 | | CODE | COURSE code (013) — default course |
| 151–160 | | | future use |

> 🔶 cl2: **The M2 meet-type field (col 121) is blank in 100%** of 2,190 files — Hy-Tek
> never records the meet type. The course field (col 150) uses the **alpha** course
> alternative: `Y` (1,731 files) / `L` (429) / `S` (30). Meet state (M2) is blank in 8.6%.

### B2 — Meet host (optional)

| Cols | M | Type | Field |
|---|---|---|---|
| 1–2 | M1 | CONST | `B2` |
| 3 | M2 | CODE | ORG code (001) |
| 4–11 | | | future use |
| 12–41 | M2 | ALPHA | meet host name |
| 42–63 | | ALPHA | host address line 1 |
| 64–85 | | ALPHA | host address line 2 |
| 86–105 | | ALPHA | host city |
| 106–107 | | USPS | host state |
| 108–117 | | ALPHA | postal code |
| 118–120 | | CODE | COUNTRY code (004) |
| 121–132 | | PHONE | meet host phone |
| 133–160 | | | future use |

> 🔶 cl2: **Never emitted** (0 of 2,190 files). Meet-host data, when present, lives in the
> sibling `.hy3` file's `B2` record, not the `.cl2`.

### C1 — Team ID (1 per team)

| Cols | M | Type | Field |
|---|---|---|---|
| 1–2 | M1 | CONST | `C1` |
| 3 | M2 | CODE | ORG code (001) |
| 4–11 | | | future use |
| 12–17 | M1 | CODE | TEAM code (006) — 2-char LSC + 4-char team |
| 18–47 | M1 | ALPHA | full team name |
| 48–63 | | ALPHA | abbreviated team name |
| 64–85 | | ALPHA | team address line 1 |
| 86–107 | | ALPHA | team address line 2 |
| 108–127 | | ALPHA | team city |
| 128–129 | | USPS | team state |
| 130–139 | | ALPHA | postal code |
| 140–142 | | CODE | COUNTRY code (004) |
| 143 | | CODE | REGION code (007) |
| 144–149 | | | future use |
| 150 | | ALPHA | optional 5th char of team code |
| 151–160 | | | future use |

> 🔶 cl2: **non-USPS values appear in the state field** — e.g. `ON` (Ontario, a Canadian
> province, not a USPS state) — and `---` appears in the COUNTRY field; both are outside
> the spec's typed/table-checked domain (rare: ~tens of records).

### C2 — Team entry (optional: coach + counts)

| Cols | M | Type | Field |
|---|---|---|---|
| 1–2 | M1 | CONST | `C2` |
| 3 | M2 | CODE | ORG code (001) |
| 4–11 | | | future use |
| 12–17 | M2 | CODE | TEAM code (006) |
| 18–47 | M2 | ALPHA | coach name |
| 48–59 | | PHONE | coach phone |
| 60–65 | | INT | # individual entries (= D0 count) |
| 66–71 | | INT | # different athletes |
| 72–76 | | INT | # relay entries (= E0 count) |
| 77–82 | | INT | # relay swimmer entries (= F0 count) |
| 83–88 | | INT | # split records (= G0 count) |
| 89–104 | | ALPHA | short team name (display) |
| 105–149 | | | future use |
| 150 | | ALPHA | optional 5th char of team code |
| 151–160 | | | future use |

> 🔶 cl2: **Never emitted** (0 of 2,190 files). Consequently the per-team entry counts and
> coach name are unavailable from `.cl2`, and `D0` records are preceded by `C1` only.

---

## 4. Swim records

### D0 — Individual event (1 per individual splash)

| Cols | M | Type | Field |
|---|---|---|---|
| 1–2 | M1 | CONST | `D0` |
| 3 | M2 | CODE | ORG code (001) |
| 4–11 | | | future use |
| 12–39 | M1 | NAME | swimmer name |
| 40–51 | M2 | ALPHA | USS# (12-char) |
| 52 | | CODE | ATTACH code (016) |
| 53–55 | | CODE | CITIZEN code (009) |
| 56–63 | M2 | DATE | swimmer birth date |
| 64–65 | | ALPHA | swimmer age or class (e.g. `Jr`/`Sr`) |
| 66 | M1 | CODE | SEX code (010) |
| 67 | M1# | CODE | EVENT SEX code (011) |
| 68–71 | M1# | INT | event distance |
| 72 | M1# | CODE | STROKE code (012) |
| 73–76 | | ALPHA | event number |
| 77–80 | M1# | CODE | EVENT AGE code (025) |
| 81–88 | M2 | DATE | date of swim |
| 89–96 | | TIME | seed time |
| 97 | * | CODE | COURSE of seed time (013) |
| 98–105 | | TIME | prelim time |
| 106 | * | CODE | COURSE of prelim time (013) |
| 107–114 | | TIME | swim-off time |
| 115 | * | CODE | COURSE of swim-off time (013) |
| 116–123 | | TIME | finals time |
| 124 | * | CODE | COURSE of finals time (013) |
| 125–126 | | INT | prelim heat |
| 127–128 | | INT | prelim lane |
| 129–130 | | INT | finals heat |
| 131–132 | | INT | finals lane |
| 133–135 | ** | INT | prelim place ranking |
| 136–138 | ** | INT | finals place ranking |
| 139–142 | ** | DEC | points scored (finals) |
| 143–144 | | CODE | EVENT TIME CLASS code (014) |
| 145 | | ALPHA | flight status (time-standard subdivision) |
| 146–160 | | | future use |

`*` mandatory **iff** the immediately preceding time field is non-blank. `**` mandatory
(M1) only for championship meets (MEET code 6/7). `#` event sex/distance/stroke/age and
seed are not mandatory for relay-only swimmers.

> **Spec note.** The spec reserves *"an additional record type … for open water swimming"*
> and requires **multiple D0 records when there are multiple swim-offs**.

> 🔶 cl2:
> - **EVENT TIME CLASS (col 143–144) is blank in 100%** of 3,352,073 D0 records; **flight
>   status (col 145) is blank** in all but 1.
> - **Birth date (M2) is blank in 16.6%** of records — the privacy "WODOB" (without-DOB)
>   export practice — and **USS# (M2) is blank in 1.8%**.
> - **Citizenship is blank in 83%** (optional field, usually omitted; `USA` when present).
> - **A non-spec STROKE code `H` (diving)** appears 2,840× — the STROKE table (012) defines
>   only `1`–`7`. The seed-course code uses the alpha alternative (`Y`/`L`/`S`).
> - ATTACH is `A` (attached) or `U` (unattached); seen 3,325,716 / 26,357.

### D3 — Individual info (new USS# + preferred name)

| Cols | M | Type | Field |
|---|---|---|---|
| 1–2 | M1 | CONST | `D3` |
| 3–16 | M2 | USSNUM | USS# (new 14-char) |
| 17–31 | | ALPHA | preferred first name |
| 32–33 | * | CODE | ethnicity (026) |
| 34 | * | LOGICAL | Junior High School |
| 35 | * | LOGICAL | Senior High School |
| 36 | * | LOGICAL | YMCA/YWCA |
| 37 | * | LOGICAL | College |
| 38 | * | LOGICAL | Summer Swim League |
| 39 | * | LOGICAL | Masters |
| 40 | * | LOGICAL | Disabled Sports Org. |
| 41 | * | LOGICAL | Water Polo |
| 42 | * | LOGICAL | None |
| 43–160 | | | future use |

`*` required only for LSC registration submissions. One `D3` follows a swimmer's **first**
`D0` (or `F0`). It is the source of the modern 14-char SWIMS ID and the preferred name.

### E0 — Relay event (1 per relay squad)

| Cols | M | Type | Field |
|---|---|---|---|
| 1–2 | M1 | CONST | `E0` |
| 3 | M2 | CODE | ORG code (001) |
| 4–11 | | | future use |
| 12 | M1 | ALPHA | relay designator (`A`,`B`,… concatenated with team abbr) |
| 13–18 | M1 | CODE | TEAM code (006) |
| 19–20 | | INT | # F0 relay-name records to follow |
| 21 | M1 | CODE | EVENT SEX code (011) |
| 22–25 | M1 | INT | relay distance |
| 26 | M1 | CODE | STROKE code (012) |
| 27–30 | | ALPHA | event number |
| 31–34 | M1 | CODE | EVENT AGE code (025) |
| 35–37 | | INT | total age of all athletes |
| 38–45 | M2 | DATE | date of swim |
| 46–53 | | TIME | seed time |
| 54 | * | CODE | COURSE of seed (013) |
| 55–62 | | TIME | prelim time |
| 63 | * | CODE | COURSE of prelim (013) |
| 64–71 | | TIME | swim-off time |
| 72 | * | CODE | COURSE of swim-off (013) |
| 73–80 | | TIME | finals time |
| 81 | * | CODE | COURSE of finals (013) |
| 82–83 | | INT | prelim heat |
| 84–85 | | INT | prelim lane |
| 86–87 | | INT | finals heat |
| 88–89 | | INT | finals lane |
| 90–92 | ** | INT | prelim place ranking |
| 93–95 | ** | INT | finals place ranking |
| 96–99 | ** | DEC | points scored (finals) |
| 100–101 | | CODE | EVENT TIME CLASS code (014) |
| 102–160 | | | future use |

`*`/`**` as for D0.

> 🔶 cl2: the **non-spec STROKE code `H`** also appears here (245×). Relay strokes are
> otherwise `6` (free relay) / `7` (medley relay) as specified.

### F0 — Relay name (one per relay leg/alternate)

| Cols | M | Type | Field |
|---|---|---|---|
| 1–2 | M1 | CONST | `F0` |
| 3 | M2 | CODE | ORG code (001) |
| 4–15 | | | future use |
| 16–21 | M1 | CODE | TEAM code (006) |
| 22 | M1# | ALPHA | relay designator |
| 23–50 | M1 | NAME | swimmer name |
| 51–62 | M2 | ALPHA | USS# (12-char) |
| 63–65 | | CODE | CITIZEN code (009) |
| 66–73 | M2 | DATE | swimmer birth date |
| 74–75 | | ALPHA | swimmer age or class |
| 76 | M1 | CODE | SEX code (010) |
| 77 | M1 | CODE | ORDER (024) — prelim leg |
| 78 | M1 | CODE | ORDER (024) — swim-off leg |
| 79 | M1 | CODE | ORDER (024) — finals leg |
| 80–87 | | TIME | leg time |
| 88 | * | CODE | COURSE of leg time (013) |
| 89–92 | | DEC | automatic take-off time (`s.ss`) |
| 93–106 | M2 | USSNUM | USS# (new 14-char) |
| 107–121 | | ALPHA | preferred first name |
| 122–160 | | | future use |

`#` not mandatory for pre-finalized meet-entry teams. `*` mandatory iff preceding time
non-blank.

### G0 — Splits (0+ per D0 or F0)

| Cols | M | Type | Field |
|---|---|---|---|
| 1–2 | M1 | CONST | `G0` |
| 3 | M2 | CODE | ORG code (001) |
| 4–15 | | | future use |
| 16–43 | | NAME | swimmer name |
| 44–55 | | ALPHA | USS# |
| 56 | M1 | INT | sequence # (orders multiple G0 for one swim) |
| 57–58 | M1 | INT | total # splits for this event |
| 59–62 | M1 | INT | split distance |
| 63 | M1 | CODE | SPLIT code (015) — cumulative vs interval |
| 64–71 | | TIME | split time 1 |
| 72–79 | | TIME | split time 2 |
| 80–87 | | TIME | split time 3 |
| 88–95 | | TIME | split time 4 |
| 96–103 | | TIME | split time 5 |
| 104–111 | | TIME | split time 6 |
| 112–119 | | TIME | split time 7 |
| 120–127 | | TIME | split time 8 |
| 128–135 | | TIME | split time 9 |
| 136–143 | | TIME | split time 10 |
| 144 | | CODE | PRELIMS/FINALS code (019) |
| 145–160 | | | future use |

Up to ten split times per record; long races continue on further `G0` records ordered by
the col-56 sequence number. When the swimmer name (cols 16–43) is unavailable, the spec
says to enter the literal `NO SWIMMER NAME` (or another meaningful string).

### Z0 — File terminator (required, last record)

| Cols | M | Type | Field |
|---|---|---|---|
| 1–2 | M1 | CONST | `Z0` |
| 3 | M2 | CODE | ORG code (001) |
| 4–11 | | | future use |
| 12–13 | M1 | CODE | FILE / transmission type (003) |
| 14–43 | | ALPHA | notes |
| 44–46 | | INT | # B records |
| 47–49 | | INT | # different meets |
| 50–53 | | INT | # C records |
| 54–57 | | INT | # different teams |
| 58–63 | | INT | # D records |
| 64–69 | | INT | # different swimmers |
| 70–74 | | INT | # E records |
| 75–80 | | INT | # F records |
| 81–86 | | INT | # G records |
| 87–91 | | INT | batch number |
| 92–94 | | INT | # new members |
| 95–97 | | INT | # renew members |
| 98–100 | | INT | # member changes |
| 101–103 | | INT | # member deletes |
| 104–160 | | | future use |

> 🔶 cl2: the **# D records count (col 58–63) equals the actual `D0` record count in 100%**
> of 2,190 files — the terminator's D-count is reliable.

---

## 5. Records not used by meet results

The spec defines these for the **LSC-registration** and **time-standards** transmission
pyramids. They are documented here for completeness; **none appear in meet-results
`.cl2`** (🔶 cl2: 0 of 2,190 files).

### D1 — Individual administrative (registration; PII)

| Cols | M | Type | Field |
|---|---|---|---|
| 1–2 | M1 | CONST | `D1` |
| 3 | M2 | CODE | ORG code (001) |
| 12–17 | * | CODE | TEAM code (006) |
| 18 | | ALPHA | 5th char of team code |
| 19–46 | M1 | NAME | swimmer name |
| 48–59 | M2 | ALPHA | USS# |
| 60 | | CODE | ATTACH (016) |
| 61–63 | * | CODE | CITIZEN (009) |
| 64–71 | M2 | DATE | birth date |
| 72–73 | | ALPHA | age/class |
| 74 | M1 | CODE | SEX (010) |
| 75–104 | | ALPHA | admin info field 1 |
| 105–124 | * | ALPHA | old member number (on init/DOB change) |
| 125–136 | * | PHONE | phone 1 |
| 137–148 | | PHONE | phone 2 |
| 149–156 | * | DATE | USS registration date |
| 157 | * | CODE | MEMBER transaction (021) |
| 158–160 | | | future use |

### D2 — Individual contact (registration; mailing PII)

| Cols | M | Type | Field |
|---|---|---|---|
| 1–2 | M1 | CONST | `D2` |
| 3 | M2 | CODE | ORG code (001) |
| 12–17 | * | CODE | TEAM code (006) |
| 18 | | ALPHA | 5th char of team code |
| 19–46 | M1 | NAME | swimmer name |
| 47–76 | | ALPHA | alternate mailing name |
| 77–106 | * | ALPHA | mailing street |
| 107–126 | * | ALPHA | mailing city |
| 127–128 | * | USPS | mailing state |
| 129–140 | | ALPHA | mailing country |
| 141–150 | * | ALPHA | postal code |
| 151–153 | | CODE | COUNTRY (004) |
| 154 | | CODE | REGION (007) |
| 155 | * | CODE | ANSWER (023) — member of another FINA federation? |
| 156 | * | CODE | SEASON (022) |
| 157–160 | | | future use |

### J0 — Meet qualifying times

| Cols | M | Type | Field |
|---|---|---|---|
| 1–2 | M1 | CONST | `J0` |
| 3–10 | M1 | DATE | effective date |
| 11 | M1 | CODE | MEET (005) |
| 17 | M1 | CODE | EVENT SEX (011) |
| 18–21 | M1 | INT | distance |
| 22 | M1 | CODE | STROKE (012) |
| 23–30 | | TIME | SCY time |
| 31–38 | | TIME | SCM time |
| 39–46 | | TIME | LCM time |
| 47–50 | M1 | CODE | EVENT AGE (025) |
| 51 | | CODE | ZONE (017) |
| 52–53 | | CODE | REGION (007) |
| 54–55 | | CODE | LSC (002) |
| 56–160 | | | future use |

### J1 — National Age Group qualifying times

| Cols | M | Type | Field |
|---|---|---|---|
| 1–2 | M1 | CONST | `J1` |
| 3–10 | M1 | DATE | effective date |
| 11 | M1 | CODE | EVENT SEX (011) |
| 12–15 | M1 | INT | distance |
| 16 | M1 | CODE | STROKE (012) |
| 17–20 | M1 | CODE | EVENT AGE (025) |
| 21 | M1 | CODE | COURSE (013) |
| 22–29 | | TIME | BB |
| 30–37 | | TIME | B |
| 38–45 | | TIME | A |
| 46–53 | | TIME | AA |
| 54–61 | | TIME | AAA |
| 62–69 | | TIME | AAAA |
| 70–160 | | | future use |

### J2 — USS motivational times

| Cols | M | Type | Field |
|---|---|---|---|
| 1–2 | M1 | CONST | `J2` |
| 3 | M1 | CODE | EVENT SEX (011) |
| 4–7 | M1 | INT | distance |
| 8 | M1 | CODE | STROKE (012) |
| 9–12 | M1 | CODE | COLOR (018) |
| 13–20 | | TIME | SCY level 1 |
| 21–28 | | TIME | SCY level 2 |
| 29–36 | | TIME | SCY level 3 |
| 37–44 | | TIME | LCM level 1 |
| 45–52 | | TIME | LCM level 2 |
| 53–60 | | TIME | LCM level 3 |
| 61–68 | M1 | DATE | effective date |
| 69–160 | | | future use |

---

## 6. Code tables

**ORG (001)** — Organization:
`1` USS · `2` Masters · `3` NCAA · `4` NCAA Div I · `5` NCAA Div II · `6` NCAA Div III ·
`7` YMCA · `8` FINA · `9` High School.

**LSC (002)** — Local Swimming Committee (2-letter):
AD Adirondack · AK Alaska · AM Allegheny Mountain · AR Arkansas · AZ Arizona · BD Border ·
CA Southern California · CC Central California · CO Colorado · CT Connecticut ·
FG Florida Gold Coast · FL Florida · GA Georgia · GU Gulf · HI Hawaii · IA Iowa ·
IE Inland Empire · IL Illinois · IN Indiana · KY Kentucky · LA Louisiana · LE Lake Erie ·
MA Middle Atlantic · MD Maryland · ME Maine · MI Michigan · MN Minnesota · MR Metropolitan ·
MS Mississippi · MT Montana · MV Missouri Valley · MW Midwestern · NC North Carolina ·
ND North Dakota · NE New England · NI Niagara · NJ New Jersey · NM New Mexico ·
NT North Texas · OH Ohio · OK Oklahoma · OR Oregon · OZ Ozark · PC Pacific ·
PN Pacific Northwest · PV Potomac Valley · SC South Carolina · SD South Dakota ·
SE Southeastern · SI San Diego Imperial · SN Sierra Nevada · SR Snake River · ST South Texas ·
UT Utah · VA Virginia · WI Wisconsin · WT West Texas · WV West Virginia · WY Wyoming.

**FILE (003)** — File/transmission type:
`01` Meet Registrations · `02` Meet Results · `03` OVC · `04` National Age Group Record ·
`05` LSC Age Group Record · `06` LSC Motivational List · `07` National Records & Rankings ·
`08` Team Selection · `09` LSC Best Times · `10` USS Registration · `16` Top 16 ·
`20` Vendor-defined.

**COUNTRY (004)** — standard **FINA three-letter** codes (effective 1993). The full table
is below; a few entries reflect early-1990s geopolitics (e.g. `TCH` Czechoslovakia, `ZAI`
Zaire, `YUG` Yugoslavia, `GER`/`GEO` reuse) and are reproduced verbatim from the spec.

??? note "COUNTRY Code 004 — full FINA table (effective 1993)"
    `AFG` Afghanistan · `AHO` Antilles Netherlands (Dutch West Indies) · `ALB` Albania ·
    `ALG` Algeria · `AND` Andorra · `ANG` Angola · `ANT` Antigua · `ARG` Argentina ·
    `ARM` Armenia · `ARU` Aruba · `ASA` American Samoa · `AUS` Australia · `AUT` Austria ·
    `AZE` Azerbaijan · `BAH` Bahamas · `BAN` Bangladesh · `BAR` Barbados · `BEL` Belgium ·
    `BEN` Benin · `BER` Bermuda · `BHU` Bhutan · `BIZ` Belize · `BLS` Belarus · `BOL` Bolivia ·
    `BOT` Botswana · `BRA` Brazil · `BRN` Bahrain · `BRU` Brunei · `BUL` Bulgaria ·
    `BUR` Burkina Faso · `CAF` Central African Republic · `CAN` Canada · `CAY` Cayman Islands ·
    `CGO` People's Rep. of Congo · `CHA` Chad · `CHI` Chile · `CHN` People's Rep. of China ·
    `CIV` Ivory Coast · `CMR` Cameroon · `COK` Cook Islands · `COL` Columbia · `CRC` Costa Rica ·
    `CRO` Croatia · `CUB` Cuba · `CYP` Cyprus · `DEN` Denmark · `DJI` Djibouti ·
    `DOM` Dominican Republic · `ECU` Ecuador · `EGY` Arab Republic of Egypt · `ESA` El Salvador ·
    `ESP` Spain · `EST` Estonia · `ETH` Ethiopia · `FIJ` Fiji · `FIN` Finland · `FRA` France ·
    `GAB` Gabon · `GAM` Gambia · `GBR` Great Britain · `GER` Germany · `GEO` Georgia ·
    `GEQ` Equatorial Guinea · `GHA` Ghana · `GRE` Greece · `GRN` Grenada · `GUA` Guatemala ·
    `GUI` Guinea · `GUM` Guam · `GUY` Guyana · `HAI` Haiti · `HKG` Hong Kong · `HON` Honduras ·
    `HUN` Hungary · `INA` Indonesia · `IND` India · `IRL` Ireland · `IRI` Islamic Rep. of Iran ·
    `IRQ` Iraq · `ISL` Iceland · `ISR` Israel · `ISV` Virgin Islands · `ITA` Italy ·
    `IVB` British Virgin Islands · `JAM` Jamaica · `JOR` Jordan · `JPN` Japan · `KEN` Kenya ·
    `KGZ` Kyrghyzstan · `KOR` Korea (South) · `KSA` Saudi Arabia · `KUW` Kuwait ·
    `KZK` Kazakhstan · `LAO` Laos · `LAT` Latvia · `LBA` Libya · `LBR` Liberia · `LES` Lesotho ·
    `LIB` Lebanon · `LIE` Liechtenstein · `LIT` Lithuania · `LUX` Luxembourg · `MAD` Madagascar ·
    `MAS` Malaysia · `MAR` Morocco · `MAW` Malawi · `MDV` Maldives · `MEX` Mexico · `MGL` Mongolia ·
    `MLD` Moldova · `MLI` Mali · `MLT` Malta · `MON` Monaco · `MOZ` Mozambique · `MRI` Mauritius ·
    `MTN` Mauritania · `MYA` Union of Myanmar · `NAM` Namibia · `NCA` Nicaragua ·
    `NED` The Netherlands · `NEP` Nepal · `NIG` Niger · `NGR` Nigeria · `NOR` Norway ·
    `NZL` New Zealand · `OMA` Oman · `PAK` Pakistan · `PAN` Panama · `PAR` Paraguay · `PER` Peru ·
    `PHI` Philippines · `PNG` Papau-New Guinea · `POL` Poland · `POR` Portugal ·
    `PRK` Democratic People's Rep. of Korea · `PUR` Puerto Rico · `QAT` Qatar · `ROM` Romania ·
    `RSA` South Africa · `RUS` Russia · `RWA` Rwanda · `SAM` Western Samoa · `SEN` Senegal ·
    `SEY` Seychelles · `SIN` Singapore · `SLE` Sierra Leone · `SLO` Slovenia · `SMR` San Marino ·
    `SOL` Solomon Islands · `SOM` Somalia · `SRI` Sri Lanka · `SUD` Sudan · `SUI` Switzerland ·
    `SUR` Surinam · `SWE` Sweden · `SWZ` Swaziland · `SYR` Syria · `TAN` Tanzania ·
    `TCH` Czechoslovakia · `TGA` Tonga · `THA` Thailand · `TJK` Tadjikistan · `TOG` Togo ·
    `TPE` Chinese Taipei · `TRI` Trinidad & Tobago · `TUN` Tunisia · `TUR` Turkey ·
    `UAE` United Arab Emirates · `UGA` Uganda · `UKR` Ukraine · `URU` Uruguay ·
    `USA` United States of America · `VAN` Vanuatu · `VEN` Venezuela · `VIE` Vietnam ·
    `VIN` St. Vincent and the Grenadines · `YEM` Yemen · `YUG` Yugoslavia · `ZAI` Zaire ·
    `ZAM` Zambia · `ZIM` Zimbabwe.

**MEET (005)** — Meet type:
`1` Invitational · `2` Regional · `3` LSC Championship · `4` Zone · `5` Zone Championship ·
`6` National Championship · `7` Juniors · `8` Seniors · `9` Dual · `0` Time Trials ·
`A` International · `B` Open · `C` League.

**TEAM (006)** — 2-char LSC + 4-char team code (e.g. `COFAST`); Unattached is always `UN`
(e.g. `FG  UN`).

**REGION (007)** — `1`–`9` Regions 1–9; `A` Region 10 · `B` 11 · `C` 12 · `D` 13 · `E` 14.

**USS# (008)** — USA-Swimming member number. Refers to USS membership files; the code list
itself is not published. See [USSNUM construction](#field-format-conventions) for the
14-char layout.

**CITIZEN (009)** — `2AL` dual USA + other · `FGN` foreign · *or* any COUNTRY (004) code.

**SEX (010)** — `M` Male · `F` Female.

**EVENT SEX (011)** — `M` Male · `F` Female · `X` Mixed.

**STROKE (012)** — `1` Freestyle · `2` Backstroke · `3` Breaststroke · `4` Butterfly ·
`5` Individual Medley · `6` Freestyle Relay · `7` Medley Relay.

> 🔶 cl2: a non-spec `H` also occurs (diving) — see [§7](#7-how-real-cl2-files-deviate-from-the-spec).

**COURSE (013)** — `1`/`S` Short Course Meters · `2`/`Y` Short Course Yards ·
`3`/`L` Long Course Meters · `X` Disqualified. (🔶 cl2: real files use the alpha forms `S`/`Y`/`L`.)

**EVENT TIME CLASS (014)** — two concatenated chars (left = lower limit, right = upper limit);
`U` no lower limit · `O` no upper limit · `1` Novice · `2` B · `P` BB · `3` A · `4` AA ·
`5` AAA · `6` AAAA · `J` Junior · `S` Senior. Examples: `22` = B meets, `23` = B–A meets,
`4O` = AA+ meets. (🔶 cl2: blank in 100% of D0 records.)

**SPLIT (015)** — `C` Cumulative · `I` Interval.

**ATTACH (016)** — `A` Attached · `U` Unattached.

**ZONE (017)** — `E` Eastern · `S` Southern · `C` Central · `W` Western.

**COLOR (018)** — `GOLD` · `SILV` · `BRNZ` · `BLUE` · `RED ` · `WHIT`.

**PRELIMS/FINALS (019)** — `P` Prelims · `F` Finals · `S` Swim-offs.

**TIME (020)** — explanation codes used in place of a numeric time:
`NT` No Time · `NS` No Swim/No Show · `DNF` Did Not Finish · `DQ` Disqualified · `SCR` Scratch.

**MEMBER (021)** — `R` Renew · `N` New · `C` Change · `D` Delete.

**SEASON (022)** — `1` Season 1 · `2` Season 2 · `N` Year-round.

**ANSWER (023)** — `T`/`F` logical (other-FINA-federation membership).

**ORDER (024)** — relay leg: `0` not on team for this swim · `1`–`4` legs 1–4 · `A` alternate.

**EVENT AGE (025)** — 4 chars: lower age (2 digits or `UN`) + upper age (2 digits or `OV`);
single-digit ages zero-filled (no blanks).

**ETHNICITY (026)** — 1–2 chars: `Q` African American · `R` Asian/Pacific Islander ·
`S` Caucasian · `T` Hispanic · `U` Native American · `V` Other · `W` Decline
(if first char is `V`/`W`/`X`, second must be blank).

---

## 7. How real `.cl2` files deviate from the spec

Every item here is a **measured fact** from the 2,190-file / 6,354,732-record corpus
(Pacific + Michigan LSCs); nothing is conjecture.

| # | Deviation / convention | Evidence |
|---|---|---|
| 1 | **Only 9 of the spec's record types are emitted** — `A0 B1 C1 D0 D3 E0 F0 G0 Z0`. `B2`, `C2`, `D1`, `D2`, `J0`, `J1`, `J2` never appear. (Omission is spec-legal — only `A0`/`Z0` are required — but `C2`'s absence means the `D0` "must be preceded by C1 **and** C2" rule is met via the C2-absent fallback.) | 0 occurrences of those 7 codes in 6.35 M records |
| 2 | **B1 meet-type (col 121, M2) is always blank** — the meet type is never recorded. | 2,190 / 2,190 files blank |
| 3 | **D0/E0 EVENT TIME CLASS is always blank**; D0 flight-status (col 145) effectively always blank. | 3,352,073 / 3,352,073 D0 blank; 1 non-blank flight |
| 4 | **A non-spec STROKE code `H` is used for diving** — the STROKE table (012) defines only `1`–`7`. | D0 `H` ×2,840; E0 `H` ×245 |
| 5 | **Out-of-domain geography codes** — `ON` (Ontario) in a USPS state field; `---` in a COUNTRY field. | tens of records, both LSCs |
| 6 | **Birth date (M2) is frequently blank** — the privacy "WODOB" export practice. | 555,019 / 3,352,073 D0 = 16.6% |
| 7 | **USS# (M2) occasionally blank**; **citizenship usually blank** (optional field). | USS# 1.8%; citizen 83% |
| 8 | **Alpha course alternative used** (`Y`/`L`/`S`) rather than the numeric `1`/`2`/`3`. | B1 + all time-course fields |
| 9 | **CP-1252 encoding** (not 7-bit ASCII) and **`.cl2`/`.sd3` extension** (spec says `.SD3`). | accented names throughout |
| 10 | **Content can be partial** — some `.cl2` carry only a fraction of the swims in the sibling `.hy3` (e.g. a cl2 with 30 of 954 swims). | observed in pacswim batch |

**Things that do *not* deviate** (verified, to forestall guesses): records are exactly 160
data chars + CRLF; `A0` is first and `Z0` last; the **Z0 "# D records" count matches the
actual `D0` count** in 100% of files; A0 contact name/phone (M1) are always present; ATTACH,
SEX, EVENT SEX, PRELIMS/FINALS, ORDER, SPLIT codes and the heat/lane/place/time/seed fields
all follow the spec. (Note: `100`-yard / 4×25 relays and other unusual distances are
**spec-valid** SDIF, even though `tunas` currently skips events it can't map — that is a
parser limitation, not a file deviation.)

---

## 8. Coding examples

Only two records are required — `A0` and `Z0`; everything between is optional and ordered
less-frequent-to-more-frequent. The spec works through a **two-team dual meet** in which the
host merges visiting-team data with its own.

**Meet entry.** The visiting team contributes `A0`, `B1`, `B2` (the latter two as a
courtesy), `C1`, `C2`, 74 `D0`/`D3` records for 48 swimmers, 5 `E0` relay entries, 29 `F0`,
and a `Z0`. The host merges its own `C1`, `C2`, 63 `D0`/`D3` for 51 swimmers, 6 `E0`, and 35
`F0`, sharing the visiting team's `A0`/`B1`/`B2`/`Z0`:

```
Visiting team                    Host team
A0  1 record                     (shares same record)
B1  1 dual meet                  (shares same record)
B2  1 names host team            (shares same record)
 C1 1 visiting team               C1 1 host team
 C2 1 visiting team               C2 1 host team
  D0/D3 74 athl-event              D0/D3 63 athl-event
  E0     5 relay entries           E0     6 relay entries
  F0    29 relay swimmers          F0    35 relay swimmers
Z0  1 record                     (shares same record)
```

**Meet results** from the same dual meet add `G0` split records:

```
A0  1 record (sanction number + text)
 B1 1 / B2 1   meet + host data
 C1 1 / C2 1   visiting team
  D0 64 visiting        G0 31 individual splits
  E0  5 visiting        F0 20 relay names   G0 4 lead-off splits
 C1 1 / C2 1   host team
  D0 61 host            G0 22 individual splits
  E0  4 host            F0 16 relay names
Z0  1 terminator
```

**Conventions drawn from these examples:**

- A swimmer who has not completed the **120-day waiting period** is coded **UNATTACHED** on
  the individual record but may still be associated with the team.
- Individual event records may appear in any order within a team; relay-name (`F0`) records
  must immediately follow their relay-event (`E0`) record.
- For multi-team meets, all records for one team are grouped together, then the next team.
  Unattached swimmers not tied to a team form an "unattached team" with their own `C1`.

---

## 9. Revision history

SDIF v3 is dated **April 28, 1998** (United States Swimming, *"Standard Data Interchange
Format Ver. 3.0, official"*). The spec's own revision lists are reproduced below. A few
entries describe edits the published tables don't fully reflect — e.g. revision 18 retires
`ANSWER Code 023`, yet the `D2` table still lists it; the layouts above reproduce the tables
as printed.

??? note "Revision list — Version 3 changes"
    1. Revise the definition of mandatory fields (p.2).
    2. Remove all vendor-defined fields → future use.
    3. Remove all "checksum" fields → future use.
    4. Add A0 field (156/2) "submitted by LSC" for Top-16 tabulation.
    5. Make D0 "EVENT SEX Code 011" (67/1) mandatory.
    6. Top-16 pyramid only: allow multiple meets.
    7. Revise phone-number formatting restrictions (p.3).
    8. Revise Time field format #3 (p.3).
    9. Remove the H0 record.
    10. Revise the Name field format (p.3).
    11. Remove the "Transaction" field from all records → future use.
    12. Change B1 "meet city" & "meet state" to M2 (p.10).
    13. Remove the mandatory flag on C1 "Region Code" (p.13).
    14. Rename "USS or other ID" to "USS#" everywhere and make it M2.
    15. Remove "unique Event ID#" everywhere → future use.
    16. Convert D1 "admin info" fields → future use.
    17. Convert D1 "middle initial" → future use.
    18. Remove "ANSWER Code 023" everywhere → future use.
    19. Make M1: B1 "meet name"/"meet start"; C1 "TEAM code"/"full team name".
    20. Make M2: D0 & E0 "date of swim"; D1 & F0 "swimmer birth date"; "ORG Code" in all records.
    21. Convert D0 "flight status" → future use.
    22. Prelims & finals place and points are M1 for championship meets.

??? note "Revision list — D3 / new-USS# additions"
    1. Add a new record (D3) with the new USS# and the swimmer's preferred first name.
    2. Revise the pyramids to include the D3 record.
    3. Add an SDIF-version-number field to A0 at 4/8.
    4. Add the new-USS# definition to the format-design section.
    5. Add condition (#) to D0 to allow relay-only swimmers.
    6. Add the file-extension definition (`.SD3`) under format design (p.2).
    7. Add registration-submission fields to the D3 record.
    8. Add the ETHNICITY Code 026 definition.
    9. Add and define a LOGICAL field type.
    10. Revise the ALPHA type to allow right-justification of numeric data.
    11. Add back Event Numbers.
    12. Change the participation selections in the D3 record.
    13. Implement the new USS# and preferred first name in F0 (instead of following F0 with a D3).

---

## What `tunas` does with each record

| Code | `tunas` behaviour |
|---|---|
| `A0` | Captured as `SourceFile` (provenance). |
| `B1` | Starts a `Meet`. |
| `B2` | Builds `Meet.host` (when present — not in these files). |
| `C1` | Creates a `Club`, or marks the swimmer context unattached. |
| `C2` | Adds coach/phone/entry counts (when present — not in these files). |
| `D0` | Creates an `IndividualSwim` per session; resolves/creates the `Swimmer`. |
| `D1`/`D2` | Populate `Swimmer.contact`/`registration` (PII; absent in results files). |
| `D3` | Sets `id_long`, `preferred_first_name`, demographics. |
| `E0` | Creates a `Relay` per session. |
| `F0` | Appends a `RelaySwim` (counting leg or alternate). |
| `G0` | Appends `Split`s to the current swim. |
| `J0`–`J2` | Surface as `ParseWarning` (qualifying-time records). |
| `Z0` | Resets parser context; keeps any note on `SourceFile.notes`. |

Any 2-char code not in this table is recorded as a `ParseWarning` rather than parsed.

## Bundled spec & further reading

- The authoritative SDIF v3 specification ships verbatim with the library at
  `src/tunas/_data/sdif-v3.txt` (~65 KB).
- [The Hy-Tek `.hy3` file format](hy3_format.md): the reverse-engineered sibling results
  format, cross-validated against this one.
- USA Swimming developer / SWIMS resources: <https://www.usaswimming.org>.
