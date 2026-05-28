"""SDIF name parsing helper."""

from __future__ import annotations

__all__ = ["parse_name"]


def parse_name(raw: str) -> tuple[str, str, str | None]:
    """Split an SDIF `Last, First MI` NAME field into `(last_name, first_name, middle_initial)`.

    Only the first comma separates last from first; the first whitespace token after it
    is the first name and the next token's leading letter is the middle initial. A field
    with no comma is treated as a bare last name (empty first name, no middle initial).
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
