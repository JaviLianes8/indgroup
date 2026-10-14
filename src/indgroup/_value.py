"""Exact decimal text of an int, float or Decimal, with no rounding and no float drift."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TypeAlias

Number: TypeAlias = int | float | Decimal

DIGITS = re.compile(r"[0-9]+")


def split_value(value: object) -> tuple[bool, str, str]:
    """Sign, integer digits and fraction digits of ``value``, as written.

    A float is read through its shortest round-trip spelling (its ``repr``), so ``0.1`` is
    ``0.1`` and not the binary value it stands for. A Decimal keeps its exponent: trailing
    zeros and negative zero survive.
    """
    if isinstance(value, bool):
        raise TypeError("value must be an int, float or Decimal, not bool")
    if isinstance(value, int):
        text = int.__repr__(value)
    elif isinstance(value, float):
        text = _finite(Decimal(float.__repr__(value)))
    elif isinstance(value, Decimal):
        text = _finite(value)
    else:
        raise TypeError(f"value must be an int, float or Decimal, not {type(value).__name__}")
    negative = text.startswith("-")
    integer, _, fraction = text.removeprefix("-").partition(".")
    return negative, integer, fraction


def _finite(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError(f"value must be a finite number, not {value}")
    return format(value, "f")
