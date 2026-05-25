# The Hy-Tek `.hy3` file format

`.hy3` is **Hy-Tek's own proprietary results format** — the sibling of the open
[`.cl2` / SDIF v3](cl2_format.md) interchange format. Where SDIF is a published
standard, `.hy3` has no public specification, so this page documents it from
reverse engineering.

!!! note "Reference documentation, not a parser (yet)"
    `tunas` parses **`.cl2` / SDIF v3** today. This page is a format reference for
    the related `.hy3` format — the spec an `.hy3` reader would be built against.
    It does not describe shipped behaviour.

> **Status:** Draft, derived empirically and **cross-validated against SDIF**. Not an official Hy-Tek document.
>
> **Derived from** three primary results exports:
> - `Meet Results-2016 CA December CA NV Speedo Sectionals-16Dec2016-002.hy3` (SCY, 12,252 records)
> - `Meet Results-2016 USA Swimming Futures Stanford-04Aug2016-002.hy3` (LCM, 12,361 records)
> - `Meet Results-2013 Pacfifc Swimming SCY - LCM WalkOn Meet-12May2013-001.hy3` (mixed SCY+LCM, 3,409 records)
>
> plus **12 additional Pacific Swimming meets** downloaded from pacswim.org (Far Western
> LCM/SCY champs, age-group C/B/BB meets, prelims/finals meets — ~45,000 more
> records) each diffed against its `.cl2`. See [§11](#11-validation-against-sdif).
>
> Cross-referenced against the USA-Swimming **SDIF v3** spec bundled with this
> library (`src/tunas/_data/sdif-v3.txt`) and — critically — by **parsing the
> matching `.cl2` (SDIF) file with the `tunas` parser and diffing record-for-record**
> against a parser built from this spec. See [§11 Validation](#11-validation-against-sdif).
>
> **Confidence tags** used throughout:
> - **[C] Confirmed** — verified directly against many records, and where possible
>   matched field-for-field against the SDIF `.cl2` for the same meet.
> - **[I] Inferred** — strongly implied by the data + SDIF, but not independently proven.
> - **[?] Uncertain** — best guess; treat as a placeholder.
>
> The cross-validation resolved several fields that were guesses in the first draft
> (notably **place vs. heat/lane columns**, the **two seed-time fields**, the
> **split distance unit**, and the **result-status flag**). Items still not exercised
> by either meet (SCM course, diving, masters, some flags) remain inferred —
> see [§9 Known gaps](#9-known-gaps).

---

## 1. Relationship to SDIF / `.cl2`

`.hy3` is **Hy-Tek's own proprietary format**, related to but *distinct from* USA
Swimming's open SDIF (`.cl2`/`.sd3`) interchange format documented in
[the SDIF reference](cl2_format.md):

| | SDIF (`.cl2`) | Hy-Tek (`.hy3`) |
|---|---|---|
| Record length | 160 chars | **130 chars** (128 data + 2 checksum) |
| Line checksum | none | **2 trailing digits** (see §3) |
| Encoding | CP-1252 / ASCII | CP-1252 / ASCII |
| File terminator | `Z0` record | **none** (this sample just ends) |

The record-code vocabularies differ. Rough semantic mapping:

| hy3 | SDIF | Meaning |
|---|---|---|
| `A1` | `A0` | File / software description |
| `B1` | `B1` | Meet |
| `B2` | `B2` | Meet host |
| `C1` | `C1` | Team / club |
| `C2` | `C2` (part) | Team mailing address |
| `C3` | `C2` (part) | Team contact (phones, email) |
| `D1` | `D0`+`D3` (athlete part) | Athlete identity |
| `E1` | `D0` (entry part) | Individual event entry / seed |
| `E2` | `D0` (result part) | Individual event result |
| `F1` | `E0` (entry part) | Relay entry / seed |
| `F2` | `E0` (result part) | Relay result |
| `F3` | `F0` (×N) | Relay athletes (legs) |
| `G1` | `G0` | Splits |
| `H1`/`H2` | (DQ code on result) | Disqualification reason text |

The most important structural difference: SDIF packs an entire individual swim into
one `D0` record, whereas **hy3 splits it into three records** — `D1` (who),
`E1` (what they entered / seed), `E2` (how they did) — plus `G1` splits.

---

## 2. Physical layout

- **Fixed-width records**, one per line, **exactly 130 characters** before the
  line terminator. **[C]**
- Line terminator is **CRLF** (`\r\n`). **[C]**
- Columns **1–2**: 2-character **record-type code** (`A1`, `B1`, …). **[C]**
- Columns **3–128**: data fields, **space-padded**, fixed positions per record type. **[C]**
- Columns **129–130**: **line checksum** (two decimal digits). **[C]**
- Encoding is a single-byte code page (CP-1252); accented athlete names occur.
  Decode byte-for-byte to preserve column alignment. **[I]**

All column numbers in this document are **1-based and inclusive**.

### Record inventory (this file)

| Code | Count | Record |
|---|--:|---|
| `A1` | 1 | File description |
| `B1` | 1 | Meet |
| `B2` | 1 | Meet host |
| `C1` | 91 | Team |
| `C2` | 77 | Team address |
| `C3` | 34 | Team contact |
| `D1` | 783 | Athlete |
| `E1` | 3421 | Individual entry/seed |
| `E2` | 3421 | Individual result |
| `F1` | 220 | Relay entry/seed |
| `F2` | 220 | Relay result |
| `F3` | 216 | Relay athletes |
| `G1` | 3621 | Splits |
| `H1` | 144 | DQ reason (primary) |
| `H2` | 1 | DQ reason (secondary) |

---

## 3. Line checksum (columns 129–130) — **[C], verified on all 12,252 records**

Each record carries a 2-digit checksum over its first 128 characters.

```python
def hy3_checksum(data: str) -> str:
    """data = the first 128 characters of the record (cols 1-128)."""
    assert len(data) == 128
    sum_odd = sum(ord(data[i]) for i in range(0, 128, 2))   # 1-based ODD positions
    sum_even = sum(ord(data[i]) for i in range(1, 128, 2))  # 1-based EVEN positions
    result = (2 * sum_even + sum_odd) // 21 + 205
    tens, units = (result // 10) % 10, result % 10
    return f"{units}{tens}"   # NOTE: digits are emitted reversed (units, then tens)
```

Steps:

1. `sumOdd`  = Σ ASCII of chars at 1-based **odd** positions (cols 1,3,5,…,127).
2. `sumEven` = Σ ASCII of chars at 1-based **even** positions (cols 2,4,…,128).
3. `result  = (2·sumEven + sumOdd) // 21 + 205` (integer division).
4. Take the last two digits of `result` and **emit them reversed** — units digit
   into col 129, tens digit into col 130.

This held for **every** record in the sample (12,252 / 12,252). The two
non-intuitive constants are integer-division by **21** and the additive **205**,
plus the digit reversal.

---

## 4. File / record hierarchy

```
A1                              File description           (1 per file)
B1                              Meet                       (1)
B2                              Meet host                  (1, optional)
(repeated per team:)
  C1                            Team
  C2                            Team address
  C3                            Team contact               (optional)
  (per individual swimmer:)
    D1                          Athlete
    (per swim by that athlete:)
      E1                        Entry / seed
      E2                        Result
      G1                        Splits        (0+ lines; long races span several)
      H1 [H2]                   DQ reason     (only if the result was disqualified)
  (per relay:)
    F1                          Relay entry / seed
    F2                          Relay result
    G1                          Splits
    F3                          Relay athletes (legs)
    H1 [H2]                     DQ reason (if disqualified)
(no terminator record)
```

Notes:

- `E*`/`F3` records link back to their `D1` athlete by the **4-digit athlete
  number** (cols 5–8), in addition to appearing positionally right after it. **[C]**
- `H1`/`H2` DQ-reason lines **follow** the disqualified result's records and their
  2-char code matches the DQ code embedded in the result (`E2`/`F2` cols 14–15). **[C]**
- This file has **no `Z0`-style terminator**; it ends on the last `E2`. **[C]**

---

## 5. Individual / common records

### 5.1 `A1` — File description (1 per file)

Example:

```
A107Results From MM to TM    Hy-Tek, Ltd    MM5 6.0De     12202016  6:52 AMFAST - CA
```

| Cols | Field | Conf | Notes |
|---|---|---|---|
| 1–2 | record code `A1` | C | |
| 3–4 | file/result type code | ? | `07` in sample |
| 5–29 | description | I | `Results From MM to TM` |
| 30–44 | software vendor | I | `Hy-Tek, Ltd` |
| 45–58 | software name/version | I | `MM5 6.0De` (Meet Manager) |
| 59–66 | file creation date `MMDDYYYY` | C | `12202016` |
| 67–74 | file creation time | I | `  6:52 AM` |
| 75–~124 | licensee / exported-by | I | `FAST - CA` |

(Single record — boundaries inferred from word spacing; only the date is firmly anchored.)

### 5.2 `B1` — Meet

Example:

```
B12016 CA December CA NV Speedo Sectionals     East Los Angeles College                     121620161219201612162016   0
```

| Cols | Field | Conf | Notes |
|---|---|---|---|
| 1–2 | record code `B1` | C | |
| 3–47 | meet name (45) | C | |
| 48–92 | facility / location (45) | I | `East Los Angeles College` |
| 93–100 | start date `MMDDYYYY` | C | `12162016` |
| 101–108 | end date `MMDDYYYY` | C | `12192016` |
| 109–116 | age-up date `MMDDYYYY` | I | `12162016` |
| 117–120 | meet type/code | ? | `   0` |

### 5.3 `B2` — Meet host

Example:

```
B22016 CA December CA NV Speedo Sectionals     Hosted by: SCS & FAST                        010102Y1 10.00  S16-321
```

| Cols | Field | Conf | Notes |
|---|---|---|---|
| 1–2 | record code `B2` | C | |
| 3–47 | meet name (45, repeat) | C | |
| 48–92 | host text (45) | I | `Hosted by: SCS & FAST` |
| 93–~115 | misc meet config | ? | `010102Y1`, `10.00`, `S16-321` — unidentified (course/fee/sanction?) |

### 5.4 `C1` — Team

Example:

```
C1ARSC Arcadia Riptides              ARSC            CA
```

| Cols | Field | Conf | Notes |
|---|---|---|---|
| 1–2 | record code `C1` | C | |
| 3–7 | team abbreviation (5) | C | `ARSC` |
| 8–37 | full team name (30) | C | `Arcadia Riptides` |
| 38–52 | short team name (15) | I | repeats abbreviation, or truncated name |
| 54–55 | LSC code (2) | I | `CA` (USA-Swimming Local Swimming Committee) |
| ~118–122 | counts / flags | ? | e.g. `0  2` |

### 5.5 `C2` — Team address

Example:

```
C2ARSC                          128 Fowler Drive              Monrovia                      CA91016     USA
```

| Cols | Field | Conf | Notes |
|---|---|---|---|
| 1–2 | record code `C2` | C | |
| 3–32 | address line 1 / attn (30) | I | sometimes holds the team code |
| 33–62 | address line 2 / street (30) | I | `128 Fowler Drive` |
| 63–92 | city (30) | I | `Monrovia` |
| 93–94 | state (2) | I | `CA` |
| 95–104 | postal code (10) | I | `91016` |
| 105–107 | country (3) | I | `USA` |

### 5.6 `C3` — Team contact

Example:

```
C3                              6268406780          6268406780          6263580164          swimarcadia@gmail.com
```

| Cols | Field | Conf | Notes |
|---|---|---|---|
| 1–2 | record code `C3` | C | |
| 3–32 | contact name (30) | I | often blank |
| 33–52 | phone 1 (20) | I | digits left-justified |
| 53–72 | phone 2 (20) | I | |
| 73–92 | fax (20) | I | |
| 93–122 | email (30) | C | |

### 5.7 `D1` — Athlete

Example:

```
D1F 3420Allison             Bridgette                                033199BRIAALLI    003311999 17     0       USA         N
D1M 3008Lim                 Adrian              Adrian               082299ADR*LIM*    008221999 17SO   0                   N
```

| Cols | Field | Conf | Notes |
|---|---|---|---|
| 1–2 | record code `D1` | C | |
| 3 | sex (`M`/`F`) | C | |
| 4 | (flag) | ? | blank in sample |
| 5–8 | athlete number (4) | C | in-file ID; links `E*`/`F3` |
| 9–28 | last name (20) | C | |
| 29–48 | first name (20) | C | |
| 49–68 | preferred / middle name (20) | I | `Adrian` repeated for Lim |
| 69 | registration flag | ? | `A` or blank |
| 70–83 | USA-S member ID (14) | C | `MMDDYY` + first3(first) + middleInit + first4(last), `*`=pad |
| 88 | (flag) | ? | `0` |
| 89–96 | birth date `MMDDYYYY` | C | `03311999` |
| 98–99 | age (2) | C | `17` |
| 100–101 | squad / group code | I | e.g. `SO`; usually blank |
| 105 | (flag) | ? | `0` |
| 113–115 | citizenship (3) | I | `USA` |
| 125 | (flag) | ? | `N` in every record |

The USA-S member ID encodes the birth date (`033199` = 03/31/1999) and name
(`BRI`+`A`+`ALLI` = Bridgette **A**. Allison), with `*` filling short names
(`ADR*LIM*` = Adrian * Lim *).

### 5.8 `E1` — Individual entry / seed

Example:

```
E1F 3420AllisFW   200A  0109  0S 11.00 17   114.87Y  114.87Y    0.00    0.00   NN               N
```

| Cols | Field | Conf | Notes |
|---|---|---|---|
| 1–2 | record code `E1` | C | |
| 3 | athlete sex (`M`/`F`) | C | |
| 5–8 | athlete number → `D1` | C | |
| 9–13 | last name, first 5 | C | `Allis` |
| 14 | sex (`M`/`F`/`X`) | C | `X` = mixed |
| 15 | event sex (`W`/`M`/`X`) | C | women / men / mixed |
| 16–21 | distance (right-justified) | C | `200` |
| 22 | **stroke code** | C | `A`=Free `B`=Back `C`=Breast `D`=Fly `E`=IM |
| 25–28 | event number | I | `0109` |
| 29–32 | age-group / round code | ? | `  0S` |
| 34–38 | entry value | ? | `11.00` / `15.00` (fee or qualifying mark?) |
| 40–41 | heat / age | ? | `17` |
| 44–50 | **seed time — converted to meet course** | C | `137.36` |
| 51 | **course of converted seed** | C | meet course (`L` here) |
| 53–59 | **seed time — as entered** | C | `121.32` ← **this is what SDIF stores** |
| 60 | **course of as-entered seed** | C | `Y` (original course of the time) |
| 64–67, 73–76 | additional times | ? | `0.00` |
| 80–81 | flags | ? | `NN` |
| 96–97 | flag | ? | `N` |

> The inline example above is from the single-course SCY meet, where the converted
> and as-entered seeds coincide (`114.87Y  114.87Y`). The mixed-meet values in the
> Notes column (`137.36`, `121.32`) come from the LCM export, where they differ.

**Times are total seconds as a decimal, no colon** (validated against SDIF): `137.36`
→ 2:17.36, `52.69` → 52.69 s, `479.16` → 7:59.16. Convert to centiseconds with
`round(value × 100)`.

**Two seed times. [C]** `E1` carries the seed in *two* forms: the **meet-course
conversion** (cols 44–50, e.g. `137.36L`) and the **as-entered time in its original
course** (cols 53–59, e.g. `121.32Y` — a yards time entered into a long-course meet).
SDIF/`.cl2` stores the **as-entered** value, so cols 53–59 are the ones that match
the SDIF seed (3328/3329 in the LCM meet, vs only 2536/3329 for cols 44–50). When the
seed was already in the meet course, the two fields are identical. A swimmer entered
with "no time" (NT) shows `0.00` here (SDIF stores no seed at all).

!!! warning "`E1` does NOT carry the event's course"
    Col 51 is the course of the *converted seed* — i.e. the meet's **primary** course —
    and col 60 is the course of the *as-entered seed*. **The event's own course is in
    `E2` col 12.** In a single-course meet these all coincide, but in a **mixed
    SCY+LCM meet** col 51 is the conversion target (e.g. `Y`) while the actual event
    may be LCM. Using col 51 as the event course silently mislabels every
    off-primary-course event. Take event distance + stroke from `E1`, but **event
    course from `E2`**.

### 5.9 `E2` — Individual result

Example (normal, then a DQ):

```
E2P  117.91Y       0 10  8  5 113  0  118.00  118.01    0.00       117.91     0.00     12182016
E2F   62.29YQ7A    0  2  4  0   0  0   62.39   62.32    0.00        62.29     0.00     12172016
```

| Cols | Field | Conf | Notes |
|---|---|---|---|
| 1–2 | record code `E2` | C | |
| 3 | **round** (`P`/`F`) | C | Prelims / Finals |
| 5–11 | **result time** (total seconds) | C | authoritative; matches SDIF exactly. `0.00` = no swim (NS/DNF) |
| 12 | **course** (`Y`/`L`/`S`) | C | **authoritative event course** — use this, not `E1` col 51 |
| 13 | **status flag** | C | see status table in §8 |
| 14–15 | **DQ code** → `H1` | C | e.g. `7A` (only when col 13 = `Q`) |
| 20 | (flag) | ? | `0` |
| 22–23 | **heat** | C | matched SDIF heat 3169/3169 |
| 25–26 | **lane** | C | matched SDIF lane 3168/3169 |
| 28–29 | place within heat | I | |
| 31–33 | **place** (overall rank) | C | matched SDIF rank 3157/3169 |
| 38–44 | backup/timer time 1 | I | `118.00` |
| 46–52 | backup/timer time 2 | I | `118.01` |
| 57–60 | time | ? | `0.00` |
| 67–73 | secondary time | I | usually equals cols 5–11; sometimes `0.00` in finals |
| 79–82 | time | ? | `0.00` |
| 88–95 | **swim date** `MMDDYYYY` | C | `12182016` |

!!! warning "Correction from the first draft"
    The result block was originally mis-labeled (place at 22–23). Cross-referencing
    SDIF proved cols **22–23 = heat**, **25–26 = lane**, **31–33 = place/rank**. For
    disqualified swims, **hy3 keeps the swum time in cols 5–11**, whereas SDIF nulls
    the time of a DQ.

---

## 6. Relay records

### 6.1 `F1` — Relay entry / seed (analogous to `E1`)

Example:

```
F1ALPH A   0FFW   400E  0109  0S 24.00 11   243.30Y  243.30Y    0.00    0.00   NN   4           NA
```

| Cols | Field | Conf | Notes |
|---|---|---|---|
| 1–2 | record code `F1` | C | |
| 3–6 | team abbreviation (4) | C | `ALPH` |
| 8 | relay designator | C | `A`,`B`,`C`… (A relay, B relay) |
| 13–15 | sex / event-sex codes | I | `FFW` (women), `MMM` (men) |
| 19–21 | distance | C | `400`, `800` |
| 22 | **relay stroke** | C | `A`=Free relay, `E`=Medley relay |
| 25–28 | event number | I | `0109` |
| 45–51 | seed time | C | `243.30` = 4:03.30 |
| 52 | course | C | `Y` |
| 85 | number of swimmers | I | `4` |
| 97–98 | flag | ? | `NA` |

### 6.2 `F2` — Relay result (analogous to `E2`)

Example:

```
F2F  249.87Y       0  6  5  3  39  0  249.81  249.93    0.00       249.87     0.00                    12172016            0
```

The **result block is at the same columns as `E2`** — round (col 3), status (col 13),
**heat 22–23, lane 25–26, place 31–33** — all validated against SDIF (143/143 paired
relays matched on time and place). The only offset difference is the **time field,
which starts one column later: time = cols 6–11, course = col 12** (`F2F  526.67L…`).
The swim date appears later than in `E2` (around cols 103–110). **[C]**

### 6.3 `F3` — Relay athletes

Example:

```
F3F 3422DoyleF1F 3417Mate F2F 3414MorteF3F 3415YoungF4
```

| Cols | Field | Conf | Notes |
|---|---|---|---|
| 1–2 | record code `F3` | C | |
| 3–… | up to 8 athlete slots, **13 chars each** | C | legs + alternates |

Each 13-char slot, starting at col 3:

| Offset in slot | Field | Notes |
|---|---|---|
| 1 | sex (`M`/`F`) | |
| 2 | (space) | |
| 3–6 | athlete number → `D1` | |
| 7–11 | last name, first 5 | |
| 12–13 | leg code | `F1`,`F2`,`F3`,`F4` for legs 1–4 |

Slots 5–8 (cols 55+) are reserved for alternates; blank in the sample.

---

## 7. `G1` — Splits

Example (and a continuation across two lines for an 800):

```
G1P 2   27.29P 4   56.68P 6   87.17P 8  117.91
G1F 2   26.04F 4   55.61 ... F22  328.23
G1F24  360.30F26  386.71F28  416.46F30  447.44F32  479.16
```

| Cols | Field | Conf | Notes |
|---|---|---|---|
| 1–2 | record code `G1` | C | |
| 3–… | up to **11 split blocks, 11 chars each** (stride confirmed) | C | |

Each 11-char block:

| Offset in block | Field | Notes |
|---|---|---|
| 1 | round (`P`/`F`) | matches the result |
| 2–3 | distance counter | **cumulative distance ÷ 25** (see below) |
| 4–11 | cumulative (elapsed) split time | total seconds |

**Distance unit = 25, in the course's distance unit.** The counter is
`cumulative_distance / 25`: validated against SDIF, e.g. an LCM 400 free has splits
at 50,100,…,400 m and the hy3 counters are `2,4,6,…,16` (×25 = the SDIF distance,
exactly). So splits land every 50 (counter steps of 2) in both yard and meter pools.
Split times matched SDIF on every real swim. Races with more than 11 splits
**continue on additional `G1` lines**. **[C]**

**hy3 vs SDIF split differences (representation, not data).** When comparing to
`.cl2`, expect two harmless divergences: (1) hy3 writes a `0.00` placeholder for split
points that weren't recorded by the timing system, whereas SDIF omits them; and
(2) hy3 records the **final cumulative distance** (the finish) as a split entry, so a
100 carries a `G1` block that SDIF leaves empty. **Drop zero-valued splits before
comparing** — after that, the real intermediate split times agree across all meets
tested.

---

## 8. `H1` / `H2` — Disqualification reason

Example:

```
H17AFalse start
H27ZOther - Misc
```

| Cols | Field | Conf | Notes |
|---|---|---|---|
| 1–2 | record code `H1` (primary) / `H2` (secondary) | C | |
| 3–4 | DQ code (matches `E2`/`F2` cols 14–15) | C | |
| 5–52 | reason text | C | |

### Enumerations

**Stroke** (`E1`/`F1` col 22) — **[C]**

| Code | Stroke | Relay |
|---|---|---|
| `A` | Freestyle | Free relay |
| `B` | Backstroke | |
| `C` | Breaststroke | |
| `D` | Butterfly | |
| `E` | Individual Medley | Medley relay |

**Course** — `Y`=SCY (25 yd), `L`=LCM (50 m), `S`=SCM (25 m). **All three
confirmed** across an SCY meet, an LCM meet, and a mixed SCY/LCM meet (the last also
carried `S` as a seed-time course). Note the distinct roles of the course bytes:
**`E2` col 12 = the event's course (authoritative)**; `E1` col 51 = course of the
meet-converted seed (= meet primary course); `E1` col 60 = course of the as-entered
seed. These coincide in single-course meets and diverge in mixed-course meets.

**Sex** — `M`, `F`, `X` (mixed). **Event sex** (`E1` col 15): `W`=women,
`M`=men, `X`=mixed.

**Round** (`E2`/`F2`/`G1` col 3) — `P`=Prelims, `F`=Finals (timed-finals also
emit `F`). `S` (swim-off) plausible but not observed.

**Result status flag** (`E2`/`F2` col 13) — decoded by cross-referencing the SDIF
result status for every matched swim in the LCM meet:

| Flag | SDIF status | Has time? | Meaning | Conf |
|---|---|---|---|---|
| `' '` | OK | yes | Normal swim | C |
| `Q` | DQ | **yes in hy3** | Disqualified; DQ code in cols 14–15 → `H1`. hy3 keeps the swum time; SDIF nulls it. | C |
| `D` | DNF | no (`0.00`) | Did Not Finish | C |
| `F` | NS | no (`0.00`) | No-show / scratch (likely declared/forfeit) | I |
| `R` | NS | no (`0.00`) | No-show / scratch (a second no-show variant; almost always NS) | I |
| `S` | OK | yes | Valid swim flagged specially — SDIF treats it as a normal result; the exact hy3 distinction (exhibition? swim-off? bonus?) is **unconfirmed** | ? |

The flag→SDIF-status mapping itself is **[C]** (exact cross-tab match: ` `→OK 3088,
`F`→NS 83, `S`→OK 82, `Q`→DQ 44, `R`→NS 31, `D`→DNF 1). The plain-English gloss for
`F`/`R`/`S` is inferred.

**DQ codes — read them from each file; do NOT rely on a fixed table. [C]**
The code→text mapping is **not a stable global enumeration**: different Meet Manager
versions ship different DQ-code dictionaries. The same code carries different text
across meets — e.g. `2C` was *"More than one arm pull while on breast"* in the 2016
MM5 file but *"Delay initiating turn"* in the pacswim files; `3D` was *"Downward
butterfly kick"* vs *"Arms past hipline"*. **The `H1`/`H2` records are the
authoritative text for their own file** — always use them rather than a lookup table.

What *is* stable is the **leading digit = stroke category**:

| Lead | Category | Example codes seen |
|---|---|---|
| `1` | Butterfly | `1A` alternating kick, `1F` arms underwater recovery, `1L` non-simultaneous touch |
| `2` | Backstroke | `2H` not on back off wall, `2L` shoulders past vertical, `2A` no touch at turn |
| `3` | Breaststroke | `3A` alternating kick, `3M` shoulders not past vertical, `3J` one-hand touch |
| `4` | Freestyle | `4K` no touch on turn |
| `5` | Individual Medley | `5B` out of sequence |
| `6` | Relay | `61`–`64` stroke infraction swimmer #1–4, `66`–`68` early take-off, `6Q` not enough swimmers |
| `7` | Misc / administrative | `7A` false start, `7C` did not finish, `7D` delay of meet, `7W` pulling on lane line |

(Note: this is Hy-Tek's DQ category numbering, **not** the SDIF stroke-code order.)
Across the test meets ~60 distinct codes appeared; the table above is illustrative.

---

## 9. Known gaps

Derived from 15 meets total (SCY, LCM, mixed, age-group, and championship). Still
unverified or absent:

- **`S` result-status flag** exact meaning — consistently maps to SDIF *OK* (valid
  time, 617 cases) but the hy3-specific distinction is unconfirmed; `F`/`R` (→ SDIF
  *NS*) glosses inferred.
- Numerous **single-byte flags** (`D1` col 69/88/105/125, `E1` cols 29–32/80–81/96,
  `E2` col 20 and the place-in-heat at 28–29) — present but not decoded.
- **`B2` configuration fields** (`010102Y1`, `10.00`, `S16-321`) — unidentified.
- **`C1` short-name / count** and **`C2`/`C3`** sub-field boundaries are approximate.
- Relay strokes beyond Free (`A`) and Medley (`E`) not observed.
- No diving, masters, or time-trial variants in the sample.
- Whether any hy3 file includes a **terminator record** — none of the 15 do.
- The **full DQ-code dictionary** is version-specific and not globally fixed (read
  `H1`/`H2` per file; only the leading-digit categories are stable).

**Validated with high confidence** (each meet diffed field-for-field against its SDIF
`.cl2`): the 130-char fixed-width structure; the **checksum** (100% of **~73,000
records** across 15 meets); the **complete record-code inventory** (no code outside
`A1 B1 B2 C1 C2 C3 D1 E1 E2 F1 F2 F3 G1 H1 H2` appeared in any meet); the record
hierarchy; athlete↔swim linkage; **all three course codes (`Y`/`L`/`S`)**; **`E2`
col 12 as the authoritative event course**; stroke/sex/round codes; **time = total
seconds**; the **two seed-time fields**; **heat (22–23) / lane (25–26) / place
(31–33)**; **split distance = counter × 25** and split times; the **status-flag →
SDIF-status** mapping; relay legs; and the DQ-code stroke categories. "No time"/"no
swim" entries are `0.00` in hy3 vs null/blank in SDIF.

---

## 10. Appendix — quick column reference

```
Record  Key fields (cols)
A1      type 3-4 | date 59-66 (MMDDYYYY) | time 67-74
B1      meet 3-47 | venue 48-92 | start 93-100 | end 101-108 | ageup 109-116
B2      meet 3-47 | host 48-92
C1      abbr 3-7 | name 8-37 | shortname 38-52 | LSC 54-55
C2      addr1 3-32 | addr2 33-62 | city 63-92 | state 93-94 | zip 95-104 | ctry 105-107
C3      name 3-32 | phone1 33-52 | phone2 53-72 | fax 73-92 | email 93-122
D1      sex 3 | num 5-8 | last 9-28 | first 29-48 | pref 49-68 | USAS-id 70-83 |
        dob 89-96 (MMDDYYYY) | age 98-99 | squad 100-101 | citizen 113-115
E1      sex 3 | num 5-8 | last5 9-13 | sex 14 | evsex 15 | dist 16-21 | stroke 22 |
        event# 25-28 | seed_conv 44-50 course 51 | seed_entered 53-59 course 60
E2      round 3 | time 5-11 | course 12 | status 13 | dqcode 14-15 |
        heat 22-23 | lane 25-26 | place_in_heat 28-29 | place 31-33 |
        backup1 38-44 | backup2 46-52 | date 88-95 (MMDDYYYY)
F1      team 3-6 | relay 8 | dist 19-21 | stroke 22 | event# 25-28 | seed 45-51 | course 52
F2      round 3 | time 6-11 | course 12 | status 13 | heat 22-23 | lane 25-26 |
        place 31-33 | date ~103-110 (MMDDYYYY)
F3      8×13-char slots from col 3: [sex(1) sp(1) num(4) last5(5) leg(2)]
G1      11×11-char blocks from col 3: [round(1) dist÷25 (2) cumtime(8)]
H1/H2   code 3-4 | text 5-52
all     time fields = total seconds (decimal, no colon); checksum 129-130
```

---

## 11. Validation against SDIF

This spec was checked by parsing each **`.cl2` (SDIF v3)** export with the independent
`tunas` SDIF parser, parsing the matching `.hy3` with a parser built from this spec,
and diffing the two record-for-record (joined on swimmer + event + session). Results
from the **LCM (Futures)** meet, with the **mixed SCY+LCM (WalkOn)** meet in the last
column:

| Check | LCM meet | Mixed meet |
|---|---|---|
| Record counts | 3406 ind + 213 relay = SDIF | 1094 ind = SDIF |
| Swimmer/event/session join | 3329 / 3406 | 1086 / 1094 |
| **Result time** | **100% of OK swims exact** | **100% of OK swims exact** (SCY 821 + LCM 265) |
| **Seed time** (cols 53–59) | 3328 / 3329 | 100% where a seed exists (13 "misses" = NT → `0.00`) |
| **Heat / Lane / Place** | 3169 / 3168 / 3157 of 3169 | **1018 / 1018 / 1018** |
| **Splits** (times) | every real swim; **dist = counter × 25** | every real swim |
| **Status flag → SDIF** | ` `→OK, `Q`→DQ, `D`→DNF, `F`/`R`→NS, `S`→OK | ` `→OK, `Q`→DQ, `F`/`R`→NS |
| **Relays** | 143/143 paired, **524/524 legs** | (no relays in meet) |

Unmatched joins in both meets are **SDIF first-name truncation** (`Chua, Min` vs hy3
`Min Zhi`; `Mutuc, Paolo` vs `Paolo Gabriel`), not data disagreement — hy3 preserves
*more* of the name.

The mixed meet specifically caught a first-draft error: taking the **event course from
`E1` col 51** (the seed-conversion course = meet primary, `Y`) mislabeled all 265 LCM
events until the parser was switched to **`E2` col 12**. It also confirmed **`S` = SCM**
(swimmer Mutuc's seeds were SCM times, e.g. `26.75S`, converting sensibly to `24.10Y`).

**Intentional hy3↔SDIF differences found:**

1. **DQ times** — hy3 records the actual swum time of a disqualified swim (cols 5–11);
   SDIF nulls it. Don't treat a hy3 DQ as having "no time."
2. **Seed time** — hy3 stores both the as-entered seed (cols 53–59, = SDIF) *and* a
   meet-course conversion (cols 44–50).
3. **Names** — hy3's wider name fields retain detail SDIF's packed `D0` truncates.
4. **Splits** — hy3 writes `0.00` for unrecorded split points and stores the finish as
   a split; SDIF omits both (see §7).

### 11a. 12-meet pacswim batch

A further 12 Pacific Swimming meets (downloaded from pacswim.org, spanning LCM/SCY Far
Western championships, age-group C/B/BB meets, and prelims/finals meets) were run
through the same diff. Aggregate over **28,705 swims that are OK in both files**:

| Check | Result |
|---|---|
| Record-code inventory | only the 15 documented codes appeared, in every meet |
| Checksum | **0 failures** across all 12 meets |
| **Result time** | 28,683 / 28,705 — the **22 misses are all same-name collisions** (two different swimmers sharing name+event+session in age-group divisions; the join key, not the data, is at fault) |
| Heat / Lane / Place | 28,692 / 28,686 / 28,587 of 28,705 (>99.5%) |
| Splits (zeros dropped) | 27,838 / 28,705; residual 867 are almost all 100/50s where hy3 keeps a finish-split that SDIF drops — representation, not data |
| Seed time | 27,037 / 27,056 |
| Status flag → SDIF | identical mapping at scale: `' '`→OK (28,705), `R`→NS (734), `S`→OK (617), `Q`→DQ (467), `F`→NS (90), `D`→DNF (6) |

**New findings from the batch (folded into this spec):**

- The **DQ code dictionary is version-specific** (§8) — ~60 distinct codes, with text
  for the same code differing from the 2016 MM5 file; only the leading-digit
  stroke categories are stable.
- The **record-code set is complete** — no new record type in any of 15 meets.
- Some `.cl2` exports are **partial/truncated** relative to their `.hy3` (e.g. one
  meet's cl2 had 30 of 954 swims; another 1044 of 1364). The `.hy3` carried the full
  results in every case — a point in favor of parsing hy3 when both exist.
