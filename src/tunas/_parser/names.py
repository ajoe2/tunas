"""SDIF name parsing helper."""

from __future__ import annotations

__all__ = ["parse_name"]


def _is_initial(token: str) -> bool:
    """True if ``token`` is a middle initial: a single letter, optionally dotted."""
    if len(token) == 1:
        return token.isalpha()
    return len(token) == 2 and token[1] == "." and token[0].isalpha()


def parse_name(raw: str) -> tuple[str, str, str | None]:
    """Split an SDIF `Last, First [MI]` NAME field into `(last_name, first_name, middle_initial)`.

    Only the first comma separates last from first; everything after it is the
    given name. A *trailing* single-letter (optionally dotted) token is the middle
    initial — e.g. `Smith, John Q` -> first `John`, middle `Q`. A trailing token
    that is a whole word is part of a compound first name, not an initial, so it
    stays in `first_name` — e.g. `Zhou, Melissa Hanlin` -> first `Melissa Hanlin`,
    no middle initial (rather than truncating "Hanlin" to "H"). A field with no
    comma is treated as a bare last name (empty first name, no middle initial).
    """
    text = raw.strip()
    if "," not in text:
        return text, "", None
    last, rest = text.split(",", 1)
    tokens = rest.split()
    if not tokens:
        return last.strip(), "", None
    if len(tokens) > 1 and _is_initial(tokens[-1]):
        return last.strip(), " ".join(tokens[:-1]), tokens[-1][0]
    return last.strip(), " ".join(tokens), None
