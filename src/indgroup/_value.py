"""Exact decimal text of an int, float or Decimal, with no rounding and no float drift."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TypeAlias

Number: TypeAlias = int | float | Decimal

DIGITS = re.compile(r"[0-9]+")

# A bound on the integer digits written, so a value such as Decimal("1E+999999999") is refused
# instead of building a gigabyte of text.
MAX_DIGITS = 1_000_000


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
        number = Decimal(value)  # no int-to-str conversion, so no 4300-digit limit
    elif isinstance(value, float):
        number = Decimal(float.__repr__(value))
        from_float = True
    elif isinstance(value, Decimal):
        number = value
    else:
        raise TypeError(f"value must be an int, float or Decimal, not {type(value).__name__}")
    if not Decimal.is_finite(number):
        raise ValueError(f"value must be a finite number, not {Decimal.__str__(number)}")
    if Decimal.adjusted(number) >= MAX_DIGITS:
        raise ValueError(f"value has more than {MAX_DIGITS} integer digits")
    text = Decimal.__format__(number, "f")
    negative = text.startswith("-")
    integer, _, fraction = text.removeprefix("-").partition(".")
    if from_float and fraction == "0":
        fraction = ""
    return negative, integer, fraction
