"""Swimmer member-ID normalization helper."""

from __future__ import annotations

__all__ = ["normalize_id"]


def normalize_id(raw: str) -> str | None:
    """Normalize an ID field, returning None if blank."""
    return raw.strip() or None
