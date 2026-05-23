# The `.cl2` / SDIF v3 file format

`.cl2` files are USA Swimming meet result exports in the **Standard
Data Interchange Format version 3**, originally specified by USA
Swimming on April 28, 1998 and still in active use by Hy-Tek Meet
Manager and most other meet-management systems.

`tunas` parses every record type defined in the spec. This page is a
short tour of the format and a pointer to the bundled spec for
reference.

## High-level structure

A `.cl2` file is a sequence of **fixed-width text records**, one per
line, each exactly 162 bytes long (160 bytes of data + a 2-byte
checksum). Every record begins with a 2-character **type code** that
determines how its remaining 160 bytes are interpreted.

Records appear in a hierarchical order:

```
A0                              file description (one)
  B1                            meet
    B2                          meet host (optional)
    C1                          team / club
      C2                        team entry — coach, counts (optional)
      D0                        individual event result
        D1                      individual address (optional, PII)
        D2                      individual phone/email (optional, PII)
        D3                      long ID, preferred name (optional)
        G0                      splits for the individual result (optional, multiple)
      E0                        relay event result
        F0                      relay name — one per swimmer on the relay (up to 4)
        G0                      splits for the relay result (optional, multiple)
Z0                              file terminator (one)
```

A single file may contain multiple `B1 ... Z0` blocks (multiple meets).
A directory of `.cl2` files may contain the same swimmer across many
files; `read_cl2` merges them. See [parsing.md](parsing.md#multi-file-semantics).

## Record types

| Code | Name | Mandatory | What `tunas` does |
|---|---|---|---|
| `A0` | File description | Yes | Read for metadata; no domain object created. |
| `B1` | Meet record | Yes | Creates a `Meet`. |
| `B2` | Meet host record | Optional | Adds host fields to the current `Meet`. |
| `C1` | Team ID record | At least one | Creates a `Club` or marks the swimmer context unattached. |
| `C2` | Team entry record | Optional | Adds coach + entry counts to the current `Club`. |
| `D0` | Individual event entry/result | One per swim | Creates `IndividualMeetResult` and resolves/creates a `Swimmer`. |
| `D1` | Individual administrative record | Optional | Populates `swimmer_contact.address_*` (PII). |
| `D2` | Individual contact record | Optional | Populates `swimmer_contact.phone_*` / `email` (PII). |
| `D3` | Individual info record | Optional | Sets `usa_id_long` and `preferred_first_name` on the current `Swimmer`. |
| `E0` | Relay event record | One per relay | Creates `RelayMeetResult`. |
| `F0` | Relay name record | Up to 4 per relay | Appends a `RelayLeg`. |
| `G0` | Splits record | Optional, multiple | Appends `Split` entries to the current individual or relay result. |
| `Z0` | File terminator | Yes | Resets parser context. |

Forward-compatible: the parser silently ignores any 2-character header
not in this table, so future SDIF revisions that add new records won't
cause failures.

## Sample

A minimal but valid `.cl2` excerpt (whitespace-padded fixed-width
fields, abbreviated below for readability):

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

The fixed positions of every field within each record are specified in
the official spec (linked below). `tunas` uses small column-slice
helpers under `_parser/fields.py` to extract them.

## Bundled spec

The full SDIF v3 specification is shipped with the library at:

```
src/tunas/_data/sdif-v3.txt
```

It is a verbatim copy of the document published by USA Swimming. The
file is plain text (~65 KB) and is the authoritative source for the
exact byte layout of every record. Consult it if you're extending the
parser or debugging an unusual file.

## Historical notes

- **Older 14-character "USS#" IDs** (a.k.a. USSNUM): pre-2017, swimmer
  identifiers were derived from name + birthday. The parser recognizes
  the legacy format but does not store it as `usa_id_long` (which is
  reserved for the modern 14-character format). It also does not infer
  birthday from the legacy ID.
- **Encoding**: the spec predates UTF-8. Real-world files typically use
  CP-1252 or plain ASCII; `tunas` defaults to UTF-8 with
  `errors="replace"` so corrupt bytes don't fail the parse. Pass
  `encoding="cp1252"` if you're parsing very old files and want
  faithful decoding.
- **Checksums**: the trailing 2 bytes of each record are intended to be
  a checksum, but in practice many tools emit garbage there. `tunas`
  validates only the structural fields and ignores the checksum bytes.

## Further reading

- USA Swimming SDIF v3 spec: see the bundled `sdif-v3.txt`.
- Hy-Tek Meet Manager documentation (commercial; not bundled).
- USA Swimming developer / SWIMS resources: <https://www.usaswimming.org>.
