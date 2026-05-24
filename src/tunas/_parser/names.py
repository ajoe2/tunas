"""Parse the SDIF NAME field (``Last, First MI``)."""

from __future__ import annotations

__all__ = ["parse_name"]


def parse_name(raw: str) -> tuple[str, str, str | None]:
    """Split a NAME field into ``(last_name, first_name, middle_initial)``.

    SDIF format is ``last name, first name [middle initial]``. A field with no
    comma is treated as an all-last-name value (``first_name`` empty).
    """
    text = raw.strip()
    if "," not in text:
        return text, "", None
    last, rest = text.split(",", 1)
    tokens = rest.split()
    if not tokens:
        return last.strip(), "", None
    first = tokens[0]
    middle = tokens[1][0] if len(tokens) > 1 and tokens[1] else None
    return last.strip(), first, middle
