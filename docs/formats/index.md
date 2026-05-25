# File Format

This section documents the fixed-width text formats used to distribute swim meet entries and results. `tunas` parses both **SDIF v3 (`.cl2`)** via [`read_cl2`](../guide/parsing.md) and the proprietary **Hy-Tek (`.hy3`)** format via [`read_hy3`](../guide/parsing.md#read_hy3).

### Supported Formats

- **[SDIF (`.cl2`)](cl2_format.md)** — The open **Standard Data Interchange Format v3** established by USA Swimming and produced by Hy-Tek Meet Manager and TeamUnify. This guide is a complete field-level reference (covering all record types `A0`–`Z0`, registration `D1`/`D2`, and time-standard `J0`–`J2` records) derived from the official spec.
- **[Hy-Tek (`.hy3`)](hy3_format.md)** — The proprietary, **reverse-engineered** results format used across Hy-Tek Meet Manager and Team Manager — the cross-validated sibling to `.cl2`. `read_hy3` parses the fields confirmed in this reference into the same object graph.

### Methodology

Both references document **empirically verified** behavior rather than just the published specifications. The deviations for `.cl2` and the reverse-engineering details for `.hy3` were derived from a large corpus of meet files from the Pacific Swimming (2013–2026) and Michigan Swimming LSCs, comprising **2,190 files and 6.35M records**. Every documented divergence lists its observed occurrence rate.
