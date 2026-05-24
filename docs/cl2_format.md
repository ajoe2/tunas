# The `.cl2` / SDIF v3 file format

`.cl2` files contain USA Swimming meet results formatted in **Standard Data Interchange Format version 3** (SDIF v3), actively used by systems like Hy-Tek Meet Manager.

`tunas` parses every record type in the meet-results portion of the spec. (Qualifying-time records `J0`/`J1`/`J2` surface as warnings.)

## High-level structure

A `.cl2` file consists of **fixed-width text records**, one per line. Each record is exactly 160 characters (excluding trailing CR/LF line endings) and starts with a 2-character **type code** defining its field layout.

Records appear in a hierarchical order:

```
A0                              File description (one per file)
  B1                            Meet
    B2                          Meet host (optional)
    C1                          Team / club
      C2                        Team entry — coach, counts (optional)
      D0                        Individual event result
        D1                      Individual administrative — phones, registration (optional, PII)
        D2                      Individual contact — mailing address (optional, PII)
        D3                      Long ID, preferred name (optional)
        G0                      Splits for the individual result (optional, multiple)
      E0                        Relay event result
        F0                      Relay name — one per swimmer on the relay (up to 4)
        G0                      Splits for the relay leg (optional, multiple)
Z0                              File terminator (one per file)
```

Each SDIF file normally contains one `B1` meet record, so `read_cl2` yields one `Meet` per file (or per `B1 ... Z0` block). Meets are independent; swimmers and clubs are derived strictly from their containing file. See [parsing.md](parsing.md#per-meet-scope).

## Record types

| Code | Name | Mandatory | What `tunas` does |
|---|---|---|---|
| `A0` | File description | Yes | Captured as `SourceFile` (file provenance). |
| `B1` | Meet record | Yes | Starts a `Meet`. |
| `B2` | Meet host record | Optional | Builds `Meet.host` (a `MeetHost`). |
| `C1` | Team ID record | At least one | Creates a `Club`, or marks the swimmer context unattached. |
| `C2` | Team entry record | Optional | Adds coach, phone, and entry counts to the current `Club`. |
| `D0` | Individual event entry/result | One per swim | Creates an `IndividualSwim` per session; resolves/creates the `Swimmer`. |
| `D1` | Individual administrative record | Optional | Populates `Swimmer.contact` / `Swimmer.registration` (PII). |
| `D2` | Individual contact record | Optional | Populates `Swimmer.contact` / `Swimmer.registration` (PII). |
| `D3` | Individual info record | Optional | Sets `id_long`, `preferred_first_name`, and demographics (`Swimmer.registration`). |
| `E0` | Relay event record | One per relay | Creates a `Relay` per session. |
| `F0` | Relay name record | Up to 4 (+ alternates) per relay | Appends a `RelaySwim` per session swum — to the relay's `legs` (counting legs) or `alternates`. |
| `G0` | Splits record | Optional, multiple | Appends `Split`s to the current `IndividualSwim` or relay leg (`RelaySwim`). |
| `Z0` | File terminator | Yes | Resets parser context; keeps any note on `SourceFile.notes`. |

Any 2-character header not in this table (including future SDIF revisions) is recorded as a `ParseWarning` rather than parsed.

## Sample

A minimal `.cl2` excerpt. **Field positions below are illustrative, not byte-accurate** — real records are whitespace-padded to the exact columns specified in the spec:

```
A01V3      02Meet Results                  Hy-Tek, Ltd ...
B11        Winter Champs                  ... 0101202501012025 ...
C11PC      PCSCSCSanta Clara Swim Club    ...
D01PC      Zhong, Irene  49AC52F69618A   1224201410FF  501  1 UNOV01012025 1:00.00L  33.71L  ...
D349AC52F6961843Irene ...
D01PC      Zhou, Kevin   CA025D306C5FA   0101201311MM  501  1 UN1201012025 1:00.00L  30.66L  ...
D3CA025D306C5F47Kevin ...
Z01Meet Res02Successful Build on 7/01/2024   1  1  12  12  ...
```

The fixed positions of every field within each record are specified in the official spec. `tunas` uses column-slice helpers under `_parser/fields.py` to extract them.

## Bundled spec

The authoritative SDIF v3 specification is shipped verbatim with the library (~65 KB plain text) at:

```
src/tunas/_data/sdif-v3.txt
```

## Historical notes

- **14-character USS# (USSNUM):** The 14-character member ID from `D3`/`F0` is stored verbatim in `id_long`. The DOB-based USSNUM format (e.g., `011553CATADURA`) is not decoded; birth dates are never inferred from an ID.
- **Encoding:** SDIF predates UTF-8. Real-world files are encoded in CP-1252 or ASCII. `tunas` defaults to `encoding="cp1252"` (with `errors="replace"`) to preserve column alignment and decode accented names correctly. Pass `encoding="utf-8"` if your source differs.
- **Line length:** Each record must be 160 characters (excluding trailing CR/LF). `tunas` right-pads shorter lines with spaces and warns only on over-long or otherwise unusable lines.

## Further reading

- USA Swimming SDIF v3 spec: see the bundled `sdif-v3.txt`.
- USA Swimming developer / SWIMS resources: <https://www.usaswimming.org>.

