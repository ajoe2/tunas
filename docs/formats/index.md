# File Format

Fixed-width formats for swim meet entries and results. `tunas` reads **SDIF v3 (`.cl2`)** with [`read_cl2`](../guide/parsing.md) and Hy-Tek **`.hy3`** with [`read_hy3`](../guide/parsing.md#read_hy3).

- **[SDIF (`.cl2`)](cl2_format.md)**: USA Swimming's open Standard Data Interchange Format v3, written by Hy-Tek Meet Manager and TeamUnify. A field-level reference for every record type (`A0`–`Z0`, including `D1`/`D2` registration and `J0`–`J2` time standards).
- **[Hy-Tek (`.hy3`)](hy3_format.md)**: the proprietary, reverse-engineered format from Hy-Tek Meet Manager and Team Manager. `read_hy3` parses the confirmed fields into the same object graph.

Both references document observed behavior, not just the published spec: deviations and reverse-engineered fields come from a corpus of Pacific Swimming (2013–2026) and Michigan Swimming files (**2,190 files, 6.35M records**), each with its observed occurrence rate.
