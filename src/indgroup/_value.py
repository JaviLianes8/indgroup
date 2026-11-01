"""Exact decimal text of an int, float or Decimal, with no rounding and no float drift."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TypeAlias, cast

from ._bigint import to_decimal

Number: TypeAlias = int | float | Decimal

DIGITS = re.compile(r"[0-9]+")

# A bound on the digits written on each side of the decimal point, so that a hostile input
# cannot make a call build or convert text of any length (see _bigint for the conversions).
MAX_DIGITS = 100_000
_INT_LIMIT = 10**MAX_DIGITS


def input_size(text: str) -> str:
    """Length metadata only: rejected text may contain private data."""
    return f"({str.__len__(text)} characters)"


def too_long(part: str) -> ValueError:
    return ValueError(f"value has more than {MAX_DIGITS:,} digits in its {part}")


def split_value(value: object) -> tuple[bool, str, str]:
    """Sign, integer digits and fraction digits of ``value``, as written.

    A float is read through its shortest round-trip spelling (its ``repr``), so ``0.1`` is
    ``0.1`` and not the binary value it stands for, and a whole float has no fraction. A
    Decimal keeps its exponent: trailing zeros and negative zero survive. Methods of
    subclasses are never called, so they cannot change the digits.
    """
    kind = type(value)
    if kind is bool:
        raise TypeError("value must be an int, float or Decimal, not bool")
    from_float = False
    if issubclass(kind, int):
        integer_value = cast(int, value)
        if int.__abs__(integer_value) >= _INT_LIMIT:
            raise too_long("integer part")
        number = to_decimal(int.__int__(integer_value))  # past the 4300-digit limit of str
    elif issubclass(kind, float):
        number = Decimal(float.__repr__(cast(float, value)))
        from_float = True
    elif issubclass(kind, Decimal):
        number = cast(Decimal, value)
    else:
        raise TypeError("value must be an int, float or Decimal")
    if not Decimal.is_finite(number):
        special = "NaN" if Decimal.is_nan(number) else "an infinity"
        raise ValueError(f"value must be a finite number, not {special}")
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
