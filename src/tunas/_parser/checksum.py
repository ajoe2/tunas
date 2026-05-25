"""Hy-Tek `.hy3` record dimensions and line checksum.

Every `.hy3` record is 130 columns: 128 data columns plus a 2-digit checksum in
columns 129-130, computed over the raw single-byte (CP-1252) representation of the
first 128 columns. The parser does not validate the checksum (it isn't a data field
and `USAS Club Times Export` files omit it), but :func:`hy3_checksum` documents the
algorithm and is used to build byte-accurate test fixtures.
"""

from __future__ import annotations

__all__ = ["DATA_WIDTH", "RECORD_WIDTH", "hy3_checksum"]

DATA_WIDTH = 128  # columns 1-128 hold the data fields
RECORD_WIDTH = 130  # 128 data columns + a 2-digit checksum


def hy3_checksum(data: bytes) -> str:
    """Compute the 2-digit checksum for a 128-byte (CP-1252) record body."""
    if len(data) != DATA_WIDTH:
        raise ValueError(f"expected {DATA_WIDTH} bytes, got {len(data)}")
    sum_odd = sum(data[i] for i in range(0, DATA_WIDTH, 2))  # 1-based odd columns
    sum_even = sum(data[i] for i in range(1, DATA_WIDTH, 2))  # 1-based even columns
    result = (2 * sum_even + sum_odd) // 21 + 205
    tens, units = (result // 10) % 10, result % 10
    return f"{units}{tens}"  # emitted units digit first (reversed)
