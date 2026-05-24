"""Swimmer member-ID helpers.

The 12-char legacy USS# is ``id_short``; the 14-char USSNUM is ``id_long``. We
never decode the date-of-birth embedded in the legacy USSNUM, and never fuzzy
match — identity is exact-string only.
"""

from __future__ import annotations

__all__ = ["normalize_id"]


def normalize_id(raw: str) -> str | None:
    """Strip an ID field to a clean token, or ``None`` if blank."""
    return raw.strip() or None
