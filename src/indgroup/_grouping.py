"""Indian lakh and crore digit grouping for integers and decimals."""

from __future__ import annotations

from decimal import Decimal

from ._digits import group_digits, read_number
from ._value import Number, split_value

_SIZES = (3, 2)


def _check_separator(separator: object) -> str:
    if not isinstance(separator, str):
        raise TypeError(f"separator must be a str, not {type(separator).__name__}")
    if len(separator) != 1 or separator.isdigit() or separator in ".+-":
        raise ValueError("separator must be one character other than a digit, a sign or '.'")
    return separator


def format_indian(value: Number, *, separator: str = ",") -> str:
    """Render ``value`` with Indian grouping, e.g. ``1234567`` -> ``"12,34,567"``.

    Only the integer part is grouped; the fraction is kept digit for digit. A float is
    read through its shortest spelling, so ``0.1`` stays ``0.1``.
    """
    sep = _check_separator(separator)
    negative, integer, fraction = split_value(value)
    text = group_digits(integer, sep, *_SIZES, 1)
    if fraction:
        text = f"{text}.{fraction}"
    return f"-{text}" if negative else text


def parse_indian(text: str, *, separator: str = ",") -> int | Decimal:
    """Parse an Indian-grouped number back to an ``int`` or a ``Decimal``.

    A value with no fractional part returns an ``int``; otherwise a ``Decimal``.
    Western grouping and any other malformed input raise ``ValueError``.
    """
    sep = _check_separator(separator)
    return read_number(text, ".", sep, _SIZES, "-", "+")
