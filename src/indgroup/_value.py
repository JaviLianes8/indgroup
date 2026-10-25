"""Exact decimal text of an int, float or Decimal, with no rounding and no float drift."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TypeAlias

Number: TypeAlias = int | float | Decimal

DIGITS = re.compile(r"[0-9]+")

# A bound on the digits written on each side of the decimal point. Converting between int
# and Decimal takes quadratic time (a million digits take seconds), so longer values are
# refused instead of hanging the caller.
MAX_DIGITS = 100_000
_INT_LIMIT = 10**MAX_DIGITS

# Error messages quote at most this many characters of the text they reject.
_SHOWN = 40


def shown(text: str) -> str:
    """``repr`` of ``text``, cut to its first characters so a huge input stays out of messages."""
    text = str.__str__(text)
    if len(text) <= _SHOWN:
        return repr(text)
    return f"{text[:_SHOWN]!r}... ({len(text)} characters)"


def too_long(part: str) -> ValueError:
    return ValueError(f"value has more than {MAX_DIGITS:,} digits in its {part}")


def split_value(value: object) -> tuple[bool, str, str]:
    """Sign, integer digits and fraction digits of ``value``, as written.

    A float is read through its shortest round-trip spelling (its ``repr``), so ``0.1`` is
    ``0.1`` and not the binary value it stands for, and a whole float has no fraction. A
    Decimal keeps its exponent: trailing zeros and negative zero survive. Methods of
    subclasses are never called, so they cannot change the digits.
    """
    if isinstance(value, bool):
        raise TypeError("value must be an int, float or Decimal, not bool")
    from_float = False
    if isinstance(value, int):
        if int.__abs__(value) >= _INT_LIMIT:
            raise too_long("integer part")
        number = Decimal(value)  # no int-to-str conversion, so no 4300-digit limit
    elif isinstance(value, float):
        number = Decimal(float.__repr__(value))
        from_float = True
    elif isinstance(value, Decimal):
        number = value
    else:
        raise TypeError(f"value must be an int, float or Decimal, not {type(value).__name__}")
    if not Decimal.is_finite(number):
        kind = "NaN" if Decimal.is_nan(number) else "an infinity"
        raise ValueError(f"value must be a finite number, not {kind}")
    if not Decimal.is_zero(number) and Decimal.adjusted(number) >= MAX_DIGITS:
        raise too_long("integer part")
    exponent = Decimal.as_tuple(number).exponent
    if isinstance(exponent, int) and exponent < -MAX_DIGITS:
        raise too_long("fraction")
    text = Decimal.__format__(number, "f")
    negative = text.startswith("-")
    integer, _, fraction = text.removeprefix("-").partition(".")
    if from_float and fraction == "0":
        fraction = ""
    return negative, integer, fraction
