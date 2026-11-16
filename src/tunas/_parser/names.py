"""SDIF name parsing helper."""

from __future__ import annotations

__all__ = ["parse_name"]


def _is_initial(token: str) -> bool:
    if len(token) == 1:
        return token.isalpha()
    return len(token) == 2 and token[1] == "." and token[0].isalpha()


def parse_name(raw: str) -> tuple[str, str, str | None]:
    """Split an SDIF `Last, First [MI]` NAME field into `(last, first, middle_initial)`.

    Only the first comma splits. A trailing single-letter (optionally dotted) token is
    the middle initial (`Smith, John Q`); a trailing whole word stays in the first name
    (`Zhou, Melissa Hanlin`). No comma means a bare last name.
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
