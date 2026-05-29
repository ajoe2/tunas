# The Hy-Tek `.hy3` file format

`.hy3` is Hy-Tek's proprietary results format, the counterpart to the open [`.cl2` / SDIF v3](cl2_format.md) interchange format. Lacking an official public specification, this document provides a reverse-engineered specification of the format.

!!! note "Reference Documentation"
    This page is the field-level reference behind [`read_hy3`](../guide/parsing.md#read_hy3), which parses the fields documented here (those marked **C** for *confirmed* in the tables below) into the same [`Meet`](../guide/models.md) object graph as `read_cl2`.

### Specification Context
The details in this document are derived from empirical analysis of `.hy3` files and their corresponding SDIF `.cl2` files:
- **Pacific Swimming:** 14 seasons of public results (2013–2026, ~1,680 meets) comprising 7.9M records and 1,666 `.hy3`/`.cl2` pairs.
- **Michigan Swimming:** 425 meets comprising ~1.70 million records.

---

## 1. Relationship to SDIF / `.cl2`

The `.hy3` format is distinct from USA Swimming's open SDIF (`.cl2`/`.sd3`) format:

| Feature | SDIF (`.cl2`) | Hy-Tek (`.hy3`) |
|---|---|---|
| Record Length | 160 characters | 130 characters (128 data + 2 checksum) |
| Line Checksum | None | 2 trailing digits |
| Encoding | CP-1252 / ASCII | CP-1252 / ASCII |
| File Terminator | `Z0` record | None |

### Semantic Record Mapping

| `.hy3` Code | SDIF Code | Meaning |
|---|---|---|
| `A1` | `A0` | File / software description |
| `B1` | `B1` | Meet |
| `B2` | `B2` | Meet host |
| `C1` | `C1` | Team / club |
| `C2` | `C2` (part) | Team mailing address |
| `C3` | `C2` (part) | Team contact |
| `D1` | `D0`+`D3` (athlete part) | Athlete identity |
| `E1` | `D0` (entry part) | Individual event entry / seed |
| `E2` | `D0` (result part) | Individual event result |
| `F1` | `E0` (entry part) | Relay entry / seed |
| `F2` | `E0` (result part) | Relay result |
| `F3` | `F0` (×N) | Relay athletes (legs) |
| `G1` | `G0` | Splits |
| `H1`/`H2` | DQ code on result | Disqualification reason text |

Unlike SDIF—which packs athlete identity, entry, and result data into a single `D0` record—`.hy3` splits this information across three separate records: `D1` (athlete), `E1` (entry), and `E2` (result).

---

## 2. Physical Layout

- **Record Structure:** Fixed-width records, one per line, exactly 130 characters including data and checksum.
- **Line Terminator:** CRLF (`\r\n`).
- **Record Type (Columns 1–2):** 2-character code (e.g., `A1`, `B1`).
- **Data Fields (Columns 3–128):** Fixed-position, space-padded fields.
- **Line Checksum (Columns 129–130):** Two-digit checksum.
- **Encoding:** CP-1252 (single-byte). Keep raw bytes to preserve alignment when parsing accented characters.

All column ranges are 1-based and inclusive.

### Record Inventory

Distribution of record types across results files:

| Code | Record Type | Description |
|---|---|---|
| `A1` | File Description | Standard header (1 per file) |
| `B1` | Meet | Meet details (1 per file) |
| `B2` | Meet Host / Config | Host information (1 per file, optional) |
| `C1` | Team | Club/team registration |
| `C2` | Team Address | Club mailing address |
| `C3` | Team Contact | Club contact details |
| `D1` | Athlete | Swimmer registration details |
| `E1` | Individual Entry / Seed | Entry times and event metadata |
| `E2` | Individual Result | Swum times, placing, and status |
| `F1` | Relay Entry / Seed | Relay entry times and event metadata |
| `F2` | Relay Result | Relay times, placing, and status |
| `F3` | Relay Athletes | Relay swimmer lookup (legs 1–4 and alternates) |
| `G1` | Splits | Cumulative split times |
| `H1` | DQ Reason (Primary) | Primary disqualification text |
| `H2` | DQ Reason (Secondary) | Secondary disqualification text |
| `C8` | Team Block (Rare) | Undocumented, rare team-level record |

### File Variants

The `A1` file-type code (cols 3–4) indicates the file's primary purpose:
- `07`: Meet results (Standard)
- `04`: Merged meet results
- `17`: USAS Club Times Export (Does not contain meet results; does not use the standard results checksum)

---

## 3. Line Checksum (Columns 129–130)

Each record contains a 2-digit checksum computed over the raw bytes of the first 128 columns.

```python
def hy3_checksum(data: bytes) -> str:
    """Computes the 2-digit checksum for a 128-byte record (CP-1252 encoded)."""
    assert len(data) == 128
    sum_odd = sum(data[i] for i in range(0, 128, 2))   # 1-based odd positions
    sum_even = sum(data[i] for i in range(1, 128, 2))  # 1-based even positions
    result = (2 * sum_even + sum_odd) // 21 + 205
    tens, units = (result // 10) % 10, result % 10
    return f"{units}{tens}"   # Emitted in reverse order (units digit first)
```

### Calculation Steps

1. Sum the byte values at 1-based **odd** positions (cols 1, 3, 5, ..., 127).
2. Sum the byte values at 1-based **even** positions (cols 2, 4, 6, ..., 128).
3. Compute `result = (2 * sum_even + sum_odd) // 21 + 205` using integer division.
4. Extract the last two digits of `result` and reverse their order: the units digit is placed in column 129, and the tens digit in column 130.

> [!WARNING]
> Meet Manager computes the checksum over the file's raw single-byte (CP-1252) representation. To avoid validation mismatches on records containing accented characters or non-ASCII symbols, the checksum must be calculated on raw bytes rather than decoded Unicode string characters.

> [!NOTE]
> `USAS Club Times Export` files (type `17`) do not use this checksum algorithm.

---

## 4. File and Record Hierarchy

```
A1                              File description (1 per file)
B1                              Meet (1 per file)
B2                              Meet host (1 per file, optional)
(repeated per team:)
  C1                            Team
  C2                            Team address
  C3                            Team contact (optional)
  (repeated per athlete:)
    D1                          Athlete
    (repeated per individual swim:)
      E1                        Entry / seed
      E2                        Result
      G1                        Splits (0+ lines; long races span several lines)
      H1 [H2]                   DQ reason (only if the result was disqualified)
  (repeated per relay:)
    F1                          Relay entry / seed
    F2                          Relay result
    G1                          Splits
    F3                          Relay athletes (legs)
    H1 [H2]                     DQ reason (only if the relay was disqualified)
```

- **Linkage:** `E*` and `F3` records associate with their corresponding `D1` athlete using a 5-digit athlete number (cols 4–8) and appear sequentially after the athlete's `D1` record.
- **Disqualifications:** `H1`/`H2` DQ records follow the disqualified result record. The 2-character DQ code matches the code in `E2`/`F2` cols 14–15.
- **Termination:** The file has no terminator record and ends immediately after the last result-related record.

---

## 5. Individual / Common Records

### 5.1 `A1` — File Description

Example:
```
A107Results From MM to TM    Hy-Tek, Ltd    MM5 6.0De     12202016  6:52 AMFAST - CA
```

| Cols | Field | Conf | Description / Notes |
|---|---|---|---|
| 1–2 | Record Code | C | Constant `A1` |
| 3–4 | File/Result Type | C | `07` = Meet results, `04` = Merged meet results, `17` = Club times export |
| 5–29 | Description | C | Matches the type: `Results From MM to TM`, `Merge Meet Results`, etc. |
| 30–44 | Software Vendor | C | Constant `Hy-Tek, Ltd` |
| 45–58 | Software Name/Version | C | E.g., `MM5 8.0Fg` (Meet Manager 5, version and build) |
| 59–66 | Creation Date | C | `MMDDYYYY` format |
| 68–75 | Creation Time | C | `H:MM` format plus `AM`/`PM` (colon at col 70) |
| 76–128 | Licensee / Registered To | C | Organization or LSC name |

### 5.2 `B1` — Meet

Example:
```
B12016 CA December CA NV Speedo Sectionals     East Los Angeles College                     121620161219201612162016   0
```

| Cols | Field | Conf | Description / Notes |
|---|---|---|---|
| 1–2 | Record Code | C | Constant `B1` |
| 3–47 | Meet Name | C | Name of the meet (45 characters) |
| 48–92 | Facility / Location | C | Location of the meet (45 characters) |
| 93–100 | Start Date | C | `MMDDYYYY` format |
| 101–108 | End Date | C | `MMDDYYYY` format |
| 109–116 | Age-Up Date | C | `MMDDYYYY` format (determines competition age) |
| 117–120 | Altitude | C | Altitude in feet, right-justified |

### 5.3 `B2` — Meet Host

Example:
```
B22016 CA December CA NV Speedo Sectionals     Hosted by: SCS & FAST                        010102Y1 10.00  S16-321
```

| Cols | Field | Conf | Description / Notes |
|---|---|---|---|
| 1–2 | Record Code | C | Constant `B2` |
| 3–47 | Meet Name | C | Repeated meet name (often blank) |
| 48–92 | Host Text | I | Host details (often blank) |
| 93–98 | Config Codes | ? | Three 2-digit fields (e.g., `010102`) |
| 99 | Meet Course | C | Primary meet course: `Y` (SCY), `L` (LCM), `S` (SCM) |
| 100 | Course Flag | ? | Typically `1` |
| 102–106 | Base Entry Fee | I | Per-event entry fee or surcharge (`NN.NN` format) |
| 109–116 | Sanction Number | C | USA Swimming meet sanction number (typically `YY-NNN`, e.g., `16-321`) |

### 5.4 `C1` — Team

Example:
```
C1ARSC Arcadia Riptides              ARSC            CA
```

| Cols | Field | Conf | Description / Notes |
|---|---|---|---|
| 1–2 | Record Code | C | Constant `C1` |
| 3–7 | Team Abbreviation | C | 5-character team code (e.g., `ARSC`) |
| 8–37 | Team Name | C | Full team name (30 characters) |
| 38–53 | Short Team Name | I | 16-character abbreviated name |
| 54–55 | LSC Code | C | 2-letter Local Swim Committee code (e.g., `PC`, `CA`) |

`read_hy3` stores `Club.team_code` with the LSC prefix prepended (e.g. `PCARSC`), matching `read_cl2` whose SDIF `C1` already carries the prefixed code. The bare abbreviation is kept only when the LSC field is blank.
| 118, 119, 122 | Team Counts/Flags | ? | Undocumented small integers |

### 5.5 `C2` — Team Address

Example:
```
C2ARSC                          128 Fowler Drive              Monrovia                      CA91016     USA
```

| Cols | Field | Conf | Description / Notes |
|---|---|---|---|
| 1–2 | Record Code | C | Constant `C2` |
| 3–32 | Address Line 1 | I | Address line 1 or attention name |
| 33–62 | Address Line 2 | I | Street address |
| 63–92 | City | I | Team city |
| 93–94 | State | I | 2-letter state code |
| 95–104 | Postal Code | I | Postal code (up to 10 characters) |
| 105–107 | Country | I | 3-letter country code (e.g., `USA`) |

### 5.6 `C3` — Team Contact

Example:
```
C3                              6268406780          6268406780          6263580164          swimarcadia@gmail.com
```

| Cols | Field | Conf | Description / Notes |
|---|---|---|---|
| 1–2 | Record Code | C | Constant `C3` |
| 3–32 | Contact Name | I | Contact person's name |
| 33–52 | Phone 1 | I | Contact phone number 1 (left-justified) |
| 53–72 | Phone 2 | I | Contact phone number 2 |
| 73–92 | Fax | I | Contact fax number |
| 93–122 | Email | C | Contact email address |

### 5.7 `D1` — Athlete

Examples:
```
D1F 3420Allison             Bridgette                                033199BRIAALLI    003311999 17     0       USA         N
D1M 3008Lim                 Adrian              Adrian               082299ADR*LIM*    008221999 17SO   0                   N
```

| Cols | Field | Conf | Description / Notes |
|---|---|---|---|
| 1–2 | Record Code | C | Constant `D1` |
| 3 | Sex | C | Swimmer sex: `M` or `F` |
| 4–8 | Athlete Number | C | Unique in-file ID (5 digits, right-justified), links to `E*` and `F3` |
| 9–28 | Last Name | C | Athlete last name (20 characters) |
| 29–48 | First Name | C | Athlete first name (20 characters) |
| 49–68 | Preferred Name | C | Athlete preferred name (20 characters) |
| 69 | Middle Initial | C | Swimmer middle initial (blank if none) |
| 70–83 | USA-S Member ID | C | 14-character ID (see format notes below) |
| 85–88 | Secondary Index | I | Secondary tracking index, right-justified |
| 89–96 | Birth Date | C | `MMDDYYYY` format (blank in privacy-filtered files) |
| 98–99 | Age | C | Swimmer age in years (right-justified) |
| 100–101 | Grade/Class | I | Academic grade or class (e.g., `SR`, `JR`, `SO`, `FR`, or numeric grade) |
| 105 | Constant Flag | C | Constant `0` |
| 113–115 | Citizenship | C | Country code (e.g., `USA`, often blank) |
| 125 | Constant Flag | C | Constant `N` |

#### Member ID Formats
The USA Swimming member ID format varies by meet file generation era:
- **DOB-Based IDs:** Formatted as `MMDDYY` + first three characters of first name + middle initial + first four characters of last name (padded with `*` for short names, e.g., `033199BRIAALLI` or `082299ADR*LIM*`).
- **SWIMS IDs:** Modern files carry a 14-character randomized alphanumeric SWIMS ID (e.g., `9F58190E90084A`). Do not attempt to decode birth dates from these IDs.

#### Privacy Filtering (WODOB)
Many files are exported without date of birth (often designated by `-wodob` in filenames). In these cases, the birth date field (cols 89–96) is left entirely blank, and only the age field (cols 98–99) is populated.

### 5.8 `E1` — Individual Entry / Seed

Example:
```
E1F 3420AllisFW   200A  0109  0S 11.00 17   114.87Y  114.87Y    0.00    0.00   NN               N
```

| Cols | Field | Conf | Description / Notes |
|---|---|---|---|
| 1–2 | Record Code | C | Constant `E1` |
| 3 | Swimmer Sex | C | `M` or `F` |
| 4–8 | Athlete Number | C | 5-digit in-file ID linking back to `D1` |
| 9–13 | Last Name Prefix | C | First 5 characters of athlete's last name |
| 14 | Swimmer Sex | C | `M`, `F`, or `X` (Mixed) |
| 15 | Event Sex | C | Competition category: `W` (Women), `M` (Men), `G` (Girls), `B` (Boys), `X` (Mixed) |
| 16–21 | Event Distance | C | Distance in yards or meters, right-justified |
| 22 | Stroke Code | C | Stroke category: `A` (Free), `B` (Back), `C` (Breast), `D` (Fly), `E` (IM), `F`/`G` (Diving) |
| 23–25 | Event Min Age | C | Minimum event age, right-justified; `0` = no lower bound (e.g. "10 & Under") |
| 26–28 | Event Max Age | C | Maximum event age, right-justified; `109` = no upper bound (e.g. "11 & Over") |
| 31–32 | Time-Standard Class | I | Col 32 denotes the classification tier (e.g., `S` for Senior/Open, `A`, `B`, `U`) |
| 34–38 | Event Fee | ? | Event fee amount (`NN.NN` format) |
| 39–42 | Event Number | C | Event sequence number, right-justified |
| 44–50 | Converted Seed Time | C | Seed time converted to the meet's primary course (seconds as a decimal, e.g., `114.87`) |
| 51 | Converted Seed Course | C | Course code for converted seed time |
| 53–59 | Original Seed Time | C | Original entered seed time (seconds as a decimal, e.g., `114.87`) |
| 60 | Original Seed Course | C | Original entered course code |
| 64–68 | Extra Fee 1 | ? | Extra charge component (`NN.NN` format) |
| 72–76 | Extra Fee 2 | ? | Extra charge component (`NN.NN` format) |
| 77–78 | Division Code | I | Team division (e.g., `JV` or `VR` for high school meets) |
| 80–81 | Flags | ? | Undocumented characters (typically `NN`) |
| 97 | Exhibition Flag | ? | Typically `N`, occasionally `Y` |

#### Event Sex Coding
The event sex character (col 15) represents competition categorization conventions:
- `G` (Girls) / `B` (Boys): Typically used in age-group divisions.
- `W` (Women) / `M` (Men): Typically used in senior or open divisions.
- `X` (Mixed): Used for co-ed events.

#### Event Age Range
The event's age group is two right-justified integers: minimum age (cols 23–25) and maximum age (cols 26–28). Open-ended groups use sentinels — `0` for no lower bound and `109` for no upper bound — so `0`/`8` is "8 & Under", `11`/`109` is "11 & Over", and `0`/`109` is an open event. (Earlier revisions of this document mislabeled cols 25–28 as the event number; the event number is at cols 39–42.)

#### Springboard Diving Entries
For diving events, the stroke code is `F` (1-meter springboard) or `G` (3-meter springboard). The event distance field contains the required number of dives (typically `6` or `11`).

#### Time Representation
All times are represented in total seconds as a decimal without colons (e.g., `114.87` represents 1 minute and 54.87 seconds). Values can be converted to centiseconds via `round(seconds * 100)`. Swimmers entered with "No Time" (NT) are represented by a time value of `0.00`.

#### Seed Times and Course Mappings
`E1` records contain two seed time fields: the target meet course conversion (cols 44–50) and the original as-entered time (cols 53–59). In single-course meets, these values are identical. 

> [!WARNING]
> The `E1` record does not define the event's actual course. Col 51 is the course of the converted seed, and col 60 is the course of the as-entered seed. The authoritative course of the event itself is defined in **`E2` column 12**.

### 5.9 `E2` — Individual Result

Examples:
```
E2P  117.91Y       0 10  8  5 113  0  118.00  118.01    0.00       117.91     0.00     12182016
E2F   62.29YQ7A    0  2  4  0   0  0   62.39   62.32    0.00        62.29     0.00     12172016
```

| Cols | Field | Conf | Description / Notes |
|---|---|---|---|
| 1–2 | Record Code | C | Constant `E2` |
| 3 | Competition Round | C | `P` (Prelims), `F` (Finals/Timed-Finals), `S` (Swim-offs) |
| 5–11 | Result Time | C | Swum time in seconds (e.g., `117.91`). `0.00` if DNF, NS, or DQ |
| 12 | Authoritative Course | C | Authoritative event course code: `Y` (SCY), `L` (LCM), `S` (SCM) |
| 13 | Result Status Flag | C | Code indicating result status (see Status Flags under Section 8) |
| 14–15 | DQ Code | C | 2-character disqualification code (only populated if Status is `Q`) |
| 20 | Constant Flag | C | Constant `0` |
| 22–23 | Heat Number | C | Heat number in which the athlete swam |
| 25–26 | Lane Number | C | Lane number in which the athlete swam |
| 28–29 | Heat Place | I | Swimmer's finishing place within their heat |
| 31–33 | Overall Place | C | Swimmer's overall ranking in the event |
| 38–44 | Watch / Backup Time 1 | C | First manual watch time in seconds |
| 46–52 | Watch / Backup Time 2 | C | Second manual watch time in seconds |
| 54–60 | Watch / Backup Time 3 | C | Third manual watch time in seconds |
| 67–73 | Touch-Pad Time | I | Electronic touch-pad time in seconds (often matches Result Time) |
| 83 | Flag | ? | Undocumented (rarely `+`) |
| 88–95 | Swim Date | C | `MMDDYYYY` format |
| 96 | Undetermined Code | ? | Character enum `{blank, A, K, ?}` |

#### Result Disqualifications
If a swimmer is disqualified, the `E2` record retains the swum time in columns 5–11, whereas the corresponding SDIF record nulls the time.

---

## 6. Relay Records

### 6.1 `F1` — Relay Entry / Seed

Example:
```
F1ALPH A   0FFW   400E  0109  0S 24.00 11   243.30Y  243.30Y    0.00    0.00   NN   4           NA
```

| Cols | Field | Conf | Description / Notes |
|---|---|---|---|
| 1–2 | Record Code | C | Constant `F1` |
| 3–6 | Team Abbreviation | C | 4-character team abbreviation (e.g., `ALPH`) |
| 8 | Relay Designator | C | Alphabetical relay letter: `A`, `B`, `C`, etc. |
| 13–14 | Swimmer Sex | C | `M`, `F`, or `X` |
| 15 | Event Sex | C | Event category: `W`, `M`, `G`, `B`, `X` |
| 19–21 | Relay Distance | C | Total relay distance (e.g., `400`, `800`) |
| 22 | Relay Stroke Code | C | Stroke code: `A` (Freestyle Relay), `E` (Medley Relay) |
| 23–25 | Event Min Age | C | Minimum event age, right-justified; `0` = no lower bound |
| 26–28 | Event Max Age | C | Maximum event age, right-justified; `109` = no upper bound |
| 39–42 | Event Number | C | Event sequence number, right-justified |
| 44–50 | Converted Seed Time | C | Converted seed time in seconds |
| 51 | Converted Seed Course | C | Course code for converted seed time |
| 53–59 | Original Seed Time | C | Original entered seed time in seconds |
| 60 | Original Seed Course | C | Original entered course code |
| 85 | Number of Swimmers | C | Constant `4` |

### 6.2 `F2` — Relay Result

Example:
```
F2F  249.87Y       0  6  5  3  39  0  249.81  249.93    0.00       249.87     0.00                    12172016            0
```

The layout of the `F2` record is identical to the `E2` individual result record (with matching columns for round, status, heat, lane, place, watch times, and touchpad times) with the following exceptions:
- **Result Time:** Cols 6–11 (starts one column later than `E2`).
- **Course Code:** Col 12.
- **Relay Leg Exchanges:** Cols 83–102 hold four signed takeoff/leg exchange times in hundredths of a second (e.g., `+0.23`, `-0.05`).
- **Swim Date:** Cols 103–110 (`MMDDYYYY` format).
- **Undetermined Code:** Col 111 (equivalent to `E2` col 96 `{blank, A, K, ?}`).

### 6.3 `F3` — Relay Athletes

Example:
```
F3F 3422DoyleF1F 3417Mate F2F 3414MorteF3F 3415YoungF4
```

| Cols | Field | Conf | Description / Notes |
|---|---|---|---|
| 1–2 | Record Code | C | Constant `F3` |
| 3–15 | Swimmer Slot 1 | C | 13-character athlete description (Leg 1) |
| 16–28 | Swimmer Slot 2 | C | 13-character athlete description (Leg 2) |
| 29–41 | Swimmer Slot 3 | C | 13-character athlete description (Leg 3) |
| 42–54 | Swimmer Slot 4 | C | 13-character athlete description (Leg 4) |
| 55–128 | Alternate Slots | C | Up to 4 optional alternate slots (13 chars each) |

Each 13-character athlete slot is formatted as follows:

| Offset | Field | Description / Notes |
|---|---|---|
| 1 | Athlete Sex | Swimmer sex: `M` or `F` |
| 2–6 | Athlete Number | 5-digit in-file athlete ID linking back to `D1` |
| 7–11 | Last Name Prefix | First 5 characters of athlete last name |
| 12 | Event Round | Round letter matching the relay event (e.g., `F` or `P`) |
| 13 | Leg/Slot Number | Leg number `1` to `4` (or alternate indicator) |

---

## 7. `G1` — Splits

Examples:
```
G1P 2   27.29P 4   56.68P 6   87.17P 8  117.91
G1F 2   26.04F 4   55.61 ... F22  328.23
G1F24  360.30F26  386.71F28  416.46F30  447.44F32  479.16
```

- **Record Structure:** `G1` records contain up to 11 consecutive 11-character split blocks starting at column 3.
- **Continuation:** For long-distance events containing more than 11 split blocks, splits continue on subsequent `G1` records.

Each 11-character split block is structured as follows:

| Offset | Field | Description / Notes |
|---|---|---|
| 1 | Round Code | Round letter matching the result record (`P`, `F`, or `S`) |
| 2–3 | Distance Counter | Pool-length index from the start. Usually `counter × pool_length` (so `2` = 50, `4` = 100 in a 25-unit pool), but see the caveat below |
| 4–11 | Cumulative Time | Cumulative elapsed time in seconds |

> **Counter scale is not constant.** Most files index one counter unit per pool length (`× 25` in a short-course pool), but some timing systems record at half-length granularity, doubling the counter — e.g. a 200 SCY whose splits are at counters `4/8/12/16` (odd slots blank) rather than `2/4/6/8`. A blind `× 25` would then place the final split at 400 yards. Because a cumulative split can never exceed the event distance, resolve the per-counter unit by anchoring the *largest* counter in the swim to the event distance (halving the pool-length unit until the furthest counter fits). This also recovers the distance of a lone finishing split (a common DQ / relay-leadoff case).

### Differences relative to SDIF (`.cl2`) splits:
- `hy3` files populate a placeholder value of `0.00` for intermediate split points not recorded by the timing system, whereas SDIF omits these entries.
- `hy3` splits include the final race distance and finish time as the last split entry, whereas SDIF terminates splits before the final distance.
- Unlike SDIF—which carries an explicit per-record split increment—`hy3` only stores the length counter, so the per-counter distance must be inferred from the event distance (see the counter-scale caveat above).

---

## 8. Enumerations

### Stroke Codes (`E1`/`F1` column 22)

| Code | Stroke | Relay Type |
|---|---|---|
| `A` | Freestyle | Freestyle Relay |
| `B` | Backstroke | — |
| `C` | Breaststroke | — |
| `D` | Butterfly | — |
| `E` | Individual Medley | Medley Relay |
| `F` | 1-meter Springboard Diving | — |
| `G` | 3-meter Springboard Diving | — |

### Course Codes
- `Y`: Short Course Yards (SCY / 25 yards)
- `L`: Long Course Meters (LCM / 50 meters)
- `S`: Short Course Meters (SCM / 25 meters)

### Sex and Competition Category
- **Swimmer Sex:** `M` (Male), `F` (Female), `X` (Mixed/Co-ed)
- **Event Sex:** `W` (Women), `M` (Men), `G` (Girls), `B` (Boys), `X` (Mixed)

### Round Codes
- `P`: Prelims
- `F`: Finals / Timed-Finals
- `S`: Swim-off

### Result Status Flags (`E2`/`F2` column 13)

| Flag | Status | Time Populated? | Description |
|---|---|---|---|
| ` ` (blank) | OK | Yes | Normal, valid finish |
| `Q` | DQ | Yes | Disqualified. Swum time is retained; DQ code is populated in cols 14–15 |
| `D` | DNF | No (`0.00`) | Did Not Finish |
| `F` | NS | No (`0.00`) | No Show / Forfeit |
| `R` | NS | No (`0.00`) | No Show / Scratch (alternative variant) |
| `S` | Exhibition | Yes | Exhibition/Non-scoring swim. Reaches a valid time/place but does not score points |

### Disqualification Codes (`H1`/`H2` records)
DQ code mappings are not globally standardized and vary across different versions of Meet Manager. Complete DQ descriptions must be parsed directly from the `H1` and `H2` records inside the file. 

The first digit of the DQ code represents the stroke category:

| Lead Digit | Category | Example Code Meanings |
|---|---|---|
| `1` | Butterfly | `1A` alternating kick, `1F` underwater recovery, `1L` non-simultaneous touch |
| `2` | Backstroke | `2H` not on back off wall, `2L` shoulders past vertical |
| `3` | Breaststroke | `3A` alternating kick, `3J` one-hand touch |
| `4` | Freestyle | `4K` no touch on turn |
| `5` | Individual Medley | `5B` out of sequence |
| `6` | Relay | `61`–`64` stroke infraction swimmer 1–4, `66`–`68` early takeoff |
| `7` | Miscellaneous | `7A` false start, `7C` did not finish, `7W` pulling on lane line |

---

## 9. Known Gaps and Unresolved Fields

The following fields in the `.hy3` format are not represented in the SDIF format and remain unmapped or partially resolved:
- **Result Code (`E2` col 96 / `F2` col 111):** Contains `{blank, A, K, ?}`. The precise meaning is undetermined, though `K`/`?` entries correlate with a lack of backup watch times.
- **Meet Host Config (`B2` cols 93–98):** Triple 2-digit numeric block of undetermined config details. The third pair (cols 97–98) is a plausible candidate for a 2-digit meet-type code (`00`–`09`, `0A`–`0C`); the external [SwimComm/hytek-parser](https://github.com/SwimComm/hytek-parser) decodes it as such and reads a "masters" flag near cols 94–95. This is unverified against the SDIF cross-reference corpus (and the masters read straddles the field boundary), so it remains a gap here.
- **Team Registry Counts (`C1` cols 118, 119, 122):** Small integers tracking unverified team metrics.
- **Entry Surcharges (`E1` cols 34–38, 64–76):** Financial or administrative charge structures.
- **Record Structure `C8`:** A rare, near-empty team-block record type whose internal columns are undocumented.

---

## 10. Appendix — Quick Column Reference

```
Record  Key fields (cols)
A1      type 3-4 | desc 5-29 | vendor 30-44 | software 45-58 | date 59-66 (MMDDYYYY) |
        time 68-75 (H:MM AM/PM) | licensee 76-128
B1      meet 3-47 | venue 48-92 | start 93-100 | end 101-108 | ageup 109-116 |
        altitude(ft) 117-120
B2      meet 3-47 | host 48-92 | course 99 | amount 102-106 | sanction 109-116 (YY-NNN)
C1      abbr 3-7 | name 8-37 | shortname 38-53 | LSC 54-55 | counts 118/119/122
C2      addr1 3-32 | addr2 33-62 | city 63-92 | state 93-94 | zip 95-104 | ctry 105-107
C3      name 3-32 | phone1 33-52 | phone2 53-72 | fax 73-92 | email 93-122
D1      sex 3 | num 4-8 | last 9-28 | first 29-48 | pref 49-68 | middle-init 69 |
        member-id 70-83 | sec-idx 85-88 | dob 89-96 (MMDDYYYY, blank if WODOB) |
        age 98-99 | class 100-101 | citizen 113-115 | flags 105='0' 125='N'
E1      sex 3 | num 4-8 | last5 9-13 | sex 14 | evsex 15 | dist 16-21 | stroke 22 |
        agemin 23-25 (0=open) | agemax 26-28 (109=open) | event# 39-42 |
        seed_conv 44-50 course 51 | seed_entered 53-59 course 60 | team-level 77-78 (JV/VR)
E2      round 3 (P/F/S) | time 5-11 | course 12 | status 13 | dqcode 14-15 |
        heat 22-23 | lane 25-26 | place_in_heat 28-29 | place 31-33 |
        watch1 38-44 | watch2 46-52 | watch3 54-60 | date 88-95 (MMDDYYYY) | code96
F1      team 3-6 | relay 8 | evsex 15 | dist 19-21 | stroke 22 (A/E) |
        agemin 23-25 (0=open) | agemax 26-28 (109=open) | event# 39-42 |
        seed_conv 44-50 course 51 | seed_entered 53-59 course 60 | swimmers 85='4'
F2      round 3 | time 6-11 | course 12 | status 13 | heat 22-23 | lane 25-26 |
        place 31-33 | takeoffs ~83-102 | date 103-110 (MMDDYYYY) | code 111
F3      up to 8×13-char slots from col 3: [sex(1) num(5) last5(5) round(1) leg(1)]
G1      11×11-char blocks from col 3: [round(1) dist÷25 (2) cumtime(8)]
H1/H2   code 3-4 | text 5-52
all     time fields = total seconds (decimal, no colon); checksum 129-130 (over bytes)
```

---

## 11. Validation and Compatibility

### Field Cross-Validation
Crucial structural differences between `.hy3` and SDIF (`.cl2`) files include:
1. **DQ Times:** `.hy3` retains the actual swum time for disqualified swims, while SDIF nulls the result time.
2. **Seed Times:** `.hy3` holds both the original as-entered seed time and a meet-course converted time, whereas SDIF only stores the original as-entered seed.
3. **Names:** `.hy3` fields are wider and retain full names that SDIF frequently truncates.
4. **Splits:** `.hy3` encodes `0.00` placeholders for unrecorded intermediate splits and records the finish time as a split entry. SDIF omits both.
