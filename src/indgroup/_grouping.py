"""Indian lakh and crore digit grouping for integers and decimals."""

from __future__ import annotations

import re
from decimal import Decimal

_DIGITS = re.compile(r"\d+")


def _check_separator(separator: str) -> None:
    if len(separator) != 1 or separator.isdigit() or separator == ".":
        raise ValueError("separator must be a single non-digit character other than '.'")


def _group_integer(digits: str, separator: str) -> str:
    """Group the last three digits, then the rest in pairs from the right."""
    if len(digits) <= 3:
        return digits
    last, rest = digits[-3:], digits[:-3]
    groups = []
    while len(rest) > 2:
        groups.append(rest[-2:])
        rest = rest[:-2]
    if rest:
        groups.append(rest)
    groups.reverse()
    groups.append(last)
    return separator.join(groups)


def format_indian(value: int | Decimal, *, separator: str = ",") -> str:
    """Render ``value`` with Indian grouping, e.g. ``1234567`` -> ``"12,34,567"``.

    Only the integer part is grouped; any fractional part is kept as is.
    """
    _check_separator(separator)
    if isinstance(value, bool):
        raise TypeError("value must be an int or Decimal, not bool")
    if isinstance(value, int):
        text = str(value)
    elif isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("value must be a finite number")
        text = format(value, "f")
    else:
        raise TypeError("value must be an int or Decimal")

    negative = text.startswith("-")
    if negative:
        text = text[1:]
    integer, _, fraction = text.partition(".")
    result = ("-" if negative else "") + _group_integer(integer, separator)
    return f"{result}.{fraction}" if fraction else result


def parse_indian(text: str, *, separator: str = ",") -> int | Decimal:
    """Parse an Indian-grouped number back to an ``int`` or a ``Decimal``.

    A value with no fractional part returns an ``int``; otherwise a ``Decimal``.
    Western grouping and any other malformed input raise ``ValueError``.
    """
    _check_separator(separator)
    if not isinstance(text, str):
        raise TypeError("text must be a str")

    raw = text.strip()
    negative = raw.startswith("-")
    if raw[:1] in "+-":
        raw = raw[1:]
    integer, point, fraction = raw.partition(".")
    _validate_integer(integer, separator)
    if point and not _DIGITS.fullmatch(fraction):
        raise ValueError(f"not a valid fractional part: {fraction!r}")

    digits = integer.replace(separator, "")
    if not point:
        number = int(digits)
        return -number if negative else number
    sign = "-" if negative else ""
    return Decimal(f"{sign}{digits}.{fraction}")


def _validate_integer(part: str, separator: str) -> None:
    if _DIGITS.fullmatch(part):
        return
    sep = re.escape(separator)
    grouped = re.compile(rf"\d{{1,2}}(?:{sep}\d{{2}})*{sep}\d{{3}}")
    if not grouped.fullmatch(part):
        raise ValueError(f"not a valid Indian-grouped integer: {part!r}")
