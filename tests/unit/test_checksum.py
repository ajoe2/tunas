"""Unit tests for the Hy-Tek `.hy3` line checksum."""

from __future__ import annotations

import pytest

from tunas._parser.checksum import DATA_WIDTH, hy3_checksum


def test_checksum_known_record() -> None:
    # First A1 line from a real Pacific Swimming file; the file's checksum is "94".
    body = (
        "A107Results From MM to TM    Hy-Tek, Ltd    MM5 7.0Gb     "
        "01142024  7:11 PMCarson Tigersharks                                   "
    ).ljust(DATA_WIDTH)
    assert len(body) == DATA_WIDTH
    assert hy3_checksum(body.encode("cp1252")) == "94"


def test_checksum_wrong_length_raises() -> None:
    with pytest.raises(ValueError):
        hy3_checksum(b"too short")
