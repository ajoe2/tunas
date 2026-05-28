"""Unit tests for fixed-width field coercion helpers."""

from __future__ import annotations

import pytest

from tunas._parser.fields import decimal_value


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("1.5", ("dec", 1.5)),
        ("0", ("dec", 0.0)),
        ("-2.25", ("dec", -2.25)),
        ("", ("blank", None)),
        ("   ", ("blank", None)),
        ("abc", ("bad", None)),
        # Non-finite values are rejected rather than producing inf/nan floats.
        ("inf", ("bad", None)),
        ("-inf", ("bad", None)),
        ("Infinity", ("bad", None)),
        ("nan", ("bad", None)),
    ],
)
def test_decimal_value(raw: str, expected: tuple[str, float | None]) -> None:
    assert decimal_value(raw) == expected
